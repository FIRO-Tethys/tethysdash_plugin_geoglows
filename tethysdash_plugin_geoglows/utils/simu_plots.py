from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from .plot_data import get_plot_data, get_SSI_data


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


def plot_yearly_volumes(df_retro_yearly, river_id, df_retro_yearly_corrected=None):
    """
    Plots yearly cumulative discharge volumes for a river.
    
    If df_retro_yearly_corrected is provided, compares original vs bias-corrected volumes.
    Otherwise, plots only the original yearly data.

    Args:
        df_retro_yearly (pd.DataFrame): Original yearly data
        river_id (str): Column name for river discharge
        df_retro_yearly_corrected (pd.DataFrame, optional): Bias-corrected yearly data
        
    Returns:
        go.Figure: Plotly figure
    """
    seconds_per_year = 60 * 60 * 24 * 365.25

    def prepare_df(df, label_prefix):
        df = df.copy()
        df['year'] = df.index.strftime('%Y').astype('int')
        df['volume'] = df[river_id] * seconds_per_year / 1e6
        df['5year_start'] = df['year'] // 5 * 5
        df_5yr = df.groupby('5year_start').mean().drop(['year', river_id], axis=1).reset_index()
        df['label_prefix'] = label_prefix
        df_5yr['label_prefix'] = label_prefix
        return df, df_5yr

    # Prepare original data
    df_yearly, df_5yr = prepare_df(df_retro_yearly, "Simulation")

    # Prepare corrected data if provided
    if df_retro_yearly_corrected is not None and not df_retro_yearly_corrected.empty:
        df_yearly_corr, df_5yr_corr = prepare_df(df_retro_yearly_corrected, "Corrected")
    else:
        df_yearly_corr, df_5yr_corr = None, None

    fig = go.Figure()

    # Annual volumes - original
    fig.add_trace(go.Scatter(
        x=df_yearly['year'],
        y=df_yearly['volume'],
        mode='lines',
        name='Annual Volume Simulation',
        marker=dict(color='rgb(0, 166, 255)')
    ))

    # 5-year averages - original
    for idx, row in df_5yr.iterrows():
        year = row['5year_start']
        val = row['volume']
        fig.add_trace(go.Scatter(
            x=[year, year + 5],
            y=[val, val],
            mode='lines',
            legendgroup='5 Year Average',
            showlegend=idx == 0,
            name='5 Year Average Simulation',
            marker=dict(color='red')
        ))

    # Annual volumes - corrected
    if df_yearly_corr is not None:
        fig.add_trace(go.Scatter(
            x=df_yearly_corr['year'],
            y=df_yearly_corr['volume'],
            mode='lines',
            name='Annual Volume Corrected',
            marker=dict(color='rgb(0, 166, 255)')
        ))

        # 5-year averages - corrected
        for idx, row in df_5yr_corr.iterrows():
            year = row['5year_start']
            val = row['volume']
            fig.add_trace(go.Scatter(
                x=[year, year + 5],
                y=[val, val],
                mode='lines',
                legendgroup='5 Year Average',
                showlegend=idx == 0,
                name='5 Year Average Corrected',
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


def plot_retro_annual_status(df_retro_daily, df_retro_monthly, river_id, bias_corrected=False):
    """
    Corrected: Very Wet = highest flows, Very Dry = lowest flows.
    Stacked polygons like JS plotStatuses.
    """
    # Keep the original label order
    status_labels = ["Very Wet", "Wet", "Normal", "Dry", "Very Dry"]
    status_percentiles = [0, 13, 28, 72, 87]  # original percentiles
    status_colors = [
        "rgb(44, 125, 205)",   # Very Wet
        "rgb(142, 206, 238)",  # Wet
        "rgb(231, 226, 188)",  # Normal
        "rgb(255, 168, 133)",  # Dry
        "rgb(205, 35, 63)"     # Very Dry
    ]

    months = [f"{i:02d}" for i in range(1, 13)]
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    # --- Compute monthly status values (descending sort) ---
    df_daily = df_retro_daily.copy()
    df_daily["month"] = df_daily.index.strftime("%m")

    monthly_status_values = {label: [] for label in status_labels}

    for month in months:
        tmp = df_daily[df_daily["month"] == month].sort_values(by=river_id, ascending=False)
        values = tmp[river_id].to_list()
        n = len(values)
        for idx, perc in enumerate(status_percentiles):
            index = int(n * perc / 100)
            monthly_status_values[status_labels[idx]].append(values[index])

    # --- Build stacked polygons (from bottom to top) ---
    traces = []
    # Start with Very Dry at bottom
    prev_values = [0]*12
    # Reverse the labels for stacking: Very Dry at bottom → Very Wet at top
    for label in reversed(status_labels):
        curr_values = monthly_status_values[label]
        traces.append(
            go.Scatter(
                x=month_names + month_names[::-1],
                y=curr_values + prev_values[::-1],
                mode="lines",
                fill="toself",
                name=label,
                line=dict(width=0),
                fillcolor=status_colors[status_labels.index(label)],
                visible="legendonly",
                legendgrouptitle=dict(text="Monthly Status Categories")
            )
        )
        prev_values = curr_values

    # --- Long-term monthly average line ---
    df_monthly = df_retro_monthly.copy()
    df_monthly["year"] = df_monthly.index.year
    df_monthly["month"] = df_monthly.index.month
    monthly_avg = df_monthly.groupby("month")[river_id].mean().reindex(range(1,13)).values

    traces.append(
        go.Scatter(
            x=month_names,
            y=monthly_avg,
            mode="lines",
            name="Long-term Monthly Average",
            line=dict(color="rgb(0,157,255)", width=3, dash="dash"),
            visible=True
        )
    )

    # --- Each year's monthly averages ---
    years = sorted(df_monthly["year"].unique())
    for idx, year in enumerate(reversed(years)):
        yearly = df_monthly[df_monthly["year"]==year].set_index("month").reindex(range(1,13))[river_id].values
        traces.append(
            go.Scatter(
                x=month_names,
                y=yearly,
                name=f"Year {year}",
                mode="lines",
                line=dict(width=2, color="black"),
                visible=True if idx==0 else "legendonly"
            )
        )

    # --- Layout ---
    layout = go.Layout(
        title=dict(text=f"Monthly Status for River: {river_id}", x=0.5),
        xaxis=dict(title="Month", tickvals=month_names, ticktext=month_names),
        yaxis=dict(title="Flow (m³/s)", range=[0,None]),
        hovermode="x",
        annotations=[dict(
            text="Experimental Bias-Corrected Plot",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=30, color="rgba(150,150,150,0.2)"),
            textangle=-30
        )] if bias_corrected else []
    )

    fig = go.Figure(data=traces, layout=layout)
    fig.update_layout(template="plotly_white")
    return fig



def plot_retro_fdc(df_simulated, river_id, df_corrected=None):
    """
    Returns a plotly figure object showing Flow Duration Curves (FDCs).
    
    If df_corrected is provided, compares simulated vs bias-corrected data.
    Otherwise, plots only the provided df_simulated data.

    Args:
        df_simulated (pd.DataFrame): simulated or retro daily data.
        river_id (str): the river column name to plot.
        df_corrected (pd.DataFrame, optional): bias-corrected data for comparison.
        
    Returns:
        go.Figure: plotly figure object with FDCs
    """
    percentiles = [i * 2 for i in range(51)]
    percentiles_reversed = percentiles[::-1]
    visible = 'legendonly' if (df_corrected is not None and not df_corrected.empty) else True

    
    def sorted_array_to_percentiles(array):
        return [array[len(array) * p // 100 - (1 if p == 100 else 0)] for p in percentiles_reversed]

    months = [f'{i}'.rjust(2, '0') for i in range(1, 13)]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def compute_fdc(df):
        df = df.copy()
        df['month'] = df.index.strftime('%m')
        fdc = sorted_array_to_percentiles(df.sort_values(by=river_id)[river_id].to_list())
        monthly_fdc = {}
        for month in months:
            tmp = df[df['month'] == month].sort_values(by=river_id, ascending=True)
            values = tmp[river_id].to_list()
            monthly_fdc[month] = sorted_array_to_percentiles(values)
        return fdc, monthly_fdc

    # Compute FDCs for simulated data
    fdc_sim, monthly_fdc_sim = compute_fdc(df_simulated)

    # Compute FDCs for corrected data if provided
    if df_corrected is not None and not df_corrected.empty:
        fdc_corr, monthly_fdc_corr = compute_fdc(df_corrected)

    fig = go.Figure()

    # Overall FDCs
    fig.add_trace(go.Scatter(
        x=percentiles,
        y=fdc_sim,
        mode='lines',
        name='Simulated - FDC',
        line=dict(color='blue'),
        visible=visible
    ))

    if df_corrected is not None and not df_corrected.empty:
        fig.add_trace(go.Scatter(
            x=percentiles,
            y=fdc_corr,
            mode='lines',
            name='Bias-Corrected - FDC',
            line=dict(color='red')
        ))

    # Monthly FDCs
    for i, month in enumerate(months):
        month_name = month_names[i]
        fig.add_trace(go.Scatter(
            x=percentiles,
            y=monthly_fdc_sim[month],
            mode='lines',
            name=f'Simulated - {month_name}',
            line=dict(color='blue', dash='dot'),
            visible=visible
        ))
        if df_corrected is not None and not df_corrected.empty:
            fig.add_trace(go.Scatter(
                x=percentiles,
                y=monthly_fdc_corr[month],
                mode='lines',
                name=f'Bias-Corrected - {month_name}',
                line=dict(color='red', dash='dot')
            ))

    fig.update_layout(
        title=f'Flow Duration Curves for River: {river_id}',
        xaxis=dict(title='Percentile (100%)'),
        yaxis=dict(title='Flow (m³/s)', range=[0, None]),
        legend=dict(orientation='h', x=0, y=1.05),
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


def plot_ssi_all_months(df_retro=None, df_corrected=None):
    """
    Plots SSI for all months across years.
    Default visible trace = yearly average SSI (one value per year).
    Month-specific traces are toggleable via legend (x-axis = year).
    """
    if df_retro is None:
        raise ValueError("df_retro must be provided")
    
    number_to_month = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    
    fig = go.Figure()
    
    # --- Get all monthly SSI data ---
    df_ssi_all = get_SSI_data(df_retro)
    df_ssi_all['year'] = df_ssi_all.index.year
    df_ssi_all['month'] = df_ssi_all.index.month
    
    # --- Compute yearly average SSI (default visible line) ---
    yearly_avg = df_ssi_all.groupby('year')['SSI'].mean()
    fig.add_trace(go.Scatter(
        x=yearly_avg.index,
        y=yearly_avg.values,
        mode='lines+markers',
        name='Yearly Average SSI',
        line=dict(color='black', width=3, dash='dash'),
        marker=dict(symbol='circle', size=6),
        visible=True
    ))
    
    # --- Add retro month-specific traces (one value per year per month) ---
    for month in range(1, 13):
        df_month = df_ssi_all[df_ssi_all['month'] == month]
        # Take monthly average per year
        month_per_year = df_month.groupby('year')['SSI'].mean()
        fig.add_trace(go.Scatter(
            x=month_per_year.index,
            y=month_per_year.values,
            mode='lines+markers',
            name=f'Original SSI - {number_to_month[month]}',
            marker=dict(symbol='circle', size=5),
            line=dict(color='blue'),
            visible='legendonly'
        ))
    
    # --- Add corrected month-specific traces if provided ---
    if df_corrected is not None:
        df_ssi_corr_all = get_SSI_data(df_corrected)
        df_ssi_corr_all['year'] = df_ssi_corr_all.index.year
        df_ssi_corr_all['month'] = df_ssi_corr_all.index.month
        for month in range(1, 13):
            df_month_corr = df_ssi_corr_all[df_ssi_corr_all['month'] == month]
            month_per_year_corr = df_month_corr.groupby('year')['SSI'].mean()
            fig.add_trace(go.Scatter(
                x=month_per_year_corr.index,
                y=month_per_year_corr.values,
                mode='lines+markers',
                name=f'Bias-Corrected SSI - {number_to_month[month]}',
                marker=dict(symbol='square', size=5),
                line=dict(color='red'),
                visible='legendonly'
            ))
    
    fig.update_layout(
        title="SSI Values Across Years",
        xaxis_title='Year',
        yaxis_title='SSI',
        legend=dict(
            x=1.02,
            y=1,
            traceorder='normal',
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)'
        ),
        hovermode='x unified'
    )
    
    return fig
