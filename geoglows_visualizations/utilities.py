import os
from datetime import datetime, timezone
import geoglows
import pandas as pd
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go
import json


module_path = os.path.dirname(__file__)
PLOTS_CACHE_PATH = os.path.join(module_path, "geoglows_plots_cache")
if not os.path.exists(PLOTS_CACHE_PATH):
    os.makedirs(PLOTS_CACHE_PATH)


def get_plot_data(river_id, plot_name='forecast'):
    """Get newest forecast or historical data.

    Args:
        reach_id (int or str): river id
        plot_type (str, optional): The plot type. Options are forecast, historical, and return. Defaults to 'forecast'.

    Returns:
        df: the dataframe of the newest plot data
    """
    files = os.listdir(PLOTS_CACHE_PATH)
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
        cached_data_path = os.path.join(PLOTS_CACHE_PATH, cache_file)
    new_data_path = os.path.join(PLOTS_CACHE_PATH, f'{plot_name}-{river_id}-{current_date}.csv')

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

    headers = [x for x in percent_series.columns]

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


def get_SSI_data(df_retro):
    df_result = pd.DataFrame()
    for month in range(1, 13):
        monthly_average = df_retro.resample('M').mean()
        filtered_df = monthly_average[monthly_average.index.month == month].copy()
        df_mean = filtered_df.iloc[:, 0].mean()
        df_std_dev = filtered_df.iloc[:, 0].std()
        filtered_df['cumulative_probability'] = filtered_df.iloc[:, 0].apply(
            lambda x, df_mean=df_mean, df_std_dev=df_std_dev: 1-stats.norm.cdf(x, df_mean, df_std_dev)
        )
        filtered_df['probability_less_than_0.5'] = filtered_df['cumulative_probability'] < 0.5
        filtered_df['p'] = filtered_df['cumulative_probability']
        filtered_df.loc[filtered_df['cumulative_probability'] > 0.5, 'p'] = 1 - filtered_df['cumulative_probability']
        filtered_df['W'] = (-2 * np.log(filtered_df['p'])) ** 0.5
        C0 = 2.515517
        C1 = 0.802853
        C2 = 0.010328
        d1 = 1.432788
        d2 = 0.001308
        d3 = 0.001308
        filtered_df['SSI'] = filtered_df['W'] - (C0 + C1 * filtered_df['W'] + C2 * filtered_df['W'] ** 2) / (
                    1 + d1 * filtered_df['W'] + d2 * filtered_df['W'] ** 2 + d3 * filtered_df['W'] ** 3)
        filtered_df.loc[~filtered_df['probability_less_than_0.5'], 'SSI'] *= -1
        df_result = pd.concat([df_result, filtered_df])
    return df_result


def plot_ssi_each_month_since_year(reach_id, since_year):
    current_year = datetime.now().year
    assert 1941 <= since_year <= 2024 <= current_year, f'the year should be in range [1941, {current_year}]'

    df_retro = get_plot_data(reach_id, 'historical')
    df_ssi = get_SSI_data(df_retro)
    df_ssi_sorted = df_ssi.sort_index()[str(since_year):]
    fig = go.Figure(go.Scatter(
        x=df_ssi_sorted.index,
        y=df_ssi_sorted['SSI'],
        mode='lines+markers',
        marker=dict(symbol='circle', color='blue', size=5)
    ))
    fig.update_layout(xaxis_title='Date', yaxis_title='SSI')
    return fig


def get_SSI_monthly_data(df, month):
    monthly_average = df.resample('M').mean()
    filtered_df = monthly_average[monthly_average.index.month == month].copy()
    mean = filtered_df.iloc[:, 0].mean()
    std_dev = filtered_df.iloc[:, 0].std()
    filtered_df['cumulative_probability'] = filtered_df.iloc[:, 0].apply(lambda x: 1-stats.norm.cdf(x, mean, std_dev))
    filtered_df['probability_less_than_0.5'] = filtered_df['cumulative_probability'] < 0.5
    filtered_df['p'] = filtered_df['cumulative_probability']
    filtered_df.loc[filtered_df['cumulative_probability'] > 0.5, 'p'] = 1 - filtered_df['cumulative_probability']
    filtered_df['W'] = (-2 * np.log(filtered_df['p'])) ** 0.5
    C0 = 2.515517
    C1 = 0.802853
    C2 = 0.010328
    d1 = 1.432788
    d2 = 0.001308
    d3 = 0.001308
    filtered_df['SSI'] = filtered_df['W'] - (C0 + C1 * filtered_df['W'] + C2 * filtered_df['W'] ** 2) / \
        (1 + d1 * filtered_df['W'] + d2 * filtered_df['W'] ** 2 + d3 * filtered_df['W'] ** 3)
    filtered_df.loc[~filtered_df['probability_less_than_0.5'], 'SSI'] *= -1
    return filtered_df


def plot_ssi_one_month_each_year(reach_id, month):
    assert 1 <= month <= 12, f'the month number is in valid: {month}'

    df_retro = get_plot_data(reach_id, 'historical')
    df_ssi_month = get_SSI_monthly_data(df_retro, month)

    fig = go.Figure(go.Scatter(
        x=df_ssi_month.index,
        y=df_ssi_month['SSI'],
        mode='lines+markers',
        marker=dict(symbol='circle', color='blue', size=5)
    ))
    fig.update_layout(xaxis_title='Date', yaxis_title='SSI')
    return fig


def load_country_list():
    filename = os.path.join(module_path, "countries_extents.json")
    country_list = []
    with open(filename, "r") as file:
        data = json.load(file)
    for country_name, _extent in data.items():
        country_list.append({"value": country_name, "label": country_name})
    return country_list


def load_country_extents():
    filename = os.path.join(module_path, "countries_extents.json")
    country_extent = {}
    with open(filename, "r") as file:
        data = json.load(file)
    for country_name, extent in data.items():
        if extent:
            extent[0] -= 0.1
            extent[1] -= 0.1
            extent[2] += 0.1
            extent[3] += 0.1
        country_extent[country_name] = extent
    return country_extent
