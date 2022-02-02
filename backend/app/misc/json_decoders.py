import logging
from typing import Any, Union

from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely.errors import ShapelyError
from shapely.geometry import shape

logger = logging.getLogger(__name__)


def json_to_wkb_element(v: Any) -> Union[WKBElement, None]:
    geometry: Union[WKBElement, None] = None
    try:
        if (
            isinstance(v, dict)
            and all(key in v.keys() for key in ["type", "geometry"])
            and v.get("type") == "Feature"
        ):
            # Extract the features geometry.
            v = v.pop("geometry")
        geometry = from_shape(shape(v), 4326)
    except ShapelyError:
        logger.warning(f"Couldn't convert to WKBElement continuing without: {v}")
        geometry = None
    except Exception as err:
        logger.error(f"Encountered unknown error while converting to WKBElement: {v}")
        geometry = None
        raise err
    finally:
        return geometry
