import asyncio
import logging
from typing import List, Set, Union

import tqdm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.matching.base_matcher import BaseMatcher
from app.misc.data_handling import (
    check_brand_aliases,
    check_fixed_matches,
    check_name_for_year,
    get_brand_aliases,
)

logger = logging.getLogger(settings.PROJECT_NAME)


class EnvirocarMatcher(BaseMatcher):
    def __init__(self, models_path: str, db: Session):
        super().__init__(models_path, db)

    async def _match_with_wikicars(
        self, manufacturer: str, powerset: Set, accuracy: Union[float, None] = None
    ) -> List:
        tasks = [
            self.classify(
                model_name=manufacturer, car_name=power, accuracy_threshold=accuracy
            )
            # creating task starts coroutine
            for power in powerset
        ]

        pbar = tqdm.tqdm(total=len(tasks), position=0, ncols=90, desc=" Matching cars")
        matches: Set = set()
        for f in asyncio.as_completed(tasks):
            values = await f
            matches.update(values)
            pbar.update()
        return list(matches)

    async def match(
        self,
        manufacturer: str,
        car: str,
        accuracy: float = 0.91,
    ) -> List:
        year: Union[int, None] = check_name_for_year(car)
        fixed_matches: List = check_fixed_matches(
            manufacturer=manufacturer, car_name=car, year=year
        )
        if not len(fixed_matches):
            cleaned_manufacturer, cleaned_car = check_brand_aliases(
                short_name=manufacturer, car_name=car
            )
            if cleaned_manufacturer is None or cleaned_car is None:
                return []
            prepared_powerset: Set = self._prepare_match(
                cleaned_manufacturer=cleaned_manufacturer,
                manufacturer=manufacturer,
                cleaned_car=cleaned_car,
            )
            aliases: List = get_brand_aliases(brand_name=cleaned_manufacturer)
            await self._initialize_models(aliases)
            matches: List = await self._match_with_wikicars(
                manufacturer=cleaned_manufacturer,
                powerset=prepared_powerset,
                accuracy=accuracy,
            )
        else:
            matches = [(match, 1.0) for match in fixed_matches]
        wiki_cars: List = [
            (self.get_wikicars_by_name(match[0]), match[1]) for match in matches
        ]
        ids: Set = set()
        for match in list(wiki_cars):
            if not len(match[0]):
                wiki_cars.remove(match)
                continue
            if match[0][0].id in ids:
                wiki_cars.remove(match)
            ids.add(match[0][0].id)
        return wiki_cars
