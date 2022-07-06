#!/usr/bin/python3
# -*- coding: utf-8 -*-

from . import r_profiles
from . import r_student

from typing import Union, Dict, List, Type
import math
import random
import numpy as np
import pandas as pd



RANKING_MODE = 0
NORMALIZATION_MODE = 1



class Model:
    """Recommendation System for schools
    Calculates school ranking based on student preferences.
    Call that model with student object and number of schools to recommend to get recommended schools.

    Modes
    -----

    Two modes are available:
    - RANKING_MODE: (0) recommendations are calculated by comparing student and profile attributes,
        for each attribute computes ranking of best options and combines them into one ranking of best recommendations.
    - NORMALIZATION_MODE: (1) recommendations are calculated by comparing student and profile attributes,
        for each attribute computes normalized score and combines them into one recommendation ranking.

    Parameters
    ----------

    profiles: list of Profile objects to be recommended
    recommendation_attributes: dict of weights of recommendation attributes (if list, all weights are 1)
    mode: mode of recommendation system
    """

    profiles_df: pd.DataFrame
    profiles: list[r_profiles.Profile]

    def __init__(
            self,
            profiles: list[r_profiles.Profile],
            recommendation_attributes=None,
            mode=RANKING_MODE
    ):
        self.profiles = profiles
        self._init_profiles_df(self.profiles)

        if recommendation_attributes is None:
            # if no recommendation attributes are given, use all attributes with weight 1
            recommendation_attributes = {
                "mature_scores": 1,
                "extended_subjects": 1,
                "compare_points": 1,
                "school_type": 1
            }

        elif isinstance(recommendation_attributes, list):
            # if recommendation attributes are given as list, use all attributes with weight 1
            recommendation_attributes = {attr: 1 for attr in recommendation_attributes}

        self.recommendation_attributes = recommendation_attributes
        self.mode = mode

    def __call__(self, *args, **kwargs) -> list[r_profiles.Profile]:
        return self.recommend(*args, **kwargs)

    def _init_profiles_df(self, profiles: list[r_profiles.Profile]):
        # create dataframe with profile attributes and last column for recommendation score
        self.profiles_df = pd.DataFrame.from_dict(
            map(
                lambda profile: np.append(profile.array, [[0]]),
                profiles
            )
        )

    def _compare_by_ranking(self, attr: str, student: r_student.ComparableStudent):
        # calculate ranking of schools for specific attribute
        recommendation_ranking = sorted(
            list(range(len(self.profiles_df))),
            key=lambda profile_idx: student.compare(
                self.profiles_df.values[profile_idx], attr
            )
        )

        for in_ranking, i in enumerate(recommendation_ranking):
            # add weighted ranking position to the last column of df row (needed to calculate average ranking index)
            self.profiles_df.at[i, self.profiles_df.columns[-1]] += \
                in_ranking * self.recommendation_attributes[attr] * student.attributes_preferences.get(attr, 1)

    def _compare_by_normalization(self, attr: str, student: r_student.ComparableStudent):
        # compare student and profile attributes
        compared = self.profiles_df.apply(
            lambda profile: student.compare(profile, attr),
            axis=1
        ).to_numpy(dtype=np.float64)

        # add weighted normalized score to the last column of df (needed to calculate average later)
        self.profiles_df[self.profiles_df.columns[-1]] += \
            zscore_normalize(compared) * self.recommendation_attributes[attr] * student.attributes_preferences.get(attr, 1)

    def _compare(self, attr: str, student: r_student.ComparableStudent):
        """Compute recommendation ranking for specific attribute (attribute from recommendation sequence)"""

        if self.mode == RANKING_MODE:
            self._compare_by_ranking(attr, student)

        elif self.mode == NORMALIZATION_MODE:
            self._compare_by_normalization(attr, student)

    def recommend(
            self,
            student: Union[r_student.Student, r_student.ComparableStudent],
            n=None
    ) -> list[r_profiles.Profile]:
        """Recommends schools for specific student"""

        random.shuffle(self.profiles)
        self._init_profiles_df(self.profiles)

        # if Student is not ComparableStudent, convert it to ComparableStudent
        if not isinstance(student, r_student.ComparableStudent) and isinstance(student, r_student.Student):
            student = r_student.ComparableStudent.from_existing_student(student)

        # for each attribute in recommendation sequence compute ranking
        for attr in self.recommendation_attributes:
            self._compare(attr, student)

        # calculate average recommendation score
        self.profiles_df[self.profiles_df.columns[-1]] /= sum(self.recommendation_attributes.values())

        # sort initial indexes by average score
        recommendation_ranking = sorted(
            range(len(self.profiles_df)),
            key=lambda profile_idx: self.profiles_df.values[profile_idx][-1]
        )

        # yield top n schools
        for i in recommendation_ranking[:n]:
            yield self.profiles[i]



def zscore_normalize(values: Union[List, np.ndarray]) -> Union[List, np.ndarray]:
    """Normalize values to z-score."""

    if isinstance(values, np.ndarray):
        return (values - values.mean()) / np.std(values)

    elif isinstance(values, list) or isinstance(values, tuple):
        mean = sum(values) / len(values)
        sum_of_differences = sum((value - mean) ** 2 for value in values)
        standard_deviation = (sum_of_differences / (len(values) - 1)) ** .5

        return [(value - mean) / standard_deviation for value in values]
