from pydantic import BaseModel


class EnvirocarSensorStatisticBase(BaseModel):
    id: str
    name: str
    max: float
    avg: float
    min: float
    measurements: int
    tracks: int
    users: int
    sensors: int

    class Config:
        orm_mode = True


class EnvirocarSensorStatisticCreate(EnvirocarSensorStatisticBase):
    id: str
    name: str
    max: float
    avg: float
    min: float
    measurements: int
    tracks: int
    users: int
    sensors: int


class EnvirocarSensorStatisticUpdate(EnvirocarSensorStatisticBase):
    id: str
    name: str
    max: float
    avg: float
    min: float
    measurements: int
    tracks: int
    users: int
    sensors: int
