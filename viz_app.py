import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

from plotting_functions import load_trips_data, preprocess_df, get_stations_location, plot_stations, get_stations_popularity, plot_journeys

from collections import Counter

if __name__ == '__main__':

    st.write('test')


    journeys_df = load_trips_data()
    stations_df = pd.read_csv('station_metadata.csv')

    journeys_df = preprocess_df(journeys_df, stations_df[['name', 'lat', 'long']])


    st.header('Popularity Of Each Station at diff Hours')
    hour = st.slider('Hour', 0, 23, value = 12, )

    stations_loc = get_stations_location(stations_df)


    journeys_df_hour = journeys_df[journeys_df['start_hour'] == hour]

    stations_pop = get_stations_popularity(journeys_df_hour)


    fig_pop,ax_pop = plt.subplots()

    ax_pop = plot_stations(ax_pop , stations_loc, f'Station Popularity at {hour if hour > 10 else f"0{hour}"  }:00',  stations_pop, 'no. journeys', True, None)

    st.pyplot(fig_pop)

    journey_counts = Counter([tuple(sorted(x)) for x in journeys_df_hour[['Start station', 'End station']].values])
    journeys = [x[0] for x in journey_counts.most_common(10)]


    fig_journeys, ax_journeys = plt.subplots()

    ax_journeys = plot_journeys(
            ax_journeys,
            journeys=journeys,
            station_loc=stations_loc,
            title="Top 10 Rush Hour Journeys",
            journey_mapping=journey_counts,
            cmap_name="viridis_r",
            show_arrows=True)

    st.pyplot(fig_journeys)

