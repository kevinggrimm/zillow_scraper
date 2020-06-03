import json
import re

from bs4 import BeautifulSoup as bs
from urllib.parse import quote, unquote

# Configure URL with city, state
def get_base_url(root_url, city, state): 
    base_url = root_url + city + ",-" + state + "_rb/?searchQueryState="
    return base_url


def decode_query_params(full_url):
    '''
    Decode URL query parameters
    Returns: decoded params
    '''
    decoded_url = unquote(full_url)
    decoded_params = decoded_url.split("searchQueryState=")[1]
    params = json.loads(decoded_params)
    return params


def configure_query_params(*args, **kwargs):
    '''
    Configures query parameters for the URL endpoint
    - TO DO: add args for Lat, Lon coordinates; region type; etc.
    '''
    query_params = {
        'pagination': {

        },
        'usersSearchTerm': user_search_term,
        'mapBounds': {
            'west': w_coords,
            'east': e_coords,
            'south': s_coords,
            'north': n_coords
        },
        'regionSelection': [{
            'regionId': region_id, 'regionType': region_type
        }],
        'isMapVisible': True,
        'filterState': {
            'price': {
                'min': pmin, 
                'max': pmax
            },
            'beds': {
                'min': min_beds
            },
            'baths': {
                'min': 1
            },
            'sqft': {
                'min': min_sqft
            },
            'con': {
                'value': False
            },
            'pmf': {
                'value': False
            },
            'fore': {
                'value': False
            },
            'lau': {
                'value': lau
            },
            'mp': {
                'min': min_price, 
                'max': max_price
            },
            'auc': {
                'value': False
            },
            'nc': {
                'value': False
            },
            'fr': {
                'value': fr
            },
            'fsbo': {
                'value': False
            },
            'cmsn': {
                'value': False
            },
            'pf': {
                'value': False
            },
            'fsba': {
                'value': False
            },
            'ac': {
                'value': ac
            }
        },
        'isListVisible': True
    }
    string_params = json.dumps(query_params)
    encoded_params = quote(string_params)
    return encoded_params


def configure_full_url(base_url, encoded_params):
    '''
    Configures, returns full_url
    '''
    full_url = base_url + encoded_params
    return full_url


def get_page_count(soup_object):
    '''
    Get total pages in result set
    Use to modify URL for pagination
    '''
    search_pagination = soup_object.find("div", class_="search-pagination").nav.ul.find_all('li')
    page_count = len(search_pagination) - 2
    return page_count


def get_room_count(pattern, text):
    '''
    Searches for the pattern within the text
    - Suitable for bedrooms, bathrooms
    '''
    if len(re.findall(pattern, text)) > 0:
        match = re.split(pattern, text)[0][-1]
    else:
        match = "Not Listed"
    return match


def get_new_url(full_url, current_page):
    '''
    Prepare the URL for the nth page of results
    '''
    params = decode_query_params(full_url)
    params['pagination']['currentPage'] = current_page
    string_params = json.dumps(params)
    encoded_params = quote(string_params)
    new_url = base_url + encoded_params
    return new_url