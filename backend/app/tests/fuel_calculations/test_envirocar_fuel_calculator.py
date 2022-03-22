from typing import List, Union

import pytest
from pytest_lazyfixture import lazy_fixture
from sqlalchemy.orm import Session

from app.db.importer.mappings import FuelMappings
from app.fuel_calculations.envirocar_fuel_calculator import EnvirocarFuelCalculator
from app.models import EnvirocarSensor
from app.schemas import ORSFeatureCollection
from app.schemas.fuel import DrivingStyles, FuelCalculationResults


@pytest.mark.parametrize(
    "tank_size,driving_style,manual_fuel_consumption,expected_route_length",
    [
        (
            10,
            DrivingStyles.moderate,
            4.5,
            567.6399544896653,
        ),
        (10, DrivingStyles.moderate, 4.5, None),
        (None, None, None, None),
    ],
)
def test_envirocar_fuel_calculator(
    db: Session,
    tank_size: int,
    driving_style: DrivingStyles,
    manual_fuel_consumption: float,
    expected_route_length: float,
) -> None:
    mock_ids: List = ["123", "4321"]
    test = EnvirocarFuelCalculator(
        db=db,
        envirocar_car_ids=mock_ids,
        tank_size=tank_size,
        driving_style=driving_style,
        manual_fuel_consumption=manual_fuel_consumption,
    )
    assert test._envirocar_car_ids == mock_ids
    assert test._tank_size == tank_size
    assert test._driving_style == driving_style
    assert test._manual_fuel_consumption == manual_fuel_consumption
    assert test._fuel_model


@pytest.mark.parametrize(
    "tank_size,driving_style,manual_fuel_consumption,expect_to_fail",
    (
        (10, DrivingStyles.moderate, 4.5, False),
        (10, DrivingStyles.moderate, 4.5, True),
        (10, DrivingStyles.moderate, 4.5, True),
        (None, None, None, True),
    ),
)
def test_envirocar_fuel_calculator_calculate_fuel(
    db: Session,
    tank_size: int,
    driving_style: DrivingStyles,
    manual_fuel_consumption: float,
    expect_to_fail: bool,
    mock_envirocar_sensors_with_statistics_only: List,
) -> None:
    sensor: EnvirocarSensor
    envirocar_sensor_ids: List[str] = [
        sensor.id
        for sensor in mock_envirocar_sensors_with_statistics_only
        if FuelMappings.from_value(sensor.fueltype) == FuelMappings.GASOLINE
    ]
    assert len(envirocar_sensor_ids) > 0
    test = EnvirocarFuelCalculator(
        db=db,
        envirocar_car_ids=envirocar_sensor_ids,
        tank_size=tank_size,
        driving_style=driving_style,
        manual_fuel_consumption=manual_fuel_consumption,
    )

    assert len(test._envirocar_car_ids)
    assert test._envirocar_car_ids == envirocar_sensor_ids
    assert test._db == db
    # 60 km/h for 5 km
    result: FuelCalculationResults = test.calculate_fuel(kmh=60, length_in_meter=5000)
    assert isinstance(result, FuelCalculationResults)
    assert result.fuel_type == FuelMappings.GASOLINE.name  # type: ignore
    assert result.co2_gram_per_km == 146.936
    assert result.co2_gram_total == 734.678
    assert result.fuel_liter_per_100km == 6.253
    assert result.fuel_liter_total == 0.313


@pytest.mark.parametrize(
    "geometry,tank_size,driving_style,manual_fuel_consumption,expect_to_fail,co2_gram_per_km,co2_gram_total,"
    "fuel_liter_per_100km,fuel_liter_total",
    (
        (
            lazy_fixture("openrouteservice_example_response"),
            10,
            DrivingStyles.moderate,
            4.5,
            False,
            106.29679296875,
            1050.6029999999998,
            4.523189453125,
            0.44699999999999995,
        ),
        ("foo", 10, DrivingStyles.moderate, 4.5, True, 0, 0, 0, 0),
        ({}, 10, DrivingStyles.moderate, 4.5, True, 0, 0, 0, 0),
        (None, None, None, None, True, 0, 0, 0, 0),
    ),
)
def test_envirocar_fuel_calculator_calculate_fuel_ors_response(
    db: Session,
    geometry: ORSFeatureCollection,
    tank_size: int,
    driving_style: DrivingStyles,
    manual_fuel_consumption: float,
    expect_to_fail: bool,
    co2_gram_per_km: float,
    co2_gram_total: float,
    fuel_liter_per_100km: float,
    fuel_liter_total: float,
    mock_envirocar_sensors_with_statistics_only: List,
) -> None:
    sensor: EnvirocarSensor
    envirocar_sensor_ids: List[str] = [
        sensor.id
        for sensor in mock_envirocar_sensors_with_statistics_only
        if FuelMappings.from_value(sensor.fueltype) == FuelMappings.GASOLINE
    ]
    test = EnvirocarFuelCalculator(
        db=db,
        envirocar_car_ids=envirocar_sensor_ids,
        tank_size=tank_size,
        driving_style=driving_style,
        manual_fuel_consumption=manual_fuel_consumption,
    )

    assert len(test._envirocar_car_ids)
    assert test._envirocar_car_ids == envirocar_sensor_ids
    assert test._db == db
    # 60 km/h for 5 km
    if expect_to_fail:
        with pytest.raises(TypeError):
            result: Union[
                FuelCalculationResults, None
            ] = test.calculate_fuel_for_openrouteservice_response(
                geometry=geometry
            )  # type: ignore  # type: ignore
    else:
        result = test.calculate_fuel_for_openrouteservice_response(
            geometry=ORSFeatureCollection.parse_obj(geometry)
        )
        assert isinstance(result, FuelCalculationResults)
        assert result.fuel_type == FuelMappings.GASOLINE.name  # type: ignore
        assert result.co2_gram_per_km == co2_gram_per_km
        assert result.co2_gram_total == co2_gram_total
        assert result.fuel_liter_per_100km == fuel_liter_per_100km
        assert result.fuel_liter_total == fuel_liter_total
