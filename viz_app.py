import streamlit as st
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

from plotting_functions import load_trips_df, get_stations_location, get_stations_popularity, plot_stations

if __name__ == '__main__':

    st.write('test')

    st.write(os.path.exists('01_london_bike_trips_enriched.csv.zip')
    trips_df = load_trips_df('01_london_bike_trips_enriched.csv.zip')


    #creating a slider for popularity

    hour = st.slider('Hour', 0, 24, value = 12, )

    st.write('Hour of Day:' ,hour)

    stations_loc = get_stations_location(trips_df)
    stations_pop = get_stations_popularity(trips_df)


    fig,ax = plt.subplots()
    ax = plot_stations(ax , stations_loc, 'test',  stations_pop, 'popularity', True, None)

    st.pyplot(fig)

    #


