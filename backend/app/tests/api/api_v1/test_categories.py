from typing import Dict, Generator, List

import pytest
import responses
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import WikiCarCategory
from app.schemas.category import Category


@pytest.mark.anyio
async def test_read_categories(
    async_client: AsyncClient,
    db: Session,
    mock_wikipedia_responses: Generator[responses.RequestsMock, None, None],
    mock_wikipedia_car_categories: Generator[List[WikiCarCategory], None, None],
) -> None:
    response = await async_client.get(f"{settings.API_V1_STR}/categories/",)
    assert response.status_code == 200
    content: dict = response.json()
    assert isinstance(content["data"], list)
    data = content["data"]
    assert len(data) == 1
    assert isinstance(data, list)
    mock_category: WikiCarCategory = mock_wikipedia_car_categories[0]  # type: ignore
    category: Dict
    for category in data:
        wiki_car_category_orm: Category = Category.parse_obj(category)
        assert wiki_car_category_orm.id == mock_category.id
        assert (
            wiki_car_category_orm.category_short_eu == mock_category.category_short_eu
        )
        assert wiki_car_category_orm.category_name_en == mock_category.category_name_en
        assert wiki_car_category_orm.category_name_de == mock_category.category_name_de
