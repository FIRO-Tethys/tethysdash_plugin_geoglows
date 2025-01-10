import React, { useEffect, Fragment } from "react";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import Icon from "ol/style/Icon";
import { LineString } from "ol/geom";
import { Stroke, Style } from "ol/style";
import {
  View,
  Layer,
  Layers,
  Controls,
  LayersControl,
  LegendControl,
  useMapContext,
} from "backlayer";

import WebGLTile from 'ol/layer/WebGLTile.js'
import { ImageTile } from 'ol/source';
import VectorTileLayer from 'ol/layer/VectorTile';
import VectorTileSource from 'ol/source/VectorTile';
import MVT from 'ol/format/MVT';
import LayerGroup from 'ol/layer/Group';
import { applyLayerStyle } from "./lib/utils";
import {applyStyle} from 'ol-mapbox-style';

const MapComponentContent = ({
  viewConfig,
  layers,
  legend,
  updateVariableInputValues,
}) => {
  const { map } = useMapContext();
  const MIN_QUERY_ZOOM = 15;
  const markPath = `
      M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9
      c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z
    `;
  const svgIcon = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40">
        <path d="${markPath}" fill="#007bff" stroke="white" stroke-width="1"/>
      </svg>
    `;
  const svgURI = "data:image/svg+xml;base64," + btoa(svgIcon);

  let markerLayer, streamLayer, riverId;

  useEffect(() => {
    if (!map) return;

    // Add Environment Map
    const vectorTileLayers = {
      // "Environment Base": {
      //   opacity: 1,
      //   zIndex: 1
      // },
      "Environment Watersheds": {
        opacity: 0.85,
        zIndex: 2
      },
      // "Environment Surface Water and Label": {
      //   opacity: 1,
      //   zIndex: 3
      // },
      // "Environment Detail and Label": {
      //   opacity: 1,
      //   zIndex: 4
      // }
    };
    
    const hillshadeLayer = new WebGLTile({
      source: new ImageTile({
        url: 'https://services.arcgisonline.com/arcgis/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}'
      }),
      opacity: 0.75,
      zIndex: 0
    })

    const style = {
      "version": 8,
      "sprite": "https://cdn.arcgis.com/sharing/rest/content/items/3bfd1065c1a748c5ae2f9408c3fb1078/resources/styles/../sprites/sprite",
      "glyphs": "https://basemaps.arcgis.com/arcgis/rest/services/World_Basemap_v2/VectorTileServer/resources/fonts/{fontstack}/{range}.pbf",
      "sources": {
        "esri": {
          "type": "vector",
          "url": "https://basemaps.arcgis.com/arcgis/rest/services/World_Basemap_v2/VectorTileServer",
          "tiles": [
            "https://basemaps.arcgis.com/arcgis/rest/services/World_Basemap_v2/VectorTileServer/tile/{z}/{y}/{x}.pbf"
          ]
        }
      },
      "layers": [
        {
          "id": "Watershed boundary/Region",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            0
          ],
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-opacity": {
              "stops": [
                [
                  0,
                  0.1
                ],
                [
                  5,
                  0.17
                ],
                [
                  8,
                  0.35
                ]
              ]
            },
            "line-color": "#b08f8f",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  0
                ],
                [
                  3,
                  4
                ],
                [
                  6,
                  8
                ],
                [
                  7,
                  9
                ],
                [
                  10,
                  12
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Basin",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            1
          ],
          "minzoom": 4,
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-opacity": {
              "stops": [
                [
                  0,
                  0.1
                ],
                [
                  5,
                  0.16
                ],
                [
                  8,
                  0.35
                ]
              ]
            },
            "line-color": "#ba907f",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  2
                ],
                [
                  3,
                  3
                ],
                [
                  6,
                  7
                ],
                [
                  7,
                  8
                ],
                [
                  10,
                  11
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Sub-basin",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            2
          ],
          "minzoom": 6,
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-opacity": {
              "stops": [
                [
                  0,
                  0.1
                ],
                [
                  6,
                  0.17
                ],
                [
                  8,
                  0.35
                ]
              ]
            },
            "line-color": "#cc977a",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  1
                ],
                [
                  3,
                  2
                ],
                [
                  6,
                  6
                ],
                [
                  7,
                  7
                ],
                [
                  10,
                  10
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Watershed",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            3
          ],
          "minzoom": 8,
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-opacity": {
              "stops": [
                [
                  0,
                  0.1
                ],
                [
                  6,
                  0.17
                ],
                [
                  9,
                  0.35
                ]
              ]
            },
            "line-color": "#e0af77",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  1
                ],
                [
                  3,
                  2
                ],
                [
                  6,
                  4
                ],
                [
                  7,
                  6
                ],
                [
                  10,
                  9
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Sub-watershed",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            4
          ],
          "minzoom": 9,
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-opacity": {
              "stops": [
                [
                  0,
                  0.1
                ],
                [
                  6,
                  0.17
                ],
                [
                  9,
                  0.35
                ]
              ]
            },
            "line-color": "#e0be76",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  0.5
                ],
                [
                  3,
                  1
                ],
                [
                  6,
                  3
                ],
                [
                  7,
                  5
                ],
                [
                  10,
                  8
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Region/1",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            0
          ],
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-color": {
              "stops": [
                [
                  0,
                  "#a68d80"
                ],
                [
                  1,
                  "#a88979"
                ],
                [
                  2,
                  "#947465"
                ],
                [
                  3,
                  "#806659"
                ],
                [
                  4,
                  "#7a5f52"
                ],
                [
                  5,
                  "#7a6256"
                ]
              ]
            },
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  1.5
                ],
                [
                  4,
                  2
                ],
                [
                  6,
                  2.55
                ],
                [
                  8,
                  3.15
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Basin/1",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            1
          ],
          "minzoom": 4,
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-color": "#946c5a",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  0.5
                ],
                [
                  4,
                  1.25
                ],
                [
                  6,
                  2
                ],
                [
                  8,
                  2.75
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Sub-basin/1",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            2
          ],
          "minzoom": 6,
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-color": "#b3805f",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  0.5
                ],
                [
                  4,
                  1
                ],
                [
                  6,
                  1.75
                ],
                [
                  8,
                  2.25
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Watershed/1",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            3
          ],
          "minzoom": 8,
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-color": "#b3977f",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  0.5
                ],
                [
                  4,
                  1
                ],
                [
                  6,
                  1.25
                ],
                [
                  9,
                  1.5
                ]
              ]
            }
          }
        },
        {
          "id": "Watershed boundary/Sub-watershed/1",
          "type": "line",
          "source": "esri",
          "source-layer": "Watershed boundary",
          "filter": [
            "==",
            "_symbol",
            4
          ],
          "minzoom": 9,
          "layout": {
            "line-cap": "round",
            "line-join": "round"
          },
          "paint": {
            "line-color": "#baa797",
            "line-width": {
              "base": 1,
              "stops": [
                [
                  0,
                  0.75
                ],
                [
                  4,
                  0.75
                ],
                [
                  6,
                  1
                ],
                [
                  9,
                  1.25
                ]
              ]
            }
          }
        }
      ],
      "metadata": {
        "arcgisStyleUrl": "https://www.arcgis.com/sharing/rest/content/items/3bfd1065c1a748c5ae2f9408c3fb1078/resources/styles/root.json",
        "arcgisOriginalItemTitle": "Environment Watersheds",
        "arcgisSpriteData": {
          "spriteImage": {
            "__zone_symbol__loadfalse": [
              {
                "type": "eventTask",
                "state": "scheduled",
                "source": "HTMLImageElement.addEventListener:load",
                "zone": "angular",
                "runCount": 2
              }
            ],
            "__zone_symbol__errorfalse": [
              {
                "type": "eventTask",
                "state": "scheduled",
                "source": "HTMLImageElement.addEventListener:error",
                "zone": "angular",
                "runCount": 0
              }
            ]
          },
          "spriteJson": {
            "Water area/Swamp or marsh": {
              "x": 0,
              "y": 0,
              "width": 128,
              "height": 128,
              "pixelRatio": 1,
              "sdf": false
            },
            "Water area/Playa": {
              "x": 128,
              "y": 0,
              "width": 128,
              "height": 128,
              "pixelRatio": 1,
              "sdf": false
            },
            "Water area/Inundated area": {
              "x": 0,
              "y": 128,
              "width": 128,
              "height": 128,
              "pixelRatio": 1,
              "sdf": false
            },
            "Water area/Lake or river intermittent": {
              "x": 128,
              "y": 128,
              "width": 128,
              "height": 128,
              "pixelRatio": 1,
              "sdf": false
            },
            "Road/Rectangle white black/1": {
              "x": 0,
              "y": 256,
              "width": 16,
              "height": 17,
              "pixelRatio": 1,
              "sdf": false
            },
            "Road/Rectangle white black/7": {
              "x": 16,
              "y": 256,
              "width": 40,
              "height": 17,
              "pixelRatio": 1,
              "sdf": false
            },
            "Road/Rectangle white black/6": {
              "x": 56,
              "y": 256,
              "width": 36,
              "height": 17,
              "pixelRatio": 1,
              "sdf": false
            },
            "Road/Rectangle white black/5": {
              "x": 92,
              "y": 256,
              "width": 32,
              "height": 17,
              "pixelRatio": 1,
              "sdf": false
            },
            "Road/Rectangle white black/4": {
              "x": 124,
              "y": 256,
              "width": 28,
              "height": 17,
              "pixelRatio": 1,
              "sdf": false
            },
            "Road/Rectangle white black/3": {
              "x": 152,
              "y": 256,
              "width": 24,
              "height": 17,
              "pixelRatio": 1,
              "sdf": false
            },
            "Road/Rectangle white black/2": {
              "x": 176,
              "y": 256,
              "width": 20,
              "height": 17,
              "pixelRatio": 1,
              "sdf": false
            },
            "Seamount depression": {
              "x": 196,
              "y": 256,
              "width": 9,
              "height": 9,
              "pixelRatio": 1,
              "sdf": false
            },
            "Seamount rise": {
              "x": 205,
              "y": 256,
              "width": 9,
              "height": 9,
              "pixelRatio": 1,
              "sdf": false
            },
            "SpotElevation": {
              "x": 214,
              "y": 256,
              "width": 7,
              "height": 7,
              "pixelRatio": 1,
              "sdf": false
            }
          },
          "spriteImage2x": {
            "__zone_symbol__loadfalse": [
              {
                "type": "eventTask",
                "state": "scheduled",
                "source": "HTMLImageElement.addEventListener:load",
                "zone": "angular",
                "runCount": 2
              }
            ],
            "__zone_symbol__errorfalse": [
              {
                "type": "eventTask",
                "state": "scheduled",
                "source": "HTMLImageElement.addEventListener:error",
                "zone": "angular",
                "runCount": 0
              }
            ]
          },
          "spriteJson2x": {
            "Water area/Swamp or marsh": {
              "x": 0,
              "y": 0,
              "width": 256,
              "height": 256,
              "pixelRatio": 2,
              "sdf": false
            },
            "Water area/Playa": {
              "x": 256,
              "y": 0,
              "width": 256,
              "height": 256,
              "pixelRatio": 2,
              "sdf": false
            },
            "Water area/Inundated area": {
              "x": 0,
              "y": 256,
              "width": 256,
              "height": 256,
              "pixelRatio": 2,
              "sdf": false
            },
            "Water area/Lake or river intermittent": {
              "x": 256,
              "y": 256,
              "width": 256,
              "height": 256,
              "pixelRatio": 2,
              "sdf": false
            },
            "Road/Rectangle white black/1": {
              "x": 0,
              "y": 512,
              "width": 32,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false
            },
            "Road/Rectangle white black/7": {
              "x": 32,
              "y": 512,
              "width": 80,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false
            },
            "Road/Rectangle white black/6": {
              "x": 112,
              "y": 512,
              "width": 72,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false
            },
            "Road/Rectangle white black/5": {
              "x": 184,
              "y": 512,
              "width": 64,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false
            },
            "Road/Rectangle white black/4": {
              "x": 248,
              "y": 512,
              "width": 56,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false
            },
            "Road/Rectangle white black/3": {
              "x": 304,
              "y": 512,
              "width": 48,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false
            },
            "Road/Rectangle white black/2": {
              "x": 352,
              "y": 512,
              "width": 40,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false
            },
            "Seamount depression": {
              "x": 392,
              "y": 512,
              "width": 18,
              "height": 18,
              "pixelRatio": 2,
              "sdf": false
            },
            "Seamount rise": {
              "x": 410,
              "y": 512,
              "width": 18,
              "height": 18,
              "pixelRatio": 2,
              "sdf": false
            },
            "SpotElevation": {
              "x": 428,
              "y": 512,
              "width": 14,
              "height": 14,
              "pixelRatio": 2,
              "sdf": false
            }
          },
          "spriteList": [
            {
              "x": 0,
              "y": 512,
              "width": 32,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Road/Rectangle white black/1",
              "centerColor": {
                "0": 253,
                "1": 253,
                "2": 253,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAiCAYAAAA+stv/AAAAAXNSR0IArs4c6QAAALxJREFUWEftmLsRwyAMQAU1C+DUTOCMkV3YQKfTBi4zlCegTrIANeTIxfbl505HCrl0IT297mGg82c674cXAGYea62DJFStdSai67JjBSCiwVp7BoCTJAAA3BBxPfId4OKcA++9CENK6TG3lHJYLHwFiDGKAEzTBDlnBVADakANqAE1oAbUgBpQA2rgzw20IAghiHTBbpi0jczcmk0mi7aTZkQ8frRh+9H60Bgzipz/HPozTiWX7s3u/j5wB8RtgzICDGS/AAAAAElFTkSuQmCC",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAiCAYAAAA+stv/AAAAAXNSR0IArs4c6QAAALxJREFUWEftmLsRwyAMQAU1C+DUTOCMkV3YQKfTBi4zlCegTrIANeTIxfbl505HCrl0IT297mGg82c674cXAGYea62DJFStdSai67JjBSCiwVp7BoCTJAAA3BBxPfId4OKcA++9CENK6TG3lHJYLHwFiDGKAEzTBDlnBVADakANqAE1oAbUgBpQA2rgzw20IAghiHTBbpi0jczcmk0mi7aTZkQ8frRh+9H60Bgzipz/HPozTiWX7s3u/j5wB8RtgzICDGS/AAAAAElFTkSuQmCC)",
                "background-size": "16px 17px"
              }
            },
            {
              "x": 352,
              "y": 512,
              "width": 40,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Road/Rectangle white black/2",
              "centerColor": {
                "0": 253,
                "1": 253,
                "2": 253,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAiCAYAAAAtZZsLAAAAAXNSR0IArs4c6QAAAN1JREFUWEftmL0NgzAQhZ+pWcCskYwRZQgGsSy2SMNEeAL6eAHXODkpkKD8IJHiXLzrXFj36Z2fpXsGhZcpnA8rwK7rDjnnRhM65xy899eZYQH03jdVVV0AnDQBAUTn3CLSAijq3eGGuq5hrVVhHMdx7nt0zgU5vAEKXNu2KoB93yPGKL0JuGsCVHCXbC+XqCAVlI+a/+CPd0CT0CQ0ycYboEloEpqEJvnXBVSwBAU1F3fZiVNKn/fiR/QxANCJFZ7TCdM0ned8ZhUeCaQxRiIQtfoaHqkRbTQuPh+8AaroPDLzy5lfAAAAAElFTkSuQmCC",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAiCAYAAAAtZZsLAAAAAXNSR0IArs4c6QAAAN1JREFUWEftmL0NgzAQhZ+pWcCskYwRZQgGsSy2SMNEeAL6eAHXODkpkKD8IJHiXLzrXFj36Z2fpXsGhZcpnA8rwK7rDjnnRhM65xy899eZYQH03jdVVV0AnDQBAUTn3CLSAijq3eGGuq5hrVVhHMdx7nt0zgU5vAEKXNu2KoB93yPGKL0JuGsCVHCXbC+XqCAVlI+a/+CPd0CT0CQ0ycYboEloEpqEJvnXBVSwBAU1F3fZiVNKn/fiR/QxANCJFZ7TCdM0ned8ZhUeCaQxRiIQtfoaHqkRbTQuPh+8AaroPDLzy5lfAAAAAElFTkSuQmCC)",
                "background-size": "20px 17px"
              }
            },
            {
              "x": 304,
              "y": 512,
              "width": 48,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Road/Rectangle white black/3",
              "centerColor": {
                "0": 253,
                "1": 253,
                "2": 253,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAiCAYAAAAZHFoXAAAAAXNSR0IArs4c6QAAAOpJREFUWEftmbENgzAQRf9RewFYI5mIJltYFoMwEUxAjxegd3QFKIhIifQLztK5c3HH/+9TfQsqP1K5fpwMDMPwKKV0lk2VUuaU0rprPAyklLqmaSYArWUDAHKM8YB8GFD6AKYQAtrWpodlWXa2zxjjrJeLARXf973JEMZxRM5ZtbmBWxLyBG7B/vFRT8ATIAn4L0QCpMc9ARohucATIAHS454AjZBc4AmQAOlxT4BGSC7wBEiA9LgnQCMkF/yVgOViSzuhbdu+90IVVYvayL0uzZzaUhMiohWj2SMi6y7+VC2aVfxDWPXvA29YkzYyNNTl2gAAAABJRU5ErkJggg==",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAiCAYAAAAZHFoXAAAAAXNSR0IArs4c6QAAAOpJREFUWEftmbENgzAQRf9RewFYI5mIJltYFoMwEUxAjxegd3QFKIhIifQLztK5c3HH/+9TfQsqP1K5fpwMDMPwKKV0lk2VUuaU0rprPAyklLqmaSYArWUDAHKM8YB8GFD6AKYQAtrWpodlWXa2zxjjrJeLARXf973JEMZxRM5ZtbmBWxLyBG7B/vFRT8ATIAn4L0QCpMc9ARohucATIAHS454AjZBc4AmQAOlxT4BGSC7wBEiA9LgnQCMkF/yVgOViSzuhbdu+90IVVYvayL0uzZzaUhMiohWj2SMi6y7+VC2aVfxDWPXvA29YkzYyNNTl2gAAAABJRU5ErkJggg==)",
                "background-size": "24px 17px"
              }
            },
            {
              "x": 248,
              "y": 512,
              "width": 56,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Road/Rectangle white black/4",
              "centerColor": {
                "0": 253,
                "1": 253,
                "2": 253,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADgAAAAiCAYAAAAKyxrjAAAAAXNSR0IArs4c6QAAAONJREFUWEftmcEJxCAQRf/knAZMG7sV5bJdiKSQVJRUkHtsIHeXgTUQsuDRjHxvguA85+nhK2h8SON8uABO0/RKKQ2WoVNKawhhzwwnYAhh6LpuAeAsAwKI3vuzSSegdg/A0vc9nLPJuG1b7s3be7/q5AaocOM4mmziPM+IMWrtBGQHn3gCVFRfUT4yT3TzVxMVpaIP1lNLo6JUlIrWPQHeQd7BugYWd6eiVLQoSd0FVJSK1jWwuDsVtR78aiZ6HMf/XLSh6F4T7c8t2VZshRQRjfDNDhHZM9wlujdLVCi8+f/BL8IBNjJAEVUqAAAAAElFTkSuQmCC",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADgAAAAiCAYAAAAKyxrjAAAAAXNSR0IArs4c6QAAAONJREFUWEftmcEJxCAQRf/knAZMG7sV5bJdiKSQVJRUkHtsIHeXgTUQsuDRjHxvguA85+nhK2h8SON8uABO0/RKKQ2WoVNKawhhzwwnYAhh6LpuAeAsAwKI3vuzSSegdg/A0vc9nLPJuG1b7s3be7/q5AaocOM4mmziPM+IMWrtBGQHn3gCVFRfUT4yT3TzVxMVpaIP1lNLo6JUlIrWPQHeQd7BugYWd6eiVLQoSd0FVJSK1jWwuDsVtR78aiZ6HMf/XLSh6F4T7c8t2VZshRQRjfDNDhHZM9wlujdLVCi8+f/BL8IBNjJAEVUqAAAAAElFTkSuQmCC)",
                "background-size": "28px 17px"
              }
            },
            {
              "x": 184,
              "y": 512,
              "width": 64,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Road/Rectangle white black/5",
              "centerColor": {
                "0": 253,
                "1": 253,
                "2": 253,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAAAiCAYAAADvVd+PAAAAAXNSR0IArs4c6QAAAOxJREFUaEPtmrENgzAQRf9Rs4DpmSBZIylZIVuAYRzKZA4moA4sQH/RSQGJEEWpz9+VC5r/jO27/y1IfEji+rED0HXdSVULz1BUdYgxTqvGDYCJB/AAEDwDeGs713U92HwD0LbtRUTuIQTkee6SwTzPWJYFqnptmsYW+wigLEtUVeUSQN/3GMeRAPgHcAvwDOAhyFuA1yDrABZCrARZCrMXYDN0aIfZDbIdph9AQ4SOEC0xeoI0RT0SoCv8jy1uoYiFIx7Hz2AkxlhkWfb0KPxDk0Vit0M0Zh+lEI6KyLSK3xkiCaz8V4nJvw94AViOijI4p1iqAAAAAElFTkSuQmCC",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAAAiCAYAAADvVd+PAAAAAXNSR0IArs4c6QAAAOxJREFUaEPtmrENgzAQRf9Rs4DpmSBZIylZIVuAYRzKZA4moA4sQH/RSQGJEEWpz9+VC5r/jO27/y1IfEji+rED0HXdSVULz1BUdYgxTqvGDYCJB/AAEDwDeGs713U92HwD0LbtRUTuIQTkee6SwTzPWJYFqnptmsYW+wigLEtUVeUSQN/3GMeRAPgHcAvwDOAhyFuA1yDrABZCrARZCrMXYDN0aIfZDbIdph9AQ4SOEC0xeoI0RT0SoCv8jy1uoYiFIx7Hz2AkxlhkWfb0KPxDk0Vit0M0Zh+lEI6KyLSK3xkiCaz8V4nJvw94AViOijI4p1iqAAAAAElFTkSuQmCC)",
                "background-size": "32px 17px"
              }
            },
            {
              "x": 112,
              "y": 512,
              "width": 72,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Road/Rectangle white black/6",
              "centerColor": {
                "0": 253,
                "1": 253,
                "2": 253,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAAAiCAYAAAD8gp97AAAAAXNSR0IArs4c6QAAAPlJREFUaEPt2rERgkAQheG3xDQAORVoGxrSgl3AQTmEWgcVEAsNkK+zM8KMMkKwZveICEj4+G+TRcBrV0Dosy/wAdS27UlV85jRVLUPIYyLwQpkOAAeALKYgd7vfq6qqrf7FahpmouI3LMsQ5qmURpN04R5nqGq17quLZYtUFEUKMsySqCu6zAMA4F+fX0CHZwLAhHINzpZEAtiQT4BFuTz4wxiQSzIJ8CCfH6cQSyIBfkEWJDPjzOIBbEgnwAL8vlxBrEgFuQT+EdBtjS05WGM1+7iMISQJ0nyjBHm651t5XzbrJ7tIf68AIjIuOCYCX9/OTgyBDoAegGsH4oy2C4z9QAAAABJRU5ErkJggg==",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAAAiCAYAAAD8gp97AAAAAXNSR0IArs4c6QAAAPlJREFUaEPt2rERgkAQheG3xDQAORVoGxrSgl3AQTmEWgcVEAsNkK+zM8KMMkKwZveICEj4+G+TRcBrV0Dosy/wAdS27UlV85jRVLUPIYyLwQpkOAAeALKYgd7vfq6qqrf7FahpmouI3LMsQ5qmURpN04R5nqGq17quLZYtUFEUKMsySqCu6zAMA4F+fX0CHZwLAhHINzpZEAtiQT4BFuTz4wxiQSzIJ8CCfH6cQSyIBfkEWJDPjzOIBbEgnwAL8vlxBrEgFuQT+EdBtjS05WGM1+7iMISQJ0nyjBHm651t5XzbrJ7tIf68AIjIuOCYCX9/OTgyBDoAegGsH4oy2C4z9QAAAABJRU5ErkJggg==)",
                "background-size": "36px 17px"
              }
            },
            {
              "x": 32,
              "y": 512,
              "width": 80,
              "height": 34,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Road/Rectangle white black/7",
              "centerColor": {
                "0": 253,
                "1": 253,
                "2": 253,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFAAAAAiCAYAAADI+15nAAAAAXNSR0IArs4c6QAAAQ9JREFUaEPt2s2JwzAQxfGRz27A6cIkVbiQ3S6EcBdJGwF3YVzFxg34rt2BTUjIhyAPcvFf53kC/Xg3TTCOJBCkNGG7Aez7fptz3uDyXCDnPKaUTueJC6DjmdnRzBoAiwK7GOPoU9eAX394+6ZprK7r4g1rHJjn2ZZl8ad/xxgPDwHbtrWu69boU3zzMAw2TROARaknAwC+K/efAxBAUUCM00AARQExTgMBFAXEOA0EUBQQ4zQQQFFAjNNAAEUBMU4DARQFxDgNBFAUEOM0EEBRQIzTQABFATFOAz8B6J/q/rnOuRd4+bGeUtpUVfUDXFHAVzp8M+F2tcNjLBcV8SyEcDrj+TTrbWWzlxMAioC/sbE8MuAFbyEAAAAASUVORK5CYII=",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFAAAAAiCAYAAADI+15nAAAAAXNSR0IArs4c6QAAAQ9JREFUaEPt2s2JwzAQxfGRz27A6cIkVbiQ3S6EcBdJGwF3YVzFxg34rt2BTUjIhyAPcvFf53kC/Xg3TTCOJBCkNGG7Aez7fptz3uDyXCDnPKaUTueJC6DjmdnRzBoAiwK7GOPoU9eAX394+6ZprK7r4g1rHJjn2ZZl8ad/xxgPDwHbtrWu69boU3zzMAw2TROARaknAwC+K/efAxBAUUCM00AARQExTgMBFAXEOA0EUBQQ4zQQQFFAjNNAAEUBMU4DARQFxDgNBFAUEOM0EEBRQIzTQABFATFOAz8B6J/q/rnOuRd4+bGeUtpUVfUDXFHAVzp8M+F2tcNjLBcV8SyEcDrj+TTrbWWzlxMAioC/sbE8MuAFbyEAAAAASUVORK5CYII=)",
                "background-size": "40px 17px"
              }
            },
            {
              "x": 392,
              "y": 512,
              "width": 18,
              "height": 18,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Seamount depression",
              "centerColor": {
                "0": 92,
                "1": 130,
                "2": 153,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAAXNSR0IArs4c6QAAANpJREFUOE/VlEEOgjAQRWeI8RBcA46hro3iUuspKvYKbigubTiAXEPO4S1Am1gDQ0vVsHGWbeb1z+9vEUYqHIkDfwhaiXOkxy/4thqywTtaIqQEgEhxFv8M0moCqG8agE2zuBz2pQs2qGgtshIBZ6/mu+Is/BqUCLkDAD1Wu9gTlttgVkXL9BROgulVe0ObFGfWHuuiQ41h5oozRg/ogdoGu/yoIYhpHHogYrCLVdE4dECfqDFkqqoDSoTUmekZ7JDVicMbtDlm8waRXrfvc0hNHLxPxEcy+6OBHp6KQRNOMtKnAAAAAElFTkSuQmCC",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAAXNSR0IArs4c6QAAANpJREFUOE/VlEEOgjAQRWeI8RBcA46hro3iUuspKvYKbigubTiAXEPO4S1Am1gDQ0vVsHGWbeb1z+9vEUYqHIkDfwhaiXOkxy/4thqywTtaIqQEgEhxFv8M0moCqG8agE2zuBz2pQs2qGgtshIBZ6/mu+Is/BqUCLkDAD1Wu9gTlttgVkXL9BROgulVe0ObFGfWHuuiQ41h5oozRg/ogdoGu/yoIYhpHHogYrCLVdE4dECfqDFkqqoDSoTUmekZ7JDVicMbtDlm8waRXrfvc0hNHLxPxEcy+6OBHp6KQRNOMtKnAAAAAElFTkSuQmCC)",
                "background-size": "9px 9px"
              }
            },
            {
              "x": 410,
              "y": 512,
              "width": 18,
              "height": 18,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Seamount rise",
              "centerColor": {
                "0": 92,
                "1": 130,
                "2": 153,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAAXNSR0IArs4c6QAAANpJREFUOE/VlEEOgjAQRWeI8RBcA46hro3iUuspKvYKbigubTiAXEPO4S1Am1gDQ0vVsHGWbeb1z+9vEUYqHIkDfwhaiXOkxy/4thqywTtaIqQEgEhxFv8M0moCqG8agE2zuBz2pQs2qGgtshIBZ6/mu+Is/BqUCLkDAD1Wu9gTlttgVkXL9BROgulVe0ObFGfWHuuiQ41h5oozRg/ogdoGu/yoIYhpHHogYrCLVdE4dECfqDFkqqoDSoTUmekZ7JDVicMbtDlm8waRXrfvc0hNHLxPxEcy+6OBHp6KQRNOMtKnAAAAAElFTkSuQmCC",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAAXNSR0IArs4c6QAAANpJREFUOE/VlEEOgjAQRWeI8RBcA46hro3iUuspKvYKbigubTiAXEPO4S1Am1gDQ0vVsHGWbeb1z+9vEUYqHIkDfwhaiXOkxy/4thqywTtaIqQEgEhxFv8M0moCqG8agE2zuBz2pQs2qGgtshIBZ6/mu+Is/BqUCLkDAD1Wu9gTlttgVkXL9BROgulVe0ObFGfWHuuiQ41h5oozRg/ogdoGu/yoIYhpHHogYrCLVdE4dECfqDFkqqoDSoTUmekZ7JDVicMbtDlm8waRXrfvc0hNHLxPxEcy+6OBHp6KQRNOMtKnAAAAAElFTkSuQmCC)",
                "background-size": "9px 9px"
              }
            },
            {
              "x": 428,
              "y": 512,
              "width": 14,
              "height": 14,
              "pixelRatio": 2,
              "sdf": false,
              "id": "SpotElevation",
              "centerColor": {
                "0": 0,
                "1": 0,
                "2": 0,
                "3": 255
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAAAXNSR0IArs4c6QAAAIhJREFUOE/NksENg0AMBIc2QhmkDKCM1EEbUAakjNAGtBEvAhQZn4TulX2ePN61zwWZKjI5/gt8AQ8bpYvGSUUVMAIVUAKLh1Ngb8VylN5AcweUy8cVPg2ef98ix8nA2oGCBJ/yoOIpZqTWZlbTTR5UREWNtO5bvoBaQMrtaKSvGSLH2xeYfXJfIrwPD2vFEp0AAAAASUVORK5CYII=",
              "style": {
                "background-image": "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAAAXNSR0IArs4c6QAAAIhJREFUOE/NksENg0AMBIc2QhmkDKCM1EEbUAakjNAGtBEvAhQZn4TulX2ePN61zwWZKjI5/gt8AQ8bpYvGSUUVMAIVUAKLh1Ngb8VylN5AcweUy8cVPg2ef98ix8nA2oGCBJ/yoOIpZqTWZlbTTR5UREWNtO5bvoBaQMrtaKSvGSLH2xeYfXJfIrwPD2vFEp0AAAAASUVORK5CYII=)",
                "background-size": "7px 7px"
              }
            },
            {
              "x": 0,
              "y": 256,
              "width": 256,
              "height": 256,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Water area/Inundated area",
              "centerColor": {
                "0": 166,
                "1": 195,
                "2": 209,
                "3": 77
              },
              "imageData": "data:image/png;base64,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",
              "style": {
                "background-image": "url(data:image/png;base64,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)",
                "background-size": "128px 128px"
              }
            },
            {
              "x": 256,
              "y": 256,
              "width": 256,
              "height": 256,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Water area/Lake or river intermittent",
              "centerColor": {
                "0": 142,
                "1": 174,
                "2": 193,
                "3": 255
              },
              "imageData": "data:image/png;base64,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",
              "style": {
                "background-image": "url(data:image/png;base64,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)",
                "background-size": "128px 128px"
              }
            },
            {
              "x": 256,
              "y": 0,
              "width": 256,
              "height": 256,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Water area/Playa",
              "centerColor": {
                "0": 0,
                "1": 0,
                "2": 0,
                "3": 0
              },
              "imageData": "data:image/png;base64,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",
              "style": {
                "background-image": "url(data:image/png;base64,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)",
                "background-size": "128px 128px"
              }
            },
            {
              "x": 0,
              "y": 0,
              "width": 256,
              "height": 256,
              "pixelRatio": 2,
              "sdf": false,
              "id": "Water area/Swamp or marsh",
              "centerColor": {
                "0": 0,
                "1": 0,
                "2": 0,
                "3": 0
              },
              "imageData": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAAAXNSR0IArs4c6QAAIABJREFUeF7tXU+oLsWVr+rvPn2OwmSRxTAYkEEGFy6ECSgYovkHLrOYhYvgzX0yCMIDAwZkuMYb5hqECM9Zyui9714luMwyYCCZAcGAgSxcuJAhBhezcBFkHsh79+ue6eo6/XWfr893TlVX99f93XMXtq+/quqqU1W/OnX+WsP8Hb59duSKWPNK9cy/Uz6ODw5+z9XV31cUUDpOYzUcnpwVvif/6dbxtf0nN/XsZ2fv/rb8PV8uv+fL22b5w9PTqn6R/a56mp+7cs/uV/vG/x2enMF+eUKyj4ZaL4en71T7uMhd/1qD6SLEUB2ZxnIYrxdKx/FovelLCgChAAAIl2cO6fay/Gb5PDo4+PM0pnQevVAAmMY8wUlsrf2iOgiLjzet67E5gPqENstvVCe1fbB85DZ/oXz+4uDgT30oWXMsfj/zHIACQB96r1hAvUoloWPfRhQA/JVFCgB9Ca71KwooBzCtlYDvwpRsa2wO4Gdv3bzjTvzMflA+ORlFX6qyHEDfD2h9BYAprgEFgGpWRgMAfAJ+9dWtH5QduHrPPRfVXactRTVZXklN4T1aRcfX9jdLY1F5+N7rzz/vpLp9/6jxUO2HcgBr0mXVvvSdslb9o9PTB8oXF8a4Z2OdtbQD/3p6+ojbKPnCycCsLW5U5Stp/9o6pd4b82a14/L3yseeMe4uf5Fn7m4PWrY7t+/8tPzn4u6FW6d97/wc0RQAOAoRvysARBJuItUUAKqJGA0AXn77/McOOG3hnrduffli+bznvvscB5AV2RuuQ4V1WoZltnQICe/xusF3I0Bqqjx878b16x9tWoP1wsgz109AeGz3gMdjjPnE9//D8vlvzz7jxgF/Ug6gUe7vfN2HyiclBa77YQp3kmH9c+r9Bv2zxjot0CJbOk7tgqAXLg90qceJOkhpmah2Uo2voaf/b9dmYf7SnP/6OxynynAGMD/1+LPi/up7lbRfuk5TjVsBAFFSAWDz0lIAYK6qCgCpsGk77Ugtu3DvOOmtmANYWaq5T2BZB/4utjDjyvelKjakMbayKKMs4SjDm8b7dpcIWUeoAU/sOKn5F9/1pQAQaJEYOx6u3mgcANeRqfyuAMBwAGjhKgAgYbUCwFS2clw/jk5Pv+butMY46a8pstd8S49uOpHH4gAAoLJs8X7Zn3xZvO3656XLQ/towPdzY/5afvYuY5wsAOi15/8NlqK4PEi1a6BF0wTS8aODA9c+/FHthM7yBo6k01Y/y64cV3RePu7p7Hxh8LoAO4KI96/7MfyTW18Hz1wpn4cn54fV94b1wVEOAK0gBQCGA/CWoQoA7YNBASAUimdS/vDkzGknTM0RGHdSgBQcpNpgMVbkuTu5sI15LSVHiF6TwZtmGmue8u++cieC91ZraB0e87877QBoTbDWYSbkHb2bDZmJ0zIdX9t3eng8z0D3o/NfuRP64uLON5vzQZVP8P775Xdefvv8R24dea1ZKl8ATHDlAJglqAAw+h4d9IMKAG3yKgAELjdOGk1J+83qhG/FVaDe47v8mrTf3xWNtZUlpf4pBSIooAAQSDQFgECCafFJUyA5AEhPwMF9AYjILH1no6EmfNq39Vz5rMdz973fcu/xXT+QA6j7ufKFaNmSDy3t70unudYX2wFQAwz1ERhonUrprwAgpZQvpwAQSLCZFVcA6Dlh2EYepJeLfOH06mP5AvSVjrM27MiGG3wBjC32HAm9bXf0+9U8VNJ+r3cvisqLDGzKU/kCUO1Q73FkGWrZgG1/7XWHIkvh97HtpIpQhX1KpL4p0G+qPPc+tRZH6muRnANQAFAAaG5iBYDNTm59DyoKMLcGAD0ZiMlUF9iwt/zGKUvA0HawjTzY9q+9B4ux03OIb+Cizcb6AlBahkOi/TVZDzVz3rZfrAUJbCd1nIfJLMCeHaF8LTC9knMAPfs9meqhG1cBgJg6BYCtrGkFgJ5k52zYwRQW27aneg/dB2k/tp2H9/Wd1RjnwxCrHaDaod6vBdQg6A22/cb3D+781HtSBuAj6FDtYN+BntM/++pSXwvlAIipVgCoEr8oAMwTCxQABp43LAWnhF2xUm1Kap5K2t2XPKm0D337ofX7UUA5gEj6KQD4EG8jhSKLnCatxlBAASByiZBRjrElYKBUu3YrJSwHY+/4kcMkq40diSh1/7W9igIKAJErQQGgnewyVv0YSX6tlogCllIXUBPaoR5z/suHJ2cuo4kxpqUfJ2O/oQE09N2tyCyUHpwaP5Rfy+iS2HsOS8FTS7WnLu1OpX2g5lEaQzHRPmCbEZsII9t+gTqZ+ja1j0RZjUm64uzACgDs3HcWUACoEmZkPdWPCgDk+hsNAODEbfWEyknWEVDBxfc/PDkDizQcaaWzfTxs+N6GiCpB7XREcnGcShW+Tv+mToGpcQBSHwFs2rshAAm3nql91HofOo/YVL+8AigAhFJRyw9OAQUA7/S1ClkG+zQtAAw+k/oBpUAEBaYGABFDmEUV1QLMYpouXycVAMaZ88EBgAuhNc4w9SvbpgDlJk5lvw0FAOqOntrPftt0TP19BYDUFNX2OimgADDNhTEGAAQJL4bWLw89DVL1oMBLDlQWVYYi4g8y8RgfMYjK0IOr4wQose1Au1z23o74AWdlXVtYtz5isyk3gOVJ35d99yRi7akPQ3slKAAkRgQFgCptOLuhjVEASLz2YpobHABCOzV3G3NpVGTO5r+m2yoqcDcphckocWXOsq3OPXhRvFrWhRiE1HyGynooi1Kw05DKANYsPq/tb1zTc19fofuJK68AwFEo8HcFgLYpeABgtAy1FAACF15kcQWASMKRC9snz4QYeKFBMaE8tF/nFKQ+mFXpqeEOX5f37ynvwfqqkmc/dk1HtlPLAPy4i2LxbXe3N8V3yyeV024sDgBkSnvZFZfjb7nM/8v1zy7dk/OupHIDwril2oeAnIHgWwNZg50MqCNHZDVvxB8XjfvG9esfVfM0sb+5s2jSOAEcMCgAnB05GjDpsbkrgAJAdzh+BYCJAd+udOcQeZsVhf1JObYiWzpOpY6heHJW+DH/odro+Uuek3Gmrhd55rL2YgAA7QloO7LsyrHjNJbLx/1J6Q412Pg2XzjtwGIv+6Urd7EUyTRgPjiAoWQpWGZCHWxjR2OefFTguXMAu7KRY8ehAGB+7oDo2f2Kg/F/lxYAIqTDnfEAqAWpgBG7Vcepx81/sNAUug3aEULfr9mUZfM7uAyAWwC4m6EbOrS8jCxaKhUFuPlXAEhF6bh2WACQpvraIO11J3phitvVlc7eVT5v3frSxREAYQTHKsHvWOqK26XiGDTuch/7u2J1x9S/QSlQb3CUSxHWS5ZnP3QdkGZTJjiAPMt/Xf6UFVUqLmOLT90zt5+7+UYs+aCDnlHjCgAzmqw5dlUBYNqzxgJAKItG6VWpIJqvP/88RBJylOJYeqnUFZOdSt2Fy1EJQaAcZeqLM9OEZtqRlqeWE6fPHnoZcolUTJE97fvwXPkE7YC1hct+bIwRvc9s8b+uvjH/4eu96dv7xB38trjRfG9s/p7jAA42JzoZmj5TbV8BAM2MAkDcUlUAiKPbtmuxACDtYKiwh8rqmooDwOqoY2FUYI5TkJqoJlP7rEK2uey/JAfA2MBL5zG2nCD6LRfkUhpdup2V+exdx0Hmy+X33Env6RCqX48d99zrKQCgGVQAiFvSCgBxdNt2rZQA4KT91tov3J0sL5y0HUxel94iq7AF2DC7O5spzP845PZSWurkbGgjHvNEc3dHiMK68JZmtS28NVd9OVf++Nq+KCowcA42Lz4r6625tRK2/jhnH+V33vc9yQFsWcpNxQMY+n1fekq1AxOKCtxaAhu0b5U2xJiWLwFePwoAiCIKAHFn0tAbnWpfASB36mwcWo1yPhoMAKBh6R25wWrvbby7UXc6dOeN1Q7ELXetFUoBaaAUqt3QCErgHZkqmzIXP8EQlomCqxE1ZFmGLZt/x+0fr+Wo9yGSHVGZvpJxAAoAoVvicpVXAAhOmTdPAMATXSMjyhmYigPAMgOItJP6BLhc2zX9aMX2JNSn/UkHcRbAchC0SVfvuafK+MT4CKQf2bxbTM4BKADMe0EM1XsFgKEo26/daACQBr4w1jxVdtHayiYbtAPwvu5+YX7jymX2YVeuKO6vED3ufd8IN/3IqrUxBcTrhSBdcAAVJiKSzlBFAQUAXQmjUEABYBQyB3/E1hNDVM19vPk1NcPb3SGb8B2Nin7L3d3gBMd3utj3oVFugynpK0iFXQKp9tfKJi+MeWBTXxrtuGIQKQfXGdpXgDOhjqWn1utHAZz/AbemANCPvmu1FQDMX0uiUCm/EpNbm2MowAPAKjYb1VRLHQGFEi701snFZaihMuCEvk+lH1676/bkjMh8AdTsgHQcfifyCFB64FQ7iPMFSfUdbSeMAmv2C6i6bUycAkAYbTtLi6XdhFpLASDBJGgTNQV4AIATiyCaNd2pnqQ0lppwUu2BrXaoyae0f6nLSYVdnFS7vvvnGeS86+yqNI+A1OY9lh5jcQA4QhXuL44IFVo+dvxTrbeW/2GNA1AASDp3CgCyzECxRA/d0KHlY/s11XosAAzdcepkwPHWSQ6A8QXg4gcMPT5tv6IAxwHgiEegvcCRlDh6dmQZblXBso7Q8tz3d+33aDsAKSEUAKSUmnc5BYB5zt/wAOD957E9AT4RSA6AieVGxdKb53RMr9dS704OACifjaHtE8amKKbX0NqXvuNTAOhLwR2vrwAQNsEKAAS9sDCGygsQRm4tPTQFFADCKKwAoAAQtmImXloBIGyCFAAIeknzAoSRW0sPTYFYANizucv4U/smFNlrvq+PuicRyWbo8QzdvgKAAsDQa2zU9hUAwsi9cwCwFuDD04PyEqTINTYHQNoZUNlksQ3/aiCdvhBhy2K+paUBXrAWwNi8So+98k1wGXwgU0+sHcDYlMTriJPqhwLA2PsC04/VAigADGvZNvaCDv2eAkB34hHpQRcKGFTCnNB5k5ZnAWCDJRWcjKJ4+2NrAY7Of/W6u4Ne3PlmkxiQRwDH+99gMvqnsv7xtf2k2YQbevFB2pcugNByVL/x+z2bu7j0dZ6GiUXoWTORJfrXWEffqjiaKkIVxKVYi8aLOEkKAKikqWTWbGSyn8q3QwHA7wAFABkUKABcNgBAmXBgmfT1EpQtt90txVnO7e7IpzGy0DwS0vJSGUDo/GO3fe5qIaUyzwEoAEhpGVQudAEENa6FWQpINzQ0JC2/cwDAUlILRFFgagBAZtM9OT90A7TmlepZZaJZi/1IUQHKF1mlFTDGZTmus/gSEZSG9hFYC5WF7BTWvArhIGTyDqQCANxOUdifOPJny0pmhDIBRS3CPlGBYz+o9SoKKADsO+5TameQet0oAFQUZa8AqQm/YqnecScKzsLLJZnE/YGIOFx23rreQNLohr7YZUXmtAahANCR7FGkfZHOH9X+y2+f/6hsA7I6QzbaRb5wWWcb2Z47PwXlsyKDrNCtbLVY+Eplu5WOI7ZcY/xV9mkk7Qe7l6zIqqy7tvjUPfMq30Wd3ZrQAuBAMY28GB821wskpzVm+Y2qH/bB6jPdSUBjxwv1FAD6UtDXVwDoJqQCgOd0sCzNJ8wxxlxOAGjkBvzAI6CLfRecTZWwKQ+1BKRwQBpvoDGeP1YnRP5S+aAs3jgOgGVRD565Un3Hupx4uLzmRoxDdrGwj8i+S8kApFcdal/EjYavtTUOQAHgrPDTQ4Vdh8QgjmU2WEilAMCv7ogSCgARRIupQmWS4d7jb1EnLBVxKPRkDI05KEV6jgOQLkSgR2j5mDkTcmgO0NZ8AQgfjNh+DFUPc1JZduW4/Fa+XD7uOdVKeJmIA8DalDu37/y0bH9x9+K35TN1gpVaxlBUvhpb4wC4jY6djagUZgoA1VZQAEgDCZcOAFY2yfnvK+BeuFx0hSncc026iehcx7fPKynvrlkI4nwExhqI099pwz82B8BJr1Ppi2tOY3XytcaPTYRzm98s64DUnPLBoLYtFV6d0/ZIbeQpmQnOMGWK7JnqCmb+0T2zvLKLgPfG/APieJ72Y3rOv3d2E0Wx+Ha1P4rv+pP3XcdZGPv3Xe+XNv+oyQGkyr2ItS5WAWDzyaEA0KaP1BdAAcDMBAAgN6C/ozVOuLbFFpFDsM7ye/Xe9/1S2Wn/efbuLrRsY9uRWp4Rd9E0DPH2WpFyUqH++jUnQ9A3NPt0zSGv9kfLS/bw5OxO174gw+W/ddOVzzMr0o71naFVbkAFABEt2Y2rACCiI1dIAWAsAPBICNLx28Y49VPmn3CH5IRwEPstNFIQtxCm+rs0kovArqHFMXFaB5iHLFs4jiu/KF4tn9K771TpiftFZZ/GmYSkdhpk+152BSc/7AMcx4B6X+8PD/xYBsZZtq6VPw2zkO07nxYWlAJAGCkVAMLoFVpaAaD4rKQZBK6hgCSUrrj84GrAWHVfajVgaml4RwCRT5w0t7DOtLOeuPW7IWfx6LQx2Guu8b3KVt2Yh/z3nLQdRzjquzBC6w+1QEP7kbo8xWFQofLw90FNbTxHDVmfufehORNjx60AEEk5BYA24RQAuhcSt9EpYNgdACBOwLFNgY+R6Wzkvier9RiPSAZA+euDL0Dq8YS2xwlHQ9ubSnlKy7AhVma761T8BOL95IKC9p2IVOoOHBKp7pfQGUgBoO9Mbq6vAEDQ59IDACUdDZR21oiL6CyNBxArJafUUZQN95W7rjj/bWMqQ5A6kost3J2de2+N+ZeyUF7Y+8qntcUNX8/F1S8K62QNi73sl67cxdJpASj9dey4gcxSdVyopVoHYCSNb5AK7rAhWK33J0Ll4e/WlrLGOMtaWDfce2zxmGo8uJ3hZQAKAFUoJwWA1tpTAKhMpUEoiIFhZwBgKOQaq10qYg2OiAPx3O/7m7992J3UtnC+EVQEHe49jA/b0i99TLi97IrLe1Bc5M6mHN7H2t5T9BwqYk+HSfGLvg8uvoH+jUOBwTmAcYYx3FcUAM4dkGFA6+umqgAw3JoNaVkBIIRaWlYpsGMUUADYsQnV4SgFQiigABBCrQ1lBXYAVG1sB9AZKmxbdgDUFaiOjuvj/JOk8WqwOs4Eko1kefZDVxfyDlAN8fkIdtoLNdEyXWtGASARZRUACEIqACRaYcM0Ew0AVMQWSq2B31PDAf0o/M56ZVEN+fj/nBdXKrJSYcEbJzf1qY2RdSC/wNB5AajOkXYQhT+5jamClhJ/dVhwfNITwMC1syEfwaBZlsURhNAAtmUKLPWSVABIhAAKAN2EVAAwDpjGdgYaHgCIwBdrOeP4u1t75UB5eItysa1ZvFEbGAKceE5g1/3nE+GYNkNQgAq6yq7HLZkCc3ElYJjxHIACgG6WS0QBBQA02VTABimrQ8oATM0yuSIQaQju8mtRW4mGqPKheQEu0RrXoW6gQL3euQhCWAaQbTb5DTUFlvpmUD4MeIjRHIACgO6Xy0SBnQUALtZfqsAEFAFTR+q5TItyTmOVao1IzpA4SVd3Wfvn8v+3HRlp6DlJ7ZtRxwTEHacy7sQOUAEglnK7UU8BIM08pgcAIt6/IQJtxA5jrNRVsf3TesNSQBpXgewFr01SS8CIKVzlBViTDuQupVEqFl0BIGJ2dqiKAsA0J3OVGoyQXqYKTDB0/vra8KHI3iiHEpqLbqjpkabSalj8QVRgykKQ6iou7+hgvKXe8bV9yGk41FA3tisVGpMygJV2CNKmVxF2/N9Q+SiOzn/l4i5cXNz5pjsQPR07LDMh2nOL7o0udloqdgSXhSqi8lRcCYqOELfixvXrLvegAsDA20EBoCKwAkCl3gagh2W3dQAYeP2P1vxUrxgRmYEob0B4T9FUFF14tAnZkQ+RUYGJnIzYAq9Bhk4ZxYbowrLyvGykNRM46nC0HcDU5lcBwCgADLAoFQAGIOoQTU4VAIYYq7apFEhFAeUAUlFS21EKzJACkwWAUMOhWA5gV1NazXAtape3QAEFACJvwRbmQj+pFBidAsEAgNOJg51AaGYYbqShJ3poefj+XBJUcPTq+7s0Cy6YiN/2mW4yn/WW+j4XESeVr0nf8V/W+goA68lLJ5miaugFqgAwNIWn2X44AMCG8RF36lxpRBZgathUEE0ojy0HTZG95n97tHweX9tv9V3KAWC9K+TuK7Kls8DDCS+k/tfTnF55r6iow4cn54euFYjaC3rnIjvyrT+x8StMRJxUpubykWrJJgUUAArrcvcpAJyBCbLb0JBNWQFgtwEjHAAgFJiPtQcIHipNbxhY/MWRuDDVE7XbuKu3F2giDoDyeqxP/qy4v+qfdVl/wfaaSo0lddekTIRhvJRvA/yOU3XBeyqXYCOOf2tFg227NAsuRG1e5gtn+16YomWTj7fLVLLgctuYsu0P9QXoa9qLbfW5fvf9XQGAcHtWANh3LD7lx68AcNbpbLXzANAXcXB98d2dsL2uOQTI146iCIOMoi5HBDPFd1HKhp8bv1RmwLVPBqGEDuA7ec0aZL/zHNXPmxyVAbqgAWBZCje+Xf2diqIbbAqM19eKYCLbfmyrL6U35WzFaVmCOQBph6TlFADaNvwcoNV0VQCQLjFROQUAEZnSF5JK++FObP3d09rixsaTDmkpGlqHP7p6Nn+pfICe+iLPXqjem1fKB6cdSE8JbVEpEE+Bw9N33Lo1RV5pZwjty+S8ARUA4iddayoFVhzjTAEAT2FDGvuYP+F/455eO1CX5zIG0RzAB2UbdWSXWqsRJu3XpddNAakWROmXlgKssNZnZV6LCJS2G/1bUwDoT8NttqAAsB3qbx0AUsf8E6diQjkAa2m3lANQU+CkK5a6i6rFX1IyJ2ssmRZAASDZnMy6IQWAeU0fCwCCmGXOeebw9PRb1Z29rYfGenggj1S/WkszkS8A9z7LrhyX38qXy8fLJ0g/r1699599H55z3fWmwNYWDzXfU1LU1PkS5rVc+N4qAPA02mYJPD8KAAoASdejAkBSciZvLBgABKaNL5a9PDo9dTbzFyh7KnX3C7WxlsZhB+l+R/uOU3n57fMfuZPfS0WpuOrce8oXAM8YZWPf9z21MmrvTNBu4IKErwW30nCEJmu6c/FxADB2/gZxUk9PF8geXa9jijBCX5iagybawXQE+tm8+KyskjrXId7PLAegALB4pAswFAAUAMp1wTnDzR4AuJNBf99MAcrEtO97kgPwXpINX4N2UaQdkc7fmlbGUCbM3QYp9UYR+mxI+8WVg35n2eL9smx+Ubzq6oBdCWdPQn2Aj4dRycZOzu4wfWz5CHBxMrjxhv7OcgChDWr5NgX6bnRw1tmQcKL1wUb57kQiCgAKAI0VM1kAENsBMAgNSI9PgA2RjJKGBKNCbfV9T3IABwcubkJNP1QQ7rihOR/nygFQ6mljzF9L0lz43IlAF/yeojOmIxUTk5oHaBfnNEwdW5M7kBUABjYE6rvRgXXG7SgAcEu7+l0BYDOdJgsAlLR4mS1dkkUqwg0MF7IDQ/m97IrL8lpc5O+WT5CudkTmcVqN6nDQP6DA2nxY+4WjZ158XD7ryD+gBVqPIfhD31ZlL2LM/5b/mUoWZxhnaD6Kua8QBYBVoBHI3qoA0LGqFQCqq9Wu/U0WAHaN0Ls2HirykckzFyuQiyI81UhE0gA1uzKfCgC7MpMjj0MBYGSCD/S5GgA4C66Bvq/NzpQCVAw64zMFXfjMQRBxiYtNNxUypHZqSz2u1ByKAkDqGbok7SkAbGeiBwOA0EAOVAACQH64C4J0GMiFfQU422vKm1BK/jWpLqqI2+fKw3hC9ejS/m67HCcFp/I/SE1eFz4DE+UzEppfYtv0Gvv7CgCBFOc2tAJAm6AKAIELbOTigwFA6DiChUDwgUDb677S4jVb8GWx1xwrm2MQE4ZIJBJKP658KEfGtSf9nbKd53JAkr4Hqw87m3djfdRaIm4Ely9BOo5dLacAEDizCgBhBFMACKPX2KUnAwChQqBaBhBoe903ltxa2HEsA/C28/CaKz+WVFuaYSj1AuSk4H1t3u8y5s9ln7ENPshUxraFT02/0PbwPHOZgUIBgCsfbQegAHDgnEmG+lMAqJx1pHEXhpqHodudDABQUv2xpd0qBa6W3LYAQLrgQ7VAOJloX+0O18/QiEtce7G/c+u5I+DOJ05UUtgPyyeOCMSd6NDPRrtVfg1jXMxL7HvRsAM4rUw4vSnnttRdHMFiJ2Ju9RQA+s2YAsD5j0sKFraQAsDmSC79pkNee1elwKFS/VAAGDvWXrAWqMiqnHXGPFH+p692h1tRa4FYDp654jir0/PfjtwPCMzSmR0Yj4OLCCTlAKhANPh7k7MEVACopkgBgNvim39XADgD78WNgGsbG+7fHUlt/uvyMZa0G0/jXAGAk17jDc1lH5YCAJc1Gd+1qQAlodstVAh82/sGZN5XIFS7Q60LKr9EaCCW0PFLyzdO7Kd9HZePgsovMToHoAAgnUrmxPHBLnGIJ6ilAGAeKGmhAGAmBwCOVRg6Mgt1YmAvMY4DmIq2IvTuFsrpSDkA6V0Pvk+dmGlgcLhWOiI3vVB+jcovMVxP4lqWSvthfoo8d2pQiLjEZcfGEZlsZh929Yvi6+UT8mVg4Wh5BVAAiJvTVi2OdVMA6EdkBYC8HZEImVJHA0C/aZHXlho88BzANLQVaxv61PfLLL/hfivsg+UDMgxhgxZ2nJDZB8XWw3dnjgPA2gFji09d/3L7uTsZnt0H6bx8MrVkbwoEzz+TBZvKc4DnF3OA0ZaAoRRQADhwMQfhL3gBEE5ICgChK3Ea5YPnXwGgmripRy6SCvsaC+APbmA2f6l8gPblIs/cHRfH1qt/9z4VBmVNBv16qHZgGtvi8vSC0g7UWazvvreKngwcYCQArHEGxrzp19t7VfMj/e06B1Cf7Ih1p9QpzLtxAAAOCUlEQVR9CgAjLbyJfmZyAECZTqaiHwaAO7fv/LRse3H3wllmwR2ZYo3q+lnhshBzd+xU/e7bDsvqgeyg8H7yntUno+v6DlGZjhpXDJEhSN/xaf3NFGAjKKH1bIxxvgDG+rgVXpZUy24KC/kqnG1/9HsvA6o5AAWAYZayAsAwdJ1Lq7MBgLH1w5TajOQA1lN4Vc5LE/9rcD5XK87FfFU+2Ew6VHx9ggPoaK/1PZX2b2ehhK7nDfuik6MLTT5LagEUAIZZIAoAw9B1Lq3OBgBS2YhLJwak+TYvPivr1Ln6vBDNGusix9TvGVNb6Xe3VS7Yey6QA5DqgUPHz6kZGzKHjV5vycaP6MJF0Akdb+ryXAQlaXbgUN8GaflaBqAAkHrq2+0l2wDEFUAB4Hlw8x12IgNbnw0ABI6LLB7qJYYzyVANN/K3uyI48wzUa8Sac4Y32NdgKKATyDRa+n4DppzGhL0vzAdurFl+WMkUstf82B91T9AiEPYBoVe9w5OzN3z7j5RPsCnH80SZ6kI5Kh7CIl+4dgtbuAAWYDkpfX/r1pcumeuN69c/SrWGx2xnw36Bde7oI9gXzncAx1o0pgqtRsVgTG4HoABg3QaFjULp+xUAcmfoJN3oFDAoAFRBVqmNPjoASFld0uKJgjqwhILfcf55eO9PVupuKL3Thp4CjZP1Yw8AboFTJ2OC9+7kOzw5e73rhKZO7rl4z4XSf67lKQO5q/fcU+n7V5xi9xAjLQRBK5ScA1AAWCoAzHU3bqHfuwcAXlqPg4tSOQPxe3IOMuQOiYKXQj3IOUcFNR3a4GkLa0g/OWMKUPEt8Hrm9sVajk2/X6j34FWangNQAJjxctSuj02BnQMAKQFJ9QhhBzD3k1t6NSLpJ/QRqO+M/m6oFoDSFdldbiitUb9epaudnAOQdk0BIP+OoxU2+KEIqAAgXVpJyykAJCXnqjGB3rwVR30o6f1Aw1trVqoHp/rD6cehXlZkTm8/dIzHsei27e+E2k1su7+h398aB6AA0K0HVwAIXcLDllcACKSvNAMO6QtA2PzPnQMIJKMWnwgFxgYAyp4klBycZSa0l5wDUAAInSotP2UKKAAEzo40nn1gs6XFm8gmPbRdLd+PAkenp18rW6BszaF1aV6IRnlRu/16z9ceHQDeunmn7FWetU3KQ+nIBaIZjANQAOAX1S6VUABIO5tcfgkpkG4NANKSQ1ubOgXE2WqFeQ5gvNJ2Y+kjbZ/jANYOvIHtL1IfsMllALETovXmSQHpRgpduNJ2Y6kmbV8BIJbCWm+rFBhLZlKzpHnm/PkhMMlaBiPCRPzo4ADcWVv0krYbS+TZAkAgHTn6KAfAUWimvysAbJ44BYCKPiQAUATqyDTSTelQP2VqvtCdqiEk2WtVIVJnbXv/ciGhcP8akY+oCC+uChcRicoYlIoeczeRnSsASAPuUPMMmaUgUpYCQKodQbSjADAwgSObVwA4cAcMCQA4qyzYli+zpYu1BzbnFP2p8rHtQHTghlCmxQFQWXgj10eyaoKw0O1vcZwTlGYiIpmhpdE+rbwx5omyS5CTMBnhBm4Iqy8pjokSAm5I7eZkGpRso++w+nqV4khZCgB9Z4SprwAwMIEjm1cAqKIoqxAwcgFJq7GpoXBDTCSXujgTEYmSxkv7zZXbNd+M0BiKUlt7jo6hv1MBRKSRtXCkLAWA0BkILK8AEEiwLRVXANgS4anPJpB2doZLxt/D+uo11hBVACnqbWMeKH/KjHE26/CHM71MjKzJurNrHEAywsysoclyAAoA015JCgDTnh9p7yYLAH2lnSAFh7twli3eL4mSL33edU8hLL1eUw9hSq4y7xz5n5wUvPHXimQknYhtl1vb0AfPXHF9snU++lYXQwEg1BQ4FT3IdQQfgLj7lPaF6khgnoqhtTKx9FIAuLbfooECgFfrKQD8buOmUgCIxRxZvb7STjj51+Kio8/jqLlrNuioPEhRl/niyfKnwhROFgB/OKuxbLTDlaLoiPXUDSHYY643hfmNe3qtxJptv9AOoD6Bs+L+ql37YPmg7DYooWkshagANdAejqEYaudSMxIotyHVPtizxI4ndb3pcgDC/AIkQSh1mgLAzZIECgDVQlAASA0p2t6kKACxF02RO5kFlTMROg0cQy0zuSheLX/DnJJUBiANTFF//+Ss8P8/S1nKpCZf0JnJcgCCvmsRAQUUAAREusRFFAB2fPKxOhVrQygtyFgcAJbSF4X9iRMVZMvfl89fHBw435Oh/yiORuALMGtORQFg6JW15fYVAGQToAAgo5OW2hIFOkxVv++7UuWRF/41TrT7XBUk7QdLxr3syuvlz3l+UVlU5vbz8gGyAGrDYK2DseYp37UPXf1r+y+Uz1DtgHB40cXGNgXmtB3S8PrUgKlcmrhd5QCil8y4FRUAhqW3AsCw9NXWe1Ig1FKP+5w0IAZ50hN2AFjoaIhITR3agSiOhhvnVH/ntCN9LSdpDu2dVyrOr9IKKQcw1RWC+qUAMJOJEnZz9gAgttWn0lpThGLSYGOLNCG9kxfD42f164Fx8ZN3GDXIBsTwpsCHp+cucASO/CM9YYADwGnQtyXtH5qu0vapUHHS+lw5aczGaA5AAeCscgbyobkUACqfCuoKoADQ3rKzBwBpvnsqrz2FYFT5qcX8w+O/devLF8sx3bh+/aOusfWV6nKIT/1OxdfHPhI2sw+7q2EBNvuVL0Doe2PNVd+XyqfAmE8qoPRemN4XAN7bwjrtANjIc9LxWDrE1pP6UsS2v+160RyAAsC5S4RReCcQBQDvPKQAsO09HfT9aAAI+ooW3hoFxPkdkD88tgRcywfBRC9u2At02vZTWoDDkzOXHdcYMwkLO6lWY2sT3PPDCgA9CTj16goA/WZIAaAf/bT2lilApe82xlCZh5K8B3djLjEKjqE4tHAMpkNqByFNx123OzFtD7f8lAPgKDTz3xUAuidQAaCiy2gAwEXaqaeJiYu/FuGHiFiTat9SNtVrNu/EByGCkDRue33XhvaE8f/70oW1HUeRj/Bw4c4vpReOL5BqvqTtUJmv+kbs2Za2RzpuXE4BgKGcdEFTzSgA7Dt7CQyYCgCxWzZtvdEAgA22CePicuP5E9+gaK5DLSjS4g3f9ah5CbWEFAablErppXShTI2xJSA1TIgrQPrPI3rNLZdg2m03ndYUAJi5UABomwIrAExn86boyWgAENrZUOHVUNlYpTbVoePjym9IjOKqXhjzSPmEuz8l1ZfShRonfk8CwMGBi+BDtYPHs22fDk4I2LBToIbcslMQ2DWI2vnZWzedHUSe2Vb2a8qrkltH3O8KAAyFFABOHdDgFGiYbLChFQBqAybn3twwbFIA4NBojN+3taHHGJt+Q04BTgvQuPpRjbpYhXWEo1V8BHjvfEMOT87Am1LUTkOG0uIAhvKFmSwHIJ/KsJIKAGH02tXSCgDVzF46AJDGs9/Vha/jUgo0KaAAgHID6vJQClwmCigAKADMar1z0vtZDWYCnVUAUACYwDKUd0EBQE4rSUkWALApLDRKZcGlbOSHypobKtQLlQGEeoNJiK5l4inACe/iW+5Xk/N6pFqnvCFx+T1jnHbh6ODAeWvCX73fUAXKPgS3qwDAcAAKAP02RuraCgAjAwA+MRsTCpZQrXjua8FCVxUGifASeqIHl5+Zf3fqDaftySiwLUtA0mKR8qlBw2E5AAWAdvTfoUwyZctMS02VAjsLAJQtOL67wMRglhneU+WpCZWyeg3/a4hC+1DZpi3szfKJ/bulHACUs9Z+UbZT5MXH5RPce7GNfcOCy5UDC7HUCxbufFJvQHEsP9TRY58XwFjbyj3IJbRIPd65tEdFM645YmIgWDZWhyDL89bhTK07sn0qrkYoB6AAoADQEjqdnHUG+ZzLRh2qnzsLAEMRjGu3I37Am66Ozd9zJ6z3PoN2pOqhAA5g40LfkHb7A88BPMmNMeZ3AGTI3ltc5O+W7SyzpZMSZ0X2RpMDkr7HfTm+tt+Zq69Bv5YtfOhYuA0zlNYotJ+7Xp6VAWyLAAoA3ZRXANjWitzN704WADC5uZN7bA4gNDfgbi6f+FEJhGaDaI3ie7ybNRUACDsATtilANBvQygA9KNfqtqzAQBO2r/Ili4izUWeuZRdjZx2X/d3cgjQ0JntFkdzJXPXeb9vqXYg1UTtWjuc5Vyo1mjb9OmQjbh4AFXwpun+KQB4DkABYNxFqgAwLr2pr7EAQPkCgH4ZS+OpbLSpYsBJhYNr0Wm5fPeExV8db9+YBxwRIRrxRHLXTWMZpe9Fqqy8Q69HGDl1pdk2B8DRUQHAcwBrJsw+nLcCQPrNLWmRW7iSNsoyCgCnlToaJZgBQzYWAEhTYG9rjOPOS6Xx0gnkylHagVQcABDOWPOK64sHhlQcDTe+y/o7BcihdKcsJ6X5EqT0nywHgDjbr7669YNyTK8//7yThSkAMByAAoB0C6QtpwCQhp6ctooFAMoUGFhjbBNPxfOXxqeHYVO+ANiyzdji0+puXtusO1+A4PfGfFi1Y76q6pun3MPaz91r7wsA740vDzb/qXwBQi3kSBkNWj9w4lGs9TJfOFaxEOYATMWiU8s8lRt26HqMvTKEcgDUPKfZ9qtWODoqABhTAYYCgALA/68CBYDUEBTZHiVLEHu3IX9oqfdcfVISTi+UgVAjo0svXwCq/Q2GMy27BorckIuv9jYrcpe0E2QapsiqfxvzxKYpq9vZ0TgJsTKsYA5gIk5VLAcQuX97V1MAqDPMuJNZAaD3khI1cNkA4P8AWy1b3za+yUcAAAAASUVORK5CYII=",
              "style": {
                "background-image": "url(data:image/png;base64,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)",
                "background-size": "128px 128px"
              }
            }
          ]
        }
      }
    };

    const watershedsLayer = new VectorTileLayer({
      source: new VectorTileSource({
          format: new MVT(),
          url: 'https://basemaps.arcgis.com/arcgis/rest/services/World_Basemap_v2/VectorTileServer/tile/{z}/{y}/{x}.pbf'
      }),
      name: "Environment Watersheds"
    });
    applyStyle(watershedsLayer, style, {updateSource: false});
    map.addLayer(watershedsLayer);

    // Click eventlisteners
    const handleMapClick = (event) => {
      const coordinate = event.coordinate;
      let zoom = map.getView().getZoom();
      if (zoom < MIN_QUERY_ZOOM) {
        map.getView().setCenter(coordinate);
        map.getView().setZoom(MIN_QUERY_ZOOM);
      } else {
        const url =
          "https://livefeeds3.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer/identify";
        if (markerLayer) {
          map.removeLayer(markerLayer);
        }
        const marker = new Feature({
          type: "marker",
          geometry: new Point(coordinate),
        });
        marker.setStyle(
          new Style({
            image: new Icon({
              src: svgURI,
              anchor: [0.5, 1], // Align the bottom-center of the icon to the point
            }),
          })
        );
        markerLayer = new VectorLayer({
          source: new VectorSource({
            features: [marker],
          }),
          zIndex: 4,
          name: "Stream Marker",
        });
        map.addLayer(markerLayer);

        // Build the identify request parameters
        const params = new URLSearchParams({
          f: "json",
          tolerance: 5, // Pixel tolerance
          returnGeometry: true,
          geometryType: "esriGeometryPoint",
          sr: 4326,
          geometry: coordinate.join(","),
          mapExtent: map.getView().calculateExtent().join(","),
          imageDisplay: "800,600,96",
        });

        fetch(`${url}?${params.toString()}`)
          .then((response) => response.json())
          .then((data) => {
            if (data.results && data.results.length > 0) {
              if (streamLayer) {
                map.removeLayer(streamLayer);
              }
              riverId = data.results[0].attributes["TDX Hydro Link Number"];
              console.log(riverId);
              const features = data.results[0].geometry.paths.map((path) => {
                return new Feature({
                  geometry: new LineString(path),
                  name: "Polyline",
                });
              });
              streamLayer = new VectorLayer({
                source: new VectorSource({
                  features: features,
                }),
                style: new Style({
                  stroke: new Stroke({
                    color: "#00008b",
                    width: 3,
                  }),
                }),
                zIndex: 3,
                name: "Stream Segment",
              });
              map.addLayer(streamLayer);

              updateVariableInputValues({
                "River ID": riverId,
              })
            } else {
              map.removeLayer(markerLayer);
              alert(
                "River not found. Try to zoom in and be precise when clicking the map."
              );
            }
          })
          .catch((error) => {
            console.error("Identify request failed:", error);
          });
      }
    };

    map.on("click", handleMapClick);
  }, [map]);

  return (
    <Fragment>
      <View {...viewConfig} />
      <Layers>
        {layers &&
          layers.map((config, index) => <Layer key={index} config={config} />)}
      </Layers>
      <Controls>
        <LayersControl />
        <LegendControl items={legend} />
      </Controls>
    </Fragment>
  );
};

export default MapComponentContent;
