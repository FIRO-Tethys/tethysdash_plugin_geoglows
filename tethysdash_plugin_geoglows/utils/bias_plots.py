import pandas as pd
import numpy as np
import plotly.graph_objs as go
import math
import datetime
import pytz


def gumbel1(rp: int, xbar: float, std: float) -> float:
    """
    Solves the Gumbel Type 1 distribution
    Args:
        rp: return period (years)
        xbar: average of the dataset
        std: standard deviation of the dataset

    Returns:
        float: solution to gumbel distribution
    """
    return round(-math.log(-math.log(1 - (1 / rp))) * std * .7797 + xbar - (.45 * std), 2)


def compute_return_periods(df_corrected: pd.DataFrame, river_id: str, rps=None) -> pd.DataFrame:
    """
    Compute return period flows from a bias-corrected daily streamflow dataframe.

    Parameters
    ----------
    df_corrected : pd.DataFrame
        Bias-corrected dataframe from geoglows.bias.correct_historical().
    river_id : str
        River ID for labeling the output column.
    rps : list[int], optional
        Return periods to compute (default = [2, 5, 10, 25, 50, 100]).

    Returns
    -------
    pd.DataFrame
        Return period flows (m³/s) with index = return period and column = river_id.
    """

    if rps is None:
        rps = [2, 5, 10, 25, 50, 100]

    # Ensure column name is standardized
    if "Corrected Simulated Streamflow" in df_corrected.columns:
        df_corrected = df_corrected.rename(columns={"Corrected Simulated Streamflow": "return_periods"})
    elif "return_periods" not in df_corrected.columns:
        raise ValueError("df_corrected must contain a 'Corrected Simulated Streamflow' or 'return_periods' column.")

    # Compute annual maxima
    annual_max_flow_list = (
        df_corrected.groupby(df_corrected.index.strftime("%Y"))["return_periods"].max().values.flatten()
    )

    # Fit Gumbel distribution parameters
    xbar = np.mean(annual_max_flow_list)
    std = np.std(annual_max_flow_list)

    # Compute return period flows
    rp_values = [round(gumbel1(rp, xbar, std), 3) for rp in rps]

    # Format as DataFrame
    results_formatted = pd.DataFrame(
        data=rp_values,
        index=rps,
        columns=[river_id]
    )
    results_formatted.index.name = "return_period"

    return results_formatted


def build_title(main_title, plot_titles: list):
    if plot_titles is not None:
        main_title += '<br>'.join(plot_titles)
    return main_title


def return_period_plot_colors():
    return {
        '2 Year': 'rgba(254, 240, 1, .4)',
        '5 Year': 'rgba(253, 154, 1, .4)',
        '10 Year': 'rgba(255, 56, 5, .4)',
        '20 Year': 'rgba(128, 0, 246, .4)',
        '25 Year': 'rgba(255, 0, 0, .4)',
        '50 Year': 'rgba(128, 0, 106, .4)',
        '100 Year': 'rgba(128, 0, 246, .4)',
    }


def _rperiod_scatters(startdate, enddate, rperiods: pd.DataFrame, y_max: float,
                      label_prefix: str = '', show: bool = True):
    colors = return_period_plot_colors()
    x_vals = (startdate, enddate, enddate, startdate)

    r2 = float(rperiods.loc[2].values[0])
    r5 = float(rperiods.loc[5].values[0])
    r10 = float(rperiods.loc[10].values[0])
    r25 = float(rperiods.loc[25].values[0])
    r50 = float(rperiods.loc[50].values[0])
    r100 = float(rperiods.loc[100].values[0])
    rmax = max(1.75*r100 - r25, y_max)

    # Helper: color is now required
    def template(name, y, color):
        return go.Scatter(
            name=f"{label_prefix} {name}" if label_prefix else name,
            x=x_vals,
            y=y,
            legendgroup=label_prefix,
            fill='toself',
            visible=show,
            line=dict(color=color, width=0)
        )

    traces = [
        template('2-Year', (r2, r2, r5, r5), colors['2 Year']),
        template('5-Year', (r5, r5, r10, r10), colors['5 Year']),
        template('10-Year', (r10, r10, r25, r25), colors['10 Year']),
        template('25-Year', (r25, r25, r50, r50), colors['25 Year']),
        template('50-Year', (r50, r50, r100, r100), colors['50 Year']),
        template('100-Year', (r100, r100, rmax, rmax), colors['100 Year']),
    ]

    return traces


