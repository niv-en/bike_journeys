import streamlit as st
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

from plotting_functions import load_trips_df, get_stations_location, get_stations_popularity, plot_stations

if __name__ == '__main__':

    st.write('test')

    st.write(os.path.exists('01_london_bike_trips_enriched.csv.zip'))
    trips_df = load_trips_df('01_london_bike_trips_enriched.csv.zip')


    #culd maybe plot the dataframe here

    st.header('Popularity Of Each Station at diff Hours')
    hour = st.slider('Hour', 0, 23, value = 12, )

    st.write('Hour of Day:' ,hour)

    #filter trips by hour
    trips_df_hour = trips_df[trips_df['start_hour']==hour]
    stations_loc = get_stations_location(trips_df_hour)
    stations_pop = get_stations_popularity(trips_df_hour)


    fig,ax = plt.subplots()
    ax = plot_stations(ax , stations_loc, f'Station Popularity at {hour if hour > 10 else f"0{hour}"  }:00',  stations_pop, 'popularity', True, None)

    st.pyplot(fig)

    #


