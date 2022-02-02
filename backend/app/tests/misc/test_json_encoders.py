from typing import Any, Union

import pytest
from geoalchemy2 import WKBElement
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

from app.misc.json_encoders import ToShapeDecoder


@pytest.mark.parametrize(
    "geojson,wkb_object",
    (
        (
            shape({"type": "Point", "coordinates": [30, 10]}),
            WKBElement("01010000000000000000003e400000000000002440"),
        ),
        (
            shape(
                {"type": "LineString", "coordinates": [[30, 10], [10, 30], [40, 40]]}
            ),
            WKBElement(
                "0102000000030000000000000000003e40000000000000244000000000000024400000000000003e4000000000000"
                "044400000000000004440",
            ),
        ),
        (None, WKBElement(""),),
        (None, None),
        (None, None),
        ("foobar", "foobar"),
    ),
)
def test_tojsondecoder(
    geojson: Union[Any, BaseGeometry, None], wkb_object: Union[WKBElement, None, str]
) -> None:
    decoder = ToShapeDecoder()
    decoded: Point = decoder.__serialize__(wkb_object)
    assert decoded == geojson
