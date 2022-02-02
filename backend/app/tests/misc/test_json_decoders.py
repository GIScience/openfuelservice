import logging
from typing import Any

import pytest
from geoalchemy2 import WKBElement

from app.misc.json_decoders import json_to_wkb_element

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "geojson,wkbstring",
    (
        (
            {"type": "Point", "coordinates": [30, 10]},
            "01010000000000000000003e400000000000002440",
        ),
        (
            {"type": "LineString", "coordinates": [[30, 10], [10, 30], [40, 40]]},
            "0102000000030000000000000000003e40000000000000244000000000000024400000000000003e4000000000000044400000000000004440",  # noqa: E501
        ),
        ({}, None),
        (None, None),
        ("foobar", None),
    ),
)
def test_json_to_wkb_element(geojson: Any, wkbstring: WKBElement) -> None:
    geometry: WKBElement = json_to_wkb_element(geojson)
    if isinstance(geojson, dict) and len(geojson):
        assert geometry.srid == 4326
        assert geometry.desc == wkbstring
    else:
        assert geometry is None
