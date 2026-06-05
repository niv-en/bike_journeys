import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from plotting_functions import load_trips_data, preprocess_df, get_stations_location, plot_stations, get_stations_popularity, plot_journeys, get_stations_source_sink

from collections import Counter

if __name__ == '__main__':

    journeys_df = load_trips_data()
    stations_df = pd.read_csv('station_metadata.csv')

    journeys_df = preprocess_df(journeys_df, stations_df[['name', 'lat', 'long']])


    st.markdown('''
    
    # TfL Bike Journeys Visualisation App
    
    *App can take a long time to load :(
    
    Web app which displays visualisations about the Transport for London (TfL) cycle hire network by leveraging TfL open data. 
    All visualisations are based off of 2 weeks of data from the 1st to the 14th of April 2025. 
    
    TfL cycling open data is available from: https://cycling.data.tfl.gov.uk/ 
    
    ''')

    st.markdown('''
    
    ## Popularity of Each Station at Different Hours
    
    The visualisation below displays the popularity of each station given a particular hour of the day, station popularity
    is computed by counting the total number of journeys which have either started or ended at each station. 
    
    A slider is provided to configure the visualisation to a particular hour of day. 
    
    ''')

    hour = st.slider('Hour', 0, 23, value = 12, key = 'station_hour')

    stations_loc = get_stations_location(stations_df)


    journeys_df_hour = journeys_df[journeys_df['start_hour'] == hour]

    stations_pop = get_stations_popularity(journeys_df_hour)


    fig_pop,ax_pop = plt.subplots()
    ax_pop = plot_stations(ax_pop , stations_loc, f'Station Popularity at {hour if hour > 10 else f"0{hour}"  }:00',  stations_pop, 'no. journeys', True, None)

    st.pyplot(fig_pop)

    st.markdown('''
    Different stations have different levels of popularity throughout the day. At 08:00 cycle hire stations around Waterloo are particularly 
    popular, which is likely a result of commuters. However, at 12:00 cycle hire stations around Hyde Park are the most popular.   
    ''')

    st.markdown('''
    
    ## Popularity of Each Journey at Different Hours
    
    The visualisation below displays the top 10 most popular undirected journeys at different hours of the day.
    The popularity of an undirected journey is calculated through summing the number of journeys from A to B and B to A to get an aggregate figure for travelling between A and B. 

    A slider is provided to configure the visualisation to a particular hour of day. 
    ''')

    hour_journey = st.slider('Hour', 0, 23, value = 12, key = 'journey_hour' )

    journeys_df_hour = journeys_df[journeys_df['start_hour'] == hour_journey]
    journey_counts = Counter([tuple(sorted(x)) for x in journeys_df_hour[['Start station', 'End station']].values])
    journeys = [x[0] for x in journey_counts.most_common(10)]


    fig_journeys, ax_journeys = plt.subplots()
    ax_journeys = plot_journeys(
            ax_journeys,
            journeys=journeys,
            station_loc=stations_loc,
            title= f'Top 10 Most Popular Undirected Journeys at {hour_journey if hour_journey> 10 else f"0{hour_journey}"  }:00',
            journey_mapping=journey_counts,
            cmap_name="viridis_r",
            show_arrows=True)

    st.pyplot(fig_journeys)

    st.markdown('''
    Similarly to the popularity of each station, at 08:00 the majority of the top 10 journeys are between cycle hire stations near Waterloo and the City of London (Commuters). 
    At 12:00 all of the top 10 journeys are between cycle hire stations within Hyde Park, which indicates recreational cycling. 
    ''')

    st.markdown('''

    ## Stations Sink-Source Disparity at Different Hours

    The visualisation below displays the sink source disparity for each station at different hours of the day.
    
    The Sink Source disparity measures the difference between the number of journeys which end at a particular location
    and those which start at a particular location is defined as the following:
    
    ''')

    st.latex(
        r"\text{sink-source disparity} = \frac{\text{sink count} - \text{source count}}{\text{sink count} + \text{source count}}")


    st.markdown('''
    
    It is bounded between (1,-1), values close to 1 indicate that more journeys end at a particular location than start,
    and vice versa for values close to -1
    
    A slider is provided to configure the visualisation to a particular hour of day. 
    ''')

    fig_sink , ax_sink = plt.subplots()

    hour_sink= st.slider('Hour', 0, 23, value = 12, key = 'hour_sink' )

    journeys_df_hour = journeys_df[journeys_df['start_hour'] == hour_sink]

    stations_delta = get_stations_source_sink(journeys_df_hour)

    ax_sink = plot_stations(ax_sink , stations_loc, f'Station Sink-Source Disparity at {hour_sink if hour_sink > 10 else f"0{hour_sink}"  }:00',  stations_delta, 'no. journeys', True, None, size_scaling= False, alpha_scaling=False)

    st.pyplot(fig_sink)

    st.markdown('''
    
    Stations around the outskirts tend to have a negative Sink-Source disparity in the mornings (~07:00),
    as more people are likely to start their journey into the centre of the city. However, during the night(~21:00) stations around
    the outskirts tend to have a positive Sink-Source disparity, as people arrive back from the city centre after their day. 
    ''')


    st.markdown('''
    ### Thanks for Reading! 
    ''')

