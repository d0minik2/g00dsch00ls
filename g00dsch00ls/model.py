#!/usr/bin/python3
# -*- coding: utf-8 -*-


from . import _profiles
from . import _student
from . import r_systems

from typing import Union, Dict, List, Type
import math
import random
import numpy as np
import pandas as pd



RANKING_MODE = 1
NORMALIZATION_MODE = 2

MODES = {
    RANKING_MODE: r_systems.RankingSystem,
    NORMALIZATION_MODE: r_systems.NormalizationSystem
}



class SchoolRecommendationModel:
    """Recommendation System for schools
    Calculates school ranking based on student preferences.
    Call that model with student object and number of schools to recommend to get recommended schools.

    Modes (systems)
    ---------------

    You can use multiple recommendation systems in one model, by using binary numbers to specify which systems to use
    (sum numbers of systems to get system combination). For example, if you want to use both ranking (1) and
    normalization (2) systems, you can use mode 3 (ranking + normalization), if you want to use only ranking system,
    you can use mode 1 (ranking). You can also use list or tuple of modes to specify multiple systems.
    Recommendation of multiple systems is done by averaging rankings of each system.

    Two modes are available:
    - RANKING_MODE: (1) recommendations are calculated by comparing student and profile attributes,
        for each attribute computes ranking of best options and combines them into one ranking of best recommendations.
    - NORMALIZATION_MODE: (2) recommendations are calculated by comparing student and profile attributes,
        for each attribute computes normalized score and combines them into one recommendation ranking.

    Parameters
    ----------

    profiles: list of Profile objects to be recommended
    system: mode of recommendation system
    system_kwargs: dict of arguments for recommendation system
    """

    profiles_df: pd.DataFrame
    profiles: list[_profiles.Profile]
    systems: list[r_systems.RecommendationSystem]

    def __init__(
            self,
            profiles: list[_profiles.Profile],
            system=NORMALIZATION_MODE,
            system_kwargs=None
    ):
        if system_kwargs is None:
            system_kwargs = {}

        self.profiles = profiles
        self.system = system

        self._init_systems(self.system, system_kwargs)
        self._init_profiles_df(self.profiles)

    def __call__(self, *args, **kwargs) -> list[_profiles.Profile]:
        return self.recommend(*args, **kwargs)

    def _init_profiles_df(self, profiles: list[_profiles.Profile]):
        # create dataframe with profile attributes and last column for recommendation score
        self.profiles_df = pd.DataFrame.from_dict(
            map(
                lambda profile: np.append(profile.array, [[0]]),
                profiles
            )
        )

    def _init_systems(self, mode: Union[int, list, tuple], system_kwargs: dict):
        """Initialize recommendation systems"""

        # create list of recommendation systems based on mode
        systems = []

        if isinstance(mode, int):
            # decompose mode into binary numbers and create recommendation systems
            i = 1
            while i <= mode:
                if i & mode:
                    systems.append(MODES[i](self, **system_kwargs))
                i <<= 1

        elif isinstance(mode, list) or isinstance(mode, tuple):
            # create recommendation systems from list of modes

            if all(isinstance(m, int) for m in mode):
                # if all modes are integers, create recommendation systems from them
                systems = []
                for m in mode:
                    systems.append(MODES[m](self, **system_kwargs))

            elif all(issubclass(m, r_systems.RecommendationSystem) for m in mode):
                # if all modes are recommendation systems, create them
                systems = [m(self, **system_kwargs) for m in mode]

        elif issubclass(mode, r_systems.RecommendationSystem):
            # if mode is recommendation system, create it
            systems = [mode(self, **system_kwargs)]

        self.systems = systems

    def _compare(self, system: r_systems.RecommendationSystem, student: _student.StudentCalculator):
        """Compute recommendation ranking for system"""

        recommendation_ranking = system(student)

        for in_ranking, i in enumerate(recommendation_ranking):
            # add ranking position to the last column of df row (needed to calculate average ranking index)
            self.profiles_df.at[i, self.profiles_df.columns[-1]] += in_ranking

    def recommend(
            self,
            student: Union[_student.Student, _student.StudentCalculator],
            n=None
    ) -> list[_profiles.Profile]:
        """Recommends schools for specific student"""

        random.shuffle(self.profiles)
        self._init_profiles_df(self.profiles)

        # for each system in recommendation systems compute ranking
        for system in self.systems:
            self._compare(system, student)

        # calculate average recommendation score
        self.profiles_df[self.profiles_df.columns[-1]] /= len(self.systems)

        # sort initial indexes by recommendation score
        recommendation_ranking = sorted(
            range(len(self.profiles_df)),
            key=lambda profile_idx: self.profiles_df.values[profile_idx][-1]
        )

        # yield top n schools
        for i in recommendation_ranking[:n]:
            yield self.profiles[i]
