import math
from functools import partial

import pyproj
from shapely.geometry import LineString
from shapely.ops import transform


def truncate(f: float, n: int) -> str:
    """Truncates/pads a float f to n decimal places without rounding"""
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d + '0' * n)[:n]])


def parse_geometry(geometry: list) -> list:
    """
     GeoJSON order is [longitude, latitude, elevation].

    :param geometry: Is a list of coordinates in latLng order
    :type geometry: list

    :return: returns a list of coordinates in lngLat order for geojson
    :type: list
    """

    geom = []
    for coords in geometry:
        geom.append((float(coords[0]), float(coords[1])))
        if coords[2]:
            geom.append(float(coords[2]))
    return geom


def transform_geom(g1, src_proj: str, dest_proj: str):
    project = partial(
        pyproj.transform,
        pyproj.Proj(init=src_proj),
        pyproj.Proj(init=dest_proj))

    g2 = transform(project, g1)

    return g2


def validate_limit(radius: int, limit: int) -> bool:
    """
    Returns True if radius is in custom specific limits.

    :param radius: The radius of the request in meters
    :type radius: int

    :param limit: The limit set by the custom settings
    :type limit: int

    :return: True if radius within limits, otherwise False
    :type: bool
    """

    if 0 <= radius <= limit:
        return True

    return False


def convert_wgs_to_utm_epsg(lon: float, lat: float):
    utm_band = str((math.floor((lon + 180) / 6) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0' + utm_band
    if lat >= 0:
        epsg_code = '326' + utm_band
    else:
        epsg_code = '327' + utm_band
    return epsg_code


def true_linestring_length(linestring: LineString) -> float:
    """
    Calculates the true length in meter from a linestring not the geometric non-unit distance.
    :param linestring: Shapely BaseGeometry!!!
    :return: Returns the length in float
    """
    centroid_longitude: float = linestring.centroid.coords.xy[0][0]
    centroid_latitude: float = linestring.centroid.coords.xy[1][0]
    destination_epsg = convert_wgs_to_utm_epsg(lon=centroid_longitude, lat=centroid_latitude)
    transformation_profile = partial(pyproj.transform,
                                          pyproj.Proj(init='epsg:4326'),
                                          pyproj.Proj(init='epsg:{}'.format(destination_epsg)))
    route_length_in_meter = transform(transformation_profile, linestring).length
    return route_length_in_meter
