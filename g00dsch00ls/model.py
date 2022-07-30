from . import _student
from . import r_systems

from typing import Union, Dict, List, Type
import math
import random
import numpy as np
import pandas as pd



AVG_RANKING_MODE = 1
NORMALIZATION_MODE = 2

MODES = {
    AVG_RANKING_MODE: r_systems.AverageRankingSystem,
    NORMALIZATION_MODE: r_systems.NormalizationSystem,
    "avg_ranking": r_systems.AverageRankingSystem,
    "normalization": r_systems.NormalizationSystem
}



class G00dSch00ls:
    """G00dSch00ls recommendation model for schools
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
    - AVG_RANKING_MODE: (1) recommendations are calculated by comparing student and profile attributes,
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
    scores: np.ndarray
    systems: list[r_systems.RecommendationSystem]

    def __init__(
            self,
            profiles: pd.DataFrame,
            system=AVG_RANKING_MODE,
            system_kwargs=None
    ):
        if system_kwargs is None:
            system_kwargs = {}

        assert isinstance(profiles, pd.DataFrame), "Profiles must be pandas DataFrame"

        self.profiles_df = profiles
        self.system = system

        self._init_systems(self.system, system_kwargs)

    def __call__(self, *args, **kwargs) -> list[pd.Series]:
        return self.recommend(*args, **kwargs)

    def _init_scores_array(self):
        assert not self.profiles_df.empty, "Profiles DF must be initialized first"

        self.scores = np.zeros(len(self.profiles_df))

    def _init_systems(self, mode: Union[int, list, tuple], system_kwargs: dict):
        """Initialize recommendation systems"""

        # create list of recommendation systems based on mode
        systems = []

        if isinstance(mode, int):
            # decompose mode into binary numbers and create recommendation systems
            i = 1
            while i <= mode:
                if i & mode:
                    assert i in MODES, f"Mode {i} is not supported"
                    systems.append(MODES[i](self, **system_kwargs))
                i <<= 1

        elif isinstance(mode, list) or isinstance(mode, tuple):
            # create recommendation systems from list of modes

            if all(isinstance(m, int) for m in mode):
                # if all modes are integers, create recommendation systems from them
                systems = []
                for m in mode:
                    assert m in MODES, f"Mode {m} is not supported"
                    systems.append(MODES[m](self, **system_kwargs))

            elif all(issubclass(m, r_systems.RecommendationSystem) for m in mode):
                # if all modes are recommendation systems, create them
                systems = [m(self, **system_kwargs) for m in mode]

            elif all(isinstance(m, str) for m in mode):
                # if all modes are strings, create recommendation systems from them
                systems = [MODES[m](self, **system_kwargs) for m in mode]

        elif issubclass(mode, r_systems.RecommendationSystem):
            # if mode is recommendation system, create it
            systems = [mode(self, **system_kwargs)]

        elif isinstance(mode, str):
            # if mode is string, create recommendation system from string
            assert mode in MODES, f"Mode {mode} is not supported"
            systems = [MODES[mode](self, **system_kwargs)]

        assert systems, "No recommendation systems specified"

        self.systems = systems

    def _compare(self, system: r_systems.RecommendationSystem, student: _student.Student):
        """Compute recommendation ranking for system"""

        recommendation_ranking = system(student)

        for in_ranking, i in enumerate(recommendation_ranking):
            # add ranking position to the last column of df row (needed to calculate average ranking index)
            self.scores[i] += in_ranking

    def recommend(
            self,
            student: _student.Student,
            n=None
    ) -> list[pd.Series]:
        """Recommends schools for specific student"""

        self._init_scores_array()

        # for each system in recommendation systems compute ranking
        for system in self.systems:
            self._compare(system, student)

        # calculate average recommendation score
        self.scores /= len(self.systems)

        # sort initial indexes by recommendation score
        recommendation_ranking = sorted(
            range(len(self.profiles_df)),
            key=lambda profile_idx: self.scores[profile_idx]
        )

        # yield top n schools
        for i in recommendation_ranking[:n]:
            yield self.profiles_df.iloc[i]

    @classmethod
    def from_csv(
            cls,
            csv_path: str,
            *args, **kwargs
    ) -> 'G00dSch00ls':
        """Create G00dSch00ls model from CSV file"""

        profiles_df = pd.read_csv(csv_path)

        return cls(profiles_df, *args, **kwargs)
