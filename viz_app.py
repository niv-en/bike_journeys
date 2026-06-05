import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

from plotting_functions import load_trips_data

if __name__ == '__main__':

    st.write('test')


    journeys_df = load_trips_data()
    station_df = pd.read_csv('station_medata.csv')


    st.header('Popularity Of Each Station at diff Hours')
    hour = st.slider('Hour', 0, 23, value = 12, )

    #filter trips by hour
#    trips_df_hour = trips_df[trips_df['start_hour']==hour]
#    stations_loc = get_stations_location(trips_df_hour)
#    stations_pop = get_stations_popularity(trips_df_hour)
#
#
#    fig,ax = plt.subplots()
#    ax = plot_stations(ax , stations_loc, f'Station Popularity at {hour if hour > 10 else f"0{hour}"  }:00',  stations_pop, 'no. journeys', True, None)
#
#    st.pyplot(fig)

    #


