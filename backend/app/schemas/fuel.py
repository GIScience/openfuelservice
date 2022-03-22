from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException
from pydantic import BaseModel, Field, validator
from shapely.geometry import LineString, shape

from app.schemas import ORSFeatureCollection
from app.schemas.schema_base import ReturnSchemaBase


class DrivingStyles(str, Enum):
    moderate = "moderate"
    fast = "fast"


class DataSource(str, Enum):
    carfueldata = "carfueldata"
    envirocar = "envirocar"


class FuelCalculationResults(BaseModel):
    fuel_type: str
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

    def __add__(self, other: Any) -> Any:
        if self.fuel_type != other.fuel_type:
            raise ValueError("FuelCalculationResults need the same fuel type.")
        if not isinstance(other, FuelCalculationResults):
            raise TypeError(
                "Addition can only happen between FuelCalculationResults with the same fuel types."
            )
        self.fuel_liter_total += other.fuel_liter_total
        self.fuel_liter_per_100km = (
            self.fuel_liter_per_100km + other.fuel_liter_per_100km
        ) / 2
        self.co2_gram_total += other.co2_gram_total
        self.co2_gram_per_km = (other.co2_gram_per_km + self.co2_gram_per_km) / 2
        return self


class GeojsonFuelRequestCars(BaseModel):
    car_ids: List[str] = Field(
        None, example=["a1234"], description="Provide with valid car IDs."
    )
    geometry: Dict = Field(
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

    @validator("geometry", pre=True, always=True, allow_reuse=True)
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


class OpenrouteserviceFuelRequest(GeojsonFuelRequestCars):
    @validator("geometry", pre=True, always=True, allow_reuse=True)
    def geom_parser(cls, v: Any) -> Union[Any, None]:
        try:
            geometry = ORSFeatureCollection.parse_obj(v)
        except Exception:
            geometry = None
        if not geometry:
            raise HTTPException(
                status_code=422, detail="Openrouteservice response couldn't be parsed."
            )
        elif not isinstance(geometry, ORSFeatureCollection):
            raise HTTPException(
                status_code=400,
                detail="Unknown error while parsing Openrouteservice response.",
            )
        return v


class FuelResponse(BaseModel):
    co2_gram_per_km: float
    co2_gram_total: float
    fuel_liter_per_100km: float
    fuel_liter_total: float
    fuel_type: str


class FuelResponseEncapsulated(ReturnSchemaBase):
    data: FuelCalculationResults
