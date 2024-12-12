import os
from datetime import datetime, timezone
import geoglows
import pandas as pd
import plotly.graph_objects as go


CACHE_DIR_PATH = "../geoglows_plots_cache"  # TODO how to put it under tethysdash_plugin_geoglows?
if not os.path.exists(CACHE_DIR_PATH):
    os.makedirs(CACHE_DIR_PATH)


def get_plot_data(river_id, plot_name='forecast'):
    """Get newest forecast or historical data.

    Args:
        reach_id (int or str): river id
        plot_type (str, optional): The plot type. Options are forecast, historical, and return. Defaults to 'forecast'.

    Returns:
        df: the dataframe of the newest plot data
    """
    files = os.listdir(CACHE_DIR_PATH)
    cache_file = None
    for file in files:
        if file.startswith(f'{plot_name}-{river_id}'):
            cache_file = file

    # Check if we can use the cached data, if not, delete it
    current_date = datetime.now(timezone.utc).strftime('%Y%m%d')
    need_new_data, cached_data_path = True, None
    if cache_file:
        cached_date = cache_file.split('-')[-1].split('.')[0]
        need_new_data = current_date != cached_date
        cached_data_path = os.path.join(CACHE_DIR_PATH, cache_file)
    new_data_path = os.path.join(CACHE_DIR_PATH, f'{plot_name}-{river_id}-{current_date}.csv')

    match plot_name:
        case "forecast":
            if need_new_data:
                df = geoglows.data.forecast(river_id)
            else:
                df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
        case "forecast-stats":
            if need_new_data:
                df = geoglows.data.forecast_stats(river_id)
            else:
                df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
        case "forecast-ensembles":
            if need_new_data:
                df = geoglows.data.forecast_ensembles(river_id)
            else:
                df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
        case 'historical':
            if need_new_data:
                df = geoglows.data.retrospective(river_id)
            else:
                df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
                df.columns.name = 'rivid'
                df.columns = df.columns.astype('int64')
        case 'return-periods':
            if need_new_data:
                df = geoglows.data.return_periods(river_id)
            else:
                df = pd.read_csv(cached_data_path, index_col=[0])
                df.columns = df.columns.astype('int')
        case 'daily-averages':
            if need_new_data:
                df = geoglows.data.daily_averages(river_id)
            else:
                df = pd.read_csv(cached_data_path, index_col=[0])
        case 'monthly-averages':
            if need_new_data:
                df = geoglows.data.monthly_averages(river_id)
            else:
                df = pd.read_csv(cached_data_path, index_col=[0])
        case _:
            raise ValueError("plot_name is unacceptable")

    if need_new_data:
        df.to_csv(new_data_path)
        if cached_data_path:
            os.remove(cached_data_path)

    return df


def stream_estimate(df, val):
    # Find the row with percentile <= 0.87
    lower_row = df[df['percentile'] <= val].iloc[-1]

    # Find the row with percentile > 0.87
    upper_row = df[df['percentile'] > val].iloc[0]

    # Linear interpolation formula
    percentile_lower = lower_row['percentile']
    percentile_upper = upper_row['percentile']
    streamflow_lower = lower_row['streamflow_m^3/s']
    streamflow_upper = upper_row['streamflow_m^3/s']
    target_percentile = val

    streamflow_estimate = (
            (streamflow_upper - streamflow_lower) /
            (percentile_upper - percentile_lower) *
            (target_percentile - percentile_lower) +
            streamflow_lower
    )
    return streamflow_estimate


def flood_probabilities(ensem: pd.DataFrame, rperiods: pd.DataFrame) -> str:
    """
    Processes the results of forecast_ensembles and return_periods and shows the probabilities of exceeding the
    return period flow on each day.

    Args:
        ensem: the csv response from forecast_ensembles
        rperiods: the csv response from return_periods

    Return:
         string containing html to build a table with a row of dates and for exceeding each return period threshold
    """
    ens = ensem.drop(columns=['ensemble_52']).dropna()
    ens = ens.groupby(ens.index.date).max()
    ens.index = pd.to_datetime(ens.index).strftime('%Y-%m-%d')
    # for each return period, get the percentage of columns with a value greater than the return period on each day
    percent_series = {rp: (ens > rperiods[rp].values[0]).mean(axis=1).values.tolist() for rp in rperiods}
    percent_series = pd.DataFrame(percent_series, index=ens.index)
    percent_series.index.name = 'Date'
    percent_series.columns = [f'{c} Year' for c in percent_series.columns]
    percent_series = percent_series * 100
    percent_series = percent_series.round(1)
    percent_series = percent_series.reset_index()

    colors = {
        'Date': 'rgba(0, 0, 0, 0)',
        '2 Year': 'rgba(254, 240, 1, {0})',
        '5 Year': 'rgba(253, 154, 1, {0})',
        '10 Year': 'rgba(255, 56, 5, {0})',
        '20 Year': 'rgba(128, 0, 246, {0})',
        '25 Year': 'rgba(255, 0, 0, {0})',
        '50 Year': 'rgba(128, 0, 106, {0})',
        '100 Year': 'rgba(128, 0, 246, {0})',
    }

    headers=[x for x in percent_series.columns]

    rows = []
    for _idx, row in enumerate(percent_series.values.tolist()):
        cells = []
        for col_idx, cell in enumerate(row):
            if col_idx == 0:
                cells.append(cell)
                continue
            cells.append(cell)
        rows.append(cells)
    df = pd.DataFrame(data=rows, columns=headers)

    fill_color = []
    for col in df.columns:
      col_colors = []
      for val in df[col]:
        color = colors[col] if col == 'Date' else colors[col].format(round(val * 0.005, 2))
        col_colors.append(color)
      fill_color.append(col_colors)

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            fill_color='rgba(0, 0, 0, 0)'
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color=fill_color
        ))
    ])
    return fig