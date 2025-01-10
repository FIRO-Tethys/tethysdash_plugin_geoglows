import React, { useEffect } from "react";
import "ol/ol.css";
import { Map } from "backlayer";
import MapComponentContent from "./MapContent";

const MapComponent = ({
  mapConfig,
  viewConfig,
  layers,
  legend,
  updateVariableInputValues,
}) => {
  return (
    <Map {...mapConfig}>
      <MapComponentContent
        viewConfig={viewConfig}
        layers={layers}
        legend={legend}
        updateVariableInputValues={updateVariableInputValues}
      />
    </Map>
  );
};

export default MapComponent;
