from typing import List, Set, Union

from sqlalchemy.orm import Session

from app.matching.manufacturer_matching import ManufacturerAnnCollection
from app.misc.data_handling import (
    check_name_for_year,
    create_permutations,
    get_brand_aliases,
)
from app.models import WikiCar


class BaseMatcher(ManufacturerAnnCollection):
    def __init__(self, models_path: str, db: Session):
        super().__init__(models_path)
        self._db = db

    @staticmethod
    def _prepare_match(
        cleaned_manufacturer: str,
        cleaned_car: str,
        manufacturer: str = "",
    ) -> Set:
        avoidables: Set = {manufacturer, cleaned_manufacturer}
        aliases: List = get_brand_aliases(brand_name=cleaned_manufacturer)
        avoidables.update(aliases)
        permutations: List = create_permutations(
            f"{cleaned_manufacturer} {cleaned_car}"
        )
        year: Union[int, None] = check_name_for_year(cleaned_car)
        if year is not None:
            car_without_year: Union[str, None] = cleaned_car.replace(
                str(year), " "
            ).strip()
            if car_without_year:
                permutations.extend(
                    create_permutations(f"{cleaned_manufacturer} {car_without_year}")
                )
        return set(permutations)

    def get_wikicars_by_name(self, wiki_name: str) -> Union[List[WikiCar], None]:
        return self._db.query(WikiCar).filter(WikiCar.wiki_name == wiki_name).all()

    async def match(self, manufacturer: str, car: str, accuracy: float = 0.99) -> List:
        pass
