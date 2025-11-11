import os
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import scipy.stats as stats
import geoglows
import getpass
import pwd  
import math

username = os.environ.get("NGINX_USER", getpass.getuser())
uid = pwd.getpwnam(username).pw_uid
gid = pwd.getpwnam(username).pw_gid

module_path = os.path.dirname(__file__)
PLOTS_CACHE_PATH = os.path.join(module_path, "geoglows_plots_cache")
if not os.path.exists(PLOTS_CACHE_PATH):
    os.makedirs(PLOTS_CACHE_PATH)
    os.chown(PLOTS_CACHE_PATH, uid, gid)

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


def get_bias_corrected_plot_data(river_id, plot_name='forecast'):
    """Get newest data for the selected plot.

    Args:
        river_id (int or str): river id
        plot_type (str, optional): The plot type. Options are forecast,
            historical, and return. Defaults to 'forecast'.  # TODO update doc

    Returns:
        df: the dataframe of the newest plot data
    """
   
    match plot_name:
        case "forecast":
            sim = geoglows.data.forecast(river_id)
            df = geoglows.bias.discharge_transform(sim, river_id)
        case "forecast-stats":
            sim = geoglows.data.forecast_stats(river_id)
            df = geoglows.bias.discharge_transform(sim, river_id)
        case "forecast-ensembles":
            sim = geoglows.data.forecast_ensembles(river_id)
            df = geoglows.bias.discharge_transform(sim, river_id)
        case 'retro-simulation':
            sim = geoglows.data.retrospective(river_id)
            df = geoglows.bias.discharge_transform(sim, river_id)
        case 'return-periods':
            #TODO Fix this to use bias corrected data
            sim_data = geoglows.data.retro_daily(river_id)
            df = geoglows.bias.discharge_transform(sim_data = sim_data, river_id=river_id)
            rps = [2, 5, 10, 25, 50, 100]
            results = []
            df = df.rename(columns={str(river_id): 'return_periods'})
            for column in ["return_periods"]:
                annual_max_flow_list = df.groupby(df.index.strftime('%Y'))[column].max().values.flatten()
                xbar = np.mean(annual_max_flow_list)
                std = np.std(annual_max_flow_list)

                # Compute return periods
                ret_pers = {'Data Type': column, 'max_simulated': round(np.max(annual_max_flow_list), 2)}
                ret_pers.update({f'{rp}': round(gumbel1(rp, xbar, std), 2) for rp in rps})
                
                results.append(ret_pers)
            df = (pd.DataFrame(results).set_index("Data Type")).transpose()
            df.columns = df.columns.astype(str)
            df = df.astype(float).round(2)
        case 'retro-daily':
            sim = geoglows.data.retro_daily(river_id)
            df = geoglows.bias.discharge_transform(sim, river_id)
        case 'retro-monthly':
            sim_data = geoglows.data.retro_daily(river_id, skip_log=True)
            df = geoglows.bias.discharge_transform(sim_data, river_id).resample("MS").mean()
        case 'retro-yearly':
            sim_data = geoglows.data.retro_daily(river_id, skip_log=True)
            df = geoglows.bias.discharge_transform(sim_data, river_id).resample("YS").mean()
        case _:
            raise ValueError("plot_name is unacceptable")

    return df
