### YST Functions ###

# imports 
import os
import datetime as dt
import scipy.io
import numpy as np  
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
import shapely.geometry
from shapely.geometry import Point, Polygon
import geopandas as gpd


# reading data from OPS and DustTrak
def read_ops(csv_file_path):
    """ Reads the OPS data from a CSV file and returns a DataFrame with metadata.
    Returns (Tuple):
        metadata_dict (dict): Dictionary containing metadata from the OPS file.
        df (pd.DataFrame): DataFrame containing the OPS data.
    """
    # read the csv file
    with open(csv_file_path, 'r') as f:
        content = f.readlines()

    metadata = content[0:37]  # first 37 lines are metadata
    # convert metadata to a dictionary
    metadata_dict = {}
    bin_cut_points = {}
    for line in metadata:
        key, value = line.strip().split(',', 1)
        match = re.match(r'Bin (\d+) Cut Point \(um\)', key)
        if match:
            bin_number = int(match.group(1))
            bin_cut_points[bin_number] = float(value)
        else:
            metadata_dict[key.strip()] = value.strip()
    metadata_dict['Bin Cut Points'] = bin_cut_points

    df = pd.read_csv(csv_file_path, skiprows=37) 
    # convert columns to appropriate data types
    start_datetime = dt.datetime.strptime(
            f"{metadata_dict['Test Start Date']} {metadata_dict['Test Start Time']}"
            , "%Y/%m/%d %H:%M:%S"
        )
    print(f"Start datetime: {start_datetime}")
    df['datetime'] = start_datetime + pd.to_timedelta(df['Elapsed Time [s]'], unit='s')

    return [metadata_dict, df]



def read_dusttrak(csv_file_path):
    """ Reads the DustTrak data from a CSV file and returns a DataFrame with metadata.
    Returns (Tuple):
        metadata_dict (dict): Dictionary containing metadata from the DustTrak file.
        df (pd.DataFrame): DataFrame containing the DustTrak data.
    """
    # read the csv file
    with open(csv_file_path, 'r') as f:
        content = f.readlines()

    metadata = content[0:19]  # first 6 lines are metadata
    # convert metadata to a dictionary
    metadata_dict = {}
    for line in metadata:
        try:
            key, value = line.split(',')
            print(key, value)
            metadata_dict[key.strip()] = value.strip()
        except ValueError:
            pass

    df = pd.read_csv(csv_file_path, skiprows=19) 
    # convert columns to appropriate data types
    start_datetime = dt.datetime.strptime(
            f"{metadata_dict['Test Start Date']} {metadata_dict['Test Start Time']}"
            , "%m/%d/%Y %I:%M:%S %p"
        )
    print(f"Start datetime: {start_datetime}")
    df['datetime'] = start_datetime + pd.to_timedelta(df['Elapsed Time [s]'], unit='s')
    
    # reoder columns to have datetime first
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]

    return [metadata_dict, df]

def load_wind_data(mat_file_path: str, site_name: str, avg: str = "1min", round_time: bool = True) -> pd.DataFrame:
    """
    Load wind data from a .mat file into a pandas DataFrame.

    Parameters
    ----------
    mat_file_path : str
        Path to the .mat file.
    site_name : str
        Name of the site (e.g., "Site1", "Site2", "Site3").
    avg : str
        Averaging interval (e.g., "1min", "10min", "30min").
    round_time : bool
        If True, round time up to the nearest full minute.

    Returns
    -------
    pd.DataFrame
        DataFrame with time, direction, speed, and flag_angle.
    """
    mat_data = scipy.io.loadmat(mat_file_path)
    key = f"{site_name}_{avg}"

    if key not in mat_data:
        raise ValueError(f"Key {key} not found in {mat_file_path}. Available keys: {mat_data.keys()}")

    site_data = mat_data[key][0, 0]

    time = site_data['time'].flatten()
    direction = site_data['direction'].flatten()
    speed = site_data['speed'].flatten()
    flag_angle = site_data['flag_angle'].flatten()

    # Convert MATLAB datenum to Python datetime
    datetimes = [dt.datetime.fromordinal(int(t)) +
                 dt.timedelta(days=t % 1) -
                 dt.timedelta(days=366)
                 for t in time]

    dt_series = pd.to_datetime(datetimes)

    if round_time:
        dt_series = dt_series.ceil("min")  # round UP to nearest minute

    df = pd.DataFrame({
        'time': dt_series,
        'direction': direction,
        'speed': speed,
        'flag_angle': flag_angle
    })

    return df



if __name__ == '__main__':
    # Establish the project directory
    try:
        proj_dir = os.path.dirname(os.path.abspath(__file__))  # get the project directory
    except NameError:
        proj_dir = os.getcwd()  # fallback if __file__ is not defined