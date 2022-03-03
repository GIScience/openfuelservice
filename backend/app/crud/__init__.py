from .crud_envirocar_sensor import envirocar_sensor
from .crud_envirocar_track import envirocar_track
from .crud_envirocar_track_measurement import envirocar_track_measurement
from .crud_item import item
from .crud_user import user

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
