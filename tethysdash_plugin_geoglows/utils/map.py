import os
import json
from pyproj import Transformer


module_path = os.path.dirname(__file__)


def load_country_list():
    filename = os.path.join(module_path, "../data/countries_extents.json")
    country_list = []
    with open(filename, "r") as file:
        data = json.load(file)
    for country_name, _extent in data.items():
        country_list.append({"value": country_name, "label": country_name})
    return country_list


def load_country_extents():
    filename = os.path.join(module_path, "../data/countries_extents.json")
    country_extent = {}
    with open(filename, "r") as file:
        data = json.load(file)
    for country_name, extent in data.items():
        if extent:
            extent[0] -= 0.1
            extent[1] -= 0.1
            extent[2] += 0.1
            extent[3] += 0.1
        country_extent[country_name] = extent
    return country_extent


def convert_4326_to_3857(lon, lat):
    """
    Convert WGS84 (EPSG:4326) to Web Mercator (EPSG:3857).

    Parameters:
        lat (float): Latitude in degrees.
        lon (float): Longitude in degrees.

    Returns:
        (x, y): Tuple of coordinates in meters.
    """
    transformer = Transformer.from_crs(4326, 3857, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y
