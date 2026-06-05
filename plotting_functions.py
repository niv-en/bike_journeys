import matplotlib.pyplot as plt
import geopandas as gpd
from cartopy import crs as ccrs

from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points

from pyproj import Transformer

import contextily as ctx
import matplotlib.pyplot as plt
import geopandas as gpd
from cartopy import crs as ccrs
from geodatasets import get_path
import requests
from io import StringIO
import pandas as pd
import numpy as np
import matplotlib as mpl
import numbers
from collections import Counter
from matplotlib.patches import FancyArrowPatch, Circle


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

    stations, counts = np.unique(trips_df[['Start station', 'End station']].values.ravel(), return_counts=True)
    return  dict(zip(stations, counts))

def get_stations_location(stations_df : pd.DataFrame) -> dict:

    stations_df['location'] = stations_df.apply(lambda x: (x.long, x.lat), axis=1)
    stations_loc = dict(stations_df[['name', 'location']].values)

    return stations_loc

def get_stations_source_sink(journeys_df : pd.DataFrame) -> dict:

    source_counts = journeys_df['Start station'].value_counts().reset_index()
    sink_counts = journeys_df['End station'].value_counts().reset_index()

    source_sink_df = source_counts.merge(sink_counts, left_on='Start station', right_on='End station',
                                         suffixes=['_source', '_sink'])

    source_sink_df['delta'] = source_sink_df['count_sink'] - source_sink_df['count_source']
    source_sink_df['popularity'] = source_sink_df['count_sink'] + source_sink_df['count_source']
    source_sink_df['normalised_delta'] = source_sink_df['delta'] / source_sink_df['popularity']

    return dict(source_sink_df[['Start station', 'normalised_delta']].values)

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


def plot_journeys(
        ax,
        journeys: list[tuple],
        station_loc: dict,
        title: str,
        journey_mapping: dict | None = None,
        background: bool = True,
        cmap_name: str = "plasma",
        show_arrows: bool = True,
        location_labels: dict = None) -> None:

    if journey_mapping is None:
        journey_mapping = Counter(journeys)

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


    unique_journeys = list(dict.fromkeys(journeys))
    values = np.array([journey_mapping.get(j, 0) for j in unique_journeys], dtype=float)

    if len(values) == 0:
        raise ValueError("No journeys to plot.")

    vmin = np.percentile(values, 5)
    vmax = np.percentile(values, 95)
    if vmin == vmax:
        vmin, vmax = values.min(), values.max() + 1

    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.get_cmap(cmap_name)

    max_value = values.max()

    top_journeys = journeys
    station_points = {}

    def projected(station):
        # function to project coordinates to the correct system.
        if station not in station_points:
            station_points[station] = transformer.transform(*station_loc[station])
        return station_points[station]

    x_min, x_max, y_min, y_max = +1e10, -1e10, +1e10, -1e10

    for journey in unique_journeys:
        start, end = journey
        value = journey_mapping.get(journey, 0)

        x1, y1 = projected(start)
        x2, y2 = projected(end)

        # updating the x,y map limits if necessary
        temp_x_min, temp_x_max = sorted([x1, x2])
        temp_y_min, temp_y_max = sorted([y1, y2])

        x_min = temp_x_min if temp_x_min < x_min else x_min
        x_max = temp_x_max if temp_x_max > x_max else x_max

        y_min = temp_y_min if temp_y_min < y_min else y_min
        y_max = temp_y_max if temp_y_max > y_max else y_max

        colour = cmap(norm(value))

        # Popularity controls thickness

        popularity = value / max_value if max_value else 0
        linewidth = 2 + 2 * popularity
        alpha = 1

        is_top = journey in top_journeys
        zorder = 4 if is_top else 2

        if start != end:
            # if not a loop plot an arrow from A to B
            rad = 0.18 if hash(journey) % 2 == 0 else -0.18

            arrow = FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                connectionstyle=f"arc3,rad={rad}",
                arrowstyle="<|-|>" if show_arrows else "-",
                mutation_scale=8 + 10 * popularity,
                linewidth=linewidth,
                color=colour,
                alpha=alpha,
                linestyle="-",
                zorder=zorder,
            )
            ax.add_patch(arrow)

        else:
            # if it is a loop then plot a circle from A to A
            radius = 250 + 200 * popularity
            circle = Circle(
                (x1 - radius, y1),
                radius,
                fill=False,
                edgecolor=colour,
                linewidth=linewidth,
                alpha=alpha,
                zorder=zorder,
            )
            ax.add_patch(circle)

    xs, ys = zip(*[projected(station) for station in station_loc])
    ax.scatter(
        xs,
        ys,
        s=10,
        c="black",
        alpha=0.2,
        linewidths=0,
        zorder=5,
    )

    if background:
        ctx.add_basemap(
            ax,
            source=ctx.providers.CartoDB.PositronNoLabels,
            alpha=0.95,
        )

    if location_labels:
        for location, (lon, lat) in location_labels.items():
            x, y = transformer.transform(lon, lat)
            ax.text(x, y, s=location, fontsize=16, weight="bold")

    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    fig = ax.get_figure()
    cbar = fig.colorbar(sm, ax=ax, shrink=0.75, pad=0.01)
    cbar.set_label("Journey popularity", fontsize=10)

    ax.set_title(title, fontsize=16, weight="bold", pad=12)
    ax.set_axis_off()

    # adjusting the x,y lims to only show the section of the map relevant to the journeys.
    x_range = x_max - x_min
    y_range = y_max - y_min

    x_pad = 0.1 * x_range
    y_pad = 0.1 * y_range

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    plt.tight_layout()
    return ax