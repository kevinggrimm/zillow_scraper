'''
Recreational scraper for Apartments on Zillow.

Enhancements:

I. Data Collection
- UI to enter city, state, radius, other initial params
- Lat, lon coordinnates to match city; add logic for desired radius
- IP rerouting to avoid recapthca (or rewrite in selenium / add other headers)

II. Data Ingestion/Processing
- Store raw results in S3
- Collect metadata; process data with AWS Glue
- Load into DynamoDB, QuickSights
- Configure endpoints for web UI
'''

import json 
import numpy as np 
import pandas as pd 
import re
import requests
import time
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

from functions import *

# Set the user agent
ua = UserAgent()
firefox = ua.firefox

headers = {
    'User-Agent': firefox
}

root_url = "https://www.zillow.com/homes/"

# These are your args, swap as needed. Prices/beds/baths are numeric
city = "CITY_NAME"
state = "STATE"

min_price = "MIN_PRICE"
max_price = "MAX_PRICE"
pmin = "P_MIN"
pmax = "P_MAX"

min_beds = "MIN_BEDS"
min_sqft = "MIN_SQFT"
ac = True
fr = True
lau = True

base_url = get_base_url(root_url, city, state)
searchTerm = city + ", " + state

# Configure params
encoded_params = configure_query_params(min_price, max_price, pmin, pmax, min_beds, min_sqft, ac, fr, lau)

# Get full URL
full_url = configure_full_url(base_url, encoded_params)

# Send request
r = requests.get(full_url, headers=headers)

# Create soup object
soup = bs(r.content, "html.parser")

# Get page count (e.g. 7 total pages in result set)
page_count = get_page_count(soup)
current_page = 1

sqft_regex = re.compile(r'\d*,*\d{3} sqft')
scraped_info = []

# to catch failed attempts for future improvements
failed_scrapes = [] 

total_results = 0
while current_page <= page_count - 1:

    # All results 
    all_results = soup.find('div', attrs={"id":"grid-search-results"}). \
                       find("ul", class_="photo-cards"). \
                       find_all('article')

    for result in all_results:

        try:
            # 
            address = result.find("address").get_text()
            description = result.find("div", class_="list-card-footer").get_text()
            link = result.find("a", class_="list-card-link").get("href")
            last_updated = result.find("div", class_="list-card-top").get_text()

            # Rent, sqft, beds, baths arer all found within info
            info = result.find("div", class_="list-card-heading").get_text()
            rent = re.split(r"[+/mo]", info)[0].replace("$","").replace(",","")

            # Some listings do not display square feet, beds, or baths - check first
            if len(re.findall("sqft", info)) > 0:
                sqft = sqft_regex.findall(info)[0].split(" sqft")[0].replace(",","")
            else:
                sqft = 'Not Listed'

            # Abstracted logic away, same concept as sqft
            num_beds = get_room_count(r" bds", info)
            num_baths = get_room_count(r" ba", info)

            unit_info = {
                'address': address,
                'description': description,
                'baths': num_baths,
                'beds': num_beds,
                'price': rent,
                'sqft': sqft,
                'link': link,
                'updated': last_updated
            }
            scraped_info.append(unit_info)
            total_results += 1
            
        except Exception as e:
            print(str(e), i)
            failed_scrapes.append(result)    
    
    # If there are multiple pages of responses, repeat the above process
    # with a new URL that reflects the appropriate page number         
    current_page += 1
    full_url = get_new_url(full_url, current_page)
    
    print('Sending request for page ', current_page, '.....')
    r = requests.get(full_url, headers=headers)
    soup = bs(r.content, "html.parser")