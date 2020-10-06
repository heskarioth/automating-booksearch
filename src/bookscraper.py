
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import re
import json
from PARAMETERS import GOODREADS_KEY,OPERATION_NAME,SECURITY_APPNAME_KEY,GLOBAL_ID


class BookScraper:
    
    def  get_price_abebooks(self,payload):
        url = "https://www.abebooks.co.uk/servlet/DWRestService/pricingservice"
        resp = requests.post(url, data=payload)
        #resp.raise_for_status()
        return resp.json()
    
    def get_price_ebay(self,isbn):
        #OPERATION_NAME ='findItemsByProduct'
        #SECURITY_APPNAME_KEY = 'CamilloH-bookscra-PRD-a500a4123-6c88b0c5'
        #GLOBAL_ID = 'EBAY-GB'
        url = 'https://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME={}&SECURITY-APPNAME={}&GLOBAL-ID={}&RESPONSE-DATA-FORMAT=JSON&productId.@type=ISBN&productId={}&itemFilter.name=Condition&itemFilter.value=Used&sortOrder=PricePlusShippingLowest'.format(OPERATION_NAME,SECURITY_APPNAME_KEY,GLOBAL_ID,isbn)
        receive = requests.get(url).json()
        return receive
    
    def get_payload(self,isbn):
        payload = {'action': 'getPricingDataByISBN',
           'isbn': isbn,
           'container': 'pricingService-'.format(isbn)}        
        return payload
    
    def load_isbns_goodreads(self,GOODREADS_KEY):
        # get list of isbns from the goodreads account to-read list
        url = 'https://www.goodreads.com/review/list/67052324.xml?key={}&v=2&per_page=200&shelf=to-read'.format(GOODREADS_KEY)
        page = urlopen(url)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "lxml")
        list_isbns = []
        for a_tag in soup.find_all('isbn'):
            try:
                list_isbns.append(a_tag.contents[0])
            except:
                pass
        return list_isbns
    
    def get_price_bookdepository(self,isbn):
        url = "https://www.bookdepository.com/search?searchTerm={}&search=Find+book".format(isbn)
        page = urlopen(url)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "lxml")
        
        try:
            price = float((re.compile(r'[^\d.,]+').sub('', [x.string for x in soup.find_all(['span','class']) if str(x).startswith('<span class="sale-price">')][0])).replace(',','.'))
        except:
            # this means, price no found -> the book is not available. We set price to nan.
            price = np.nan
        
        # author
        # publisher
        try:
            authors_publisher_pair = [x.string.strip() for x in soup.find_all(['span','itemprop']) if str(x).startswith('<span itemprop="name">')]
            author = authors_publisher_pair[:-1]
            publisher = authors_publisher_pair[-1]
        except:
            # this means that we didn't find author or publisher. This happens when the book is not actually
            # listed on the marketplace
            author,publisher = np.nan,np.nan
        
        book_title = [x.string.strip() for x in soup.find_all(['h1'])]
        
        response = {'price':price,'author':author,'publisher':publisher, 'book_title':book_title, 'urlPurchase':url}
        
        return response
