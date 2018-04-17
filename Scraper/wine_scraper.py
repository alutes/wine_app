#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 08:27:56 2018

@author: andrewlutes
"""
import pandas as pd
import time
import json
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup


def load_url(url, sleep_time=3):

    browser = webdriver.Chrome(path_to_chrome_driver) # Open chrome instance
    browser.get(url) # web page
    time.sleep(sleep_time) # wait to load
    
    # Get rid of the auto-pop-up. STFU chas, I know its jenky
    elem = browser.find_elements_by_class_name("tooltipComponent_text")
    for e in elem:
        if e.is_enabled() and e.is_displayed():
            e.click() 
    return(browser)

    
def extract_wine_url_list(url_base, url_color, no_of_pagedowns=1000):
    
    browser = load_url(url_base+url_color+'?showOutOfStock=true')
    
    # Scroll down to the bottom
    elem = browser.find_element_by_tag_name("body")
    while no_of_pagedowns:
        elem.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.2)
        no_of_pagedowns-=1
    
    # Get the item list from the fully rendered page source
    soup = BeautifulSoup(browser.page_source, 'lxml') #req.text
    item_list = soup.findAll(attrs={'class':'prodItemInfo_link'})
    item_list = [url_base+x.get('href') for x in item_list]
    
    browser.close()
    
    return item_list


def parse_review(review_list_element,
                 fmt={'rating' : 'wineRatings_rating',
                    'initials' : 'wineRatings_initials',
                    'author' : 'pipProfessionalReviews_authorName',
                    'review_text' : 'pipProfessionalReviews_review'
                    }):
    ret_dict = {}
    for key_val in fmt:
        content_value = review_list_element.find(attrs={'class': fmt[key_val]})
        if content_value:
            ret_dict[key_val] = content_value.text
    return ret_dict
    

# The scraping function that returns both the wine data and the review
# url='https://www.wine.com/product/columbia-crest-grand-estates-red-blend-2012/152746'
def scrape_wine_data(url, wine_id, image_path, base_url='https://www.wine.com'):
    
    #html = requests.get(url).page_source
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    
    
    # Pulling out key sections
    wine_text = soup.find(attrs={'class': 'pipName'}).text
    description = soup.find(attrs={'class': 'pipSecContent'}).text
    winery = soup.find(attrs={'class': 'pipWinery_headline'}).text
    headers = soup.find_all(attrs={'class': 'productPageContentHead_title'})
    pro_reviews = soup.find_all(attrs={'class': 'pipProfessionalReviews_list'})
    wine_image = soup.find(attrs={'class': 'pipHero_image',
                                  'itemprop': "image"})

    ### Parsing fields from html objects ###
    
    # Location and wine type
    location, wine_type = None, None    
    if len(headers)==2:
        location = headers[0].text
        wine_type = headers[1].text
    
    # Parse reviews
    review_list = []
    for p in pro_reviews:
        review_list.append(parse_review(p))

    # Image url
    image_url = base_url+wine_image['src']

    # Final Dictionary
    wine_dict = {'wine':wine_text, 
                 'description':description, 
                 'winery':winery,
                 'reviews':review_list,
                 'location':location,
                 'wine_type':wine_type,
                 'url':url,
                 'image_url':image_url,
                 'wine_id':wine_id}
    
    # download the image
    image_file_path = os.path.join(image_path,str(wine_id)+'.jpeg')
    req = requests.get(image_url)
    if req.status_code == 200:
        with open(image_file_path, 'wb') as f:
            for chunk in req:
                f.write(chunk)
    
    return wine_dict





# Path to your chrome driver
path_to_chrome_driver = '/Users/andrewlutes/Downloads/old_downloads/WebDrivers/chromedriver'
outpath = '/Users/andrewlutes/Documents/Wine/Data/'
image_path = os.path.join(outpath,'images')


 # Urls for wine categories
base_url = 'https://www.wine.com/'
color_urls = ['list/wine/red-wine/7155-124',
              'list/wine/white-wine/7155-125']

# Print out the list of all urls pointing to specific wine brands
wine_urls = []
for color_url in color_urls:
    wine_urls.extend(extract_wine_url_list(base_url, color_url))
pd.Series(wine_urls).to_csv(os.path.join(outpath,'wine_url_list.csv'), index=False)


# Scrape all urls
wine_dicts = []
for i,url in enumerate(wine_urls):
    wine_dicts.append(scrape_wine_data(url,i,image_path))
    print(i)

# Save to file
json.dump(os.path.join(outpath,'wine_data.json'))



