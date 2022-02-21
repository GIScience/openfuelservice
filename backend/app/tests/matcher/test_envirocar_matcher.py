import logging
from typing import Dict, Generator, Set

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.matching.envirocar_matcher import EnvirocarMatcher
from app.models import WikiCar

logger = logging.getLogger(settings.PROJECT_NAME)


def test_envirocar_matcher_initialization(
    db: Session, mock_wikipedia_cars: Generator[WikiCar, None, None]
) -> None:
    envirocar_matcher: EnvirocarMatcher = EnvirocarMatcher(
        models_path=settings.UNCOMPRESSED_MATCHING_DATA, db=db
    )
    assert envirocar_matcher._db == db


@pytest.mark.parametrize(
    "manufacturer, model, accuracy, expected_result",
    (
        (
            "Citroën",
            "Berlingo 2012",
            1.0,
            {
                "brand_name": "Citroën",
                "car_name": "Berlingo",
                "category_short_eu": "a",
                "id": 9628,
                "page_id": 9628,
                "page_language": "de",
                "wiki_name": "Citroën Berlingo",
            },
        ),
        (
            "Abarth",
            "Competizione",
            0.98,
            {
                "brand_name": "Abarth",
                "car_name": "595 Competizione",
                "category_short_eu": "a",
                "id": 9459628,
                "page_id": 9459628,
                "page_language": "de",
                "wiki_name": "Abarth 595 Competizione",
            },
        ),
        (
            "Abarth",
            "595",
            0.97,
            {
                "brand_name": "Abarth",
                "car_name": "595 Competizione",
                "category_short_eu": "a",
                "id": 9459628,
                "page_id": 9459628,
                "page_language": "de",
                "wiki_name": "Abarth 595 Competizione",
            },
        ),
        (
            "Abarth",
            "595 Competizione",
            0.99,
            {
                "brand_name": "Abarth",
                "car_name": "595 Competizione",
                "category_short_eu": "a",
                "id": 9459628,
                "page_id": 9459628,
                "page_language": "de",
                "wiki_name": "Abarth 595 Competizione",
            },
        ),
        (
            "Nissan",
            "NV400",
            0.99,
            {
                "brand_name": "Nissan",
                "car_name": "NV400",
                "category_short_eu": "a",
                "id": 7566964,
                "page_id": 7566964,
                "page_language": "de",
                "wiki_name": "Nissan NV400",
            },
        ),
        (
            "PSA/Fiat",
            "124 Spider (2016)",
            0.99,
            {
                "brand_name": "Fiat",
                "car_name": "124 Spider (2016)",
                "category_short_eu": "a",
                "id": 776964,
                "page_id": 776964,
                "page_language": "de",
                "wiki_name": "Fiat 124 Spider (2016)",
            },
        ),
        (
            "VW",
            "Golf V Plus 1.6",
            0.58,
            {
                "brand_name": "VW",
                "car_name": "Golf Plus",
                "category_short_eu": "a",
                "id": 4153628,
                "page_id": 4153628,
                "page_language": "de",
                "wiki_name": "VW Golf Plus",
            },
        ),
        (
            "VW",
            "Golf 5 Plus",
            0.55,
            {
                "brand_name": "VW",
                "car_name": "Golf Plus",
                "category_short_eu": "a",
                "id": 4153628,
                "page_id": 4153628,
                "page_language": "de",
                "wiki_name": "VW Golf Plus",
            },
        ),
    ),
)
@pytest.mark.asyncio
async def test_match(
    manufacturer: str,
    model: str,
    accuracy: float,
    expected_result: Dict,
    db: Session,
    mock_wikipedia_cars: Generator[WikiCar, None, None],
) -> None:
    envirocar_matcher: EnvirocarMatcher = EnvirocarMatcher(
        models_path=settings.UNCOMPRESSED_MATCHING_DATA, db=db
    )
    matched_envirocar_data = await envirocar_matcher.match(
        manufacturer=manufacturer, car=model, accuracy=accuracy
    )
    assert len(matched_envirocar_data) == 1
    matching_accuracy: float = matched_envirocar_data[0][1]
    assert matching_accuracy >= accuracy
    matched_car: WikiCar = matched_envirocar_data[0][0][0]
    assert matched_car.brand_name == expected_result["brand_name"]
    assert matched_car.car_name == expected_result["car_name"]
    assert matched_car.category_short_eu == expected_result["category_short_eu"]
    assert matched_car.id == expected_result["id"]
    assert matched_car.page_id == expected_result["page_id"]
    assert matched_car.page_language == expected_result["page_language"]
    assert matched_car.wiki_name == expected_result["wiki_name"]


@pytest.mark.parametrize(
    "manufacturer, powerset, accuracy, expected_result",
    (
        (
            "Abarth",
            {"Abarth Competizione"},
            0.98,
            "Abarth 595 Competizione",
        ),
        ("Abarth", {"595"}, 0.97, "Abarth 595 Competizione"),
        ("Abarth", {"595 Competizione"}, 0.99, "Abarth 595 Competizione"),
        ("Nissan", {"NV400"}, 0.99, "Nissan NV400"),
        ("Fiat", {"124 Spider (2016)"}, 0.25, "Fiat 124 Spider (2016)"),
        ("VW", {"Golf V Plus 1.6"}, 0.85, "Volkswagen Golf Plus"),
        ("VW", {"Golf 5 Plus"}, 0.55, "Volkswagen Golf Plus"),
    ),
)
@pytest.mark.asyncio
async def test__match_with_wikicars(
    manufacturer: str, powerset: Set, accuracy: float, expected_result: str, db: Session
) -> None:
    envirocar_matcher: EnvirocarMatcher = EnvirocarMatcher(
        models_path=settings.UNCOMPRESSED_MATCHING_DATA, db=db
    )
    matched_envirocar_data = await envirocar_matcher._match_with_wikicars(
        manufacturer=manufacturer, powerset=powerset, accuracy=accuracy
    )
    assert len(matched_envirocar_data) == 1
    matching_accuracy: float = matched_envirocar_data[0][1]
    assert matching_accuracy >= accuracy
    matched_car: str = matched_envirocar_data[0][0]
    assert matched_car == expected_result
