from app.crud.base import CRUDBase
from app.models import EnvirocarSensorStatistic
from app.schemas.envirocar_sensor_statistic import (
    EnvirocarSensorStatisticCreate,
    EnvirocarSensorStatisticUpdate,
)

envirocar_sensor_statistic = CRUDBase[
    EnvirocarSensorStatistic,
    EnvirocarSensorStatisticCreate,
    EnvirocarSensorStatisticUpdate,
](EnvirocarSensorStatistic)
