from typing import Generator, List

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CarFuelDataCar


@pytest.mark.anyio
async def test_read_brands(
    async_client: AsyncClient,
    db: Session,
    mock_cfd_cars: Generator[List[CarFuelDataCar], None, None],
) -> None:
    response = await async_client.get(f"{settings.API_V1_STR}/brands/",)
    assert response.status_code == 200
    content: dict = response.json()
    assert isinstance(content["data"], list)
    data = content["data"]
    assert len(data) == 10
    assert isinstance(data, list)
    assert data.sort() == [
        "Aston Martin",
        "Abarth",
        "Honda",
        "Alpine",
        "Dacia",
        "Jeep",
        "Alfa Romeo",
        "Citroën",
        "Tesla",
        "Hyundai",
    ].sort()
