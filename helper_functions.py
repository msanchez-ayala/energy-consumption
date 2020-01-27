import requests
import time
from bs4 import BeautifulSoup as BS
import csv
import pymongo
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans


"""
CONNECT TO MONGODB
------------------

    This allows data to be loaded into the dash app and in the final ipython notebook.

"""

client = pymongo.MongoClient('mongodb://localhost/')
db = client.admin

# Issue the serverStatus command and print the results
serverStatusResult=db.command("serverStatus")

mydb = client['energy_data']

energy_collection = mydb['energy_data']

# Get dict with state abbreviations and full names
state_abbrevs = open('state-abbreviations.csv')
state_abbrevs_reader = csv.reader(state_abbrevs)
state_abbrevs_dict = dict(state_abbrevs_reader)

"""
ENERGY TYPES
------------

    For the dash app and some functions below.
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

def get_page(url,headers):
    """
    Returns
    -------

         A list of 50 IMDB html tags representing each one movie block from the specified url.

    Parameters
    -----------

        url: [str] url to search on.

        headers: [str] headers to pass into requests.get so that the website knows we are not russian hackers.
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
    Returns
    -------

        A parsed json of the weather data for the given station from 1960 - 2018.


    Parameters
    -----------

        station: [str] A station code from the list of stations

        start_date: [str] Start date of the query. In the form 'YYYY-MM-DD'

        end_date: [str] End date of the query. In the form 'YYYY-MM-DD'
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
    Returns
    -------

        A dataframe with datetime index and columns for each temperature designation

    Parameters
    -----------

        weather_data: [dict] Dict taken directly from mongo containing weather data
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
    Returns
    --------

        A df with two new columns that aggregate other columns in the df: renewable_sources and nonrenewable_sources

    Parameters
    -----------

        df: [pd.DataFrame] dataframe to peform this action on
    """

    # Determine which ones of the possible columns are in our df (some sectors don't have all types reported)
    renewable_in_df = [column for column in df.columns if column in renewable_sources]

    nonrenewable_in_df = [column for column in df.columns if column in nonrenewable_sources]

    # Create columns
    df['Renewable Sources'] = df[renewable_in_df].sum(axis=1)
    df['Nonrenewable Sources'] = df[nonrenewable_in_df].sum(axis=1)

    return df

def get_weather_df(state_data):
    """
    Returns
    --------

        A dataframe with datetime index and columns for each temperature designation

    Parameters
    ----------

        weather_data: [dict] Full state-level data
    """
    for series in state_data:
        if series.get('description') == 'Temperature':
            data = series['data']

    # Array for dates, which will be the index
    dates = np.arange(1960,2018,1)

    # Convert to a list of strings for easy manipulation
    dates = [str(date) for date in dates]

    # Add to a dataframe and convert to datetime (yyyy-mm-dd)
    df = pd.DataFrame(data = dates, columns=['Date'])
    df['Date'] = pd.to_datetime(df['Date'])

    # Set index
    df.set_index('Date', inplace=True)

    # Add each row of data to a matrix


    matrix = [data[year][0] for year in data]


    # Limit to only 2017 because some missing 2018 energy data
    matrix = matrix[:-1]

    # Prepare column titles
    above_temps = np.arange(100, 65, -5)
    above_temps = ['days_above_'+str(temp) for temp in above_temps]

    below_temps = np.arange(70, 0, -5)
    below_temps = ['days_below_'+str(temp) for temp in below_temps]

    descriptive_stats = ['Max Temp', 'Min Temp', 'Mean Temp', 'Std Temp']

    temp_column_titles = above_temps + below_temps + descriptive_stats

    df = pd.DataFrame(matrix, columns = temp_column_titles, index = df.index)

    return df

def plot_descriptive_fig(df, columns, state, sector):
    """
    Returns
    --------

        Interactive plotly line plot for the given dataframe and columns.

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

