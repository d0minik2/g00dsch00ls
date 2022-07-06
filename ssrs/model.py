
from . import r_profiles
from . import r_student

from typing import Union, Dict, List, Type
import math
import random
import numpy as np
import pandas as pd



class SchoolRecommendationModel:
    """Recommendation System for schools

    Calculates school ranking based on student preferences.

    Compares student attributes to attributes of schools,
    for each attribute computes ranking of best options
    and combines them into one ranking of best recommendations.
    """

    profiles_df: pd.DataFrame
    profiles: list[r_profiles.Profile]

    def __init__(
            self,
            profiles: list[r_profiles.Profile],
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

    def __call__(self, *args, **kwargs) -> list[r_profiles.Profile]:
        return self.recommend(*args, **kwargs)

    def __init_profiles_df(self, profiles: list[r_profiles.Profile]):
        self.profiles_df = pd.DataFrame.from_dict(
            map(
                lambda profile: np.append(profile.array, [[0]]),
                profiles
            )
        )

    def __compare(self, attr: str, student: r_student.ComparableStudent):
        """Compute recommendation ranking for specific attribute (attribute from recommendation sequence)"""

        # calculate ranking of schools for specific attribute
        recommendation_ranking = sorted(
            list(range(len(self.profiles_df))),
            key=lambda profile_idx: student.compare(self.profiles_df.values[profile_idx], attr)
        )

        for in_ranking, i in enumerate(recommendation_ranking):
            # add weighted ranking position to the last column of df row (needed to calculate average ranking index)
            self.profiles_df.at[i, self.profiles_df.columns[-1]] += in_ranking * self.recommendation_attributes[attr]

    def recommend(
            self,
            student: Union[r_student.Student, r_student.ComparableStudent],
            n=None
    ) -> list[r_profiles.Profile]:
        """Recommends schools for specific student"""

        random.shuffle(self.profiles)
        self.__init_profiles_df(self.profiles)

        if type(student) is type(r_student.Student):
            student = r_student.ComparableStudent.from_existing_student(student)

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
