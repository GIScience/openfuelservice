from typing import Generator, List, Tuple

import pytest
from shapely.geometry import LineString, shape

from app.fuel_calculations.base_fuel_calculator import BaseFuelCalculator
from app.schemas.fuel import DrivingStyles


@pytest.mark.parametrize(
    "geometry,tank_size,driving_style,manual_fuel_consumption,request_id,expected_route_length",
    [
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
            10,
            DrivingStyles.moderate,
            4.5,
            "foo123",
            567.6399544896653,
        ),
        ("foo", 10, DrivingStyles.moderate, 4.5, "foo123", None),
        (None, None, None, None, None, None),
    ],
)
def test_base_fuel_calculator(
    geometry: LineString,
    tank_size: int,
    driving_style: DrivingStyles,
    manual_fuel_consumption: float,
    request_id: str,
    expected_route_length: float,
) -> None:
    test = BaseFuelCalculator(
        geometry=geometry,
        tank_size=tank_size,
        driving_style=driving_style,
        manual_fuel_consumption=manual_fuel_consumption,
        request_id=request_id,
    )
    assert test._geometry == geometry
    assert test._tank_size == tank_size
    assert test._driving_style == driving_style
    assert test._manual_fuel_consumption == manual_fuel_consumption
    assert test._request_id == request_id
    assert test._route_length == expected_route_length
    assert len(test._categories) == 0
    assert not test._fuel_models
