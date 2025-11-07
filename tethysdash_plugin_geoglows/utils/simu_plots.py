from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .plot_data import get_plot_data, get_SSI_data, get_SSI_monthly_data


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

def plot_flood_probabilities(
    ensem: pd.DataFrame,
    rperiods: pd.DataFrame,
    ensem_corrected: pd.DataFrame = None,
    rperiods_corrected: pd.DataFrame = None
) -> go.Figure:
    """
    Processes the results of forecast_ensembles and return_periods and shows
    the probabilities of exceeding the return period flow on each day.
    Optionally processes a second ensemble (bias-corrected) dataset.

    Args:
        ensem: Forecast ensemble DataFrame.
        rperiods: Return periods DataFrame.
        ensem_corrected: Optional bias-corrected forecast ensemble.
        rperiods_corrected: Optional bias-corrected return periods.

    Returns:
        go.Figure: Plotly figure containing one or two tables.
    """
    def compute_probability_table(ensem_df, rperiods_df):
        """Inner function to compute exceedance probability table."""
        ens = ensem_df.drop(columns=['ensemble_52'], errors='ignore').dropna()
        ens = ens.groupby(ens.index.date).max()
        ens.index = pd.to_datetime(ens.index).strftime('%Y-%m-%d')

        rperiods_df = rperiods_df.T
        percent_series = {
            rp: (ens > rperiods_df[rp].values[0]).mean(axis=1).values.tolist()
            for rp in rperiods_df
        }
        percent_series = pd.DataFrame(percent_series, index=ens.index)
        percent_series.index.name = 'Date'
        percent_series.columns = [f'{c} Year' for c in percent_series.columns]
        percent_series = percent_series * 100
        percent_series = percent_series.round(1).reset_index()
        return percent_series

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

    def make_table(percent_series, title):
        """Create a Plotly Table figure for one dataset."""
        df = percent_series.copy()

        fill_color = []
        for col in df.columns:
            col_colors = []
            for val in df[col]:
                color = colors[col] if col == 'Date' else colors[col].format(round(val * 0.005, 2))
                col_colors.append(color)
            fill_color.append(col_colors)

        return go.Table(
            header=dict(values=list(df.columns), fill_color='rgba(0, 0, 0, 0)'),
            cells=dict(values=[df[col] for col in df.columns], fill_color=fill_color),
            domain=dict(x=[0, 1], y=[0, 1])
        )

    # --- Main execution ---
    tables = []

    # Original
    df_main = compute_probability_table(ensem, rperiods)
    tables.append(("Forecast Exceedance Probabilities", make_table(df_main, "Forecast Exceedance Probabilities")))

    # Optional corrected
    if ensem_corrected is not None and rperiods_corrected is not None:
        df_corrected = compute_probability_table(ensem_corrected, rperiods_corrected)
        tables.append(("Bias-Corrected Exceedance Probabilities", make_table(df_corrected, "Bias-Corrected Exceedance Probabilities")))

    # --- Combine into one figure ---
    if len(tables) == 1:
        fig = go.Figure(data=[tables[0][1]])
        fig.update_layout(title_text=tables[0][0])
        return fig

    # Two tables → must define table specs
    fig = make_subplots(
        rows=2, cols=1,
        specs=[[{"type": "table"}],
               [{"type": "table"}]],
        subplot_titles=[t[0] for t in tables]
    )

    for i, (_, table) in enumerate(tables, start=1):
        fig.add_trace(table, row=i, col=1)

    fig.update_layout(height=1200)
    return fig


def plot_ssi_each_month_since_year(since_year=None, df_retro=None, df_corrected=None):
    """
    Plots SSI monthly values over time since a given year.

    Works with either:
      - A reach_id (fetches retro data internally), OR
      - Pre-loaded DataFrames (df_retro, and optionally df_corrected).

    Args:
        reach_id (str, optional): ID of reach, used if df_retro is not provided.
        since_year (int): Year from which to start plotting (inclusive).
        df_retro (pd.DataFrame, optional): Retro-simulation DataFrame.
        df_corrected (pd.DataFrame, optional): Bias-corrected DataFrame.

    Returns:
        plotly.graph_objects.Figure
    """
    if since_year is None:
        raise ValueError("since_year must be provided")

    current_year = datetime.now().year
    assert 1941 <= since_year <= current_year, f'The year should be in range [1941, {current_year}]'

    # Process SSI for retro data
    df_ssi = get_SSI_data(df_retro)
    df_ssi_sorted = df_ssi.sort_index()[str(since_year):]

    fig = go.Figure()

    # Add retro trace
    fig.add_trace(go.Scatter(
        x=df_ssi_sorted.index,
        y=df_ssi_sorted['SSI'],
        mode='lines+markers',
        name='Original SSI',
        marker=dict(symbol='circle', color='blue', size=5),
        line=dict(color='blue')
    ))

    # Add corrected trace if provided
    if df_corrected is not None:
        df_ssi_corrected = get_SSI_data(df_corrected)
        df_ssi_corrected_sorted = df_ssi_corrected.sort_index()[str(since_year):]
        fig.add_trace(go.Scatter(
            x=df_ssi_corrected_sorted.index,
            y=df_ssi_corrected_sorted['SSI'],
            mode='lines+markers',
            name='Bias-Corrected SSI',
            marker=dict(symbol='square', color='red', size=5),
            line=dict(color='red')
        ))

    fig.update_layout(
        title=f"SSI Monthly Values Since {since_year}",
        xaxis_title='Date',
        yaxis_title='SSI',
        legend=dict(x=0.02, y=0.98)
    )

    return fig


def plot_ssi_one_month_each_year(month=None, df_retro=None, df_corrected=None):
    """
    Plots SSI for a given month across years.
    
    Can handle either:
      - Only df_retro (or reach_id for retro simulation), OR
      - Both df_retro and df_corrected for bias-corrected comparison.
    
    Args:
        reach_id (str, optional): Required if df_retro is not provided. Used to fetch retro data.
        month (int): Month number (1-12) to plot.
        df_retro (pd.DataFrame, optional): Pre-loaded retro simulation data.
        df_corrected (pd.DataFrame, optional): Pre-loaded bias-corrected data.
    
    Returns:
        plotly.graph_objects.Figure
    """
    if month is None:
        raise ValueError("Month must be provided")
    month = int(month)
    assert 1 <= month <= 12, f'The month number is invalid: {month}'

    
    df_ssi_month = get_SSI_monthly_data(df_retro, month)
    
    number_to_month = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    
    fig = go.Figure()
    
    # Add retro trace
    fig.add_trace(go.Scatter(
        x=df_ssi_month.index,
        y=df_ssi_month['SSI'],
        mode='lines+markers',
        name='Original SSI',
        marker=dict(symbol='circle', color='blue', size=5),
        line=dict(color='blue')
    ))
    
    # Add corrected trace if provided
    if df_corrected is not None:
        df_ssi_corrected = get_SSI_monthly_data(df_corrected, month)
        fig.add_trace(go.Scatter(
            x=df_ssi_corrected.index,
            y=df_ssi_corrected['SSI'],
            mode='lines+markers',
            name='Bias-Corrected SSI',
            marker=dict(symbol='square', color='red', size=5),
            line=dict(color='red')
        ))
    
    fig.update_layout(
        title=f"SSI Monthly Values for {number_to_month[month]} Over Time",
        xaxis_title='Date',
        yaxis_title='SSI',
        legend=dict(x=0.02, y=0.98)
    )
    
    return fig
