from intake.source import base
import geoglows
import numpy as np
from .utilities import (
    get_plot_data, plot_retro_simulation, plot_retro_annual_status, plot_yearly_volumes, plot_retro_fdc,
    flood_probabilities, plot_ssi_each_month_since_year, plot_ssi_one_month_each_year
)
from datetime import datetime


class Plots(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "geoglows_plots"
    visualization_tags = [
        "geoglows",
        "streamflow",
        "ensemble",
        "exceedance",
        "return period",
    ]
    visualization_description = (
        "Depicts various streamflow based interactive charts based on the geoglows streamflow model. "
        "Charts included are derived from deterministic forecasts, ensemble forecasts, and statistical "
        "analysis."
    )
    visualization_args = {
        "river_id": "text",
        "plot_name": [
            {"value": "forecast", "label": "Forecast"},
            {"value": "forecast-stats", "label": "Forecast Statistics"},
            {"value": "forecast-ensembles", "label": "Forecast Ensembles"},
            {"value": "retro-simulation", "label": "Retrospective Simulation"},
            {"value": "retro-daily", "label": "Retrospective Daily Averages"},
            {"value": "retro-monthly", "label": "Retrospective Monthly Averages"},
            {"value": "retro-yearly", "label": "Retrospective Yearly Averages"},
            {"value": "retro-yearly-volume", "label": "Yearly Cumulative Discharge Volume"},
            {"value": "retro-status", "label": "Annual Status by Month"},  # need Year
            {"value": "retro-fdc", "label": "Flow Duration"},
            {"value": "exceedance", "label": "Exceedance"},
            {"value": "ssi-monthly", "label": "SSI Monthly"},
            {"value": "ssi-one-month", "label": "SSI One Month"}  # need Month
        ],
        "month": [{"value": i, "label": i} for i in range(1, 13)],
        "year": [{"value": i, "label": i} for i in range(1940, datetime.now().year)],
    }
    visualization_group = "GEOGLOWS"
    visualization_label = "GEOGLOWS Plots"
    visualization_type = "plotly"
    visualization_attribution = 'pygeoglows'
    _user_parameters = []

    def __init__(self, river_id, plot_name, year, month, metadata=None):
        self.river_id = int(river_id)
        self.plot_name = plot_name
        self.year = year
        self.month = month
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
            case "retro-simulation":
                df_retro_daily = get_plot_data(self.river_id, "retro-daily")
                df_retro_monthly = get_plot_data(self.river_id, "retro-monthly")
                plot = plot_retro_simulation(df_retro_daily, df_retro_monthly, self.river_id)
            case "retro-daily":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.daily_averages(df)
            case "retro-monthly":
                df = get_plot_data(self.river_id, self.plot_name)
                df['month'] = df.index.strftime('%m')
                df = df.groupby('month').mean()
                plot = geoglows.plots.monthly_averages(df)
            case "retro-yearly":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.annual_averages(df)
            case "retro-yearly-volume":
                df_retro_yearly = get_plot_data(self.river_id, "retro-yearly")
                plot = plot_yearly_volumes(df_retro_yearly, self.river_id)
            case "retro-status":
                df_retro_daily = get_plot_data(self.river_id, "retro-daily")
                df_retro_monthly = get_plot_data(self.river_id, "retro-monthly")
                plot = plot_retro_annual_status(df_retro_daily, df_retro_monthly, self.river_id, self.year)
            case "retro-fdc":
                df_retro_daily = get_plot_data(self.river_id, "retro-daily")
                plot = plot_retro_fdc(df_retro_daily, self.river_id)
            case "exceedance":
                df_ensemble = get_plot_data(self.river_id, "forecast-ensembles")
                df_return = get_plot_data(self.river_id, "return-periods")
                plot = flood_probabilities(df_ensemble, df_return)
            case "ssi-monthly":
                plot = plot_ssi_each_month_since_year(
                    self.river_id, 2010
                )  # TODO year is hardcoded?
            case "ssi-one-month":
                plot = plot_ssi_one_month_each_year(self.river_id, self.month)

        data = []
        for trace in plot.data:
            trace_json = trace.to_plotly_json()
            if "x" in trace_json and isinstance(trace_json["x"], np.ndarray):
                trace_json["x"] = trace_json["x"].tolist()
            if "y" in trace_json and isinstance(trace_json["y"], np.ndarray):
                trace_json["y"] = trace_json["y"].tolist()
            data.append(trace_json)
        layout = plot.to_plotly_json()["layout"]
        config = {"autosizable": True, "responsive": True}
        return {"data": data, "layout": layout, "config": config}