def plot_forecast_bias_correct(
    df_sim: pd.DataFrame,
    df_corrected: pd.DataFrame,
    rp_df_sim: pd.DataFrame = None,
    rp_df_corrected: pd.DataFrame = None,
    plot_titles: list = None,
) -> go.Figure:
    """
    Plots simulated and bias-corrected forecasted streamflow with optional return periods.
    Median + uncertainty shading toggle together; return periods remain independent.
    """

    scatter_traces = []

    # --- Simulated traces ---
    scatter_traces += [
        go.Scatter(
            x=df_sim.index,
            y=df_sim['flow_median'],
            name='Simulated (Median)',
            line=dict(color='royalblue', width=2),
            legendgroup='Simulated_line',
        ),
        go.Scatter(
            x=np.concatenate([df_sim.index, df_sim.index[::-1]]),
            y=np.concatenate([df_sim['flow_uncertainty_upper'], df_sim['flow_uncertainty_lower'][::-1]]),
            fill='toself',
            fillcolor='rgba(65, 105, 225, 0.2)',
            line=dict(color='rgba(65, 105, 225, 0)'),
            showlegend=False,
            legendgroup='Simulated_line',  # toggled with median
        ),
    ]

    # --- Bias-corrected traces ---
    scatter_traces += [
        go.Scatter(
            x=df_corrected.index,
            y=df_corrected['flow_median'],
            name='Bias-Corrected (Median)',
            line=dict(color='darkorange', width=2),
            legendgroup='Bias-Corrected_line',
        ),
        go.Scatter(
            x=np.concatenate([df_corrected.index, df_corrected.index[::-1]]),
            y=np.concatenate([df_corrected['flow_uncertainty_upper'], df_corrected['flow_uncertainty_lower'][::-1]]),
            fill='toself',
            fillcolor='rgba(255, 165, 0, 0.2)',
            line=dict(color='rgba(255, 165, 0, 0)'),
            showlegend=False,
            legendgroup='Bias-Corrected_line',  # toggled with median
        ),
    ]

    # --- Add return period lines ---
    if rp_df_sim is not None:
        traces_sim = _rperiod_scatters(
            df_sim.index[0], df_sim.index[-1],
            rp_df_sim, df_sim['flow_uncertainty_upper'].max(),
            label_prefix='Simulated',  # return periods labeled but independent
            show=True
        )
        scatter_traces += traces_sim

    if rp_df_corrected is not None:
        traces_corr = _rperiod_scatters(
            df_corrected.index[0], df_corrected.index[-1],
            rp_df_corrected, df_corrected['flow_uncertainty_upper'].max(),
            label_prefix='Bias-Corrected',  # return periods labeled but independent
            show=True
        )
        scatter_traces += traces_corr

    # --- Layout ---
    layout = go.Layout(
        title=build_title('Forecasted Streamflow (Simulated vs Bias-Corrected)', plot_titles),
        yaxis={'title': 'Streamflow (m<sup>3</sup>/s)', 'range': [0, 'auto']},
        xaxis={
            'title': timezone_label(df_sim.index.tz),
            'range': [df_sim.index[0], df_sim.index[-1]],
            'hoverformat': '%d %b %Y %X',
        },
        legend=dict(orientation='h', y=-0.2),
    )

    return go.Figure(scatter_traces, layout=layout)


def timezone_label(timezone: str = None):
    timezone = str(timezone) if timezone is not None else 'UTC'
    # get the number of hours the timezone is offset from UTC
    now = datetime.datetime.now(pytz.timezone(timezone))
    utc_offset = now.utcoffset().total_seconds() / 3600
    # convert float number of hours to HH:MM format
    utc_offset = f'{int(utc_offset):+03d}:{int((utc_offset % 1) * 60):02d}'
    return f'Datetime ({timezone} {utc_offset})'


