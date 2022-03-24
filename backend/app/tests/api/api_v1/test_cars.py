from typing import Dict, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CarFuelDataCar, EnvirocarSensor
from app.schemas import Car, SensorBase


@pytest.mark.anyio
async def test_read_cars(
    async_client: AsyncClient,
    db: Session,
    mock_cfd_cars: Generator[CarFuelDataCar, None, None],
) -> None:
    response = await async_client.get(f"{settings.API_V1_STR}/cars/")
    assert response.status_code == 200
    content: dict = response.json()
    assert isinstance(content["data"], list)
    data = content["data"]
    assert isinstance(data, list)
    assert len(data) == 602
    cfd: CarFuelDataCar
    car: Dict
    for car in data:
        orm_car = Car.parse_obj(car)
        cfd_car: CarFuelDataCar
        db_car: CarFuelDataCar = [
            cfd_car for cfd_car in mock_cfd_cars if cfd_car.id == orm_car.id
        ][0]
        assert orm_car.id == db_car.id
        assert orm_car.manufacturer == db_car.manufacturer
        assert orm_car.model == db_car.model
        assert orm_car.description == db_car.description
        assert orm_car.fuel_type == db_car.fuel_type
        assert orm_car.year == db_car.year


@pytest.mark.anyio
async def test_read_carfueldata_car_by_id(
    async_client: AsyncClient,
    db: Session,
    mock_cfd_cars: Generator,
) -> None:
    missed_counter: int = 0
    for mock_cfd_car in mock_cfd_cars:
        if not mock_cfd_car.id:
            missed_counter += 1
            continue
        response = await async_client.get(
            f"{settings.API_V1_STR}/cars/carfueldata/{mock_cfd_car.id}"
        )
        assert response.status_code == 200
        content: dict = response.json()
        assert isinstance(content["data"], dict)
        data = content["data"]
        assert len(data) == 6
        orm_car = Car.parse_obj(data)
        assert orm_car.id == mock_cfd_car.id
        assert orm_car.manufacturer == mock_cfd_car.manufacturer
        assert orm_car.model == mock_cfd_car.model
        assert orm_car.description == mock_cfd_car.description
        assert orm_car.fuel_type == mock_cfd_car.fuel_type
        assert orm_car.year == mock_cfd_car.year
    assert missed_counter == 47


@pytest.mark.anyio
async def test_read_carfueldata_car_by_id_must_fail(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(f"{settings.API_V1_STR}/cars/carfueldata/foo")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_read_envirocar_car_by_id(
    async_client: AsyncClient,
    db: Session,
    mock_envirocar_sensors_with_statistics_only: Dict,
) -> None:
    mock_envirocar: EnvirocarSensor
    assert len(mock_envirocar_sensors_with_statistics_only) > 0
    for mock_envirocar in mock_envirocar_sensors_with_statistics_only:
        if not mock_envirocar.id:
            continue
        response = await async_client.get(
            f"{settings.API_V1_STR}/cars/envirocar/{mock_envirocar.id}"
        )
        assert response.status_code == 200
        content: dict = response.json()
        assert isinstance(content["data"], dict)
        data = content["data"]
        assert len(data) == 7
        orm_car = SensorBase.parse_obj(data)
        assert orm_car.id == mock_envirocar.id
        assert orm_car.manufacturer == mock_envirocar.manufacturer
        assert orm_car.model == mock_envirocar.model
        assert orm_car.fueltype == mock_envirocar.fueltype
        assert orm_car.constructionyear == mock_envirocar.constructionyear


@pytest.mark.anyio
async def test_read_envirocar_car_by_id_must_fail(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(f"{settings.API_V1_STR}/cars/envirocar/foo")
    assert response.status_code == 404
