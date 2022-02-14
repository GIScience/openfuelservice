from typing import List

from pydantic import BaseModel

from app.schemas.schema_base import SchemaBase


class Category(BaseModel):
    id: str
    category_short_eu: str
    category_name_de: str
    category_name_en: str

    class Config:
        orm_mode = True


class Categories(SchemaBase):
    data: List[Category]
