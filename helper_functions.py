import requests
import time
from bs4 import BeautifulSoup as BS
import numpy as np

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

def get_matrix(temp_data):
    """
    Returns a 2-D matrix outlining how many days in a given year had temperatures above or below certain values Farenheit.
    [[above_100  above_95  above_90  above_85  above_80  above_75  above_70], 
     [below_70 below_65 below_60 below_55 below_50 below_below_45 below_40 
      below_35 below_30 below_25 below_20 below_15 below_10 below_5]]
     
    Param temp_data: [list] All of the TMAXs for a given day
    """
    
   
