from typing import List

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.models import CarFuelDataCar
from requests import Response


def test_read_brands(
        client: TestClient, db: Session, mock_cfd_brands: List[models.CarFuelDataCar]
) -> None:
    response: Response = client.get(f"{settings.API_V1_STR}/brands/", )
    assert response.status_code == 200
    content: dict = response.json()
    assert isinstance(content["brands"], list)
    assert len(content["brands"]) == 10
    carfueldatacar: CarFuelDataCar
    for carfueldatacar in mock_cfd_brands:
        assert carfueldatacar.manufacturer in content["brands"]
