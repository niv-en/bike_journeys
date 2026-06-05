import matplotlib.pyplot as plt
import geopandas as gpd
from cartopy import crs as ccrs

import pandas as pd
from shapely.geometry import Point, Polygon
import numpy as np

import matplotlib as mpl
import seaborn as sns

from pyproj import Transformer

import os
import re

import contextily as ctx
import numbers

from zipfile import ZipFile
import pandas as pd

import requests
from io import StringIO

#def load_trips_df(path):
#    with ZipFile(path) as zf:
#        csv_files = [
#            name for name in zf.namelist()
#            if name.endswith(".csv") and not name.startswith("__MACOSX")
#        ]
#
#        if not csv_files:
#            raise ValueError(f"No CSV found in ZIP: {zf.namelist()}")
#
#        # just take the first valid CSV
#        with zf.open(csv_files[0]) as f:
#            return pd.read_csv(f)

def load_trips_data():

    dataset_urls =  ['417JourneyDataExtract01Apr2025-14Apr2025.csv',]
    journeys_df = pd.DataFrame()

    headers = {
        "User-Agent": "Mozilla/5.0"
    }


    for url in dataset_urls:
        url = f'https://cycling.data.tfl.gov.uk/usage-stats/{url}'
        response = requests.get(url, headers=headers)
        temp_df = pd.read_csv(StringIO(response.text))
        journeys_df = pd.concat((journeys_df, temp_df))

    return journeys_df


def preprocess_df(df, stations_df):
    df = df.copy()

    df['start_date'] = pd.to_datetime(df['Start date'], format='mixed')
    df['end_date'] = pd.to_datetime(df['End date'], format='mixed')
    df['start_hour'] = df['start_date'].dt.hour
    df['end_hour'] = df['end_date'].dt.hour

    df.drop(columns=['Start date', 'End date'], inplace=True)
    # dividing by 60_000 to get to minutes
    df['duration_mins'] = df['Total duration (ms)'] / 60_000

    df = df[df['duration_mins'] > 3]
    df = df[df['duration_mins'] < 180]

    rush_hours = {7, 8, 17, 18}
    weekdays = {1, 2, 3, 4, 5}

    start_weekday, end_weekday = df.start_date.dt.weekday, df.end_date.dt.weekday

    df['rush_hour'] = ((df.start_hour.isin(rush_hours) & start_weekday.isin(weekdays)) |
                       (df.end_hour.isin(rush_hours) & end_weekday.isin(weekdays)))

    df = df.merge(stations_df, left_on='Start station', right_on='name')

    return df


def get_stations_popularity(trips_df : pd.DataFrame) -> dict:

    stations, counts = np.unique(trips_df[['start_station', 'end_station']].values.ravel(), return_counts=True)
    return  dict(zip(stations, counts))

def get_stations_location(stations_df : pd.DataFrame) -> dict:

    stations_df['location'] = stations_df.apply(lambda x: (x.long, x.lat), axis=1)
    stations_loc = dict(stations_df[['name', 'location']].values)

    return stations_loc

def plot_stations(ax,
                  stations_loc: dict,
                  title: str,
                  stations_mapping: dict = {},
                  mapping_label: str | None = None,
                  background: bool = None,
                  xy_limits: tuple = None,
                  location_labels: dict = None,
                  size_scaling: bool = True,
                  alpha_scaling: bool = True) -> None:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

    counts = False

    x_points = []
    y_points = []
    mapping_values = []

    for station, loc in stations_loc.items():
        x, y = transformer.transform(loc[0], loc[1])
        x_points.append(x)
        y_points.append(y)

        mapping_values.append(stations_mapping.get(station, None))

    points_df = pd.DataFrame.from_dict({'x': x_points,
                                        'y': y_points,
                                        'vals': mapping_values})

    match points_df.loc[0, 'vals']:

        case numbers.Number():

            points_df['vals'].fillna(0)
            x_points, y_points = points_df['x'], points_df['y']
            mapping_values = points_df['vals']

            for x, y, val in zip(x_points, y_points, mapping_values):
                alpha = min((val - min(mapping_values)) / (max(mapping_values) - min(mapping_values)), 1)
                alpha = alpha if alpha == alpha else 0

                sp = ax.scatter(x,
                                y,
                                s=3 + 15 * alpha if size_scaling else 5,
                                c=val,
                                cmap='viridis_r',
                                vmin=min(mapping_values),
                                vmax=max(mapping_values),
                                alpha=0.5 + (alpha * 0.5) if alpha_scaling else 1)

            fig = ax.get_figure()
            sp = ax.scatter(x,
                            y,
                            s=0,
                            c=val,
                            cmap='viridis_r',
                            vmin=min(mapping_values),
                            vmax=max(mapping_values),
                            alpha=1)

            fig.colorbar(sp, ax=ax, label=mapping_label, location='bottom')

        case str():

            print('categorical plot')

            points_df['vals'].fillna('NA')
            groups = points_df['vals'].unique()
            for group in groups:
                temp_df = points_df[points_df['vals'] == group]
                x_points, y_points = temp_df['x'], temp_df['y']
                sp = ax.scatter(x_points, y_points,
                                s=2,
                                label=group,
                                alpha=1)

        case _:

            x_points, y_points = points_df['x'], points_df['y']
            sp = ax.scatter(x_points, y_points, s=3, alpha=0, c='lightblue')

    if xy_limits:
        ax.set_xlim(xy_limits[0])
        ax.set_ylim(xy_limits[1])

    if background:
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

    if location_labels:
        for location, (lon, lat) in location_labels.items():
            x, y = transformer.transform(lon, lat)
            ax.text(x, y, s=location, fontsize=12, weight="bold")

    ax.set_title(title, size=16)
    ax.axis('off');

    return ax