from typing import Any, Union

from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry.base import BaseGeometry

json_encoders = {}


class ToShapeDecoder:
    @staticmethod
    def __serialize__(v: Any) -> Union[Any, BaseGeometry, None]:
        if isinstance(v, WKBElement):
            if not v.data:
                return None
            return to_shape(v)
        return v


json_encoders[WKBElement] = ToShapeDecoder.__serialize__
