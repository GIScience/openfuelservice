import logging
from pathlib import Path
from typing import Dict, List, Union

import wikipediaapi
from tqdm import tqdm

from app.core.config import settings
from app.db.importer.base_reader import BaseReader
from app.misc.data_handling import (
    check_brand_aliases,
    check_brands,
    check_static_vehicles_list,
    clean_vehicle_name,
    vehicle_is_ignored,
)
from app.misc.requests_tools import ThreadedRequests
from app.models import WikiCar, WikiCarCategory

logger = logging.getLogger(__name__)


class WikipediaReader(BaseReader):
    def __init__(
        self,
        categories: Dict,
        file_or_url: Union[str, Path, None],
        threads: Union[int, None] = None,
    ):
        super().__init__(file_or_url)
        self._headers = settings.GLOBAL_HEADERS
        self._threads = threads
        self._threaded_requests = ThreadedRequests()
        if "car_categories" not in categories:
            logger.warning(
                f"No car categories found. Partially initialized class: {self.__class__}."
            )
            return
        self._raw_car_categories: Dict = categories["car_categories"]

    def get_category_data(self, categories: Dict) -> List[WikiCarCategory]:
        category_objects: List = []
        category: str
        for category in categories:
            category_names: List = categories[category]["category_names"]
            category_objects.append(
                WikiCarCategory(
                    category_name_de=categories[category]["de"],
                    category_name_en=categories[category]["en"],
                    id=category,
                    category_wiki_names=category_names,
                )
            )
        return category_objects

    def get_category_car_data(
        self, category_db_objects: List[WikiCarCategory]
    ) -> List[WikiCar]:
        wiki_cars: List = []
        category: WikiCarCategory
        for category in tqdm(
            category_db_objects,
            total=len(category_db_objects),
            unit=" Processing Wikipedia Categories",
        ):
            sub_category: str
            for sub_category in category.category_wiki_names:
                if "Category" in sub_category:
                    wiki_wiki = wikipediaapi.Wikipedia(language="en", timeout=None)
                else:
                    wiki_wiki = wikipediaapi.Wikipedia(language="de", timeout=None)
                page: wikipediaapi.WikipediaPage = wiki_wiki.page(sub_category)
                category_members: Dict = page.categorymembers
                if not category_members:
                    logger.warning(f"Category: {sub_category} is empty")
                    continue
                category_members = {
                    k: v
                    for (k, v) in category_members.items()
                    if not vehicle_is_ignored(k)
                }
                for key in list(category_members):
                    wiki_car: Union[WikiCar, None] = self._process_category_member(key)
                    if not wiki_car:
                        continue
                    wiki_car.page_id = page.pageid
                    wiki_car.page_language = page.language
                    wiki_car.category_short_eu = category.category_short_eu
                    wiki_car.category_short_eu = category.id
                    wiki_car.wiki_name = key
                    wiki_cars.append(wiki_car)
        return wiki_cars

    @staticmethod
    def _process_category_member(member_name: str) -> Union[WikiCar, None]:
        ignore_check: bool = vehicle_is_ignored(car_brand_or_name=member_name)
        if ignore_check or not member_name:
            return None
        # Todo check if cleaning is necessary
        revised_member_name: Union[str, None] = clean_vehicle_name(member_name)
        if not revised_member_name or not len(revised_member_name) > 1:
            return None
        short_name: str = revised_member_name
        # Iterate over the chars and remove them one after the other. TODO Revise
        for char in range(len(revised_member_name)):
            model_brand, model_name = check_static_vehicles_list(
                car_name=revised_member_name
            )
            if model_brand and model_name:
                return WikiCar(brand_name=model_brand, car_name=model_name)

            model_brand, model_name = check_brand_aliases(
                short_name=short_name, car_name=revised_member_name
            )
            if model_brand and model_name:
                return WikiCar(brand_name=model_brand, car_name=model_name)

            model_brand, model_name = check_brands(
                short_name=short_name, wiki_name=revised_member_name
            )
            if model_brand and model_name:
                return WikiCar(brand_name=model_brand, car_name=model_name)
            elif len(short_name) > 1:
                short_name = short_name[:-1]
            else:
                break
        logger.debug(f"Missing brand for car: {member_name}")
        return None

    def _process_data(self, data_file: Union[Path, None]) -> None:
        category_db_objects: List[WikiCarCategory] = self.get_category_data(
            categories=self._raw_car_categories
        )
        self.objects_ordered[0] = category_db_objects

        wiki_category_cars: List[WikiCar] = self.get_category_car_data(
            category_db_objects=category_db_objects
        )
        self.objects_ordered[1] = wiki_category_cars
