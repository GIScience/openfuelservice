from pydantic import BaseModel

# Shared properties
from app.schemas.schema_base import ReturnSchemaBase


class SensorBase(BaseModel):
    id: str
    type: str
    model: str
    manufacturer: str
    fueltype: str
    constructionyear: int
    enginedisplacement: int

    class Config:
        orm_mode = True


# Properties to receive on Sensor creation
class SensorCreate(SensorBase):
    id: str
    type: str
    model: str
    manufacturer: str
    fueltype: str
    constructionyear: int
    enginedisplacement: int


# Properties to receive on Sensor update
class SensorUpdate(SensorBase):
    pass


# Properties shared by models stored in DB
class SensorInDBBase(SensorBase):
    pass

    class Config:
        orm_mode = True


# Properties to return to client
class SensorResponse(ReturnSchemaBase):
    data: SensorBase

    class Config:
        orm_mode = True


# Properties properties stored in DB
class SensorInDB(SensorInDBBase):
    pass
