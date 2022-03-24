# Shared properties
from pydantic_sqlalchemy import sqlalchemy_to_pydantic

from app.models import CarFuelDataCar


class CarfueldataCarBase(sqlalchemy_to_pydantic(CarFuelDataCar)):  # type: ignore
    class Config:
        arbitrary_types_allowed = True


# Properties to receive on Sensor creation
class CarfueldataCarCreate(CarfueldataCarBase):
    pass


# Properties to receive on Sensor update
class CarfueldataCarUpdate(CarfueldataCarBase):
    pass


# Properties shared by models stored in DB
class CarfueldataCarInDBBase(CarfueldataCarBase):
    pass

    class Config:
        orm_mode = True


# Properties to return to client
class Sensor(CarfueldataCarInDBBase):
    pass


# Properties properties stored in DB
class SensorInDB(CarfueldataCarInDBBase):
    pass
