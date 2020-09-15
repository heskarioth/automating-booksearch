import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import json

def normalise(df_response):
    """
    This function takes
    """
    # Sometimes isbns are not listed in bookdepository, if that is the case.
    try:
        df_response = df_response[df_response['title']!='Advanced Search']
    except:
        pass

    # create a dict that contains: title, author, publisher - extracted from bookdepo response (abebooks doesn't have it)
    _ = df_response[df_response['marketplace']=='bookdepository'].T[:4].T
    _.index = _['isbn']
    info = _.T.to_dict()

    # update abebooks with info from bookrepository
    for row in range(df_response.shape[0]):
        if df_response.iloc[row]['isbn'] in list(info.keys()):
            if df_response.iloc[row]['marketplace']!='bookdepository':
                isbn = df_response.iloc[row]['isbn']
                df_response.iloc[row, df_response.columns.get_loc('title')] = info[isbn]['title']
                df_response.iloc[row, df_response.columns.get_loc('author')] = info[isbn]['author']
                df_response.iloc[row, df_response.columns.get_loc('publisher')] = info[isbn]['publisher']
                
    return df_response

def keep_better_deals(df_response):
    book_depository_prices = df_response[(df_response['marketplace']=='bookdepository') & (~df_response['new_total'].isnull())][['isbn','new_total']].set_index(['isbn']).T.to_dict()
    df_response_final = df_response[df_response['marketplace']=='abebooks'].copy()
    # here only we keep the bookrepository deals which are lower in price than abebooks
    better_deals = []
    for i in range(df_response_final.shape[0]):
        isbn = df_response_final.iloc[i]['isbn']
        if isbn in list(book_depository_prices.keys()):
            if df_response_final[df_response_final['isbn']==isbn]['new_total'].values>float(book_depository_prices[isbn]['new_total']):
                better_deals.append(isbn)

    _ = df_response[(df_response['isbn'].isin(better_deals)) & (df_response['marketplace']=='bookdepository')]
    df_response_final = pd.concat([df_response_final,_])
    
    return df_response_final

def scraper(book,isbn,marketplace,df_response):
    if marketplace=='abebooks':
        payload = book.get_payload(isbn)
        response = book.get_price_abebooks(payload)
    elif marketplace=='bookdepository':
        response = book.get_price_bookdepository(isbn)
    try:
        dict_response = {}
        _ = pd.DataFrame()
        # getting the values
        #print(response)
        #dict_response['title'] = book.get_book_name(isbn).strip()
        dict_response['title'] = '' if marketplace=='abebooks' else response['book_title']
        dict_response['isbn'] = response['isbn'] if marketplace=='abebooks' else isbn
        dict_response['author'] = '' if marketplace=='abebooks' else str(response['author'])
        dict_response['publisher'] = '' if marketplace=='abebooks' else response['publisher']
        dict_response['marketplace'] = marketplace
        dict_response['new_price'] = float(response['pricingInfoForBestNew']['bestPriceInPurchaseCurrencyValueOnly']) if marketplace=='abebooks' else response['price']

        if marketplace=='abebooks':
            used_shipping_cost = response['pricingInfoForBestUsed']['domesticShippingPriceInPurchaseCurrencyWithCurrencySymbol'] if response['pricingInfoForBestUsed']['vendorCountryNameInSurferLanguage'] =='United Kingdom' else response['pricingInfoForBestUsed']['shippingToDestinationPriceInPurchaseCurrencyWithCurrencySymbol']
            new_shipping_cost = response['pricingInfoForBestNew']['domesticShippingPriceInPurchaseCurrencyWithCurrencySymbol'] if response['pricingInfoForBestNew']['vendorCountryNameInSurferLanguage'] =='United Kingdom' else response['pricingInfoForBestNew']['shippingToDestinationPriceInPurchaseCurrencyWithCurrencySymbol']
        else:
            used_shipping_cost =0
            new_shipping_cost=0

        #dict_response['new_shipping_cost'] = float(response['pricingInfoForBestNew']['domesticShippingPriceInPurchaseCurrencyWithCurrencySymbol']) if marketplace=='abebooks' else 0
        #dict_response['new_shipping_cost'] = float((re.compile(r'[^\d.,]+').sub('', response['pricingInfoForBestNew']['domesticShippingPriceInPurchaseCurrencyWithCurrencySymbol'])).replace(',','.')) if marketplace=='abebooks' else 0
        # Rule: if vendor is UK, then take domestic shipping price. Else take shippingToDestinationPrice
        dict_response['new_shipping_cost'] = float((re.compile(r'[^\d.,]+').sub('', new_shipping_cost)).replace(',','.')) if marketplace=='abebooks' else 0

        dict_response['used_price'] = float(response['pricingInfoForBestUsed']['bestPriceInPurchaseCurrencyValueOnly']) if marketplace=='abebooks' else np.nan
        #dict_response['used_shipping_cost'] = float(response['pricingInfoForBestUsed']['domesticShippingPriceInPurchaseCurrencyWithCurrencySymbol']) if marketplace=='abebooks' else np.nan
        #dict_response['used_shipping_cost'] = float((re.compile(r'[^\d.,]+').sub('', response['pricingInfoForBestUsed']['domesticShippingPriceInPurchaseCurrencyWithCurrencySymbol'])).replace(',','.')) if marketplace=='abebooks' else 0
        # Rule: if vendor is UK, then take domestic shipping price. Else take shippingToDestinationPrice
        dict_response['used_shipping_cost'] = float((re.compile(r'[^\d.,]+').sub('', used_shipping_cost)).replace(',','.')) if marketplace=='abebooks' else 0

        dict_response['new_total'] = dict_response['new_price'] + dict_response['new_shipping_cost'] 
        dict_response['used_total'] = dict_response['used_price'] + dict_response['used_shipping_cost'] 

        # update response tables    
        _ = pd.DataFrame(dict_response,index=[1])
        df_response = pd.concat([df_response,_])
    except Exception as e:
        #print(e)
        pass
    df_response = df_response.reset_index(drop=True)
    return df_response
