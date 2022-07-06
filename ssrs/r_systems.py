from __future__ import annotations

from . import _profiles
from . import _student

from typing import Union, Dict, List, Type
import math
import random
import numpy as np
import pandas as pd



class RecommendationSystem:
    """Recommendation System, which is a function that takes a student and returns a ranking of schools"""

    scores: np.ndarray

    def __init__(self, model: SchoolRecommendationModel):
        self.model = model
        self.scores = np.zeros(len(self.model.profiles))

    def __call__(self, *args, **kwargs):
        return self.recommend(*args, **kwargs)

    def _compare(self, student: r_student.ComparableStudent):
        """Compute recommendation scores for specific student"""

    def recommend(self, student: r_student.ComparableStudent) -> list[r_profiles.Profile]:
        """Recommends schools for specific student"""

        self.scores = np.zeros(len(self.model.profiles))

        # for each attribute in recommendation sequence compute ranking
        for attr in self.model.recommendation_attributes:
            self._compare(attr, student)

        # calculate average recommendation score
        self.model.profiles_df[self.model.profiles_df.columns[-1]] /= sum(self.model.recommendation_attributes.values())

        # sort initial indexes by average score
        recommendation_ranking = sorted(
            range(len(self.model.profiles_df)),
            key=lambda profile_idx: self.scores[profile_idx]
        )

        return recommendation_ranking


class RankingSystem(RecommendationSystem):
    """Recommendation System, which recommendations are calculated by comparing student and profile attributes,
        for each attribute computes ranking of best options and combines them into one ranking of best recommendations.
    """

    def _compare(self, attr: str, student: r_student.ComparableStudent):
        """Compute recommendation ranking for specific attribute (attribute from recommendation sequence)"""

        # calculate ranking of schools for specific attribute
        recommendation_ranking = sorted(
            list(range(len(self.model.profiles_df))),
            key=lambda profile_idx: student.compare(
                self.model.profiles_df.values[profile_idx], attr
            )
        )

        for in_ranking, i in enumerate(recommendation_ranking):
            # add weighted ranking position to the last column of df row (needed to calculate average ranking index)
            self.scores[i] += in_ranking \
                              * self.model.recommendation_attributes[attr] \
                              * student.attributes_preferences.get(attr, 1)


class NormalizationSystem(RecommendationSystem):
    """Recommendation System, which recommendations are calculated by comparing student and profile attributes,
        for each attribute computes normalized score and combines them into one recommendation ranking."""

    def _compare(self, attr: str, student: r_student.ComparableStudent):
        """Compute recommendation ranking for specific attribute (attribute from recommendation sequence)"""

        # compare student and profile attributes
        compared = self.model.profiles_df.apply(
            lambda profile: student.compare(profile, attr),
            axis=1
        ).to_numpy(dtype=np.float64)

        # add weighted normalized score to the last column of df (needed to calculate average later)
        self.scores += NormalizationSystem.zscore_normalize(compared) \
                       * self.model.recommendation_attributes[attr] \
                       * student.attributes_preferences.get(attr, 1)

    @staticmethod
    def zscore_normalize(values: Union[List, np.ndarray]) -> Union[List, np.ndarray]:
        """Normalize values to z-score."""

        if isinstance(values, np.ndarray):
            return (values - values.mean()) / np.std(values)

        elif isinstance(values, list) or isinstance(values, tuple):
            mean = sum(values) / len(values)
            sum_of_differences = sum((value - mean) ** 2 for value in values)
            standard_deviation = (sum_of_differences / (len(values) - 1)) ** .5

            return [(value - mean) / standard_deviation for value in values]