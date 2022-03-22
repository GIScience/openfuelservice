from typing import Dict

import pytest
from pydantic import ValidationError
from pytest_lazyfixture import lazy_fixture

from app.schemas.geometry_objects import ORSFeatureCollection


@pytest.mark.parametrize(
    "geometry,expect_to_fail",
    (
        (lazy_fixture("openrouteservice_example_response"), False),
        ({}, True),
        ("", True),
        (None, True),
    ),
)
def test_ors_feature_collection(geometry: Dict, expect_to_fail: bool) -> None:
    if expect_to_fail:
        with pytest.raises(ValidationError):
            ORSFeatureCollection.parse_obj(geometry)
    else:
        ORSFeatureCollection.parse_obj(geometry)
