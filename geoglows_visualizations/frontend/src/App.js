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
    layers
  }) => {

  return (
    <Map {...mapConfig} >
      <MapComponentContent viewConfig={viewConfig} layers={layers} />
    </Map>
  );
}

export default MapComponent;