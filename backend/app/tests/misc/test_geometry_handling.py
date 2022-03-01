from typing import Union

import pytest
from shapely.geometry import LineString, shape

from app.misc.geometry_handling import linestring_length_in_meter


@pytest.mark.parametrize(
    "test_geometry,expected_result",
    (
        (
            shape(
                {
                    "type": "LineString",
                    "coordinates": [
                        [8.686559200286865, 50.13170710917877],
                        [8.694498538970947, 50.13210599973331],
                    ],
                }
            ),
            567.6399544896653,
        ),
        (
            shape(
                {
                    "type": "LineString",
                    "coordinates": [
                        [30.509462356567383, 50.444250960743844],
                        [30.52027702331543, 50.44247449537885],
                    ],
                }
            ),
            790.8904027228475,
        ),
        (
            shape(
                {
                    "type": "LineString",
                    "coordinates": [
                        [-105.9521484375, 35.706377408871774],
                        [-106.5618896484375, 35.32633026307483],
                        [-106.5728759765625, 35.12440157992044],
                        [-104.6173095703125, 34.95799531086792],
                    ],
                }
            ),
            270973.615601398,
        ),
        (
            shape(
                {
                    "type": "LineString",
                    "coordinates": [
                        [47.252197265625, -20.524788750414267],
                        [47.04895019531249, -19.864893620513136],
                        [47.427978515625, -19.357793596209266],
                    ],
                }
            ),
            145342.55248022705,
        ),
        ("Foobar", None),
        ("", None),
        (None, None),
    ),
)
def test_true_linestring_length(
    test_geometry: LineString, expected_result: float
) -> None:
    test: Union[float, None] = linestring_length_in_meter(linestring=test_geometry)
    assert test == expected_result
