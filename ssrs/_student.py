
from . import _profiles
from .config import *

from typing import Union, Dict, List, Type
import numpy as np
import pandas as pd
from dataclasses import dataclass, field



@dataclass
class Student:
    """Student attributes class

    Parameters
    ----------

    exam_results: dict[str: float] or np.ndarray - results of exams
    liked_subjects: list[str] or dict[str: float] - subjects that student likes
    grades: list[str] or dict[str: float] - grades that student scored
    additional_points: float - additional points that student scored (for achievements, volunteering, etc.)
    attributes_perferences: dict[str: float] - student's recommendation attributes preferences
    location: str - student's address
    school_type: int - student's school type (0 - liceum, 1 - techinkum, 2 - szkoła zawodowa)
    """

    exam_results: Union[Dict[str, float], np.ndarray]
    grades: Union[Dict[str, int], np.ndarray]
    liked_subjects: Union[List, Dict, np.ndarray]
    location: str = ""
    attributes_preferences: dict = field(default_factory=dict)
    school_type: int = 1  # desired student's school type
    additional_points: int = 0  # points for achievements, volunteering, etc.
    _base_points = 0
    _subject_points = np.array([])

    def __post_init__(self):
        # mapping subjects to arrays
        self.liked_subjects = _profiles.map_subjects(self.liked_subjects)
        self.grades = _profiles.map_subjects(self.grades)
        self._calculate_base_points()

        if not isinstance(self.exam_results, np.ndarray):
            self.exam_results = np.array(list(self.exam_results.values()))

        # calculating points for grades that will be used when calculating points for profiles
        self._subject_points = np.vectorize(_profiles.calculate_grade_points)(self.grades)

        # TODO set location to jakdojade object (if i get an API access)

    def _calculate_base_points(self):
        """Calculating base points, that cannot change depending on the profile"""

        # adding DIPLOMA_HONORS_POINTS if GPA is greater or equal than required GPA
        if self.grades[MIN_GRADE <= self.grades].mean() >= DIPLOMA_HONORS_GPA:
            self._base_points += DIPLOMA_HONORS_POINTS

        if isinstance(self.exam_results, dict):
            # if exam results are in dict, adding points for each exam result

            self._base_points += POLISH_EXAM_WEIGHT * self.exam_results["polish"]
            self._base_points += MATH_EXAM_WEIGHT * self.exam_results["math"]
            self._base_points += ENGLISH_EXAM_WEIGHT * self.exam_results["english"]

        else:
            # if exam results are in array, adding points for each exam result

            self._base_points += POLISH_EXAM_WEIGHT * self.exam_results[0]
            self._base_points += MATH_EXAM_WEIGHT * self.exam_results[1]
            self._base_points += ENGLISH_EXAM_WEIGHT * self.exam_results[2]

        self._base_points += self.additional_points

    def calculate_points(self, profile) -> float:
        """Calculating points for given profile"""

        points_for_subjects = 0

        if isinstance(profile, np.ndarray):
            assert profile[4].size == len(SUBJECTS), \
                ValueError("The scored grades attribute should be at index 4 of the array")

            points_for_subjects = (profile[4] * self._subject_points).sum()

        elif isinstance(profile, _profiles.Profile):
            points_for_subjects = (profile.scored_subjects * self._subject_points).sum()

        return self._base_points + points_for_subjects


class StudentCalculator:
    """Compares student to profiles and calculates the score (compare score: less - better)"""

    def __call__(self, *args, **kwargs):
        return self.compare(*args, **kwargs)

    @staticmethod
    def compare(student: Student, profile: np.ndarray, attr: str) -> float:
        """Compare student's and profile's attributes
        Returns the score (float value), less - better

        Parameters
        ----------
        profile: np.ndarray - attributes of the profile
        attr: str - attribute to compare (available: school_type, mature_scores, extended_subjects, compare_points)
        """

        if isinstance(profile, pd.Series):
            profile = profile.to_numpy()

        result = student_calculator_options[attr](student, profile)

        if isinstance(result, tuple):
            return result[0]

        return result

    @staticmethod
    def compare_school_type(student: Student, profile: np.ndarray):
        """Compare school type to desired school type of the student, less - better"""

        return abs(student.school_type - profile[0])

    @staticmethod
    def compare_mature_scores(student: Student, profile: np.ndarray):
        """Compare mature scores to student's exam results, less - better"""

        return abs(student.exam_results - profile[1]).mean()

    @staticmethod
    def compare_extended_subjects(student: Student, profile: np.ndarray):
        """Compare extended subjects to subjects liked by a student, less - better"""

        return 1 / (1 + (student.liked_subjects * profile[2]).sum())

    @staticmethod
    def compare_points(student: Student, profile: np.ndarray):
        """Compare student's and profile's points, less - better"""

        points_for_profile = student.calculate_points(profile)

        if profile[3][0] > points_for_profile:
            # comparing to minimum profile points

            return abs(profile[3][0] - points_for_profile),

        else:
            # comparing to average profile points

            return abs(profile[3][1] - points_for_profile)


student_calculator_options = {
    "school_type": StudentCalculator.compare_school_type,
    "mature_scores": StudentCalculator.compare_mature_scores,
    "extended_subjects": StudentCalculator.compare_extended_subjects,
    "compare_points": StudentCalculator.compare_points,
}
