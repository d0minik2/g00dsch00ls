from . import _student
from . import r_systems

from typing import Union, Dict, List, Type
import math
import random
import numpy as np
import pandas as pd



AVG_RANKING_SYSTEM = 1
NORMALIZATION_SYSTEM = 2

SYSTEMS = {
    AVG_RANKING_SYSTEM: r_systems.AverageRankingSystem,
    NORMALIZATION_SYSTEM: r_systems.NormalizationSystem,
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

    Two systems are available:
    - AVG_RANKING_SYSTEM: (1) recommendations are calculated by comparing student and profile attributes,
        for each attribute computes ranking of best options and combines them into one ranking of best recommendations.
    - NORMALIZATION_SYSTEM: (2) recommendations are calculated by comparing student and profile attributes,
        for each attribute computes normalized score and combines them into one recommendation ranking.

    Parameters
    ----------

    profiles: list of Profile objects to be recommended
    system: int or list[int] or str or list[str] or RecommendationSystem or list[RecommendationSystem]
            - recommendation system(s)
    system_kwargs: dict of arguments for recommendation system
    """

    profiles_df: pd.DataFrame
    scores: np.ndarray
    systems: list[r_systems.RecommendationSystem]

    def __init__(
            self,
            profiles: pd.DataFrame,
            system=AVG_RANKING_SYSTEM,
            system_kwargs=None
    ):
        if system_kwargs is None:
            system_kwargs = {}

        self.profiles_df = profiles
        self._init_systems(system, system_kwargs)

        assert isinstance(self.profiles_df, pd.DataFrame), "Profiles must be pandas DataFrame"
        assert all(isinstance(s, r_systems.RecommendationSystem) for s in self.systems)

    def __call__(self, *args, **kwargs) -> list[pd.Series]:
        return self.recommend(*args, **kwargs)

    def _init_scores_array(self):
        assert not self.profiles_df.empty, "Profiles DF must be initialized first"

        self.scores = np.zeros(len(self.profiles_df))

    def _init_systems(self, system: Union[int, str, list, tuple, r_systems.RecommendationSystem], system_kwargs: dict):
        """Initialize recommendation systems"""

        # create list of recommendation systems based on mode
        systems = []

        if isinstance(system, int):
            # decompose mode into binary numbers and create recommendation systems

            i = 1
            while i <= system:
                if i & system:
                    assert i in SYSTEMS, f"System {i} is not supported"
                    systems.append(SYSTEMS[i](self, **system_kwargs))
                i <<= 1

        elif isinstance(system, list) or isinstance(system, tuple):

            if all(isinstance(s, int) for s in system):

                systems = []
                for s in system:
                    assert s in SYSTEMS, f"System {s} is not supported"
                    systems.append(SYSTEMS[s](self, **system_kwargs))

            elif all(issubclass(s, r_systems.RecommendationSystem) for s in system):

                systems = [s(self, **system_kwargs) for s in system]

            elif all(isinstance(s, str) for s in system):

                systems = [SYSTEMS[s](self, **system_kwargs) for s in system]

        elif isinstance(system, str):

            assert system in SYSTEMS, f"System {system} is not supported"
            systems = [SYSTEMS[system](self, **system_kwargs)]

        elif isinstance(system, type):
            if issubclass(system, r_systems.RecommendationSystem):

                systems = [system(self, **system_kwargs)]

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

        assert isinstance(student, _student.Student), "Student must be _student.Student object"
        assert isinstance(n, int) or n is None, "n must be int or None"

        self._init_scores_array()

        # for each system in recommendation systems compute ranking
        for system in self.systems:
            self._compare(system, student)

        # calculate average recommendation score
        self.scores /= len(self.systems)

        # sort initial indexes by recommendation score
        recommendation_ranking = sorted(
            range(len(self.profiles_df)),
            key=lambda profile_idx: self.scores[profile_idx],
        )

        return [self.profiles_df.iloc[i] for i in recommendation_ranking[:n]]


    @classmethod
    def from_csv(
            cls,
            csv_path: str,
            *args, **kwargs
    ) -> 'G00dSch00ls':
        """Create G00dSch00ls model from CSV file"""

        profiles_df = pd.read_csv(csv_path)

        return cls(profiles_df, *args, **kwargs)
