"""
This performs the entire ETL process from scraping energy data,
to parsing, to storing on MongoDB.
"""

import json
import pandas as pd
import numpy as np
import re
import requests
import time
from bs4 import BeautifulSoup as BS
import pymongo
from pprint import pprint
%load_ext autoreload
%autoreload 2
import helper_functions

"""
GETTING STARTED
---------------
Do a little manipulation to the text file from EIA containing 
all of their data. It is a text file with a bunch of line-separated 
JSON objects, but I massage it here to a proper JSON and export it 
as a new file.
"""

lastline = None

# Open and read text file
with open("not_for_git/SEDS.txt","r") as f:
    lineList = f.readlines()
    
    # Keep track of last line
    lastline=lineList[-1]

# Open text file and create new json to be written
with open("not_for_git/SEDS.txt","r") as f, open("not_for_git/cleanfile2.json","w") as g:
    
    # Iterate through each line of the text file
    for i,line in enumerate(f,0):
        
        # First line gets [ and , to initialize the json
        if i == 0:
            line = "["+str(line)+","
            g.write(line)
            
        # Last line gets ] to signal the end of the json
        elif line == lastline:            
            g.write(line)
            g.write("]")
            
        # Other lines get comma separation
        else:
            line = str(line)+","
            g.write(line)

file = open('not_for_git/cleanfile2.json', 'r')
json_data = json.load(file)

"""
ASSIGN ENERGY TYPES
-------------------
"""

# The following energy types were selected based on the categories in the EIA educational page.
energy_types = [
    'All Petroleum Products',
    'Coal',
    'Natural Gas including Supplemental Gaseous Fuels',
    'Nuclear Power',
    'Biomass',
    'Fuel Ethanol excluding Denaturant',
    'Geothermal',
    'Hydroelectricity',
    'Solar Energy',
    'Wind Energy',
    'Renewable Energy'
]

# Make all lowercase in case some pages have inconsistent letter casing
for i in range(len(energy_types)):
    energy_types[i] = energy_types[i].lower()
    
# Assign nonrenewable and renewable based on EIA
nonrenewable_energies = energy_types[:4]
renewable_energies = energy_types[4:]

"""
WEB SCRAPING
------------
"""

# Set headers, base url, and first url suffix for the scraping
headers = {'user-agent': 'Safari/13.0.2 (Macintosh; Intel Mac OS X 10_15)'}
base_url = 'https://www.eia.gov/opendata/qb.php'
consumption_suffix = '?category=40204'

# Scrape the consumption page
consumption_page = helper_functions.get_page(base_url+consumption_suffix,headers)

# Create empty dict to store all info across every sector and energy type by state
env_series_ids = {}

# Start by scraping the consumption website in order to get the list of available sectors  
consumption_sectors = consumption_page.find('div',{'class':'pagecontent mr_temp2'})

# Store sector url suffixes in a list
sector_url_suffixes = [sector.a['href'] for sector in consumption_sectors.find_all('li')[:7]]

# Loop 1 - iterate through each sector
for sector_url_suffix in sector_url_suffixes:
    
    # Scrape the sector page
    sector_page = helper_functions.get_page(base_url+sector_url_suffix,headers)    

    # Go into first url and grab tags of all children categories
    children_categories = sector_page.find('div',{'class':'main_col'}).ul.find_all('li')

    # Store the urls of children cats (ccats = children categories)
    ccats_url_suffixes = [children_category.a['href'] 
                          for children_category in children_categories
                          if children_category.text.lower() in energy_types]
    
    # Loop 2 - for each sector, iterate through the relevant types of energy consumption to get state-level data
    for ccats_url_suffix in ccats_url_suffixes:
        
        # Scrape the child category page
        child_category_page = helper_functions.get_page(base_url+ccats_url_suffix,headers)

        # Grab tags of all energy unit children categories. Only want Btu
        energy_unit_cats = child_category_page.find('div',{'class':'main_col'}).ul.find_all('li')

        # Store only the url of the 'Btu' children category. I make a list and select only the first element 
        # because sometimes there will be two energy unit options or just one. This way ensures we only take 
        # the Btu option.
        btu_url_suffix = [energy_unit.a['href'] 
                   for energy_unit in energy_unit_cats
                   if energy_unit.text == 'Btu'][0]
        
        # Scrape the Btu page
        btu_page = helper_functions.get_page(base_url+btu_url_suffix,headers)
        
        # Get list of states by their tags
        states = btu_page.find('div',{'class':'main_col'}).ul.find_all('li')
        
        # Get url suffixes for each state
        state_url_suffixes = [state.a['href'] for state in states]
        
        # Isolate the sector and energy type
        sector = btu_page.find('div',{'class':'main_col'}).h3.find_all('a')[3].text
        energy_type = btu_page.find('div',{'class':'main_col'}).h3.find_all('a')[4].text
        
        # Add these to a dict which will be the values of the overarching env_series_ids dict
        series_id_values = {'sector':sector,'energy_type':energy_type}
        
        # Parse through url suffixes to get and store the series ids we want to use to parse the big JSON
        for state_suffix in state_url_suffixes:
            series_id = re.findall('SEDS.*',state_suffix)[0]
            env_series_ids[series_id] = series_id_values    

"""
PARSE DATA
----------
"""

# Set up empty bucket for parsed data
environmental_data = []

# Iterate through big json to parse relevant info
for single_json in json_data:
    
    # Only parse entries that have the series ids that we care about
    if single_json.get('series_id') in env_series_ids.keys():
        single_data_entry = {}
        single_data_entry['series_id'] = single_json['series_id']
        single_data_entry['sector'] = env_series_ids[single_json['series_id']]['sector']
        single_data_entry['data'] = single_json['data']
        single_data_entry['state'] = re.findall('(, )(\w* ?\w* ?\w*)',single_json['name'])[-1][-1]
        single_data_entry['units'] = single_json['units']
        single_data_entry['energy_type'] = env_series_ids[single_json['series_id']]['energy_type']
        
        environmental_data.append(single_data_entry)

"""
STORE DATA TO MONGODB
---------------------
This is to a localhost though, so you'll need to install MongoDB
for yourself in order to do this.
"""

client = pymongo.MongoClient('mongodb://localhost/')
db = client.admin

# Issue the serverStatus command and print the results
serverStatusResult=db.command("serverStatus")
pprint(serverStatusResult)

mydb = client['energy_data']

energy_collection = mydb['energy_data']

env_results = energy_collection.insert_many(environmental_data)