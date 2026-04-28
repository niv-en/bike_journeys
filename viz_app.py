import streamlit as st
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


from plotting_functions import load_trips_df, get_stations_location, get_stations_popularity, plot_stations

if __name__ == '__main__':

    st.write('test')

    #dataset
    trips_df = load_trips_df('01_london_bike_trips_enriched.csv.zip')

    stations_loc = get_stations_location(trips_df)
    stations_pop = get_stations_popularity(trips_df)

    fig,ax = plt.subplots()

    ax = plot_stations(ax , stations_loc, 'test',  stations_pop, 'popularity', True, None)

    st.pyplot(fig)


