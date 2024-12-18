import React, { useEffect} from 'react';
import 'ol/ol.css';
import {
  Map
} from 'backlayer';
import MapComponentContent from './MapContent';

const MapComponent = (
  { 
    mapConfig, 
    viewConfig, 
    layers,
    legend
  }) => {

  return (
    <Map {...mapConfig} >
      <MapComponentContent viewConfig={viewConfig} layers={layers} legend={legend} />
    </Map>
  );
}

export default MapComponent;