def plot_forecast_ensembles_bias_corrected(
    df: pd.DataFrame,  # geoglows.data.forecast_ensemble
    df_bias_corrected: pd.DataFrame,  # bias corrected version of above dataframe
    rp_df: pd.DataFrame = None,
    rp_df_bias_corrected: pd.DataFrame = None,
    plot_titles: list = None,
) -> go.Figure:
    """
    Plots simulated and bias-corrected streamflow ensembles with optional return periods.

    Groups in legend:
        - Simulated Ensemble
        - Bias-Corrected Ensemble
        - Simulated Return Periods (toggleable)
        - Bias-Corrected Return Periods (toggleable)
    """

    scatter_plots = []
    max_flows = []

    startdate = df.index[0]
    enddate = df.index[-1]

    def process_ensemble(df_input, color, legend_group, label_prefix):
        traces = []
        # High-resolution ensemble_52
        if 'ensemble_52' in df_input.columns:
            traces.append(go.Scatter(
                name=f"{label_prefix} Ensemble",
                x=df_input.index,
                y=df_input['ensemble_52'],
                line=dict(color=color, width=2),
                legendgroup=legend_group,
                showlegend=True
            ))
            max_flows.append(df_input['ensemble_52'].max())

        # Ensembles 01-51 (may have NaNs)
        for i in range(1, 52):
            col = f'ensemble_{i:02}'
            if col in df_input.columns:
                x_vals = df_input[col].dropna().index
                y_vals = df_input[col].dropna()
                traces.append(go.Scatter(
                    name=None,
                    x=x_vals,
                    y=y_vals,
                    line=dict(color=color, width=1),
                    opacity=0.4,
                    legendgroup=legend_group,
                    showlegend=False
                ))
                if not y_vals.empty:
                    max_flows.append(y_vals.max())
        return traces

    # --- Process ensembles ---
    scatter_plots += process_ensemble(df, 'royalblue', 'Simulated Ensemble', 'Simulated')
    scatter_plots += process_ensemble(df_bias_corrected, 'darkorange', 'Bias-Corrected Ensemble', 'Bias-Corrected')

    y_max = max(max_flows) if max_flows else 0

    # --- Return periods (toggleable) ---
    def add_rp_traces(rp_df, label_prefix):
        traces = _rperiod_scatters(startdate, enddate, rp_df, y_max, label_prefix=label_prefix, show=True)
        # Make all RP traces initially hidden but toggleable
        for t in traces:
            t.update(showlegend=True, visible='legendonly', legendgroup=f"{label_prefix} Return Periods")
        return traces

    if rp_df is not None:
        scatter_plots += add_rp_traces(rp_df, 'Simulated')

    if rp_df_bias_corrected is not None:
        scatter_plots += add_rp_traces(rp_df_bias_corrected, 'Bias-Corrected')

    # --- Layout ---
    layout = go.Layout(
        title=build_title('Simulated vs Bias-Corrected Ensemble Forecasts', plot_titles),
        yaxis={'title': 'Streamflow (m<sup>3</sup>/s)', 'range': [0, 'auto']},
        xaxis={
            'title': timezone_label(df.index.tz),
            'range': [startdate, enddate],
            'hoverformat': '%d %b %Y %X',
            'tickformat': '%b %d %Y'
        },
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1.0,
            xanchor='left',
            x=1.02,
            title='Legend',
            bgcolor='rgba(255,255,255,0.8)',
        ),
    )

    return go.Figure(scatter_plots, layout=layout)


