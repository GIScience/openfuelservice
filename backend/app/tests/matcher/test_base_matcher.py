from typing import Generator, List, Union

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.matching.base_matcher import BaseMatcher
from app.models import WikiCar


def test_base_matcher_initialization(
        db: Session, mock_wikipedia_cars: Generator[WikiCar, None, None]
) -> None:
    base_matcher: BaseMatcher = BaseMatcher(  # type: ignore
        models_path=settings.UNCOMPRESSED_MATCHING_DATA, db=db
    )
    assert base_matcher._db == db


def test_base_matcher_get_wikicar_by_name(
        db: Session, mock_wikipedia_cars: Generator[WikiCar, None, None]
) -> None:
    base_matcher: BaseMatcher = BaseMatcher(  # type: ignore
        models_path=settings.UNCOMPRESSED_MATCHING_DATA, db=db
    )
    assert base_matcher._db == db
    assert len(list(mock_wikipedia_cars))
    mock_wikipedia_car: WikiCar
    for mock_wikipedia_car in mock_wikipedia_cars:
        assert isinstance(mock_wikipedia_car, WikiCar)
        wiki_car_by_name: Union[WikiCar, None] = base_matcher.get_wikicar_by_name(mock_wikipedia_car.wiki_name)
        assert wiki_car_by_name
        assert isinstance(wiki_car_by_name, WikiCar)
        assert wiki_car_by_name.wiki_name == mock_wikipedia_car.wiki_name


@pytest.mark.parametrize(
    "wiki_name,expected_result",
    (
            ("Foo Foo", None),
            ("", None),
            (None, None),
    ),
)
def test_base_matcher_get_wikicar_by_name_is_empty(
        db: Session,
        wiki_name: str,
        expected_result: Union[str, None]
) -> None:
    base_matcher: BaseMatcher = BaseMatcher(  # type: ignore
        models_path=settings.UNCOMPRESSED_MATCHING_DATA, db=db
    )
    test: Union[WikiCar, None] = base_matcher.get_wikicar_by_name(wiki_name)
    assert test == expected_result
