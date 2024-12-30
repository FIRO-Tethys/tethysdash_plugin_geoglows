from intake.source import base
import geoglows
import numpy as np
from .utilities import get_plot_data, flood_probabilities, plot_ssi_each_month_since_year, plot_ssi_one_month_each_year


class Plots(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "geoglows_plots"
    visualization_args = {
        "river_id": "text",
        "plot_name": [
            {"value": "forecast", "label": "Forecast"},
            {"value": "forecast-stats", "label": "Forecast Statistics"},
            {"value": "forecast-ensembles", "label": "Forecast Ensembles"},
            {"value": "historical", "label": "Historical"},
            {"value": "flow-duration", "label": "Flow Duration"},
            {"value": "exceedance", "label": "Exceedance"},
            {"value": "daily-averages", "label": "Daily Averages"},
            {"value": "monthly-averages", "label": "Monthly Averages"},
            {"value": "ssi-monthly", "label": "SSI Monthly"},
            {"value": "ssi-one-month", "label": "SSI One Month"}
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
        df_return = get_plot_data(self.river_id, "return-periods")

        match self.plot_name:
            case "forecast":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.forecast(df, rp_df=df_return)
            case "forecast-stats":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.forecast_stats(df, rp_df=df_return)
            case "forecast-ensembles":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.forecast_ensembles(df, rp_df=df_return)
            case "historical":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.retrospective(df, rp_df=df_return)
            case "flow-duration":
                df = get_plot_data(self.river_id, "historical")
                plot = geoglows.plots.flow_duration_curve(df)
            case "exceedance":
                df_ensemble = get_plot_data(self.river_id, "forecast-ensembles")
                df_return = get_plot_data(self.river_id, "return-periods")
                plot = flood_probabilities(df_ensemble, df_return)
            case "daily-averages":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.daily_averages(df)
            case "monthly-averages":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.monthly_averages(df)
            case "ssi-monthly":
                plot = plot_ssi_each_month_since_year(self.river_id, 2010)  # TODO year is hardcoded?
            case "ssi-one-month":
                plot = plot_ssi_one_month_each_year(self.river_id, 1)

        data = []
        for trace in plot.data:
            trace_json = trace.to_plotly_json()
            if 'x' in trace_json and isinstance(trace_json['x'], np.ndarray):
                trace_json['x'] = trace_json['x'].tolist()
            if 'y' in trace_json and isinstance(trace_json['y'], np.ndarray):
                trace_json['y'] = trace_json['y'].tolist()
            data.append(trace_json)
        layout = plot.to_plotly_json()["layout"]
        config = {'autosizable': True, 'responsive': True}
        return {
            "data": data,
            "layout": layout,
            "config": config
        }
