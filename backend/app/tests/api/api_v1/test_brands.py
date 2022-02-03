from typing import Generator, List

from fastapi.testclient import TestClient
from requests import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CarFuelDataCar


def test_read_brands(
    client: TestClient,
    db: Session,
    mock_cfd_cars: Generator[List[CarFuelDataCar], None, None],
) -> None:
    response: Response = client.get(f"{settings.API_V1_STR}/brands/",)
    assert response.status_code == 200
    content: dict = response.json()
    assert isinstance(content["data"], list)
    data = content["data"]
    assert len(data) == 10
    assert isinstance(data, list)
    assert data == [
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
    ]
