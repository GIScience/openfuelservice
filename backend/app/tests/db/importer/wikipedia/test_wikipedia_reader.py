from typing import List, Union

import pytest
import responses

from app.core.config import settings
from app.db.importer.wikipedia.wikipedia_reader import WikipediaReader
from app.models import WikiCar, WikiCarCategory


def test_get_category_data(wikipedia_mocked_responses: responses.RequestsMock,) -> None:
    test_car_category = {
        "a": {
            "category_names": [
                "Kategorie:Kleinstwagen",
                "Kategorie:Leichtfahrzeug",
                "Category:Microcars",
            ],
            "de": "Kleinstwagen",
            "en": "mini cars",
            "single_cars": [],
            "tank_capacity": 15,
        }
    }
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, car_categories={}
    )
    category_objects: List = wikipedia_reader.get_category_data(
        categories=test_car_category
    )
    assert len(category_objects) == 1
    assert isinstance(category_objects[0], WikiCarCategory)
    category_object: WikiCarCategory = category_objects[0]
    assert category_object.category_name_de == "Kleinstwagen"
    assert category_object.category_name_en == "mini cars"
    assert category_object.category_short_eu == "a"
    assert category_object.id == category_object.category_short_eu
    assert len(category_object.category_wiki_names) == 3
    category_names: List = test_car_category["a"]["category_names"]  # type: ignore
    assert category_object.category_wiki_names.sort() == category_names.sort()


def test_get_category_car_data(
    wikipedia_mocked_responses: responses.RequestsMock,
) -> None:
    test_car_category = {
        "a": {
            "category_names": [
                "Kategorie:Kleinstwagen",
                "Kategorie:Leichtfahrzeug",
                "Category:Microcars",
            ],
            "de": "Kleinstwagen",
            "en": "mini cars",
            "single_cars": [],
            "tank_capacity": 15,
        }
    }
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, car_categories={}
    )
    category_objects: List[WikiCarCategory] = wikipedia_reader.get_category_data(
        categories=test_car_category
    )
    wiki_car_objects = wikipedia_reader.get_category_car_data(
        category_db_objects=category_objects
    )

    assert len(wiki_car_objects) == 3
    car: WikiCar
    brands: List = ["Abarth", "Nissan", "Zhidou"]
    car_names: List = ["595 Competizione", "Land Glider", "D2"]
    wiki_names: List = [
        "Abarth 595 Competizione",
        "Nissan Land Glider",
        'Zhidou D2\\"+=',
    ]
    for car in wiki_car_objects:
        assert isinstance(car, WikiCar)
        assert car.brand_name in brands
        assert car.car_name in car_names
        assert car.wiki_name in wiki_names
        assert car.category_short_eu == "a"
        assert car.page_language in ["de", "en"]


@pytest.mark.parametrize(
    "test_string,expected_result",
    (
        ("Mercedes 3 GE \\\"'#@;*<>{}`+=~|.!?,'", "3 GE"),
        ("Mercedes 3 GE;*<>{}`+=~|.!?,", "3 GE"),
        ("Mercedes +#*'3 +#*'GE", "3 GE"),
        ("Opel Foobar (22?=)", "Foobar (22)"),
        ("PSA / Fiat Foobar", "Foobar"),
        ("Kei-Car", None),
        ("Foobar", None),
        (None, None),
    ),
)
def test__process_category_member(test_string: str, expected_result: str) -> None:
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, car_categories={}
    )
    wiki_car: Union[WikiCar, None] = wikipedia_reader._process_category_member(
        member_name=test_string
    )
    if not wiki_car:
        assert not expected_result
    if wiki_car:
        assert expected_result
        assert wiki_car.car_name == expected_result


@pytest.mark.parametrize(
    "test_string", [s for s in settings.CAR_BRANDS["ignore_list"]][::100]
)
def test__process_category_member_ignore_list(test_string: str) -> None:
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, car_categories={}
    )
    wiki_car: Union[WikiCar, None] = wikipedia_reader._process_category_member(
        member_name=test_string
    )
    assert not wiki_car


@pytest.mark.parametrize(
    "test_string", [s for s in settings.CAR_BRANDS["brands"]][::100]
)
def test__process_category_member_brands_list(test_string: str) -> None:
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, car_categories={}
    )
    wiki_car: Union[WikiCar, None] = wikipedia_reader._process_category_member(
        member_name=test_string + " Foobar"
    )
    assert isinstance(wiki_car, WikiCar)
    assert wiki_car.car_name == "Foobar"
    assert wiki_car.brand_name in test_string


@pytest.mark.parametrize(
    "test_string", [s for s in settings.CAR_BRANDS["vehicles"]][::5]
)
def test__process_category_member_vehicles_list(test_string: str) -> None:
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, car_categories={}
    )
    wiki_car: Union[WikiCar, None] = wikipedia_reader._process_category_member(
        member_name=test_string
    )
    assert isinstance(wiki_car, WikiCar)
    assert wiki_car.car_name
    assert wiki_car.brand_name


def test_fetch_and_process_data(
    wikipedia_mocked_responses: responses.RequestsMock,
) -> None:
    test_car_category = {
        "a": {
            "category_names": [
                "Kategorie:Kleinstwagen",
                "Kategorie:Leichtfahrzeug",
                "Category:Microcars",
            ],
            "de": "Kleinstwagen",
            "en": "mini cars",
            "single_cars": [],
            "tank_capacity": 15,
        }
    }
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, car_categories=test_car_category
    )
    wikipedia_reader.fetch_and_process_data()
    # Check sensors and track_ids response
    assert len(wikipedia_reader.objects_ordered) == 2
    assert (
        sum([len(objects) for objects in wikipedia_reader.objects_ordered.values()])
        == 4
    )
    assert len(wikipedia_reader.objects_ordered[0]) == 1
    assert len(wikipedia_reader.objects_ordered[1]) == 3
    assert isinstance(wikipedia_reader.objects_ordered[0][0], WikiCarCategory)
    wiki_category: WikiCarCategory = wikipedia_reader.objects_ordered[0][0]
    assert wiki_category.category_wiki_names == [
        "Kategorie:Kleinstwagen",
        "Kategorie:Leichtfahrzeug",
        "Category:Microcars",
    ]
    assert wiki_category.category_name_en == "mini cars"
    assert wiki_category.category_name_de == "Kleinstwagen"
    assert wiki_category.category_short_eu == "a"
    assert wiki_category.id == wiki_category.category_short_eu

    brands: List = ["Abarth", "Nissan", "Zhidou"]
    car_names: List = ["595 Competizione", "Land Glider", "D2"]
    wiki_names: List = [
        "Abarth 595 Competizione",
        "Nissan Land Glider",
        'Zhidou D2\\"+=',
    ]

    wiki_car: WikiCar
    for wiki_car in wikipedia_reader.objects_ordered[1]:
        assert isinstance(wiki_car, WikiCar)
        assert wiki_car.brand_name in brands
        assert wiki_car.car_name in car_names
        assert wiki_car.wiki_name in wiki_names
        assert wiki_car.category_short_eu == "a"
        assert wiki_car.page_language in ["de", "en"]
