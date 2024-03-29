from __future__ import annotations

from . import _student

from abc import ABC, abstractmethod
from typing import Union, Dict, List, Type
import math
import random
import numpy as np
import pandas as pd



class RecommendationSystem(ABC):
    """Recommendation System, which is a function that takes a student and returns a ranking of schools"""

    scores: np.ndarray

    def __init__(self, model: model.G00dSch00ls, **kwargs):
        self.model = model
        self.scores = np.zeros(len(self.model.profiles_df))

    def __call__(self, *args, **kwargs):
        return self.recommend(*args, **kwargs)

    @abstractmethod
    def _compare(self, student: _student.Student, *args, **kwargs) -> None:
        """Compute recommendation scores for specific student or attribute (adds result to self.scores)"""

    @abstractmethod
    def recommend(self, student: _student.Student) -> list[int]:
        """Recommends schools for specific student,
        returns list of indices, where indices are sorted by recommendation score"""



class AverageRankingSystem(RecommendationSystem):
    """Recommendation System, which recommendations are calculated by comparing student and profile attributes,
        for each attribute computes ranking of best options and combines them into one ranking of best recommendations.
    """

    def __init__(self, model: model.G00dSch00ls, **kwargs):
        super().__init__(model, **kwargs)

        self.student_calculator = kwargs.get("student_calculator", _student.PLStudentCalculator)()

        recommendation_attributes = kwargs.get(
            "recommendation_attributes",
            # if no recommendation attributes are given, use all available attributes with weight 1
            {attr: 1 for attr in self.student_calculator.compare_options}
        )

        if isinstance(recommendation_attributes, list):
            # if recommendation attributes are given as list, use all attributes with weight 1
            recommendation_attributes = {attr: 1 for attr in recommendation_attributes}

        self.recommendation_attributes = recommendation_attributes

    def _compare(self, attr: str, student: _student.Student):
        """Compute recommendation ranking for specific attribute (attribute from recommendation sequence)"""

        # calculate ranking of schools for specific attribute
        recommendation_ranking = sorted(list(range(len(self.model.profiles_df))),
                                        key=lambda profile_idx: self.student_calculator.compare(
                                            student, self.model.profiles_df.iloc[profile_idx], attr
                                        ))

        student_preference = getattr(student, "attributes_preferences", 1)
        if student_preference != 1:
            student_preference = student_preference.get(attr, 1)

        for in_ranking, i in enumerate(recommendation_ranking):
            # add weighted ranking position to the last column of df row (needed to calculate average ranking index)
            self.scores[i] += in_ranking \
                              * self.recommendation_attributes[attr] \
                              * student_preference

    def recommend(self, student: _student.Student) -> list[int]:
        """Recommends schools for specific student"""

        self.student_calculator.check_data_correctness(self.model.profiles_df.iloc[0])
        self.scores = np.zeros(len(self.model.profiles_df))

        # for each attribute in recommendation sequence compute ranking
        for attr in self.recommendation_attributes:
            self._compare(attr, student)

        # calculate average recommendation score
        self.scores /= sum(self.recommendation_attributes.values())

        # sort initial indexes by average score
        recommendation_ranking = sorted(range(len(self.model.profiles_df)),
                                        key=lambda profile_idx: self.scores[profile_idx])

        return recommendation_ranking


class NormalizationSystem(RecommendationSystem):
    """Recommendation System, which recommendations are calculated by comparing student and profile attributes,
        for each attribute computes normalized score and combines them into one recommendation ranking."""

    def __init__(self, model: model.G00dSch00ls, **kwargs):
        super().__init__(model, **kwargs)

        self._init_normalizer(kwargs.get("normalizer", NormalizationSystem.zscore_normalize))

        self.student_calculator = kwargs.get("student_calculator", _student.PLStudentCalculator)()

        recommendation_attributes = kwargs.get(
            "recommendation_attributes",
            # if no recommendation attributes are given, use all available attributes with weight 1
            {attr: 1 for attr in self.student_calculator.compare_options}
        )

        if isinstance(recommendation_attributes, list):
            # if recommendation attributes are given as list, use all attributes with weight 1
            recommendation_attributes = {attr: 1 for attr in recommendation_attributes}

        self.recommendation_attributes = recommendation_attributes

    def _init_normalizer(self, normalizer: Union[callable, str]):
        """Initialize normalizer function"""

        if isinstance(normalizer, str):
            if normalizer == "z-score":
                self.normalizer = NormalizationSystem.zscore_normalize
            elif normalizer == "linear_scaling":
                self.normalizer = NormalizationSystem.linear_scaling_normalize
            else:
                raise f"Unknown normalizer {normalizer}"

        if callable(normalizer):
            self.normalizer = normalizer

        else:
            raise f"Unknown normalizer {normalizer}"

    @staticmethod
    def linear_scaling_normalize(values: Union[np.ndarray, list]) -> Union[np.ndarray, list]:
        """Normalize values to range 0-1
                x′ = (x − x[m i n]) / (x[m a x] − x[m i n])
        """

        if isinstance(values, np.ndarray):
            return (values - np.min(values)) / (np.max(values) - np.min(values))

        if isinstance(values, list):
            _max = max(values)
            _min = min(values)

            return [(value - _min) / (_max - _min) for value in values]

    @staticmethod
    def zscore_normalize(values: Union[List, np.ndarray]) -> Union[List, np.ndarray]:
        """Normalize values to z-score

                x′ = (x − x[m i n]) / σ
        """

        if isinstance(values, np.ndarray):
            return (values - values.mean()) / np.std(values)

        elif isinstance(values, list) or isinstance(values, tuple):
            mean = sum(values) / len(values)
            sum_of_differences = sum((value - mean) ** 2 for value in values)
            standard_deviation = (sum_of_differences / (len(values) - 1)) ** .5

            return [(value - mean) / standard_deviation for value in values]

    def _compare(self, attr: str, student: _student.Student):
        """Compute recommendation ranking for specific attribute (attribute from recommendation sequence)"""

        # compare student and profile attributes
        compared = self.model.profiles_df.apply(
            lambda profile: self.student_calculator.compare(student, profile, attr),
            axis=1
        ).to_numpy(dtype=np.float64)
        compared[np.isnan(compared)] = 1

        student_preference = getattr(student, "attributes_preferences", 1)
        if student_preference != 1:
            student_preference = student_preference.get(attr, 1)

        # add weighted normalized score to the last column of df (needed to calculate average later)
        self.scores += self.normalizer(compared) \
                       * self.recommendation_attributes[attr] \
                       * student_preference

    def recommend(self, student: _student.Student) -> list[int]:
        """Recommends schools for specific student"""

        self.student_calculator.check_data_correctness(self.model.profiles_df.iloc[0])
        self.scores = np.zeros(len(self.model.profiles_df))

        # for each attribute in recommendation sequence compute ranking
        for attr in self.recommendation_attributes:
            self._compare(attr, student)

        # calculate average recommendation score
        self.scores /= sum(self.recommendation_attributes.values())

        # sort initial indexes by average score
        recommendation_ranking = sorted(range(len(self.model.profiles_df)),
                                        key=lambda profile_idx: self.scores[profile_idx])

        return recommendation_ranking

