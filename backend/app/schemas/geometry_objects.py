from typing import Dict, List, Optional

from pydantic import BaseModel


class Geometry(BaseModel):
    coordinates: List[List[float]]
    type: str

    class Config:
        orm_mode = True


class ORSStep(BaseModel):
    distance: float
    duration: float
    type: int
    instruction: str
    name: str
    way_points: List[int]

    class Config:
        orm_mode = True


class ORSSegment(BaseModel):
    distance: float
    duration: float
    steps: List[ORSStep]
    detourfactor: float
    percentage: float
    ascent: float
    descent: float

    class Config:
        orm_mode = True


class ORSSummary(BaseModel):
    distance: float
    duration: float


class ORSProperty(BaseModel):
    ascent: float
    descent: float
    segments: List
    extras: Optional[Dict]
    summary: Dict
    way_points: List[int]

    class Config:
        orm_mode = True


class ORSFeature(BaseModel):
    bbox: List[float]
    type: str
    properties: ORSProperty
    geometry: Geometry

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True


class ORSMetadata(BaseModel):
    attribution: str
    service: str
    timestamp: int
    query: Dict
    engine: Dict


class ORSFeatureCollection(BaseModel):
    features: List[ORSFeature]
    bbox: List[float]
    metadata: Optional[ORSMetadata]

    class Config:
        orm_mode = True