def plot_forecast_stats_bias_corrected(
    df: pd.DataFrame,  # geoglows.data.forecast_stats(river_id)
    df_bias_corrected: pd.DataFrame,  # bias corrected version of above
    rp_df: pd.DataFrame = None,  # original return periods
    rp_df_bias_corrected: pd.DataFrame = None,  # new calculated return periods
    plot_titles: list = None,
    show_maxmin: bool = False,
) -> go.Figure:
    """
    Plots simulated and bias-corrected streamflow with optional max/min envelope, percentiles, and return periods.

    Groups in legend:
        - Simulated
        - Bias-Corrected
        - Simulated Return Periods
        - Bias-Corrected Return Periods
    """
    scatter_plots = []
    max_flows = []

    startdate = df.index[0]
    enddate = df.index[-1]

    def process_stats(df_input, label_prefix, color_median='red', color_avg='blue'):
        dates_stats = df_input['flow_avg'].dropna().index.tolist()
        dates_hires = df_input['high_res'].dropna().index.tolist()
        flow_max = df_input['flow_max'].dropna().tolist()
        flow_min = df_input['flow_min'].dropna().tolist()
        flow_75 = df_input['flow_75p'].dropna().tolist()
        flow_25 = df_input['flow_25p'].dropna().tolist()
        flow_avg = df_input['flow_avg'].dropna().tolist()
        flow_med = df_input['flow_med'].dropna().tolist()
        high_res = df_input['high_res'].dropna().tolist()
        y_max_local = max(flow_max + flow_75 + flow_avg + high_res)
        max_flows.append(y_max_local)

        traces = []

        # Max/Min envelope
        maxmin_visible = True if show_maxmin else 'legendonly'
        traces.append(go.Scatter(
            name=f"{label_prefix} Max & Min Flow",
            x=dates_stats + dates_stats[::-1],
            y=flow_max + flow_min[::-1],
            legendgroup=f"{label_prefix} Boundaries",
            fill='toself',
            visible=maxmin_visible,
            line=dict(color='lightblue', dash='dash')
        ))
        traces.append(go.Scatter(
            name=f"{label_prefix} Maximum",
            x=dates_stats,
            y=flow_max,
            legendgroup=f"{label_prefix} Boundaries",
            showlegend=False,
            visible=maxmin_visible,
            line=dict(color='darkblue', dash='dash')
        ))
        traces.append(go.Scatter(
            name=f"{label_prefix} Minimum",
            x=dates_stats,
            y=flow_min,
            legendgroup=f"{label_prefix} Boundaries",
            showlegend=False,
            visible=maxmin_visible,
            line=dict(color='darkblue', dash='dash')
        ))

        # Percentile envelope
        traces.append(go.Scatter(
            name=f"{label_prefix} 25-75 Percentile Flow",
            x=dates_stats + dates_stats[::-1],
            y=flow_75 + flow_25[::-1],
            legendgroup=f"{label_prefix} Percentiles",
            fill='toself',
            line=dict(color='lightgreen')
        ))
        traces.append(go.Scatter(
            name=f"{label_prefix} 75%",
            x=dates_stats,
            y=flow_75,
            legendgroup=f"{label_prefix} Percentiles",
            showlegend=False,
            line=dict(color='green')
        ))
        traces.append(go.Scatter(
            name=f"{label_prefix} 25%",
            x=dates_stats,
            y=flow_25,
            legendgroup=f"{label_prefix} Percentiles",
            showlegend=False,
            line=dict(color='green')
        ))

        # High-resolution forecast
        traces.append(go.Scatter(
            name=f"{label_prefix} High-Res Forecast",
            x=dates_hires,
            y=high_res,
            line=dict(color='black'),
            legendgroup=f"{label_prefix} Forecast"
        ))

        # Average and median
        traces.append(go.Scatter(
            name=f"{label_prefix} Average Flow",
            x=dates_stats,
            y=flow_avg,
            line=dict(color=color_avg),
            legendgroup=f"{label_prefix} Forecast"
        ))
        traces.append(go.Scatter(
            name=f"{label_prefix} Median Flow",
            x=dates_stats,
            y=flow_med,
            line=dict(color=color_median),
            legendgroup=f"{label_prefix} Forecast"
        ))

        return traces, y_max_local

    # --- Process simulated ---
    traces_sim, y_max_sim = process_stats(df, 'Simulated')
    scatter_plots += traces_sim

    # --- Process bias-corrected ---
    traces_bc, y_max_bc = process_stats(df_bias_corrected, 'Bias-Corrected')
    scatter_plots += traces_bc

    y_max = max(y_max_sim, y_max_bc)

    # --- Return periods (toggleable) ---
    def add_rp_traces(rp_df_input, label_prefix):
        traces = _rperiod_scatters(
            startdate, enddate, rp_df_input, y_max, label_prefix=label_prefix, show=True
        )
        for t in traces:
            t.update(showlegend=True, visible='legendonly', legendgroup=f"{label_prefix} Return Periods")
        return traces

    if rp_df is not None:
        scatter_plots += add_rp_traces(rp_df, 'Simulated')

    if rp_df_bias_corrected is not None:
        scatter_plots += add_rp_traces(rp_df_bias_corrected, 'Bias-Corrected')

    # --- Layout ---
    layout = go.Layout(
        title=build_title('Simulated vs Bias-Corrected Forecasted Streamflow', plot_titles),
        yaxis={'title': 'Streamflow (m<sup>3</sup>/s)', 'range': [0, 'auto']},
        xaxis={
            'title': timezone_label(df.index.tz),
            'range': [startdate, enddate],
            'hoverformat': '%d %b %Y %X',
            'tickformat': '%b %d %Y'
        },
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1.0,
            xanchor='left',
            x=1.02,
            title='Legend',
            bgcolor='rgba(255,255,255,0.8)'
        ),
    )

    return go.Figure(scatter_plots, layout=layout)


