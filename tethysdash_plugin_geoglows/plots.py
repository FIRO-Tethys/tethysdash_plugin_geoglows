from intake.source import base
import geoglows
import pandas as pd
import numpy as np
from .utils.plot_data import get_plot_data, get_bias_corrected_plot_data
from .utils.simu_plots import (
    plot_retro_simulation, plot_retro_annual_status, plot_yearly_volumes,
    plot_retro_fdc, plot_flood_probabilities, plot_ssi_each_month_since_year, plot_ssi_all_months
)
from .utils.bias_plots import (
    plot_forecast_bias_correct, compute_return_periods,
    plot_forecast_ensembles_bias_corrected, plot_forecast_stats_bias_corrected,
    plot_annual_averages_bias_corrected, plot_retro_simulation_corrected,
    plot_bias_corrected
)
import json
from tethysapp.tethysdash.exceptions import VisualizationError


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
            {"value": "forecast-ensembles", "label": "Forecast Ensemble"},
            {"value": "exceedance", "label": "Exceedance Probabilities Table"},
            {"value": "retro-simulation", "label": "Retrospective Simulation"},
            {"value": "retro-daily", "label": "Retrospective Daily Averages"},
            {"value": "retro-monthly", "label": "Retrospective Monthly Averages"},
            {"value": "retro-yearly", "label": "Retrospective Yearly Averages"},
            {"value": "retro-yearly-volume", "label": "Yearly Cumulative Discharge Volume"},
            {"value": "retro-status", "label": "Annual Status by Month"},
            {"value": "retro-fdc", "label": "Flow Duration"},
            {"value": "ssi-monthly", "label": "SSI Monthly Timeseries"},
            {"value": "ssi-one-month", "label": "SSI Individual Months Across Years"},
            {"value": "bias-performance", "label": "Bias Correction Performance"},
        ],
        "bias_correction": ["None", "Local", "Global"],
        "observed_historical_data": "csv-uploader"
    }
    visualization_group = "GEOGLOWS"
    visualization_label = "GEOGLOWS Plots"
    visualization_type = "plotly"
    visualization_attribution = 'pygeoglows'
    _user_parameters = []

    def __init__(self, river_id, plot_name, observed_historical_data=None, bias_correction="None", metadata=None):
        self.river_id = int(river_id)
        self.plot_name = plot_name
        self.observed_historical_data = observed_historical_data
        self.bias_correction = bias_correction
        super(Plots, self).__init__(metadata=metadata)

    def read(self):
        df_rp = get_plot_data(self.river_id, "return-periods")
        df_observed, df_rp_corrected = None, None
        df_retro_daily, df_retro_daily_corrected = None, None
        df_retro_daily = get_plot_data(self.river_id, "retro-daily")
        if self.bias_correction != "None":
            if self.bias_correction == "Local":
                try:
                    dict_bias = json.loads(self.observed_historical_data)
                except Exception:
                    raise VisualizationError(
                        "Please upload a valid CSV file for observed historical  or change bias correction option."
                        )
                df_observed = pd.DataFrame(dict_bias).replace("", np.nan)\
                    .assign(Datetime=lambda x: x['Datetime'].astype('datetime64[ns]')).set_index('Datetime')
                df_observed["Streamflow (m3/s)"] = df_observed["Streamflow (m3/s)"].astype(float)
                df_observed.index = df_observed.index.tz_localize("UTC")
                df_retro_daily_corrected = geoglows.bias.correct_historical(df_retro_daily, df_observed)
            elif self.bias_correction == "Global":
                df_retro_daily_corrected = geoglows.bias.discharge_transform(df_retro_daily, self.river_id)
                df_retro_daily_corrected.rename(
                    columns={self.river_id: "Corrected Simulated Streamflow"}, inplace=True
                    )
            df_rp_corrected = compute_return_periods(df_retro_daily_corrected, self.river_id)
        elif self.bias_correction == "None":
            df_retro_daily_corrected = df_retro_daily
            if self.plot_name == "bias-performance":
                raise VisualizationError("Bias performance plot requires bias correction option to be Local or Global.")

        match self.plot_name:
            case "forecast":
                df_forecast = get_plot_data(self.river_id, self.plot_name)
                if self.bias_correction == "None":
                    plot = geoglows.plots.forecast(df_forecast, rp_df=df_rp)
                else:
                    if self.bias_correction == "Local":
                        df_forecast_corrected = geoglows.bias.correct_forecast(
                            df_forecast, simulated_data=df_retro_daily, observed_data=df_observed
                        )
                    elif self.bias_correction == "Global":
                        df_forecast_corrected = geoglows.bias.discharge_transform(
                            df_forecast, self.river_id
                        )
                        df_forecast_corrected.rename(
                            columns={self.river_id: "Corrected Simulated Streamflow"}, inplace=True
                        )
                    plot = plot_forecast_bias_correct(
                        df_forecast, df_forecast_corrected, rp_df_sim=df_rp, rp_df_corrected=df_rp_corrected
                    )
            case "forecast-stats":
                df_forecast_stats = get_plot_data(self.river_id, self.plot_name)
                if self.bias_correction == "None":
                    plot = geoglows.plots.forecast_stats(df_forecast_stats, rp_df=df_rp)
                else:
                    if self.bias_correction == "Local":
                        df_forecast_stats_corrected = geoglows.bias.correct_forecast(
                            df_forecast_stats, simulated_data=df_retro_daily, observed_data=df_observed
                        )
                    elif self.bias_correction == "Global":
                        df_forecast_stats_corrected = geoglows.bias.discharge_transform(
                            df_forecast_stats, self.river_id
                        )
                        df_forecast_stats_corrected.rename(
                            columns={self.river_id: "Corrected Simulated Streamflow"}, inplace=True
                        )
                    plot = plot_forecast_stats_bias_corrected(
                        df_forecast_stats,
                        df_forecast_stats_corrected,
                        rp_df=df_rp,
                        rp_df_bias_corrected=df_rp_corrected
                    )
            case "forecast-ensembles":
                df_forecast_ensemble = get_plot_data(self.river_id, self.plot_name)
                if self.bias_correction == "None":
                    plot = geoglows.plots.forecast_ensembles(df_forecast_ensemble, rp_df=df_rp)
                else:
                    if self.bias_correction == "Local":
                        df_forecast_ensembles_corrected = geoglows.bias.correct_forecast(
                            df_forecast_ensemble, simulated_data=df_retro_daily, observed_data=df_observed
                        )
                    elif self.bias_correction == "Global":
                        df_forecast_ensembles_corrected = geoglows.bias.discharge_transform(
                            df_forecast_ensemble, self.river_id
                        )
                        df_forecast_ensembles_corrected.rename(
                            columns={self.river_id: "Corrected Simulated Streamflow"}, inplace=True
                        )
                    plot = plot_forecast_ensembles_bias_corrected(
                        df=df_forecast_ensemble,
                        df_bias_corrected=df_forecast_ensembles_corrected,
                        rp_df=df_rp,
                        rp_df_bias_corrected=df_rp_corrected
                    )
            case "retro-simulation":
                df_retro_monthly = get_plot_data(self.river_id, "retro-monthly")
                if self.bias_correction == "None":
                    plot = plot_retro_simulation(df_retro_daily, df_retro_monthly, self.river_id)
                elif self.bias_correction == "Local":
                    plot = geoglows.plots.corrected_retrospective(
                        df_retro_daily_corrected, df_retro_daily, df_observed, df_rp
                    )
                elif self.bias_correction == "Global":
                    df_retro_monthly_corrected = get_bias_corrected_plot_data(self.river_id, "retro-monthly")
                    plot = plot_retro_simulation_corrected(
                        df_retro_daily, df_retro_daily_corrected, df_retro_monthly,
                        df_retro_monthly_corrected, self.river_id)
            case "bias-performance":
                plot = geoglows.plots.corrected_scatterplots(df_retro_daily_corrected, df_retro_daily, df_observed)
            case "retro-daily":
                df_doy_mean = (
                    df_retro_daily
                    .groupby([df_retro_daily.index.month, df_retro_daily.index.day])
                    .mean()
                )
                df_doy_mean.index = pd.to_datetime(
                    [f"2000-{m:02d}-{d:02d}" for m, d in df_doy_mean.index],
                    format="%Y-%m-%d"
                )
                if self.bias_correction == "None":
                    plot = geoglows.plots.daily_averages(df_doy_mean)
                elif self.bias_correction == "Local":
                    plot = geoglows.plots.corrected_day_average(df_retro_daily_corrected, df_retro_daily, df_observed)
                elif self.bias_correction == "Global":
                    df_doy_corrected = (
                        df_retro_daily_corrected
                        .groupby([df_retro_daily_corrected.index.month, df_retro_daily_corrected.index.day])
                        .mean())
                    df_doy_corrected.index = pd.to_datetime(
                        [f"2000-{m:02d}-{d:02d}" for m, d in df_doy_corrected.index],
                        format="%Y-%m-%d"
                    )
                    plot = plot_bias_corrected(
                        df_doy_mean, df_doy_corrected,
                        "Daily Simulated Streamflow",
                        "Corrected Daily Simulated Streamflow",
                        self.river_id
                        )
            case "retro-monthly":
                df_retro_monthly = get_plot_data(self.river_id, self.plot_name)
                df_retro_monthly['month'] = df_retro_monthly.index.strftime('%m')
                df_retro_monthly = df_retro_monthly.groupby('month').mean()
                if self.bias_correction == "None":
                    plot = geoglows.plots.monthly_averages(df_retro_monthly)
                if self.bias_correction == "Local":
                    plot = geoglows.plots.corrected_month_average(df_retro_daily_corrected, df_retro_daily, df_observed)
                elif self.bias_correction == "Global":
                    df_retro_monthly_corrected = get_bias_corrected_plot_data(self.river_id, "retro-monthly")
                    df_retro_monthly_corrected['month'] = df_retro_monthly_corrected.index.strftime('%m')
                    df_retro_monthly_corrected = df_retro_monthly_corrected.groupby('month').mean()
                    df_retro_monthly_corrected = df_retro_monthly_corrected.rename(
                        columns={self.river_id: "Corrected Simulated Streamflow"}
                        )
                    plot = plot_bias_corrected(
                        df_retro_monthly,
                        df_retro_monthly_corrected,
                        "Monthly Simulated Averages",
                        "Corrected Monthly Simulated Averages",
                        self.river_id
                        )
            case "retro-yearly":
                if self.bias_correction == "None":
                    df = get_plot_data(self.river_id, self.plot_name)
                    plot = geoglows.plots.annual_averages(df)
                if self.bias_correction == "Local":
                    plot = plot_annual_averages_bias_corrected(
                        df_simulated=df_retro_daily, df_bias_corrected=df_retro_daily_corrected, df_observed=df_observed
                    )
                elif self.bias_correction == "Global":
                    plot = plot_annual_averages_bias_corrected(
                        df_simulated=df_retro_daily, df_bias_corrected=df_retro_daily_corrected, df_observed=None
                    )
            case "retro-yearly-volume":
                df_retro_yearly = get_plot_data(self.river_id, "retro-yearly")
                if self.bias_correction == "None":
                    plot = plot_yearly_volumes(df_retro_yearly, self.river_id)
                elif self.bias_correction == "Local" or self.bias_correction == "Global":
                    bias_corrected_yearly = df_retro_daily_corrected.resample('Y').mean()
                    bias_corrected_yearly = bias_corrected_yearly.rename(
                        columns={"Corrected Simulated Streamflow": self.river_id}
                        )
                    plot = plot_yearly_volumes(
                        df_retro_yearly=df_retro_yearly,
                        river_id=self.river_id,
                        df_retro_yearly_corrected=bias_corrected_yearly
                    )
            case "retro-status":
                df_retro_monthly = get_plot_data(self.river_id, "retro-monthly")
                if self.bias_correction == "None":
                    plot = plot_retro_annual_status(df_retro_daily, df_retro_monthly, self.river_id)
                elif self.bias_correction == "Global":
                    df_retro_daily_corrected = df_retro_daily_corrected.rename(
                        columns={"Corrected Simulated Streamflow": self.river_id}
                        )
                    df_retro_monthly_corrected = get_bias_corrected_plot_data(self.river_id, "retro-monthly")
                    plot = plot_retro_annual_status(
                        df_retro_daily=df_retro_daily_corrected,
                        df_retro_monthly=df_retro_monthly_corrected,
                        river_id=self.river_id,
                        bias_corrected=True
                    )
                elif self.bias_correction == "Local":
                    df_retro_monthly_corrected = df_retro_daily_corrected.resample('M').mean()
                    df_retro_monthly_corrected = df_retro_monthly_corrected.rename(
                        columns={"Corrected Simulated Streamflow": self.river_id}
                        )
                    df_retro_daily_corrected = df_retro_daily_corrected.rename(
                        columns={"Corrected Simulated Streamflow": self.river_id}
                        )
                    plot = plot_retro_annual_status(
                        df_retro_daily=df_retro_daily_corrected,
                        df_retro_monthly=df_retro_monthly_corrected,
                        river_id=self.river_id,
                        bias_corrected=True
                    )
            case "retro-fdc":
                if self.bias_correction == "None":
                    plot = plot_retro_fdc(df_retro_daily, self.river_id)
                elif self.bias_correction == "Local" or self.bias_correction == "Global":
                    df_retro_daily_corrected = df_retro_daily_corrected.rename(
                        columns={"Corrected Simulated Streamflow": self.river_id}
                        )
                    plot = plot_retro_fdc(
                        df_simulated=df_retro_daily, river_id=self.river_id, df_corrected=df_retro_daily_corrected
                    )
            case "exceedance":
                df_ensemble = get_plot_data(self.river_id, "forecast-ensembles")
                df_rp = get_plot_data(self.river_id, "return-periods")
                if self.bias_correction == "None":
                    plot = plot_flood_probabilities(df_ensemble, df_rp)
                else:
                    if self.bias_correction == "Local":
                        df_forecast_ensembles_corrected = geoglows.bias.correct_forecast(
                            df_ensemble, simulated_data=df_retro_daily, observed_data=df_observed
                        )
                    elif self.bias_correction == "Global":
                        df_forecast_ensembles_corrected = geoglows.bias.discharge_transform(
                            df_ensemble, self.river_id
                        )
                    plot = plot_flood_probabilities(
                        df_ensemble,
                        df_rp,
                        df_forecast_ensembles_corrected,
                        df_rp_corrected
                        )
            case "ssi-monthly":
                if self.bias_correction == "None":
                    plot = plot_ssi_each_month_since_year(
                        2010, df_retro_daily
                    )  # TODO year is hardcoded?
                elif self.bias_correction == "Local" or self.bias_correction == "Global":
                    plot = plot_ssi_each_month_since_year(
                        2010, df_retro_daily, df_retro_daily_corrected
                    )  # TODO year is hardcoded?
            case "ssi-one-month":
                if self.bias_correction == "None":
                    plot = plot_ssi_all_months(df_retro_daily)
                elif self.bias_correction == "Local" or self.bias_correction == "Global":
                    plot = plot_ssi_all_months(
                        df_retro_daily, df_retro_daily_corrected
                    )
        return json.loads(plot.to_json())
