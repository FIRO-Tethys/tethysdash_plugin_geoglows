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
