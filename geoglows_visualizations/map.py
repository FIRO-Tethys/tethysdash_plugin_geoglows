from intake.source import base


class Map(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "geoglows_map"
    visualization_args = {}
    visualization_group = "GEOGLOWS"
    visualization_label = "GEOGLOWS Map"
    visualization_type = "map"

    def __init__(self, metadata=None):
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

        viewConfig = {
            'center': [0, 20],
            'zoom': 2,
        }

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
                    'name': 'World Dark Gray Base Map',
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
                    'name': 'World Topographic Map',
                    'zIndex': 1,
                }
            },
            {
                'type': 'ImageLayer',
                'props': {
                    'source': {
                        'type': 'ImageArcGISRest',
                        'props': {
                            'url': 'https://livefeeds3.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer',
                        },
                    },
                    'name': 'Geoglows Streamflow',
                    'zIndex': 2,
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
            "mapConfig": mapConfig,
            "viewConfig": viewConfig,
            "layers": layers,
            "legend": legend
        }