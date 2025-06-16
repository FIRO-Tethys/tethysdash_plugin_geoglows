import os
from datetime import datetime, timezone
import geoglows
import pandas as pd
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go
import json
import getpass
import pwd
from pyproj import Transformer


username = os.environ.get("NGINX_USER", getpass.getuser())
uid = pwd.getpwnam(username).pw_uid
gid = pwd.getpwnam(username).pw_gid

module_path = os.path.dirname(__file__)
PLOTS_CACHE_PATH = os.path.join(module_path, "geoglows_plots_cache")
if not os.path.exists(PLOTS_CACHE_PATH):
    os.makedirs(PLOTS_CACHE_PATH)
    os.chown(PLOTS_CACHE_PATH, uid, gid)


def get_plot_data(river_id, plot_name='forecast'):
    """Get newest data for the selected plot.

    Args:
        river_id (int or str): river id
        plot_type (str, optional): The plot type. Options are forecast,
            historical, and return. Defaults to 'forecast'.  # TODO update doc

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
        case 'retro-simulation':
            if need_new_data:
                df = geoglows.data.retrospective(river_id)
            else:
                df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
                df.columns.name = 'rivid'
                df.columns = df.columns.astype('int')
        case 'return-periods':
            if need_new_data:
                df = geoglows.data.return_periods(river_id)
            else:
                df = pd.read_csv(cached_data_path, index_col=[0])
                df.columns = df.columns.astype('int')
        case 'retro-daily':
            if need_new_data:
                df = geoglows.data.retro_daily(river_id)
            else:
                df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
                df.columns = df.columns.astype('int')
        case 'retro-monthly':
            if need_new_data:
                df = geoglows.data.retro_monthly(river_id)
            else:
                df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
                df.columns = df.columns.astype('int')
        case 'retro-yearly':
            if need_new_data:
                df = geoglows.data.retro_yearly(river_id)
            else:
                df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
                df.columns = df.columns.astype('int')
        case _:
            raise ValueError("plot_name is unacceptable")

    if need_new_data:
        df.to_csv(new_data_path)
        if cached_data_path:
            os.remove(cached_data_path)

    return df


def plot_retro_simulation(df_retro_daily, df_retro_monthly, river_id):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_retro_daily.index,
        y=df_retro_daily[river_id],
        mode='lines',
        name='Daily Average'
    ))

    fig.add_trace(go.Scatter(
        x=df_retro_monthly.index,
        y=df_retro_monthly[river_id],
        mode='lines',
        name='Monthly Average',
        line=dict(color='rgb(0, 166, 255)'),
        visible='legendonly'
    ))

    fig.update_layout(
        title=f'Retrospective Simulation for River: {river_id}',
        legend=dict(orientation='h', x=0, y=0.9),
        hovermode='x',
        yaxis=dict(
            title="Discharge (m³/s)",
            range=[0, None]
        ),
        xaxis=dict(
            title="Date (UTC +00:00)",
            type='date',
            # autorange=False,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1 Year", step="year", stepmode="backward"),
                    dict(count=5, label="5 Years", step="year", stepmode="backward"),
                    dict(count=10, label="10 Years", step="year", stepmode="backward"),
                    dict(count=30, label="30 Years", step="year", stepmode="backward"),
                    dict(count=len(df_retro_daily.index), label="All", step="day")
                ]
            ),
            rangeslider=dict(visible=True)
        )
    )

    return fig


def plot_yearly_volumes(df_retro_yearly, river_id):
    seconds_per_year = 60 * 60 * 24 * 365.25
    df_retro_yearly['year'] = df_retro_yearly.index.strftime('%Y').astype('int')
    df_retro_yearly['volume'] = df_retro_yearly[river_id] * seconds_per_year / 1e6
    df_retro_yearly['5year_start'] = df_retro_yearly['year'] // 5 * 5
    df_5_year_avgs = df_retro_yearly.groupby('5year_start').mean().drop(['year', river_id], axis=1).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_retro_yearly['year'],
        y=df_retro_yearly['volume'],
        mode='lines',
        name='Annual Volume',
        marker=dict(color='rgb(0, 166, 255)')
    ))

    for idx, row in df_5_year_avgs.iterrows():
        year = row['5year_start']
        val = row['volume']
        fig.add_trace(go.Scatter(
            x=[year, year + 5],
            y=[val, val],
            mode='lines',
            legendgroup='5 Year Average',
            showlegend=idx == 0,  # TODO waht does this do?
            name='5 Year Average',
            marker=dict(color='red')
        ))

    fig.update_layout(
        title=f'Yearly Cumulative Discharge Volume for River: {river_id}',
        legend=dict(orientation='h'),
        hovermode='x',
        xaxis=dict(title='Year'),
        yaxis=dict(
            title='Million Cubic Meters (m³ * 10^6)',
            range=[0, None]
        )
    )

    return fig


def plot_retro_annual_status(df_retro_daily, df_retro_monthly, river_id, year):
    status_labels = ["Very Wet", "Wet", "Normal", "Dry", "Very Dry"]
    status_percentiles = [0, 13, 28, 72, 87]
    status_colors = ['rgb(44, 125, 205)', 'rgb(142, 206, 238)',
                     'rgb(231,226,188)', 'rgb(255, 168, 133)', 'rgb(205, 35, 63)']

    months = [f'{i}'.rjust(2, '0') for i in range(1, 13)]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    df_retro_daily['month'] = df_retro_daily.index.strftime('%m')

    monthly_status_values = {}
    for label in status_labels:
        monthly_status_values[label] = []

    for month in months:
        tmp = df_retro_daily[df_retro_daily['month'] == month].sort_values(by=river_id, ascending=False)
        values = tmp[river_id].to_list()

        for idx, percentile in enumerate(status_percentiles):
            index = int(len(values) * percentile / 100)
            monthly_status_values[status_labels[idx]].append(values[index])  # calculate values based on the percentile

    df_monthly_status = pd.DataFrame.from_dict(monthly_status_values)

    scatter_plots = []
    for i, label in enumerate(df_monthly_status.columns):
        scatter_plots.append(go.Scatter(
            x=month_names,
            y=df_monthly_status[label],
            mode="lines",
            fill="tozeroy",
            name=label,
            line=dict(width=0),
            fillcolor=status_colors[i]
        ))

    layout = go.Layout(
        title=f"Annual Status by Month for River: {river_id}",
        xaxis=dict(
            title="Month",
            tickvals=months,
            ticktext=month_names
        ),
        hovermode="x",
        yaxis=dict(
            title="Flow (m³/s)",
            range=[0, None]
        )
    )

    df_retro_monthly['year'] = df_retro_monthly.index.strftime('%Y')
    df_retro_monthly_year = df_retro_monthly[df_retro_monthly['year'] == str(year)]
    scatter_plots.append(go.Scatter(
        x=month_names,
        y=df_retro_monthly_year[river_id],
        name=f'year {year}',
        mode='lines',
        line=dict(width=2, color='black')
    ))

    return go.Figure(scatter_plots, layout)


def plot_retro_fdc(df_retro_daily, river_id):
    percentiles = [i * 2 for i in range(51)]
    percentiles_reversed = percentiles[::-1]

    def sorted_array_to_percentiles(array):
        return [array[len(array) * p // 100 - (1 if p == 100 else 0)] for p in percentiles_reversed]

    months = [f'{i}'.rjust(2, '0') for i in range(1, 13)]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df_retro_daily['month'] = df_retro_daily.index.strftime('%m')

    fdc = sorted_array_to_percentiles(df_retro_daily.sort_values(by=river_id)[river_id].to_list())
    monthly_fdc = {}
    for month in months:
        tmp = df_retro_daily[df_retro_daily['month'] == month].sort_values(by=river_id, ascending=True)
        values = tmp[river_id].to_list()
        monthly_fdc[month] = sorted_array_to_percentiles(values)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=percentiles,
        y=fdc,
        mode='lines',
        name='Flow Duration Curve'
    ))

    for i in range(12):
        month, month_name = months[i], month_names[i]
        fig.add_trace(go.Scatter(
            x=percentiles,
            y=monthly_fdc[month],
            mode='lines',
            name=f'FDC {month_name}'
        ))

    fig.update_layout(
        title=f'Flow Duration Curves for River: {river_id}',
        xaxis=dict(title='Percentile (100%)'),
        yaxis=dict(title='Flow (m³/s)', range=[0, None]),
        legend=dict(orientation='h'),
        hovermode='x'
    )

    return fig


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
    rperiods = rperiods.T
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

    df_retro = get_plot_data(reach_id, 'retro-simulation')
    df_ssi = get_SSI_data(df_retro)
    df_ssi_sorted = df_ssi.sort_index()[str(since_year):]
    fig = go.Figure(go.Scatter(
        x=df_ssi_sorted.index,
        y=df_ssi_sorted['SSI'],
        mode='lines+markers',
        marker=dict(symbol='circle', color='blue', size=5)
    ))
    fig.update_layout(xaxis_title='Date', yaxis_title='SSI', title="SSI Monthly Values Over Time")
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
    month = int(month)
    assert 1 <= month <= 12, f'the month number is in valid: {month}'

    df_retro = get_plot_data(reach_id, 'retro-simulation')
    df_ssi_month = get_SSI_monthly_data(df_retro, month)

    number_to_month = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    fig = go.Figure(go.Scatter(
        x=df_ssi_month.index,
        y=df_ssi_month['SSI'],
        mode='lines+markers',
        marker=dict(symbol='circle', color='blue', size=5)
    ))
    fig.update_layout(
        title=f"SSI Monthly Values for {number_to_month[month]} Over Time",
        xaxis_title='Date',
        yaxis_title='SSI'
    )
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


def convert_4326_to_3857(lon, lat):
    """
    Convert WGS84 (EPSG:4326) to Web Mercator (EPSG:3857).

    Parameters:
        lat (float): Latitude in degrees.
        lon (float): Longitude in degrees.

    Returns:
        (x, y): Tuple of coordinates in meters.
    """
    transformer = Transformer.from_crs(4326, 3857, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y
