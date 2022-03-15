from app.crud.base import CRUDBase
from app.models import EnvirocarPhenomenon
from app.schemas.envirocar_phenomenon import PhenomenonCreate, PhenomenonUpdate

envirocar_phenomenon = CRUDBase[
    EnvirocarPhenomenon, PhenomenonCreate, PhenomenonUpdate
](EnvirocarPhenomenon)
