import datetime
from typing import Any, Dict, Union

from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from pydantic import BaseModel, validator
from shapely.geometry import shape

from app.misc.json_encoders import json_encoders


class TrackBase(BaseModel):
    id: str
    sensor_id: str
    length: float
    begin: datetime.datetime
    end: datetime.datetime
    geom: dict

    class Config:
        arbitrary_types_allowed = True
        json_encoders = json_encoders


# Properties to receive on Track creation
class TrackCreate(TrackBase):
    pass


# Properties to receive on Track update
class TrackUpdate(TrackBase):
    pass


# Properties shared by models stored in DB
class TrackInDBBase(TrackBase):
    # sensor_id: str
    geom: Any

    @validator("geom", pre=True, always=True, allow_reuse=True)
    def geom_parser(cls, v: Any) -> Union[WKBElement, None]:
        geometry: Union[WKBElement, None] = None
        if isinstance(v, Dict):
            is_linestring = [
                (key, value)
                for (key, value) in v.items()
                if isinstance(key, str)
                and key.lower() == "type"
                and value.lower() == "linestring"
            ]
            if is_linestring:
                geometry = from_shape(shape(v), 4326)
        elif not isinstance(v, WKBElement):
            raise ValueError("must be a valid WKBE element")
        return geometry

    class Config(TrackBase.Config):
        orm_mode = True


# Properties to return to client
class Track(TrackInDBBase):
    pass


# Properties properties stored in DB
class TrackInDB(TrackInDBBase):
    pass
