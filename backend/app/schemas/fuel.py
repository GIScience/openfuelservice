from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException
from pydantic import BaseModel, Field, validator
from shapely.geometry import LineString, shape

from app.db.importer.mappings import FuelMappings
from app.schemas.schema_base import SchemaBase


class DrivingStyles(str, Enum):
    moderate = "moderate"
    fast = "fast"


class DataSource(str, Enum):
    carfueldata = "carfueldata"
    envirocar = "envirocar"


class FuelCalculationResults(BaseModel):
    fuel_type: FuelMappings
    fuel_liter_total: float
    fuel_liter_per_100km: float
    co2_gram_total: float
    co2_gram_per_km: float

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True

    @validator(
        "fuel_liter_total", "fuel_liter_per_100km", "co2_gram_total", "co2_gram_per_km"
    )
    def round_result(cls, v: float) -> float:
        if not isinstance(v, float) and not isinstance(v, int):
            return 0.0
        return round(v, 3)


class FuelRequestCars(BaseModel):
    car_ids: List[str] = Field(
        None, example=["a1234"], description="Provide with valid car IDs."
    )
    geojson: Dict = Field(
        ...,
        example={
            "coordinates": [
                [10.502782, 51.181212],
                [10.50239, 51.1812],
                [10.501769, 51.181171],
                [10.501072, 51.181138],
            ],
            "type": "LineString",
        },
    )
    driving_style: Optional[DrivingStyles] = Field(
        DrivingStyles.moderate.name,
    )
    tank_size: Optional[int] = Field(None, example=10)
    request_id: Optional[str] = Field(None, example="test123")

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True

    @validator("geojson", pre=True, always=True, allow_reuse=True)
    def geom_parser(cls, v: Any) -> Union[Any, None]:
        try:
            geometry = shape(v)
        except Exception:
            geometry = None
        if not geometry:
            raise HTTPException(status_code=422, detail="GeoJSON couldn't be parsed.")
        elif not isinstance(geometry, LineString):
            raise HTTPException(
                status_code=400, detail="GeoJSON is valid but not a LineString."
            )
        return v


class FuelResponse(SchemaBase):
    pass
