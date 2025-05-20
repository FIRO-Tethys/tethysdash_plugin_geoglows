from intake.source import base
import os
import json
from .utilities import load_country_list


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
                props['source']['props']['params']['LAYERDEFS'] = f"0: rivercountry='{self.country}'"
        return map_config
