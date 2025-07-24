from intake.source import base
import os
import json
from .utilities import load_country_list, load_country_extents, convert_4326_to_3857


class Map(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "geoglows_map"
    visualization_args = {
        "country": load_country_list(),
    }
    visualization_tags = [
        "geoglows",
        "streamflow",
        "map"
    ]
    visualization_description = ""
    visualization_group = "GEOGLOWS"
    visualization_label = "GEOGLOWS Map"
    visualization_type = "map"
    _user_parameters = []

    country_extents = load_country_extents()

    def __init__(self, country, metadata=None, **kwargs):
        self.country = country
        super(Map, self).__init__(metadata=metadata)

    def read(self):
        module_path = os.path.dirname(__file__)
        file_path = f'{module_path}/map_configs.json'
        map_config = {}
        with open(file_path) as file:
            map_config = json.load(file)
        map_config = map_config['args_string']
        # Link Geoglows Streamflow layer with self.country
        layers = map_config['layers']
        for layer in layers:
            props = layer['configuration']['props']
            if props['name'] == 'Geoglows Streamflow':
                if self.country == 'All Countries':
                    props['source']['props']['params']['LAYERDEFS'] = ''
                else:
                    props['source']['props']['params']['LAYERDEFS'] = f"0: rivercountry='{self.country}'"
        # Update map extent
        map_config['map_extent'] = {'extent': self.get_map_extent()}
        return map_config

    def get_map_extent(self):
        extent = Map.country_extents.get(self.country)
        if extent:
            lon_center = (extent[0] + extent[2]) / 2
            lat_center = (extent[1] + extent[3]) / 2
            center = convert_4326_to_3857(lon_center, lat_center)
            return f"{center[0]},{center[1]},6"
        else:
            return "0, 2273030.9269876895,2"
