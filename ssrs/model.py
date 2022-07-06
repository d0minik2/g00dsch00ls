from . import schools
from typing import Union, Dict, List, Type
import math
import numpy as np
import pandas as pd



class Student(schools.Student):
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
    def from_existing_student(cls, student: schools.Student):
        """Create comparable student from schools.Student class"""

        assert isinstance(student, schools.Student)

        return cls(
            exam_results=student.exam_results,
            grades=student.grades,
            liked_subjects=student.liked_subjects,
            location=student.location,
            weights_table=student.weights_table,
            school_type=student.school_type,
            additional_points=student.additional_points,
        )


class SchoolRecommendationModel:
    """Recommendation System for schools

    Calculates school ranking based on student preferences.

    Compares student attributes to attributes of schools,
    for each attribute computes ranking of best options
    and combines them into one ranking of best recommendations.
    """

    profiles_df: pd.DataFrame
    profiles: list[schools.Profile]

    def __init__(
            self,
            profiles: list[schools.Profile],
            recommendation_attributes=None
    ):
        """
        :param recommendation_attributes: dict of weights of recommendation attributes (if list, all weights are 1)
        """

        self.profiles = profiles
        self.__init_profiles_df(self.profiles)

        if recommendation_attributes is None:
            recommendation_attributes = {
                "mature_scores": 1,
                "extended_subjects": 1,
                "compare_points": 1,
                "school_type": 1
            }

        elif isinstance(recommendation_attributes, list):
            r = {}
            for attr in recommendation_attributes:
                r[attr] = 1

            recommendation_attributes = r

        self.recommendation_attributes = recommendation_attributes

    def __call__(self, *args, **kwargs) -> list[schools.Profile]:
        return self.recommend(*args, **kwargs)

    def __init_profiles_df(self, profiles: list[schools.Profile]):
        self.profiles_df = pd.DataFrame.from_dict(
            map(
                lambda profile: np.append(profile.array, [[0]]),
                profiles
            )
        )

    def __compare(self, attr: str, student: Student):
        """Compute recommendation ranking for specific attribute (attribute from recommendation sequence)"""

        # calculate ranking of schools for specific attribute
        recommendation_ranking = sorted(
            list(range(len(self.profiles_df))),
            key=lambda profile_idx: student.compare(self.profiles_df.values[profile_idx], attr)
        )

        for in_ranking, i in enumerate(recommendation_ranking):
            # add weighted ranking position to the last column of df row (needed to calculate average ranking index)
            self.profiles_df.at[i, self.profiles_df.columns[-1]] += in_ranking * self.recommendation_attributes[attr]

    def recommend(self, student: Union[schools.Student, Student], n=None) -> list[schools.Profile]:
        """Recommends schools for specific student"""

        self.__init_profiles_df(self.profiles)

        if type(student) is type(schools.Student):
            student = Student.from_existing_student(student)

        for attr in self.recommendation_attributes:
            self.__compare(attr, student)

        # calculate average recommendation ranking position
        self.profiles_df[self.profiles_df.columns[-1]] /= sum(self.recommendation_attributes.values())

        # sort initial indexes by average recommendation ranking position
        recommendation_ranking = sorted(
            range(len(self.profiles_df)),
            key=lambda profile_idx: self.profiles_df.values[profile_idx][-1]
        )

        for i in recommendation_ranking[:n]:
            yield self.profiles[i]
