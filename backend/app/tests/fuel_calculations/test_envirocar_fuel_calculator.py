from typing import Dict, List

import pytest
from shapely.geometry import LineString, shape
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.mappings import FuelMappings
from app.fuel_calculations.envirocar_fuel_calculator import EnvirocarFuelCalculator
from app.models import EnvirocarSensor
from app.schemas import ORSFeatureCollection
from app.schemas.fuel import DrivingStyles, FuelCalculationResults


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
def test_envirocar_fuel_calculator(
    db: Session,
    geometry: LineString,
    tank_size: int,
    driving_style: DrivingStyles,
    manual_fuel_consumption: float,
    request_id: str,
    expected_route_length: float,
) -> None:
    mock_ids: List = ["123", "4321"]
    test = EnvirocarFuelCalculator(
        db=db,
        envirocar_car_ids=mock_ids,
        geometry=geometry,
        tank_size=tank_size,
        driving_style=driving_style,
        manual_fuel_consumption=manual_fuel_consumption,
        request_id=request_id,
    )
    assert test._envirocar_car_ids == mock_ids
    assert test._geometry == geometry
    assert test._tank_size == tank_size
    assert test._driving_style == driving_style
    assert test._manual_fuel_consumption == manual_fuel_consumption
    assert test._request_id == request_id
    assert test._fuel_model


@pytest.mark.parametrize(
    "geometry,tank_size,driving_style,manual_fuel_consumption,request_id",
    (
        (
            settings.OPENROUTESERVICE_EXAMPLE_REQUEST_HEIDELBERG,
            10,
            DrivingStyles.moderate,
            4.5,
            "foo123",
        ),
        # ("foo", 10, DrivingStyles.moderate, 4.5, "foo123"),
        # (None, 10, DrivingStyles.moderate, 4.5, "foo123"),
        # (None, None, None, None, None),
    ),
)
def test_envirocar_fuel_calculator_calculate_cost(
    db: Session,
    geometry: Dict,
    tank_size: int,
    driving_style: DrivingStyles,
    manual_fuel_consumption: float,
    request_id: str,
    mock_all_envirocar_sensors: Dict,
) -> None:
    sensor: EnvirocarSensor
    envirocar_sensor_ids: List[str] = [
        sensor.id
        for sensor in mock_all_envirocar_sensors[1]
        if FuelMappings.from_value(sensor.fueltype) == FuelMappings.GASOLINE
    ]
    test = EnvirocarFuelCalculator(
        db=db,
        envirocar_car_ids=envirocar_sensor_ids,
        geometry=ORSFeatureCollection.parse_obj(geometry),
        tank_size=tank_size,
        driving_style=driving_style,
        manual_fuel_consumption=manual_fuel_consumption,
        request_id=request_id,
    )

    assert len(test._envirocar_car_ids)
    assert test._envirocar_car_ids == envirocar_sensor_ids
    assert test._db == db
    # 60 km/h for 5 km
    result: FuelCalculationResults = test.calculate_fuel(kmh=60, length_in_meter=5000)
    assert isinstance(result, FuelCalculationResults)
    assert result.fuel_type == FuelMappings.GASOLINE
    assert result.co2_gram_per_km == 146.936
    assert result.co2_gram_total == 734.678
    assert result.fuel_liter_per_100km == 6.253
    assert result.fuel_liter_total == 0.313
