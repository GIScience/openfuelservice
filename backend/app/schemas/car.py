from typing import Dict, List

from pydantic import BaseModel

# Properties to return to client
from app.schemas.schema_base import SchemaBase


class Car(BaseModel):
    id: str
    manufacturer: str
    model: str
    description: str
    fuel_type: str
    year: int

    class Config:
        orm_mode = True


class Cars(SchemaBase):
    data: List[Car]


class CarsSorted(SchemaBase):
    data: Dict
