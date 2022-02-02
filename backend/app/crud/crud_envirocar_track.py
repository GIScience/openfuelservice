from app.crud.base import CRUDBase
from app.models import EnvirocarTrack
from app.schemas.track import TrackCreate, TrackUpdate


class CRUDEnvirocarTrack(CRUDBase[EnvirocarTrack, TrackCreate, TrackUpdate]):
    pass


track = CRUDEnvirocarTrack(EnvirocarTrack)
