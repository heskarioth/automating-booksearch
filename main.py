import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import re
import json
from bookscraper import BookScraper
from utils_scraper import normalise, keep_better_deals, scraper



GOODREADS_KEY = "??????"

book = BookScraper()
marketplace_list = ['abebooks','bookdepository']
list_isbns = book.load_isbns_goodreads(GOODREADS_KEY)
df_response = pd.DataFrame()

for isbn in list_isbns:
    for marketplace in marketplace_list:
        df_response = scraper(book,isbn,marketplace,df_response)
        

#  the abebooks response doesn't provide book info such as title, author etc.
# bookdepo does. We take that information with the normalise util function.
df_response = normalise(df_response)

# here we only want to keep the deals where we have the same book available in bookrepo that costs less than 
# one in abebooks
df_response = keep_better_deals(df_response)
df_response= df_response.reset_index(drop=True)

# here we check the best available price between used and new books
df_response['best_price'] = df_response[['new_total','used_total']].min(axis=1)


print('Saving....')
print(df_response)
df_response.sort_values(by=['best_price'],ascending=True).to_csv('book_listing_prices.csv', index=False)
