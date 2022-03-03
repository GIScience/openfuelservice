from app.crud.base import CRUDBase
from app.models import EnvirocarSensor
from app.schemas.envirocar_sensor import SensorCreate, SensorUpdate

envirocar_sensor = CRUDBase[EnvirocarSensor, SensorCreate, SensorUpdate](
    EnvirocarSensor
)
