from typing import Dict, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CarFuelDataCar
from app.schemas import Car


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
async def test_read_car_by_id(
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
            f"{settings.API_V1_STR}/cars/{mock_cfd_car.id}"
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
    response = await async_client.get(f"{settings.API_V1_STR}/cars/foo")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_calculate_emissions_and_cost_by_id(
    async_client: AsyncClient, db: Session, mock_cfd_cars: Generator
) -> None:
    test_geojson: Dict = {
        "coordinates": [
            [10.502782, 51.181212],
            [10.50239, 51.1812],
            [10.501769, 51.181171],
            [10.501072, 51.181138],
        ],
        "type": "LineString",
    }
    missed_counter: int = 0
    for mock_cfd_car in mock_cfd_cars:
        if not mock_cfd_car.id:
            missed_counter += 1
            continue

        response = await async_client.post(
            f"{settings.API_V1_STR}/cars/{mock_cfd_car.id}/fuel",
            json={"geojson": test_geojson},
        )
        assert response.status_code == 200
    #     content: dict = response.json()
    #     assert isinstance(content["data"], dict)
    #     data = content["data"]
    #     assert len(data) == 6
    #     orm_car = Car.parse_obj(data)
    #     assert orm_car.id == mock_cfd_car.id
    #     assert orm_car.manufacturer == mock_cfd_car.manufacturer
    #     assert orm_car.model == mock_cfd_car.model
    #     assert orm_car.description == mock_cfd_car.description
    #     assert orm_car.fuel_type == mock_cfd_car.fuel_type
    #     assert orm_car.year == mock_cfd_car.year
    # assert missed_counter == 47
    # response = await async_client.get(f"{settings.API_V1_STR}/cars/foo")
    # assert response.status_code == 404


@pytest.mark.parametrize(
    "test_geojson,response_code",
    (
        (
            {
                "coordinates": [
                    [10.502782, 51.181212],
                    [10.50239, 51.1812],
                    [10.501769, 51.181171],
                    [10.501072, 51.181138],
                ],
                "type": "LineString",
            },
            200,
        ),
        ({"coordinates": [10.502782, 51.181212], "type": "Point"}, 400),
        (
            {
                "coordinates": [
                    [
                        [10.502782, 51.181212],
                        [10.50239, 51.1812],
                        [10.501769, 51.181171],
                        [10.501072, 51.181138],
                        [10.502782, 51.181212],
                    ]
                ],
                "type": "Polygon",
            },
            400,
        ),
        (
            {
                "coordinates": [[10, 40], [40, 30], [20, 20], [30, 10]],
                "type": "MultiPoint",
            },
            400,
        ),
        (
            {
                "coordinates": [
                    [[10, 10], [20, 20], [10, 40]],
                    [[40, 40], [30, 30], [40, 20], [30, 10]],
                ],
                "type": "MultiLineString",
            },
            400,
        ),
        (
            {
                "coordinates": [
                    [[[30, 20], [45, 40], [10, 40], [30, 20]]],
                    [[[15, 5], [40, 10], [10, 20], [5, 10], [15, 5]]],
                ],
                "type": "MultiPolygon",
            },
            400,
        ),
        ("Foo", 422),
        (None, 422),
    ),
)
@pytest.mark.anyio
async def test_calculate_emissions_and_cost_by_id_test_geom(
    async_client: AsyncClient,
    db: Session,
    mock_random_cfd_car: CarFuelDataCar,
    test_geojson: Dict,
    response_code: int,
) -> None:
    # request_filter = {
    #     "driving_style": "moderate",
    #     "tank_size": 10,
    #     "request_id": "test123",
    # }
    # missed_counter: int = 0
    # response = await async_client.post(
    #     f"{settings.API_V1_STR}/cars/{mock_random_cfd_car.id}/fuel",
    #     json={"geojson": test_geojson},
    # )
    # print(response.json())
    # assert response.status_code == response_code
    # if response.status_code == 200:
    #     content: dict = response.json()
    #     assert isinstance(content["data"], dict)
    #     content["data"]
    pass
