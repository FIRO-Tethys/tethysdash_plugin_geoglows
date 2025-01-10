from intake.source import base
from .utilities import load_country_list, load_country_extents


class Map(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "geoglows_map"
    visualization_args = {"country": load_country_list()}
    visualization_group = "GEOGLOWS"
    visualization_label = "GEOGLOWS Map"
    visualization_type = "custom"
    country_extents = load_country_extents()

    def __init__(self, country="All Countries", metadata=None):
        self.url = "http://localhost:4000/remoteEntry.js"
        self.scope = "geoglows_map"
        self.module = "./MapComponent"
        self.country = country
        super(Map, self).__init__(metadata=metadata)

    def read(self):
        """
            Return the configuration for the map
        """

        mapConfig = {
            'className': 'ol-map',
            'style': {
                'width': '100%',
                'height': '100%',
            },
        }

        viewConfig = self.get_viewConfig()

        layers = [
            {
                'type': 'WebGLTile',
                'props': {
                    'source': {
                        'type': 'ImageTile',
                        'props': {
                            'url': 'https://server.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
                            'attributions':
                                'Tiles © <a href="https://server.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer">ArcGIS</a>',
                        },
                    },
                    'name': 'Dark Gray Map',
                    'zIndex': 0,
                },
            },
            {
                'type': 'WebGLTile',
                'props': {
                    'source': {
                        'type': 'ImageTile',
                        'props': {
                            'url': 'https://server.arcgisonline.com/arcgis/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
                            'attributions':
                                'Tiles © <a href="https://server.arcgisonline.com/arcgis/rest/services/World_Topo_Map/MapServer">ArcGIS</a>',
                        }
                    },
                    'name': 'Topographic Map',
                    'zIndex': 1,
                }
            },
            {
                'type': 'ImageLayer',
                'props': {
                    'source': {
                        'type': 'ImageArcGISRest',
                        'props': {
                            'url':
                                'https://livefeeds3.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer',
                            'params': {
                                'layerDefs':
                                    '' if self.country == "All Countries" else f"0: rivercountry='{self.country}'"
                            },
                        },
                    },
                    'name': 'Geoglows Streamflow',
                    'zIndex': 3,
                },
            }
        ]

        legend = [
            {'label': 'Normal', 'color': '#4BACCC'},
            {'label': 'Exceeds 2yr', 'color': '#F7D23E'},
            {'label': 'Exceeds 10yr', 'color': '#FF813D'},
            {'label': 'Exceeds 25yr', 'color': '#FA4343'},
            {'label': 'Exceeds 50yr', 'color': '#BC25F7'}
        ]

        return {
            "url": self.url,
            "scope": self.scope,
            "module": self.module,
            "props": {
                "layers": layers,
                "viewConfig": viewConfig,
                "mapConfig": mapConfig,
                "legend": legend
            },
        }

    def get_viewConfig(self):
        extent = Map.country_extents.get(self.country)
        if extent:
            viewConfig = {
                'projection': 'EPSG:4326',
                'extent': extent,
                'center': [0, 0],  # doesn't matter
                'zoom': 5,  # doesn't matter
                'smoothExtentConstraint': True,
                'showFullExtent': True
            }
        else:
            viewConfig = {'projection': 'EPSG:4326', 'center': [0, 20], 'zoom': 2}
        return viewConfig
