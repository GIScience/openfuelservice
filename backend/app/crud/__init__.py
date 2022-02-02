from .crud_envirocar_sensor import sensor
from .crud_envirocar_track import track
from .crud_envirocar_track_measurement import track_measurement
from .crud_item import item
from .crud_user import user

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
