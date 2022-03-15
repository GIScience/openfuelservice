from typing import List, Set

from sqlalchemy.orm import Session

from app.db.importer.base_importer import BaseImporter
from app.db.importer.wikipedia.wikipedia_reader import WikipediaReader
from app.models import WikiCar, WikiCarCategory


def test_wikipedia_importer(db: Session) -> None:
    test_car_category = {
        "car_categories": {
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
    }
    wikipedia_reader: WikipediaReader = WikipediaReader(
        file_or_url=None, threads=None, categories=test_car_category
    )
    wikipedia_reader.fetch_and_process_data()
    # Check sensors and track_ids response
    assert len(wikipedia_reader.objects_ordered) == 2
    assert (
        sum([len(objects) for objects in wikipedia_reader.objects_ordered.values()])
        == 9
    )
    assert len(wikipedia_reader.objects_ordered[0]) == 1
    assert len(wikipedia_reader.objects_ordered[1]) == 8
    assert isinstance(wikipedia_reader.objects_ordered[0][0], WikiCarCategory)

    unique_ids_wiki_car_categories: List = []
    unique_ids_wiki_cars: List = []
    for index, object_collection in wikipedia_reader.objects_ordered.items():
        BaseImporter(db=db).import_data(db_objects=object_collection)
        if index == 0:
            category: WikiCarCategory
            unique_ids_wiki_car_categories = list(
                set(
                    [
                        category.category_short_eu
                        for category in object_collection
                        if type(category) == WikiCarCategory
                    ]
                )
            )
        if index == 1:
            unique_ids_wiki_cars = list(
                set([car.id for car in object_collection if type(car) == WikiCar])
            )
    wiki_categories_in_db: List = WikiCarCategory.get_all_by_filter(
        db=db, filter_ids=unique_ids_wiki_car_categories, id_only=False
    )

    wiki_cars_in_db: List = WikiCar.get_all_by_filter(
        db=db, filter_ids=unique_ids_wiki_cars, id_only=False
    )
    # Test wikicategories
    assert len(wiki_categories_in_db) == len(wikipedia_reader.objects_ordered[0])
    wiki_cars_via_reference: List = []
    compare_counter: int = 0
    for category in wikipedia_reader.objects_ordered[0]:
        category_in_db: WikiCarCategory
        for category_in_db in wiki_categories_in_db:
            if category_in_db.id == category.id:
                compare_counter += 1
                assert category_in_db.category_name_de == category.category_name_de
                assert category_in_db.category_name_en == category.category_name_en
                assert (
                    category_in_db.category_wiki_names == category.category_wiki_names
                )
                wiki_cars_via_reference.extend(category_in_db.car_models.all())  # type: ignore

    assert compare_counter == len(wiki_categories_in_db)
    # Test wikicars
    wiki_categories_via_reference: Set = set()
    assert len(wiki_cars_in_db) == len(wikipedia_reader.objects_ordered[1])
    assert len(wiki_cars_in_db) == len(wiki_cars_via_reference)
    compare_counter = 0
    car: WikiCar
    for car in wikipedia_reader.objects_ordered[1]:
        car_in_db: WikiCar
        for car_in_db in wiki_cars_in_db:
            assert car_in_db in wiki_cars_via_reference
            if car_in_db.id == car.id:
                compare_counter += 1
                assert car_in_db.page_id == car.page_id
                assert car_in_db.car_name == car.car_name
                assert car_in_db.wiki_name == car.wiki_name
                assert car_in_db.category_short_eu == car.category_short_eu
                assert car_in_db.brand_name == car.brand_name
                assert car_in_db.page_language == car.page_language
                wiki_categories_via_reference.add(car_in_db.category)
    assert compare_counter == len(wiki_cars_in_db)
    assert len(wiki_categories_via_reference) == 1
    assert wiki_categories_in_db[0] == wiki_categories_via_reference.pop()
    for index, object_collection in reversed(wikipedia_reader.objects_ordered.items()):
        for db_object in object_collection:
            db.delete(db_object)
    db.commit()
