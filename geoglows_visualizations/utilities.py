import os
from datetime import datetime, timezone
import geoglows
import pandas as pd
import plotly.graph_objects as go


CACHE_DIR_PATH = "../geoglows_plots_cache"  # TODO how to put it under tethysdash_plugin_geoglows?
if not os.path.exists(CACHE_DIR_PATH):
    os.makedirs(CACHE_DIR_PATH)


def get_plot_data(reach_id, plot_name='forecast'):
    """Get newest forecast or historical data.

    Args:
        reach_id (int or str): river id
        plot_type (str, optional): The plot type. Options are forecast and historical. Defaults to 'forecast'.

    Returns:
        df: the dataframe of the newest plot data
    """
    files = os.listdir(CACHE_DIR_PATH)
    cache_file = None
    for file in files:
        if file.startswith(f'{plot_name}-{reach_id}'):
            cache_file = file

    # Check if we can use the cached data, if not, delete it
    current_date = datetime.now(timezone.utc).strftime('%Y%m%d')
    need_new_data, cached_data_path = True, None
    if cache_file:
        cached_date = cache_file.split('-')[-1].split('.')[0]
        need_new_data = current_date != cached_date
        cached_data_path = os.path.join(CACHE_DIR_PATH, cache_file)
    new_data_path = os.path.join(CACHE_DIR_PATH, f'{plot_name}-{reach_id}-{current_date}.csv')

    if plot_name == 'forecast':
        if need_new_data:
            df = geoglows.data.forecast(reach_id)
        else:
            df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
    elif plot_name == 'historical':
        if need_new_data:
            df = geoglows.data.retrospective(reach_id)
        else:
            df = pd.read_csv(cached_data_path, parse_dates=['time'], index_col=[0])
            df.columns.name = 'rivid'
            df.columns = df.columns.astype('int64')
    else:
        raise ValueError("plot_name must be 'forecast' or 'historical'")

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


def plot_flow_regime(hist, selected_year, reach_id):
    """_summary_

    Args:
        reach_id (string): stream id
        selected_year (string): desired year
        hist (csv):the csv response from historic_simulation
    """

    hist = hist.rename(columns={reach_id: 'streamflow_m^3/s'})
    hdf = hist.copy()
    hdf = hdf[hdf.index.year >= 1991]
    hdf = hdf[hdf.index.year <= 2020]

    highflow = []
    above_normal = []
    normal = []
    below_normal = []

    for i in range(1, 13):
        filtered_month = hist[hist.index.month == i]
        filtered_month_mean = filtered_month.groupby(filtered_month.index.year).mean()
        avg = hdf.groupby(hdf.index.month).mean()
        filtered_month_mean["ratio"] = filtered_month_mean["streamflow_m^3/s"] / avg['streamflow_m^3/s'][i]
        filtered_month_mean["rank"] = filtered_month_mean["ratio"].rank()
        filtered_month_mean["percentile"] = filtered_month_mean["rank"] / (len(filtered_month_mean["rank"]) + 1)
        filtered_month_mean.sort_values(by='percentile', inplace=True)
        highflow.append(stream_estimate(filtered_month_mean, 0.87))
        above_normal.append(stream_estimate(filtered_month_mean, 0.72))
        normal.append(stream_estimate(filtered_month_mean, 0.28))
        below_normal.append(stream_estimate(filtered_month_mean, 0.13))
        # lowflow.append(stream_estimate(filtered_month_mean, 0.87))

    year_data = hist[hist.index.year == selected_year]
    months = ["Jan", "Feb", "March", "April", "May", "June", "July", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dataframe = pd.DataFrame(months)
    dataframe["high"] = highflow
    dataframe["above"] = above_normal
    dataframe["normal"] = normal
    dataframe["below"] = below_normal
    dataframe["year"] = year_data.groupby(year_data.index.month).mean().reset_index().drop("time", axis=1)

    # draw the plots
    scatter_plots = []
    scatter_plots.append(go.Scatter(
        x=dataframe[0], y=dataframe['below'], fill='tozeroy',
        fillcolor='rgba(205, 35, 63, 0.5)', mode='none', name="below"
    ))
    scatter_plots.append(go.Scatter(
        x=dataframe[0], y=dataframe['normal'], fill='tonexty',
        fillcolor='rgba(255, 168, 133, 0.5)', mode='none', name="normal"
    ))
    scatter_plots.append(go.Scatter(
        x=dataframe[0], y=dataframe['above'], fill='tonexty',
        fillcolor='rgba(231, 226, 188, 0.5)', mode='none', name="above"
    ))
    scatter_plots.append(go.Scatter(
        x=dataframe[0], y=dataframe['high'], fill='tonexty',
        fillcolor='rgba(142, 206, 238, 0.5)', mode='none', name="high"
    ))
    scatter_plots.append(go.Scatter(
        x=dataframe[0], y=dataframe['high'] * 2, fill='tonexty',
        fillcolor='rgba(44, 125, 205, 0.5)', mode='none', name="high * 2"
    ))

    for col in dataframe.columns[1:]:
        if col == "year":
            plot = go.Scatter(name=col, x=dataframe[0], y=dataframe[col],
                              mode="lines", line=dict(color="black", width=2))
        else:
            plot = go.Scatter(name=col, x=dataframe[0], y=dataframe[col],
                              mode="lines", line=dict(color="gray", width=1), showlegend=False)
        scatter_plots.append(plot)

    layout = go.Layout(
        # title=f"{selected_year} Monthly Streamflow with HydroSOS",
        title=None,
        yaxis={'title': 'Discharge'},
        xaxis={'title': 'Month of Year'},
        margin={"t": 0, "b": 0, "r": 0, "l": 0}
    )

    return go.Figure(scatter_plots, layout=layout)
