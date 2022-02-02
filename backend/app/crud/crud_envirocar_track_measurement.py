from app.crud.base import CRUDBase
from app.models import EnvirocarTrackMeasurement
from app.schemas.track_measurement import TrackMeasurementCreate, TrackMeasurementUpdate


class CRUDEnvirocarTrackMeasurement(
    CRUDBase[EnvirocarTrackMeasurement, TrackMeasurementCreate, TrackMeasurementUpdate]
):
    pass


track_measurement = CRUDEnvirocarTrackMeasurement(EnvirocarTrackMeasurement)
