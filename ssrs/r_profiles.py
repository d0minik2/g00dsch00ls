# -*- coding: latin-1 -*-

from .school_poperties import *

from typing import Union, Dict, List, Type
import json
import numpy as np
from dataclasses import dataclass, field



SCHOOL_DICT_STRUCTURE = {
    "name": str,
    "matura_exam_results": dict[str: float],
    "address": str,
    "type": str,
    "profiles": [
        {
            "name": str,
            "extended_subjects": list[str],
            "scored_subjects": list[str],
            "min_points": float,
            "avg_points": float,
            "max_points": float
        },
    ]
}


def map_subjects(subjects: Union[List[str], Dict]) -> np.ndarray:
    """Mapping subjects from list or dict to np.array"""

    array = np.zeros(len(SUBJECTS))

    if isinstance(subjects, list):
        # setting values to 1 when subject name is in list
        for subj in subjects:
            if subj in SUBJECTS:
                array[SUBJECTS.index(subj)] = 1
            elif subj.replace("\t", "") in SUBJECTS:
                array[SUBJECTS.index(subj.replace("\t", ""))] = 1

    elif isinstance(subjects, dict):
        # setting values in array to values from dict in indexes of subjects
        for subj, val in subjects.items():
            if subj in SUBJECTS:
                array[SUBJECTS.index(subj)] = val

    elif isinstance(subjects, np.ndarray):
        # if subjects is already array, leaving it same as it was
        return subjects

    return array


def calculate_grade_points(grade: int, scores=POINTS_FOR_GRADES):
    """Calculating points for grades"""

    return scores[int(grade)]


@dataclass
class School:
    """School attributes class"""

    name: str
    school_type: Union[str, int]
    location: str = ""
    mature_scores: Union[list[float], dict] = field(default_factory=list)
    profiles: list = field(default_factory=list)
    __array = None

    def __post_init__(self):
        # setting school type to a number
        self.school_type = SCHOOL_TYPES[self.school_type]
        self.mature_scores = np.array(list(self.mature_scores.values()))

        # TODO set location to jakdojade object (if i get an API access)

    @classmethod
    def from_dict(cls, school: dict):
        """Creating School object from dict

        Dict must have following structure:
        {
            "name": str,
            "matura_exam_results": dict[str: float],
            "address": str,
            "type": str,
            "profiles": [
                {
                    "name": str,
                    "extended_subjects": list[str],
                    "scored_subjects": list[str],
                    "min_points": float,
                    "avg_points": float,
                    "max_points": float
                },
            ]
        }
        """

        try:
            new_school = cls(
                name=school["name"],
                school_type=school["type"],
                mature_scores=school["matura_exam_results"],
                location=school["address"]
            )
            new_school.profiles = [
                Profile.from_dict(profile, school=new_school)
                for profile in school["profiles"]
            ]
            return new_school

        except KeyError as exc:
            raise type(exc)(
                f"School dict must have the following keys: {list(SCHOOL_DICT_STRUCTURE.keys())}"
            ) from exc


@dataclass
class Profile:
    """Profile of school attributes class"""

    name: str
    school: School
    extended_subjects: Union[List[str], np.ndarray]
    scored_subjects: Union[List[str], np.ndarray]
    extended_subjects_list = None
    minimum_points: float = MIN_POINTS
    average_points: float = (MAX_POINTS-MIN_POINTS)/2
    maximum_points: float = MAX_POINTS
    __array = None

    def __post_init__(self):
        self.extended_subjects_list = self.extended_subjects

        # mapping subjects to arrays
        self.extended_subjects = map_subjects(self.extended_subjects)
        self.scored_subjects = map_subjects(self.scored_subjects)

    @property
    def array(self) -> np.ndarray:
        """Return an array that can be compared with student"""

        if self.__array is None:
            self.__array = np.array([
                self.school.school_type,
                self.school.mature_scores,
                self.extended_subjects,
                [self.minimum_points, self.average_points, self.maximum_points],
                self.scored_subjects,
                # TODO self.school.location
            ], dtype=object)

        return self.__array

    @classmethod
    def from_dict(cls, proflie: dict, school: School = None):
        """Creating Profile object from dict

        Dict must have following structure:
        {
            "name": str,
            "extended_subjects": list[str],
            "scored_subjects": list[str],
            "min_points": float,
            "avg_points": float,
            "max_points": float
        }
        """

        try:
            return cls(
                name=proflie["name"],
                school=school,
                extended_subjects=proflie["extended_subjects"],
                scored_subjects=proflie["scored_subjects"],
                minimum_points=proflie["min_points"],
                average_points=proflie["avg_points"],
                maximum_points=proflie["max_points"]
            )

        except KeyError as exc:
            raise type(exc)(
                f"Profile dict must have the following keys: {list(SCHOOL_DICT_STRUCTURE['profiles'][0].keys())}"
            ) from exc


def generate_profiles(json_path: str) -> list[Profile]:
    """Generate profiles from json file"""

    assert json_path.endswith(".json"), "The file must be a json file!"

    profiles = []

    with open(json_path) as data:
        school_data = json.load(data)["schools"]

    for school in school_data:
        profiles.extend(
            School.from_dict(school).profiles
        )

    return profiles
