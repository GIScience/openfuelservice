from typing import Dict, List

import pytest
from httpx import AsyncClient
from pytest_lazyfixture import lazy_fixture
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.mappings import FuelMappings
from app.models import EnvirocarSensor
from app.schemas.fuel import FuelCalculationResults


@pytest.mark.parametrize(
    "test_geometry,response_code,request_id,expect_to_fail,co2_gram_per_km,co2_gram_total,fuel_liter_per_100km,"
    "fuel_liter_total",
    (
        (
            lazy_fixture("openrouteservice_example_response"),
            200,
            "foo123",
            False,
            103.397,
            1053.812,
            4.400,
            0.448,
        ),
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
            422,
            "foo123",
            True,
            0,
            0,
            0,
            0,
        ),
        (
            {"coordinates": [10.502782, 51.181212], "type": "Point"},
            422,
            "foo123",
            True,
            0,
            0,
            0,
            0,
        ),
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
            422,
            "foo123",
            True,
            0,
            0,
            0,
            0,
        ),
        (
            {
                "coordinates": [[10, 40], [40, 30], [20, 20], [30, 10]],
                "type": "MultiPoint",
            },
            422,
            "foo123",
            True,
            0,
            0,
            0,
            0,
        ),
        (
            {
                "coordinates": [
                    [[10, 10], [20, 20], [10, 40]],
                    [[40, 40], [30, 30], [40, 20], [30, 10]],
                ],
                "type": "MultiLineString",
            },
            422,
            "foo123",
            True,
            0,
            0,
            0,
            0,
        ),
        (
            {
                "coordinates": [
                    [[[30, 20], [45, 40], [10, 40], [30, 20]]],
                    [[[15, 5], [40, 10], [10, 20], [5, 10], [15, 5]]],
                ],
                "type": "MultiPolygon",
            },
            422,
            "foo123",
            True,
            0,
            0,
            0,
            0,
        ),
        ("Foo", 422, "foo123", True, 0, 0, 0, 0),
        (None, 422, "foo123", True, 0, 0, 0, 0),
    ),
)
@pytest.mark.anyio
async def test_calculate_fuel_by_id_openrouteservice(
    async_client: AsyncClient,
    db: Session,
    test_geometry: Dict,
    response_code: int,
    request_id: str,
    mock_envirocar_sensors_with_statistics_only: List,
    expect_to_fail: bool,
    co2_gram_per_km: float,
    co2_gram_total: float,
    fuel_liter_per_100km: float,
    fuel_liter_total: float,
) -> None:
    # TODO 1. write this test. 2. write another test with an ors export. 3. calculate detailed stats
    #  4. output them as a model.
    ec_sensor: EnvirocarSensor = mock_envirocar_sensors_with_statistics_only[0]
    request_filter = {
        "driving_style": "moderate",
        "tank_size": 10,
        "request_id": "test123",
        "geometry": test_geometry,
        "car_ids": [ec_sensor.id],
    }
    response = await async_client.post(
        f"{settings.API_V1_STR}/fuel/envirocar/openrouteservice",
        json=request_filter,
    )
    assert response.status_code == response_code
    if response.status_code == 200:
        content: dict = response.json()
        assert isinstance(content["data"], dict)
        data = content["data"]
        orm_object: FuelCalculationResults = FuelCalculationResults.parse_obj(data)
        assert orm_object.fuel_type == FuelMappings.GASOLINE.name  # type: ignore
        assert orm_object.co2_gram_per_km == co2_gram_per_km
        assert orm_object.co2_gram_total == co2_gram_total
        assert orm_object.fuel_liter_per_100km == fuel_liter_per_100km
        assert orm_object.fuel_liter_total == fuel_liter_total
