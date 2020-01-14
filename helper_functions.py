import requests
import time
from bs4 import BeautifulSoup as BS
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def get_page(url,headers):
    """
    Returns: List of 50 IMDB html tags representing each one movie block from the specified url.
    Param url: [str] IMDB url to search on.
    Param headers: [str] headers to pass into requests.get so that IMDB knows we are not russian hackers.
    """
    try:
        page = requests.get(url,headers=headers, timeout = 5)
        if page.status_code != 200:
            print(page.status_code)
            
    except requests.ConnectionError as e:
        print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
        print(str(e))
    except requests.Timeout as e:
        print("OOPS!! Timeout Error")
        print(str(e))
    except requests.RequestException as e:
        print("OOPS!! General Error")
        print(str(e))
    except KeyboardInterrupt:
        print("Someone closed the program") 
    
    soup = BS(page.content, 'html.parser')
    
    return  soup

def get_station_weather(station,start_date,end_date):
    """
    Returns: A parsed json of the weather data for the given station from 1960 - 2018.
    
    Param station: [str] A station code from the list of stations
    Param start_date: [str] Start date of the query. In the form 'YYYY-MM-DD'
    Param end_date: [str] End date of the query. In the form 'YYYY-MM-DD'
    """

    base_url = 'https://www.ncei.noaa.gov/access/services/data/v1'

    params = {'dataset': 'daily-summaries',   # the dataset to query for data
              'stations': station,            # comma separated list of station identifiers for selection and subsetting
              'startDate': start_date,        # YYYY-MM-DD
              'endDate' : end_date,           # YYYY-MM-DD
              'format' : 'json',              # json is ideal formal    
              'includeStationName' : 'True',  # Just to be sure we're looking at the right city/state
              'units' : 'standard',           # degrees fahrenheit
             }        

    return requests.get(base_url, params = params).json()

def get_energy_pop_df(state_data,sector):
    """
    Return a dataframe with datetime index and columns for each temperature designation
    
    Param weather_data: [dict] Dict taken directly from mongo containing weather data
        """
    # Generate a dates column and load this into a df
    dates = np.arange(2017,1959,-1)

    # Convert this to a string for easier date time manipulation
    dates = [str(date) for date in dates]

    # Create df
    df = pd.DataFrame(data = dates, columns=['Date'])

    # Convert type and make it the index
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # Loop through each ny series
    for series in state_data:

        # Make sure we are only grabbing the desired sector
        if series.get('sector') == sector:

            data = series['data']

            # Some series only go to 2017 so we'll cut off any ones that go to 2018
            if len(data) == 59:
                data = data[1:]

            # Store just the energy values
            ts_values = [tuple_[1] for tuple_ in data]
            
            # Add to df
            df = pd.concat([df, pd.Series(data = ts_values,
                                          name=(series['energy_type']), 
                                          index=df.index
                                         )],
                                          axis=1)
        # Also grab population data
        if series.get('description') == 'Population':

            data = series['data']

            # Some series only go to 2017 so we'll cut off any ones that go to 2018
            if len(data) == 59:
                data = data[1:]
            
            # Store just the population values
            ts_values = [tuple_[1] for tuple_ in data]
            
            # Add to df
            df = pd.concat([df, pd.Series(data = ts_values,
                                          name=series.get('description'), 
                                          index=df.index)],
                           axis=1)
            
    create_energy_columns(df)

    return df

def create_energy_columns(df):
    """
    Returns a df with two new columns that aggregate other columns in the df: renewable_sources and nonrenewable_sources
    
    Param df: [dataframe] dataframe to do this for
    """
    
    # Define possible types of renewable and nonrenewable sources
    renewable_sources = [
    'Biomass',
    'Fuel Ethanol excluding Denaturant',
    'Geothermal',
    'Hydroelectricity',
    'Solar Energy',
    'Wind Energy'
    ]

    nonrenewable_sources = [
        'All Petroleum Products',
        'Coal',
        'Natural Gas including Supplemental Gaseous Fuels',
        'Nuclear Power'
    ]
    
    # Determine which ones of the possible columns are in our df (some sectors don't have all types reported)
    renewable_in_df = [column for column in df.columns if column in renewable_sources]

    nonrenewable_in_df = [column for column in df.columns if column in nonrenewable_sources]
    
    # Create columns
    df['Renewable Sources'] = df[renewable_in_df].sum(axis=1)
    df['Nonrenewable Sources'] = df[nonrenewable_in_df].sum(axis=1)
    
    return df

def get_weather_df(weather_data):
    """
    Return a dataframe with datetime index and columns for each temperature designation
    
    Param weather_data: [dict] Dict taken directly from mongo containing weather data
    """
    
    # Create container for massaging data into a 2-D matrix
    matrix = []
    data = weather_data['data']
    
                           
    # Array for dates, which will be the index
    dates = np.arange(1960,2018,1)
    
    # Convert to a list of strings for easy manipulation
    dates = [str(date) for date in dates]
    
    # Add to a dataframe and convert to datetime (yyyy-mm-dd)
    df = pd.DataFrame(data = dates, columns=['Date'])
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Set index
    df.set_index('Date', inplace=True)
    
    for year in data:
        
        # Combine both lists into a single row and append to the matrix
        row = data[year][0] + data[year][1]
        matrix.append(row)
                           
    # Limit to only 2017 because some missing 2018 energy data
    matrix = matrix[:-1]
    
    # Prepare column titles
    above_temps = np.arange(100, 65, -5)
    above_temps = ['days_above_'+str(temp) for temp in above_temps]

    below_temps = np.arange(70, 0, -5)
    below_temps = ['days_below_'+str(temp) for temp in below_temps]

    temp_column_titles = above_temps + below_temps
    
    df = pd.DataFrame(matrix, columns = temp_column_titles, index = df.index)
        
    return df

def plot_descriptive_fig(df, columns, state, sector):
    """
    Generates interactive plotly line plot for the given dataframe and columns. 
    
    First need to melt the df and then create the plotly figure.
    
    Param df: dataframe we want to use. Index must be dates.
    Param columns: [list] Columns we want to include in the graph.
    Param title: [str] title for graph
    """
    df_melt = df[columns].reset_index().melt(id_vars='Date',
                                value_vars=columns,
                                var_name = 'Energy Source', 
                                value_name = 'Energy Consumed (Billion Btu)')
    df_melt.columns = ['Year', 'Energy Source', 'Energy Consumed (Billion Btu)']
    
    fig = px.line(df_melt, 
              x = 'Year', 
              y = 'Energy Consumed (Billion Btu)', 
              color = 'Energy Source',
              title = f'{state} Energy Consumption - {sector}',
              height = 600,
              width = 1100)

    fig.show()
    
    
   
