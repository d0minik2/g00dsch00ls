import schools
from typing import Union, Dict, List, Type
import math
import numpy as np
import pandas as pd



def normalize(x, x_min=0, x_max=1):
    return (x - x_min) / (x_max - x_min)


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

        return normalize(
            abs(self.school_type - profile[0]),
            x_min=schools.MIN_SCHOOL_TYPE,
            x_max=schools.MAX_SCHOOL_TYPE
        )

    def compare_mature_scores(self, profile: np.ndarray):
        """Compare mature scores to student's exam results (probably won't gonna work well), less - better"""

        return normalize(
            abs(self.exam_results - profile[1]).mean(),
            x_max=100
        )

    def compare_extended_subjects(self, profile: np.ndarray):
        """Compare extended subjects to subjects liked by a student, less - better"""

        return 1 / (1 + (self.liked_subjects * profile[2]).sum())

    def compare_points(self, profile: np.ndarray):
        """Compare student's and profile's points, less - better"""

        points_for_profile = self.calculate_points(profile)

        if profile[3][0] > points_for_profile:
            # comparing to minimum profile points

            return normalize(
                (profile[3][0] - points_for_profile),
                x_max=200
            )

        else:
            # comparing to average profile points

            return normalize(
                abs(profile[3][1] - points_for_profile),
                x_max=200
            )

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
            __base_points=student.__base_points,
            __subject_points=student.__subject_points
        )


class SchoolRecommendationModel:
    profiles_df: pd.DataFrame
    profiles: list[schools.Profile]

    def __init__(
            self,
            profiles: list[schools.Profile],
            recommendation_sequence=["school_type", "mature_scores", "extended_subjects", "compare_points"]
    ):
        self.profiles = profiles
        self.__create_profiles_df(self.profiles)
        self.recommendation_sequence = recommendation_sequence

    def __call__(self, *args, **kwargs) -> list[schools.Profile]:
        return self.recommend(*args, **kwargs)

    def __create_profiles_df(self, profiles: list[schools.Profile]):
        self.profiles_df = pd.DataFrame.from_dict(
            map(lambda profile: np.append(profile.array, [[0]]),
                profiles)
        )

    def __compare(self, attr: str, student: Student):
        """Compute recommendation ranking for specific attribute (attribute from recommendation sequence)"""

        recommendation_ranking = sorted(
            list(range(len(self.profiles_df))),
            key=lambda profile_idx: student.compare(self.profiles_df.values[profile_idx], attr)
        )

        for in_ranking, i in enumerate(recommendation_ranking):
            self.profiles_df.at[i, self.profiles_df.columns[-1]] += in_ranking

    def recommend(self, student: Union[schools.Student, Student], n=None) -> list[schools.Profile]:
        """Return first n recommendations for student"""

        if type(student) is type(schools.Student):
            student = Student.from_existing_student(student)

        for attr in self.recommendation_sequence:
            self.__compare(attr, student)

        # calculate average recommendation ranking position
        self.profiles_df[self.profiles_df.columns[-1]] /= (len(self.recommendation_sequence))

        recommendation_ranking = sorted(
            range(len(self.profiles_df)),
            key=lambda profile_idx: self.profiles_df.values[profile_idx][-1]
        )

        for i in recommendation_ranking[:n]:
            yield self.profiles[i]

