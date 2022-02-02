from app.crud.base import CRUDBase
from app.models import EnvirocarSensor
from app.schemas.sensor import SensorCreate, SensorUpdate

sensor = CRUDBase[EnvirocarSensor, SensorCreate, SensorUpdate](EnvirocarSensor)
