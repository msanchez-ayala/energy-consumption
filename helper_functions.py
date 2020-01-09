import requests
import time
from bs4 import BeautifulSoup as BS

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

def all_pages(genre, headers,no_results):
    """
    Runs get_page(url, headers) multiple times.
    Param genre: [str] genre to search on from IMDB advanced search.
    Param headers: [str] headers to pass into requests.get so that IMDB knows we are not russian hackers.
    Param no_results: [int] number of results we want to obtain.
    """
    base_url = f'https://www.imdb.com/search/title/?title_type=feature,tv_movie&genres={genre}&'
    suffix = 'view=advanced'
    cur = 1
    results = []
    while cur < no_results:
        if cur == 1:
            results.extend(get_page(base_url, headers))
        elif cur > 1:
            suffix = 'start={}&ref_=adv_nxt'.format(cur)
            results.extend(get_page(base_url + suffix, headers))
        time.sleep(0.5)
        cur += 50
    return results