def plot_annual_averages_bias_corrected(
    df_simulated: pd.DataFrame,  # daily geoglows data
    df_bias_corrected: pd.DataFrame,  # bias corrected data
    df_observed: pd.DataFrame = None,  # observed dataframe
    plot_titles: list = None,
    decade_averages: bool = False
) -> go.Figure:
    """
    Plots annual average flows for simulated, bias-corrected, and optional observed data.
    Automatically aggregates high-resolution data to annual averages.

    Args:
        df_simulated: simulated forecast (can already be annual or higher-resolution)
        df_bias_corrected: bias-corrected forecast (higher-resolution)
        df_observed: optional observed time series (higher-resolution)
        plot_titles: dict or list to add to the plot title
        decade_averages: if True, will plot mean flows for each decade

    Returns:
        go.Figure
    """

    scatter_plots = []

    # --- Helper to compute annual average from any time resolution ---
    def annual_mean(df_input):
        df_input = df_input.copy()
        df_input.index = pd.to_datetime(df_input.index)
        df_input['year'] = df_input.index.year
        annual_avg = df_input.groupby('year').mean()
        return annual_avg

    # --- Compute annual averages ---
    df_sim_annual = annual_mean(df_simulated)
    df_bc_annual = annual_mean(df_bias_corrected)
    df_obs_annual = annual_mean(df_observed) if df_observed is not None else None

    # --- Simulated ---
    scatter_plots.append(go.Scatter(
        name='Simulated Annual Flow',
        x=df_sim_annual.index,
        y=df_sim_annual.values.flatten(),
        line=dict(color='blue'),
        legendgroup='Simulated'
    ))

    # --- Bias-Corrected ---
    scatter_plots.append(go.Scatter(
        name='Bias-Corrected Annual Flow',
        x=df_bc_annual.index,
        y=df_bc_annual.values.flatten(),
        line=dict(color='darkorange'),
        legendgroup='Bias-Corrected'
    ))

    # --- Observed ---
    if df_obs_annual is not None:
        scatter_plots.append(go.Scatter(
            name='Observed Annual Flow',
            x=df_obs_annual.index,
            y=df_obs_annual.values.flatten(),
            line=dict(color='green'),
            legendgroup='Observed'
        ))

    # --- Decade averages ---
    if decade_averages:
        def add_decade_traces(df_annual, label_prefix, color):
            first_year = int(df_annual.index[0])
            last_year = int(df_annual.index[-1])
            decades = range(first_year - first_year % 10, last_year + 1, 10)
            traces = []
            for decade in decades:
                decade_values = df_annual[(df_annual.index >= decade) & (df_annual.index < decade + 10)]
                if len(decade_values) == 0:
                    continue
                mean_flow = decade_values.values.flatten().mean()
                traces.append(go.Scatter(
                    name=f'{label_prefix} {decade}s: {mean_flow:.2f} m³/s',
                    x=[decade_values.index[0], decade_values.index[-1]],
                    y=mean_flow * np.ones(2),
                    line=dict(color=color, dash='dash'),
                    hoverinfo='name',
                    legendgroup=f'{label_prefix} Decade Averages',
                    legendgrouptitle=dict(text=f'{label_prefix} Decade Averages')
                ))
            return traces

        scatter_plots += add_decade_traces(df_sim_annual, 'Simulated', 'blue')
        scatter_plots += add_decade_traces(df_bc_annual, 'Bias-Corrected', 'darkorange')
        if df_obs_annual is not None:
            scatter_plots += add_decade_traces(df_obs_annual, 'Observed', 'green')

    # --- Layout ---
    layout = go.Layout(
        title=build_title('Annual Average Streamflow (Simulated vs Bias-Corrected vs Observed)', plot_titles),
        yaxis={'title': 'Streamflow (m³/s)'},
        xaxis={'title': 'Year'},
    )

    return go.Figure(scatter_plots, layout=layout)
