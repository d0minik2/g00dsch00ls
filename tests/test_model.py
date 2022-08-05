import pytest

import g00dsch00ls

import numpy as np
import pandas as pd



def create_student(**kwargs):
    default_kwargs = dict(
        exam_results={
            "polish": 78,
            "math": 100,
            "english": 98
        },
        grades={
            "język polski": 4,
            "matematyka": 5,
            "język angielski": 5,
            "informatyka": 5,
            "biologia": 3,
            "fizyka": 6,
            "chemia": 4,
            "geografia": 4,
        },
        liked_subjects={
            "matematyka": 1,
            "informatyka": 1,
            "Technik programista": 1,
        },
        school_type=0,
        additional_points=3
    )

    default_kwargs.update(kwargs)

    return g00dsch00ls.PLStudent(**default_kwargs)



def test_model_avg_ranking_system():
    data = pd.read_csv("data/schools.csv")
    student = create_student()

    model = g00dsch00ls.G00dSch00ls(data, system=g00dsch00ls.AVG_RANKING_SYSTEM)

    recommendations = model(student)

    assert isinstance(recommendations, list)
    assert len(recommendations) == data.shape[0]
    assert all(isinstance(i, pd.Series) for i in recommendations)


def test_model_normalization_system():
    data = pd.read_csv("data/schools.csv")
    student = create_student(school_type=0)  # add school type to the student !!

    model = g00dsch00ls.G00dSch00ls(data, system=g00dsch00ls.NORMALIZATION_SYSTEM,
                                    system_kwargs={"recommendation_attributes": {
                                        # setting compare_school_type to 1 and the rest to 0
                                        # will make the system to compare school type only !!
                                        "compare_school_type": 1, "compare_mature_scores": 0,
                                        "compare_extended_subjects": 0, "compare_points": 0
                                    }, "normalizer": g00dsch00ls.NormalizationSystem.zscore_normalize})

    recommendations = model(student)

    assert isinstance(recommendations, list)
    assert len(recommendations) == data.shape[0]
    assert all(isinstance(i, pd.Series) for i in recommendations)

    # system should compare school type only so the first recommendation should have preferred school type
    assert recommendations[0]["school_type"] == round(student.school_type)

    # check with linear scaling normalization
    model = g00dsch00ls.G00dSch00ls(data, system=g00dsch00ls.NORMALIZATION_SYSTEM,
                                    system_kwargs={"recommendation_attributes": {
                                        # setting compare_school_type to 1 and the rest to 0
                                        # will make the system to compare school type only !!
                                        "compare_school_type": 1, "compare_mature_scores": 0,
                                        "compare_extended_subjects": 0, "compare_points": 0
                                    }, "normalizer": g00dsch00ls.NormalizationSystem.linear_scaling_normalize})

    recommendations = model(student)

    assert isinstance(recommendations, list)
    assert len(recommendations) == data.shape[0]
    assert all(isinstance(i, pd.Series) for i in recommendations)

    # system should compare school type only so the first recommendation should have preferred school type
    assert recommendations[0]["school_type"] == round(student.school_type)


def test_model_multiple_systems():
    data = pd.read_csv("data/schools.csv")
    student = create_student(school_type=0)  # add school type to the student !!

    model = g00dsch00ls.G00dSch00ls(data, system=g00dsch00ls.AVG_RANKING_SYSTEM + g00dsch00ls.NORMALIZATION_SYSTEM,
                                    system_kwargs={"recommendation_attributes": {
                                        # setting compare_school_type to 1 and the rest to 0
                                        # will make the system to compare school type only !!
                                        "compare_school_type": 1, "compare_mature_scores": 0,
                                        "compare_extended_subjects": 0, "compare_points": 0
                                    }})

    recommendations = model(student)

    assert isinstance(recommendations, list)
    assert all(isinstance(i, pd.Series) for i in recommendations)
    assert len(recommendations) == data.shape[0]

    # system should compare school type only so the first recommendation should have preferred school type
    assert recommendations[0]["school_type"] == round(student.school_type)

