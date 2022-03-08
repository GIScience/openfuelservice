import asyncio
import logging
from typing import List, Set, Tuple, Union

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
from app.models import EnvirocarSensor, WikicarEnvirocar

logger = logging.getLogger(settings.PROJECT_NAME)


class EnvirocarMatcher(BaseMatcher):
    def __init__(self, models_path: str, db: Session):
        super().__init__(models_path, db)

    async def _match_with_wikicars(
        self, manufacturer: str, powerset: Set, accuracy: Union[float, None] = None
    ) -> List:
        tasks = [
            self.classify(model_name=manufacturer, car_name=power, accuracy=accuracy)
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
        car: Union[EnvirocarSensor],
        accuracy: Union[float, None] = None,
    ) -> Union[List[WikicarEnvirocar], None]:
        if not car or not isinstance(car, EnvirocarSensor):
            return None
        year: Union[int, None] = check_name_for_year(car.model)
        if not year:
            year = car.constructionyear
        manufacturer = car.manufacturer
        car_name = car.model
        fixed_matches: List = check_fixed_matches(
            manufacturer=manufacturer, car_name=car_name, year=year
        )
        if not len(fixed_matches):
            cleaned_manufacturer, cleaned_car = check_brand_aliases(
                short_name=manufacturer, car_name=car_name
            )
            if cleaned_manufacturer is None or cleaned_car is None:
                return None
            prepared_powerset: Set = self._prepare_match(
                cleaned_manufacturer=cleaned_manufacturer,
                manufacturer=manufacturer,
                cleaned_car=cleaned_car,
            )
            prepared_powerset.add(f"{cleaned_manufacturer} {cleaned_car}")
            aliases: List = get_brand_aliases(brand_name=cleaned_manufacturer)
            await self.initialize_models(aliases)
            matches: List = await self._match_with_wikicars(
                manufacturer=cleaned_manufacturer,
                powerset=prepared_powerset,
                accuracy=accuracy,
            )
        else:
            matches = [(match, 1.0) for match in fixed_matches]
        wiki_cars: List = [
            (self.get_wikicar_by_name(match[0]), match[1]) for match in matches
        ]
        wikicar_ids: Set = set()
        wikicar_envirocar_matches: List = []
        wiki_car: Tuple
        for wiki_car in list(wiki_cars):
            if wiki_cars[0] is None or not len(wiki_cars[0]):
                continue
            if wiki_car[0] is None or wiki_car[0].id in wikicar_ids:
                continue
            wikicar_envirocar_matches.append(
                WikicarEnvirocar(
                    envirocar_sensor_id=car.id,  # type: ignore
                    wikicar_id=wiki_car[0].id,  # type: ignore
                    matching_accuracy=wiki_car[1],  # type: ignore
                )
            )
            wikicar_ids.add(wiki_car[0].id)
        if not len(wikicar_envirocar_matches):
            return None
        return list(wikicar_envirocar_matches)
