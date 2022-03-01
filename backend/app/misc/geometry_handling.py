from typing import Tuple, Union

from geopy.distance import great_circle
from shapely.geometry import LineString


def linestring_length_in_meter(linestring: LineString) -> Union[float, None]:
    """
    Calculates the true length in meter from a linestring.
    The greate_circle algorithm is costly, but delivers better results for longer routes.

    :param linestring: LineString
    :return: Returns the length in float
    """
    if linestring is None or not isinstance(linestring, LineString):
        return None
    test = linestring.coords
    coordinate_tuple: Union[Tuple[float, float, float], Tuple[float, float]]
    length: Union[float, None] = None
    last_coordinate_tuple: Union[
        Tuple[float, float, float], Tuple[float, float], None
    ] = None
    for coordinate_tuple in test:
        next_coordinate_tuple = coordinate_tuple[::-1]
        if last_coordinate_tuple:
            segment_length = great_circle(
                last_coordinate_tuple, next_coordinate_tuple
            ).m
            length += segment_length if segment_length is not None else 0
        else:
            length = 0
        last_coordinate_tuple = next_coordinate_tuple
    return length