def get_states_data():
    """
    Returns
    -------

        A dictionary containing every state's data organized in the following format:

        {state_name: {'Total All Sectors' : dataframe,
                      'Industrial Sector' : dataframe,
                      ...
                     },
         ...
        }

        Typically, we want to access data from a single sector across all states,
        so this is a convenient format to store everything

    """


    # Store each state's data from mongodb into a list
    states_data = []
    for state in state_abbrevs_dict:
        data = [x for x in energy_collection.find({'state':state_abbrevs_dict[state]})]
        states_data.append({'state':state_abbrevs_dict[state], 'data':data})

    # Create list of unique sector names
    sectors = [series.get('sector') for series in states_data[0]['data'] if series.get('sector')]
    sectors = list(set(sectors))

    # Create a dict to store all state dataframes in
    state_dfs = {}
    for state in states_data:
        dfs = {sector: get_energy_pop_df(state['data'],sector) for sector in sectors}
        state_dfs[state['state']] = dfs

    return state_dfs

def get_sustainability_indicators():
    """
    Returns
    -------

        A dict with the green score and effort score of every state.
    """
    state_dfs = get_states_data()

    # Create empty container to store the final processed data (sustainability indicators)
    sus_indicators = {}

    # Iterate through each state
    for state in state_dfs:

        # Store series of REC and NEC
        rec = state_dfs[state]['Total All Sectors']['Renewable Sources']
        nec = state_dfs[state]['Total All Sectors']['Nonrenewable Sources']

        # Divide by 10^5 to have a more interpretable scale
        rec = rec / 100000
        nec = nec / 100000

        """
        EFFORT SCORE:
        -------------
        """

        # Calculate the differences from the year 2000 onward
        diff = (nec - rec)[:'2000-01-01'].sort_index(ascending=True)

        # Create empty bin to store integral values
        integrals = []

        # Iterate through list of differences
        for i in range(len(diff)):

            # Only go up to the second to last date so that we dont have an index problem
            if i<len(diff)-1:

                # Store integral
                integrals.append(np.trapz(diff[i:i+2]))

        # Convert the list to a pd.Series
        integrals = pd.Series(integrals,index=diff.index[1:])

        # Set up and execute regression, saving the slope of the line
        X = np.array(integrals.index.year).reshape(-1, 1)
        y = integrals.values
        reg = LinearRegression().fit(X, y)

        effort_score = round((-1 * reg.coef_[0]),3)

        """
        GREEN SCORE:
        ------------
        """

        # Take ratio of rec/nec from 2000 onward
        ratios = (rec/nec)[:'2000-01-01'].sort_index(ascending=True)

        # Store average as green_score
        green_score = round(ratios.mean(),3)


        """
        COMBINE
        -------
        """

        sus_indicators[state] = {'effort_score':effort_score,'green_score':green_score}

    return sus_indicators

def get_sustainability_df():

    """
    Returns
    -------

        A df with green score, effort score, and sustainability indexes for each state.

    """

    sus_indicators = get_sustainability_indicators()

    # Put this data into a form that can easily be inserted into a df
    data = {'Effort Score' : [sus_indicators[state]['effort_score'] for state in sus_indicators],
            'Green Score' : [sus_indicators[state]['green_score'] for state in sus_indicators]}

    # Min Max scale effort score and green score for easier interpretability
    es_scaled = MinMaxScaler().fit_transform(np.array(data['Effort Score']).reshape(-1, 1)).flatten()
    es_scaled = np.round(es_scaled,3)

    gs_scaled = MinMaxScaler().fit_transform(np.array(data['Green Score']).reshape(-1, 1)).flatten()
    gs_scaled = np.round(gs_scaled,3)

    # Replace the unscaled data with the newly scaled data
    data['Effort Score'] = es_scaled
    data['Green Score'] = gs_scaled

    # Create DataFrame and include state codes for later use in chloropleth map
    sus_df = pd.DataFrame(data = data, index=sus_indicators.keys())
    sus_df['code'] = [state for state in state_abbrevs_dict]


    """
    Sustainability Index
    --------------------
    """

    # Create array with the weight the effort score will receive in that particular sustainability index
    si_range = np.arange(0,1.1,0.1)

    for number in si_range:
        number = round(number,1)

        # The number in the column name will refer to percent of Effort Score accounted for in the sustainability index
        column_name = f'SI_{number}'

        # Define SI = weight * Effort Score + (1 - weight) * Green Score
        si = ((number * sus_df['Effort Score']) + ((round(1 - number,1)) * sus_df['Green Score']))/2

        # Scale between 0-1 and round
        si_scaled = MinMaxScaler().fit_transform(np.array(si).reshape(-1, 1)).flatten()
        si_scaled = np.round(si_scaled,3)

        sus_df[column_name] = si_scaled

    return sus_df
