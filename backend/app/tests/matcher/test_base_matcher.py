from typing import Generator, List, Union

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


def test_base_matcher_get_wikicars_by_name(
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
        wiki_cars_by_name: Union[
            List[WikiCar], None
        ] = base_matcher.get_wikicars_by_name(mock_wikipedia_car.wiki_name)
        assert wiki_cars_by_name and len(wiki_cars_by_name) > 0
        assert all(
            isinstance(wiki_car_by_name, WikiCar)
            for wiki_car_by_name in wiki_cars_by_name
        )
        assert all(
            wiki_car_by_name.wiki_name == mock_wikipedia_car.wiki_name
            for wiki_car_by_name in wiki_cars_by_name
        )
