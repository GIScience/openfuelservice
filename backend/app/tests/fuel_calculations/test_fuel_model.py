import pytest
from fastapi import HTTPException

from app.db.importer.mappings import FuelMappings
from app.fuel_calculations.fuel_model import FuelModel
from app.models import EnvirocarSensorStatistic
from app.schemas.fuel import FuelCalculationResults


@pytest.mark.parametrize(
    "kmh,km,fuel_type,fuel_liter_total,fuel_liter_per_100km,co2_gram_total,co2_gram_per_km",
    (
        (0, 0, FuelMappings.GASOLINE, 0.0, 0.0, 0.0, 0.0),
        (0, 10, FuelMappings.GASOLINE, 0.0, 0.0, 0.0, 0.0),
        (10, 0, FuelMappings.GASOLINE, 0.0, 0.0, 0.0, 0.0),
        (10, 10, FuelMappings.GASOLINE, 0.001, 5.882, 1.382, 138.222),
        (20, 20, FuelMappings.GASOLINE, 0.001, 4.626, 2.174, 108.719),
        (49.5, 10, FuelMappings.GASOLINE, 0.001, 5.739, 1.349, 134.867),
        (70.5, 10, FuelMappings.GASOLINE, 0.001, 7.153, 1.681, 168.092),
        (120, 10, FuelMappings.GASOLINE, 0.001, 10.826, 2.544, 254.422),
        (150, 10, FuelMappings.GASOLINE, 0.001, 13.13, 3.086, 308.55),
        (189, 10, FuelMappings.GASOLINE, 0.002, 16.157, 3.797, 379.678),
        (200, 10, FuelMappings.GASOLINE, 0.002, 17.014, 3.998, 399.833),
    ),
)
def test_fuel_model_one_sensor(
    kmh: float,
    km: float,
    fuel_type: str,
    fuel_liter_total: float,
    fuel_liter_per_100km: float,
    co2_gram_total: float,
    co2_gram_per_km: float,
    mock_sensor_statistics_gasoline_co2_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_diesel_co2_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_speed_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_consumption_1: EnvirocarSensorStatistic,
) -> None:
    test: FuelModel = FuelModel(
        [
            mock_sensor_statistics_gasoline_co2_1,
            mock_sensor_statistics_diesel_co2_1,
            mock_sensor_statistics_gasoline_speed_1,
            mock_sensor_statistics_gasoline_consumption_1,
        ]
    )
    assert len(test._co2_statistics) == 1
    assert test._co2_statistics[0] == mock_sensor_statistics_gasoline_co2_1
    assert len(test._consumption_statistics) == 1
    assert (
        test._consumption_statistics[0] == mock_sensor_statistics_gasoline_consumption_1
    )
    assert len(test._speed_statistics) == 1
    assert test._speed_statistics[0] == mock_sensor_statistics_gasoline_speed_1

    result: FuelCalculationResults = test.calculate_fuel(kmh, km)
    assert result.fuel_type == fuel_type
    assert result.fuel_liter_total == fuel_liter_total
    assert result.fuel_liter_per_100km == fuel_liter_per_100km
    assert result.co2_gram_total == co2_gram_total
    assert result.co2_gram_per_km == co2_gram_per_km


def test_fuel_model_two_sensors(
    mock_sensor_statistics_gasoline_co2_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_co2_2: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_speed_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_speed_2: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_consumption_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_consumption_2: EnvirocarSensorStatistic,
) -> None:
    test = FuelModel(
        [
            mock_sensor_statistics_gasoline_co2_1,
            mock_sensor_statistics_gasoline_co2_2,
            mock_sensor_statistics_gasoline_speed_1,
            mock_sensor_statistics_gasoline_speed_2,
            mock_sensor_statistics_gasoline_consumption_1,
            mock_sensor_statistics_gasoline_consumption_2,
        ]
    )
    assert len(test._co2_statistics) == 2
    assert mock_sensor_statistics_gasoline_co2_1 in test._co2_statistics
    assert mock_sensor_statistics_gasoline_co2_2 in test._co2_statistics
    assert len(test._consumption_statistics) == 2
    assert mock_sensor_statistics_gasoline_consumption_1 in test._consumption_statistics
    assert mock_sensor_statistics_gasoline_consumption_2 in test._consumption_statistics
    assert len(test._speed_statistics) == 2
    assert mock_sensor_statistics_gasoline_speed_1 in test._speed_statistics
    assert mock_sensor_statistics_gasoline_speed_2 in test._speed_statistics


def test_fuel_model_must_fail(
    mock_sensor_statistics_gasoline_co2_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_diesel_co2_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_speed_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_diesel_speed_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_consumption_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_diesel_consumption_1: EnvirocarSensorStatistic,
) -> None:
    with pytest.raises(HTTPException):
        FuelModel(
            [
                mock_sensor_statistics_gasoline_co2_1,
                mock_sensor_statistics_gasoline_speed_1,
                mock_sensor_statistics_gasoline_consumption_1,
                mock_sensor_statistics_diesel_consumption_1,
            ]
        )
        FuelModel(
            [
                mock_sensor_statistics_gasoline_co2_1,
                mock_sensor_statistics_diesel_co2_1,
                mock_sensor_statistics_gasoline_speed_1,
                mock_sensor_statistics_diesel_speed_1,
                mock_sensor_statistics_gasoline_consumption_1,
                mock_sensor_statistics_diesel_consumption_1,
            ]
        )


def test_fuel_model_must_be_ampty(
    mock_sensor_statistics_gasoline_co2_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_gasoline_speed_1: EnvirocarSensorStatistic,
    mock_sensor_statistics_diesel_consumption_1: EnvirocarSensorStatistic,
) -> None:
    test = FuelModel(
        [
            mock_sensor_statistics_gasoline_co2_1,
            mock_sensor_statistics_gasoline_speed_1,
            mock_sensor_statistics_diesel_consumption_1,
        ]
    )
    assert not len(test._co2_statistics)
    assert not len(test._speed_statistics)
    assert not len(test._consumption_statistics)
    assert not test._co2_interpolator
    assert not test._consumption_interpolator
