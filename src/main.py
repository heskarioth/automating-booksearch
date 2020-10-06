import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import re
import json
from bookscraper import BookScraper
from utils_scraper import normalise, keep_better_deals, scraper, amazon_data_extraction
from PARAMETERS import GOODREADS_KEY
from email_function import send_email


if __name__ =='__main__':
    print('Starting Process....')
    book = BookScraper()
    marketplace_list = ['abebooks','bookdepository','ebay']
    print('Collecting list books from Goodreads profile')
    list_isbns = book.load_isbns_goodreads(GOODREADS_KEY)
    df_response = pd.DataFrame()
    print('Capturing book offers from marketplaces')
    # capture abebooks, bookdepo and ebay data
    for isbn in list_isbns:
        for marketplace in marketplace_list:
            df_response = scraper(book,isbn,marketplace,df_response)
    # capture amazon data
    df_response = amazon_data_extraction(list_isbns,'amazon',df_response)

    #  the abebooks response doesn't provide book info such as title, author etc.
    # bookdepo does. We take that information with the normalise util function.
    print('Normalising the data')
    df_response = normalise(df_response)

    # here we check the best available price between used and new books
    df_response['best_price'] = df_response[['new_total','used_total']].min(axis=1)

    df_response = df_response[['title', 'isbn', 'author', 'publisher', 'marketplace', 'new_shipping_cost', 'new_price','new_total','used_shipping_cost', 'used_price', 'used_total','best_price','urlPurchase']]


    # here we only want to keep the deals where we have the same book available in bookrepo that costs less than 
    # one in abebooks
    print('Keeping only best deals available per book')
    df_response = keep_better_deals(df_response)
    df_response= df_response.reset_index(drop=True)


    df_response[['title', 'isbn', 'author', 'publisher', 'marketplace', 'best_price', 'urlPurchase']].sort_values(by=['best_price']).to_html('book_list.html')
    df_response.sort_values(by=['best_price'],ascending=True)
    print('Sending email with deals')
    send_email(df_response)
