from typing import Dict, Generator, List, Union

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings


@pytest.mark.parametrize(
    "brand,response_code", (("Abarth", 200), ("", 404), ("Foo", 404), (None, 404),),
)
@pytest.mark.anyio
async def test_read_car_by_brand(
    async_client: AsyncClient,
    db: Session,
    mock_cfd_cars: Generator,
    brand: Union[Dict, None],
    response_code: int,
) -> None:
    response = await async_client.get(f"{settings.API_V1_STR}/cars/{brand}")
    assert response.status_code == response_code
    if response.status_code == 200:
        content: dict = response.json()
        assert isinstance(content["data"], list)
        data = content["data"]
        assert len(data) == 5
        ids_in_mocks: List = [cfd.id for cfd in mock_cfd_cars]
        for car in data:
            assert len(car) == 6
            assert car["id"] in ids_in_mocks
            assert car["manufacturer"]
            assert car["model"]
            assert car["description"]
            assert car["fuel_type"]
            assert car["year"]


@pytest.mark.parametrize(
    "brand,response_code", (("Abarth", 200), ("", 404), ("Foo", 404), (None, 404),),
)
@pytest.mark.anyio
async def test_read_car_by_brand_ordered(
    async_client: AsyncClient,
    db: Session,
    mock_cfd_cars: Generator,
    brand: Union[Dict, None],
    response_code: int,
) -> None:
    response = await async_client.get(f"{settings.API_V1_STR}/cars/{brand}/sorted")
    assert response.status_code == response_code
    ids = [
        "58a30c268922539271bd781aa3c059c4",
        "30f025757624185e6025ade861756d16",
        "4d67f0605929e5e6c9a4f4fbb6ef99a6",
    ]
    if response.status_code == 200:
        content: dict = response.json()
        assert len(content) == 2
        assert isinstance(content["messages"], list)
        assert isinstance(content["data"], dict)
        data = content["data"]
        assert len(data) == 2
        assert len(data["ids"]) == 3
        assert data["ids"] == ids
        car_name = data["595"]
        assert len(car_name) == 2
        assert len(car_name["ids"]) == 3
        assert car_name["ids"] == ids
        car_name_2021 = car_name["2021"]
        assert len(car_name_2021) == 2
        assert len(car_name_2021["ids"]) == 3
        assert car_name_2021["ids"] == ids
        cars = car_name_2021["cars"]
        assert len(cars) == 3
        for car in cars:
            assert car["id"] in ids
            assert car["manufacturer"]
            assert car["model"]
            assert car["description"]
            assert car["fuel_type"]
            assert car["year"]
