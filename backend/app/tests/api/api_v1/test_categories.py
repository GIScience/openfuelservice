from typing import Dict, Generator, List, Tuple

import pytest
import responses
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import WikiCar, WikiCarCategory
from app.schemas.category import Category


@pytest.mark.anyio
async def test_read_categories(
    async_client: AsyncClient,
    db: Session,
    mock_all_responses: Generator[responses.RequestsMock, None, None],
    mock_wikipedia_objects: Tuple[List[WikiCarCategory], List[WikiCar]],
) -> None:
    response = await async_client.get(
        f"{settings.API_V1_STR}/categories/",
    )
    assert response.status_code == 200
    content: dict = response.json()
    assert isinstance(content["data"], list)
    data = content["data"]
    assert len(data) == 1
    assert isinstance(data, list)
    category: Dict
    for category in data:
        wiki_car_category_orm: Category = Category.parse_obj(category)
        present: bool = False
        wikicar_category: WikiCarCategory
        for wikicar_category in mock_wikipedia_objects[0]:
            if (
                wiki_car_category_orm.category_short_eu
                == wikicar_category.category_short_eu
                and wiki_car_category_orm.category_name_en
                == wikicar_category.category_name_en
                and wiki_car_category_orm.category_name_de
                == wikicar_category.category_name_de
            ):
                present = True
        assert present
