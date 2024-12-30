import React, { useEffect } from "react";
import "ol/ol.css";
import { Map } from "backlayer";
import MapComponentContent from "./MapContent";

const MapComponent = ({
  mapConfig,
  viewConfig,
  layers,
  legend,
  setVariableInputValues,
}) => {
  return (
    <Map {...mapConfig}>
      <MapComponentContent
        viewConfig={viewConfig}
        layers={layers}
        legend={legend}
        setVariableInputValues={setVariableInputValues}
      />
    </Map>
  );
};

export default MapComponent;
