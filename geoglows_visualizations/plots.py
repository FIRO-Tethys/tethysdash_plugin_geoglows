from intake.source import base
import geoglows
import numpy as np
from .utilities import get_plot_data, plot_flow_regime


class Plots(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "geoglows_plots"
    visualization_args = {
        "river_id": "text",
        "plot_name": [
            {"value": "forecast", "label": "Forecast"},
            {"value": "historical", "label": "Historical"},
            {"value": "flow-duration", "label": "Flow Duration"},
            {"value": "flow-regime", "label": "Flow Regime"},  # TODO need a variable year
        ]
    }
    visualization_group = "GEOGLOWS"
    visualization_label = "GEOGLOWS Plots"
    visualization_type = "plotly"
    _user_parameters = []

    def __init__(self, river_id, plot_name, metadata=None):
        self.river_id = int(river_id)
        self.plot_name = plot_name
        super(Plots, self).__init__(metadata=metadata)

    def read(self):
        # Get plot data
        if self.plot_name in ["flow-duration", "flow-regime"]:
            df = get_plot_data(self.river_id, "historical")
        else:
            df = get_plot_data(self.river_id, "forecast")

        # Draw the plot
        match self.plot_name:
            case "forecast":
                plot = geoglows.plots.forecast(df)
            case "historical":
                plot = geoglows.plots.retrospective(df)
            case "flow-duration":
                plot = geoglows.plots.flow_duration_curve(df)
            case "flow-regime":
                plot = plot_flow_regime(df, selected_year=2023, reach_id=self.river_id)

        data = []
        for trace in plot.data:
            trace_json = trace.to_plotly_json()
            if isinstance(trace_json['x'], np.ndarray):
                trace_json['x'] = trace_json['x'].tolist()
            if isinstance(trace_json['y'], np.ndarray):
                trace_json['y'] = trace_json['y'].tolist()
            data.append(trace_json)
        layout = plot.to_plotly_json()["layout"]
        config = {'autosizable': True, 'responsive': True}
        return {
            "data": data,
            "layout": layout,
            "config": config
        }
