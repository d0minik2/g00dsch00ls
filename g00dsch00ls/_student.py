from .config import *

from abc import ABC, abstractmethod
from typing import Union, Dict, List, Type
import numpy as np
import pandas as pd
from dataclasses import dataclass, field



class Student(ABC):
    """Student class
    Contains student's attributes (data).

    Subclasses usage
    ----------------

    If you want to use your own type of profiles data and student attributes,
    create subclass of this class, which contains your own student's
    parameters. Then, you need to create StudentCalculator subclass that will compare this student class and profiles.

    Example class:
    class MyStudent(g00dsch00ls.Student):
        def __init__(
            self,
            exam_results: dict
            grades: dict
            liked_subjects: list
        )
            self.exam_results = exam_results
            ...

    (Tip: you can use dataclasses)
    """


class StudentCalculator(ABC):
    """Calculates score for each student attribute.
    Used in recommendation system to compare student and profile attributes.

    Subclasses usage
    ----------------

    If you want to use your own student or profile attributes, you need to create a subclass of StudentCalculator
    (or first create Student subclass, which contains your own student's parameters),
    which contains your compare functions (used in recommendation system to compare profiles and students).

    To add new comparison method, create a method that starts with "compare_"
    and takes student and profile as parameters.
    The method should return a float value, less - better (higher position in ranking).

    Example class:
    class MyStudentCalculator(g00dsch00ls.StudentCalculator):
        def compare_school_type(self, student: MyStudent, profile: pandas.Series) -> float:
            ...
            return score

    Then the method is contained in self.compare_options dictionary and class can be used in recommendation system.
    """

    compare_options: dict[str, callable]

    def __init__(self):
        self.compare_options = {
            key: func
            for key, func in self.__class__.__dict__.items()
            if key.startswith("compare_")
        }

    def __call__(self, *args, **kwargs):
        return self.compare(*args, **kwargs)

    def compare(self, student: Student, profile: Union[np.ndarray, pd.Series], attr: str) -> float:
        """Compare student's and profile's attributes
        Returns the score (float value), less - better

        Parameters
        ----------
        profile: np.ndarray - attributes of the profile
        attr: str - attribute to compare (must be in self.compare_options)
        """

        assert attr in self.compare_options, f"Attribute {attr} is not in compare_options. " \
                                             f"Available attributes: {self.compare_options.keys()}"

        result = self.compare_options[attr](self, student, profile)

        if isinstance(result, tuple):
            return result[0]

        return result



@dataclass
class PLStudent(Student):
    """Student attributes class
    Contains student's attributes (data) that are used in education system in Poland.

    Parameters
    ----------

    exam_results: dict[str: float] or np.ndarray - results of exams
    liked_subjects: list[str] or dict[str: float] - subjects that student likes
    grades: list[str] or dict[str: float] - grades that student scored
    additional_points: float - additional points that student scored (for achievements, volunteering, etc.)
    attributes_prrferences: dict[str: float] - student's recommendation attributes preferences
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

    def __post_init__(self):
        self._calculate_base_points()

        if not isinstance(self.exam_results, np.ndarray):
            self.exam_results = np.array(list(self.exam_results.values()))

        # TODO set location to jakdojade object (if i get an API access)

    def _calculate_base_points(self):
        """Calculating base points, that cannot change depending on the profile"""

        # adding DIPLOMA_HONORS_POINTS if GPA is greater or equal than required GPA
        grades = self.grades
        zachowanie = 5
        if grades.get("zachowanie") is not None:
            zachowanie = grades.pop("zachowanie")
        if sum(grades.values()) / sum(v > 0 for v in grades.values()) >= DIPLOMA_HONORS_GPA and zachowanie >= 5:
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

    def calculate_points(self, profile: pd.Series) -> float:
        """Calculating points for given profile"""

        assert isinstance(profile, pd.Series), "Profile must be a pandas.Series"

        points_for_subjects = 0

        for subject, grade in self.grades.items():
            if profile["scored_subjects"] is not np.NaN:
                if subject in profile["scored_subjects"]:
                    points_for_subjects += PLStudent.calculate_grade_points(grade)

        return self._base_points + points_for_subjects

    @staticmethod
    def calculate_grade_points(grade: int, scores=POINTS_FOR_GRADES) -> int:
        """Calculating points for grades"""

        return scores[int(grade)]


class PLStudentCalculator(StudentCalculator):
    """Compares student to profiles and calculates the score (compare score: less - better)
    Student must be a PLStudent object.
    """

    def compare(self, student: PLStudent, profile: pd.Series, attr: str) -> float:
        assert isinstance(student, PLStudent), \
            "Student must be a PLStudent object, if you want to use custom Student object, " \
            "you must use custom StudentCalculator class."
        return super(PLStudentCalculator, self).compare(student, profile, attr)

    def compare_school_type(self, student: PLStudent, profile: pd.Series):
        """Compare school type to desired school type of the student, less - better"""

        return abs(student.school_type - profile["school_type"])

    def compare_mature_scores(self, student: PLStudent, profile: pd.Series):
        """Compare mature scores to student's exam results, less - better"""

        return abs(
            student.exam_results - np.array(
                [profile["matura_polish"], profile["matura_math"], profile["matura_english"]]
            )
        ).mean()

    def compare_extended_subjects(self, student: PLStudent, profile: pd.Series):
        """Compare extended subjects to subjects liked by a student, less - better"""

        subjects_sum = 0
        for subj, val in student.liked_subjects.items():
            if subj in profile["subjects"]:
                subjects_sum += val
                continue
            subjects_sum -= .2

        return 1 / max(subjects_sum, 1e-5)

    def compare_points(self, student: PLStudent, profile: pd.Series):
        """Compare student's and profile's points, less - better"""

        points_for_profile = student.calculate_points(profile)

        if profile["min_points"] > points_for_profile:
            # comparing to minimum profile points

            return abs(profile["min_points"] - points_for_profile),

        else:
            # comparing to average profile points

            return abs(profile["avg_points"] - points_for_profile) * .8
