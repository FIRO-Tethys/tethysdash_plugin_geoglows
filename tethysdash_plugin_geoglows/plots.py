from intake.source import base
import geoglows
import pandas as pd
import numpy as np
from .utils.plot_data import get_plot_data
from .utils.simu_plots import (
    plot_retro_simulation, plot_retro_annual_status, plot_yearly_volumes,
    plot_retro_fdc, plot_flood_probabilities, plot_ssi_each_month_since_year, plot_ssi_one_month_each_year
)
from .utils.bias_plots import (
    plot_forecast_bias_correct, compute_return_periods,
    plot_forecast_ensembles_bias_corrected, plot_forecast_stats_bias_corrected,
    plot_annual_averages_bias_corrected, plot_yearly_volumes_corrected, plot_retro_simulation_corrected
)
from datetime import datetime
import json


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
            {"value": "forecast-bias-corrected", "label": "Forecast (Bias Corrected)"},
            {"value": "forecast-stats", "label": "Forecast Statistics"},
            {"value": "forecast-stats-bias-corrected", "label": "Forecast Statistics (Bias Corrected)"},
            {"value": "forecast-ensembles", "label": "Forecast Ensembles"},
            {"value": "forecast-ensembles-bias-corrected", "label": "Forecast Ensembles (Bias Corrected)"},
            {"value": "retro-simulation", "label": "Retrospective Simulation"},
            {"value": "retro-simulation-bias-corrected", "label": "Retrospective Simulation (Bias Corrected)"},
            {"value": "bias-performance", "label": "Bias Correction Performance"},
            {"value": "retro-daily", "label": "Retrospective Daily Averages"},
            {"value": "retro-daily-bias-corrected", "label": "Retrospective Daily Averages (Bias Corrected)"},
            {"value": "retro-monthly", "label": "Retrospective Monthly Averages"},
            {"value": "retro-monthly-bias-corrected", "label": "Retrospective Monthly Averages (Bias Corrected)"},
            {"value": "retro-yearly", "label": "Retrospective Yearly Averages"},
            {"value": "retro-yearly-bias-corrected", "label": "Retrospective Yearly Averages (Bias Corrected)"},
            {"value": "retro-yearly-volume", "label": "Yearly Cumulative Discharge Volume"},
            {"value": "retro-status", "label": "Annual Status by Month"},  # need Year
            {"value": "retro-fdc", "label": "Flow Duration"},
            {"value": "exceedance", "label": "Exceedance"},
            {"value": "exceedance-bias-corrected", "label": "Exceedance (Bias Corrected)"},
            {"value": "ssi-monthly", "label": "SSI Monthly"},
            {"value": "ssi-one-month", "label": "SSI One Month"}  # need Month
        ],
        "bias_correction": ["None", "Local", "Global"],
        "month": [{"value": i, "label": i} for i in range(1, 13)],
        "year": [{"value": i, "label": i} for i in range(1940, datetime.now().year)],
        "observed_historical_data": "csv-uploader"
    }
    visualization_group = "GEOGLOWS"
    visualization_label = "GEOGLOWS Plots"
    visualization_type = "plotly"
    visualization_attribution = 'pygeoglows'
    _user_parameters = []

    def __init__(self, river_id, plot_name, year, month, observed_historical_data=None, bias_correction = "None", metadata=None):
        self.river_id = int(river_id)
        self.plot_name = plot_name
        self.year = year
        self.month = month
        self.observed_historical_data = observed_historical_data
        self.bias_correction = bias_correction
        super(Plots, self).__init__(metadata=metadata)

    def read(self):
        df_rp = get_plot_data(self.river_id, "return-periods")
        df_observed, df_rp_corrected = None, None
        df_retro_daily, df_retro_daily_corrected = None, None
        if self.observed_historical_data and 'bias' in self.plot_name:
            try:
                dict_bias = json.loads(self.observed_historical_data)
            except json.JSONDecodeError as e:
                raise ValueError("Uploaded observed historical data is not valid JSON:", e[:100], "...")
            df_observed = pd.DataFrame(dict_bias).replace("", np.nan)\
                .assign(Datetime=lambda x: x['Datetime'].astype('datetime64[ns]')).set_index('Datetime')
            df_observed["Streamflow (m3/s)"] = df_observed["Streamflow (m3/s)"].astype(float)
            df_observed.index = df_observed.index.tz_localize("UTC")
            df_retro_daily = get_plot_data(self.river_id, "retro-daily")
            if self.bias_correction == "Local":
                df_retro_daily_corrected = geoglows.bias.correct_historical_local(df_retro_daily, df_observed)
            elif self.bias_correction == "Global":
                df_retro_daily_corrected = geoglows.bias.discharge_transform(df_retro_daily, self.river_id)
            elif self.bias_correction == "None":
                df_retro_daily_corrected = df_retro_daily
            df_rp_corrected = compute_return_periods(df_retro_daily_corrected, self.river_id)

        match self.plot_name:
            case "forecast":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.forecast(df, rp_df=df_rp)
            case "forecast-bias-corrected":
                df_forecast = get_plot_data(self.river_id, "forecast")
                df_retro_daily = get_plot_data(self.river_id, "retro-daily")
                if self.bias_correction == "Local":
                    df_forecast_corrected = geoglows.bias.correct_forecast(
                        df_forecast, simulated_data=df_retro_daily, observed_data=df_observed
                    )
                elif self.bias_correction == "Global":
                    df_forecast_corrected = geoglows.bias.discharge_transform(
                        df_forecast, self.river_id
                    )
                elif self.bias_correction == "None":
                    df_forecast_corrected = df_forecast
                plot = plot_forecast_bias_correct(
                    df_forecast, df_forecast_corrected, rp_df_sim=df_rp, rp_df_corrected=df_rp_corrected
                )
            case "forecast-stats":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.forecast_stats(df, rp_df=df_rp)
            case "forecast-stats-bias-corrected":
                df_forecast_stats = get_plot_data(self.river_id, "forecast-stats")
                if self.bias_correction == "Local":
                    df_forecast_stats_corrected = geoglows.bias.correct_forecast(
                        df_forecast_stats, simulated_data=df_retro_daily, observed_data=df_observed
                    )
                elif self.bias_correction == "Global":
                    df_forecast_stats_corrected = geoglows.bias.discharge_transform(
                        df_forecast_stats, self.river_id
                    )
                elif self.bias_correction == "None":
                    df_forecast_stats_corrected = df_forecast_stats
                plot = plot_forecast_stats_bias_corrected(
                    df_forecast_stats, df_forecast_stats_corrected, rp_df=df_rp, rp_df_bias_corrected=df_rp_corrected
                )
            case "forecast-ensembles":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.forecast_ensembles(df, rp_df=df_rp)
            case "forecast-ensembles-bias-corrected":
                df_forecast_ensembles = get_plot_data(self.river_id, "forecast-ensembles")
                if self.bias_correction == "Local":
                    df_forecast_ensembles_corrected = geoglows.bias.correct_forecast(
                        df_forecast_ensembles, simulated_data=df_retro_daily, observed_data=df_observed
                    )
                elif self.bias_correction == "Global":
                    df_forecast_ensembles_corrected = geoglows.bias.discharge_transform(
                        df_forecast_ensembles, self.river_id
                    )
                plot = plot_forecast_ensembles_bias_corrected(
                    df=df_forecast_ensembles,
                    df_bias_corrected=df_forecast_ensembles_corrected,
                    rp_df=df_rp,
                    rp_df_bias_corrected=df_rp_corrected
                )
            case "retro-simulation":
                df_retro_daily = get_plot_data(self.river_id, "retro-daily")y
                df_retro_monthly = get_plot_data(self.river_id, "retro-monthly")
                plot = plot_retro_simulation(df_retro_daily, df_retro_monthly, self.river_id)
            case "retro-simulation-bias-corrected":
                
                if self.bias_correction == "Local":
                    plot = geoglows.plots.corrected_retrospective(
                        df_retro_daily_corrected, df_retro_daily, df_observed, df_rp
                )
                elif self.bias_correction == "Global":
                    df_retro_monthly = get_plot_data(self.river_id, "retro-monthly")
                    plot = plot_retro_simulation_corrected(
                        df_retro_daily, df_retro_daily_corrected, df_retro_monthly,
                        df_retro_monthly_corrected, self.river_id) #TODO
            case "bias-performance":
                plot = geoglows.plots.corrected_scatterplots(df_retro_daily_corrected, df_retro_daily, df_observed)
            case "retro-daily":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.daily_averages(df)
            case "retro-daily-bias-corrected":
                if self.bias_correction == "Local":
                    plot = geoglows.plots.corrected_day_average(df_retro_daily_corrected, df_retro_daily, df_observed)
            case "retro-monthly":
                df = get_plot_data(self.river_id, self.plot_name)
                df['month'] = df.index.strftime('%m')
                df = df.groupby('month').mean()
                plot = geoglows.plots.monthly_averages(df)
            case "retro-monthly-bias-corrected":
                if self.bias_correction == "Local":
                    plot = geoglows.plots.corrected_month_average(df_retro_daily_corrected, df_retro_daily, df_observed)
            case "retro-yearly":
                df = get_plot_data(self.river_id, self.plot_name)
                plot = geoglows.plots.annual_averages(df)
            case "retro-yearly-bias-corrected":
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
                if self.bias == "None":
                    plot = plot_yearly_volumes(df_retro_yearly, self.river_id)
                else:
                    plot = plot_yearly_volumes_corrected(
                        df_retro_yearly_og=df_retro_yearly, df_retro_yearly_corrected=df_retro_daily_corrected,
                       river_id=self.river_id
                    )#TODO - should it take in yearly data?
            case "retro-status":
                df_retro_daily = get_plot_data(self.river_id, "retro-daily")
                df_retro_monthly = get_plot_data(self.river_id, "retro-monthly")
                plot = plot_retro_annual_status(df_retro_daily, df_retro_monthly, self.river_id, self.year)
            case "retro-fdc":
                df_retro_daily = get_plot_data(self.river_id, "retro-daily")
                plot = plot_retro_fdc(df_retro_daily, self.river_id)
            case "exceedance":
                df_ensemble = get_plot_data(self.river_id, "forecast-ensembles")
                df_rp = get_plot_data(self.river_id, "return-periods")
                plot = plot_flood_probabilities(df_ensemble, df_rp)
            case "exceedance-bias-corrected":
                df_forecast_ensembles = get_plot_data(self.river_id, "forecast-ensembles")
                if self.bias_correction == "Local":
                    df_forecast_ensembles_corrected = geoglows.bias.correct_forecast(
                        df_forecast_ensembles, simulated_data=df_retro_daily, observed_data=df_observed
                    )
                elif self.bias_correction == "Global":
                    df_forecast_ensembles_corrected = geoglows.bias.discharge_transform(
                        df_forecast_ensembles, self.river_id
                    )
                plot = plot_flood_probabilities(df_forecast_ensembles_corrected, df_rp_corrected)
            case "ssi-monthly":
                plot = plot_ssi_each_month_since_year(
                    self.river_id, 2010
                )  # TODO year is hardcoded?
            case "ssi-one-month":
                plot = plot_ssi_one_month_each_year(self.river_id, self.month)
        return json.loads(plot.to_json())
