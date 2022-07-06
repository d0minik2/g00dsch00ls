
from . import r_profiles
from .school_poperties import *

from typing import Union, Dict, List, Type
import numpy as np
from dataclasses import dataclass, field



@dataclass
class Student:
    """Student attributes class"""

    exam_results: Union[Dict[str, float], np.ndarray]
    grades: Union[Dict[str, int], np.ndarray]
    liked_subjects: Union[List, np.ndarray]
    location: str = ""
    weights_table: np.ndarray = np.array([])
    school_type: int = 1  # desired student's school type
    additional_points: int = 0  # points for achievements, volunteering, etc.
    __base_points = 0
    __subject_points = np.array([])

    def __post_init__(self):
        # mapping subjects to arrays
        self.liked_subjects = r_profiles.map_subjects(self.liked_subjects)
        self.grades = r_profiles.map_subjects(self.grades)
        self.__calculate_base_points()
        self.exam_results = np.array(list(self.exam_results.values()))

        # calculating points for grades that will be used when calculating points for profiles
        self.__subject_points = np.vectorize(r_profiles.calculate_grade_points)(self.grades)

        # TODO set location to jakdojade object (if i get an API access)

    def __calculate_base_points(self):
        """Calculating base points, that cannot change depending on the profile"""

        # adding DIPLOMA_HONORS_POINTS if GPA is greater or equal than required GPA
        if self.grades[MIN_GRADE <= self.grades].mean() >= DIPLOMA_HONORS_GPA:
            self.__base_points += DIPLOMA_HONORS_POINTS

        # adding points for exams
        self.__base_points += POLISH_EXAM_WEIGHT * self.exam_results["polish"]
        self.__base_points += MATH_EXAM_WEIGHT * self.exam_results["math"]
        self.__base_points += ENGLISH_EXAM_WEIGHT * self.exam_results["english"]

        self.__base_points += self.additional_points

    def calculate_points(self, profile) -> float:
        points_for_subjects = 0

        if isinstance(profile, np.ndarray):
            assert profile[4].size == len(SUBJECTS), \
                ValueError("The scored grades attribute should be at index 4 of the array")

            points_for_subjects = (profile[4] * self.__subject_points).sum()

        elif isinstance(profile, r_profiles.Profile):
            points_for_subjects = (profile.scored_subjects * self.__subject_points).sum()

        return self.__base_points + points_for_subjects


class ComparableStudent(Student):
    """Student, that can be compared to profiles (compare score: less - better)"""

    def __call__(self, *args, **kwargs):
        return self.compare(*args, **kwargs)

    def compare(self, profile: np.ndarray, attr: str):
        options = {
            "school_type": self.compare_school_type,
            "mature_scores": self.compare_mature_scores,
            "extended_subjects": self.compare_extended_subjects,
            "compare_points": self.compare_points,
        }

        return options[attr](profile)

    def compare_school_type(self, profile: np.ndarray):
        """Compare school type to desired school type of the student, less - better"""

        return abs(self.school_type - profile[0])

    def compare_mature_scores(self, profile: np.ndarray):
        """Compare mature scores to student's exam results (probably won't gonna work well), less - better"""

        return abs(self.exam_results - profile[1]).mean()

    def compare_extended_subjects(self, profile: np.ndarray):
        """Compare extended subjects to subjects liked by a student, less - better"""

        return 1 / (1 + (self.liked_subjects * profile[2]).sum())

    def compare_points(self, profile: np.ndarray):
        """Compare student's and profile's points, less - better"""

        points_for_profile = self.calculate_points(profile)

        if profile[3][0] > points_for_profile:
            # comparing to minimum profile points

            return abs(profile[3][0] - points_for_profile),

        else:
            # comparing to average profile points

            return abs(profile[3][1] - points_for_profile)

    @classmethod
    def from_existing_student(cls, student: Student):
        """Create comparable student from schools.Student class"""

        assert isinstance(student, Student)

        return cls(
            exam_results=student.exam_results,
            grades=student.grades,
            liked_subjects=student.liked_subjects,
            location=student.location,
            weights_table=student.weights_table,
            school_type=student.school_type,
            additional_points=student.additional_points,
        )
