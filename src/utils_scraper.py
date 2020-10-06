import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import json
import time
from selenium import webdriver
from PARAMETERS import AMAZON_EMAIL, AMAZON_PASSWORD



def amazon_login(AMAZON_EMAIL, AMAZON_PASSWORD,driver):
    sign_in_path = '/html/body/div[2]/header/div/div[1]/div[3]/div/a[1]/div/span'
    email_path = '/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/form/div/div/div/div[1]/input[1]'
    email_button_path = '/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div[1]/form/div/div/div/div[2]/span/span/input'
    password_path = '/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div/form/div/div[1]/input'
    password_button_path = '/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div/form/div/div[2]/span/span/input'
    driver.find_element_by_xpath(sign_in_path).click()
    driver.find_element_by_xpath(email_path).send_keys(AMAZON_EMAIL)
    driver.find_element_by_xpath(email_button_path).click()
    driver.find_element_by_xpath(password_path).send_keys(AMAZON_PASSWORD)
    driver.find_element_by_xpath(password_button_path).click()


def amazon_data_extraction(list_isbns,marketplace,df_response):
    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    # https://stackoverflow.com/questions/10399557/is-it-possible-to-run-selenium-firefox-web-driver-without-a-gui
    driver = webdriver.Chrome(executable_path=r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver_win32\chromedriver.exe',options=op)#
    first_access = True
    for isbn in list_isbns:
        url = 'https://www.amazon.co.uk/gp/offer-listing/{}/ref=tmm_pap_used_olp_0?ie=UTF8&condition=used'.format(isbn)
        driver.get(url)
        #print(url)
        if driver.title!='404 - Document Not Found':
            error_503 = 0
            while driver.title=='503 - Service Unavailable Error':
                time.sleep(10)
                driver.get(url)
                error_503+=1
                if error_503 >3:
                    break
            if first_access:
                print('Logging in...')
                amazon_login(AMAZON_EMAIL, AMAZON_PASSWORD,driver)
                first_access=False
                time.sleep(30)
            df_tmp = pd.DataFrame()
            # sometimes there is no book listed at all, in this case we have to skip the search.
            continue_search=True
            try:
                if driver.find_elements_by_xpath("//div[contains(@class, 'a-section a-padding-small')]")[0].text=='There are currently no listings for this search. Try a different refinement.':
                    continue_search=False
            except:
                pass
            if continue_search:
                for result in driver.find_elements_by_xpath("//div[contains(@class, 'a-row a-spacing-mini olpOffer')]"):
                    dict_response = {}
                    dict_response['title'] = driver.find_elements_by_xpath("//div[contains(@class, 'a-fixed-left-grid-col a-col-right')]")[0].text.split('\n')[0]
                    dict_response['isbn'] = isbn
                    dict_response['author'] = re.sub('\(Author\)','',driver.find_elements_by_xpath("//div[contains(@class, 'a-fixed-left-grid-col a-col-right')]")[0].text.split('\n')[1]).strip()
                    dict_response['publisher'] = ''
                    dict_response['marketplace'] = marketplace
                    dict_response['new_price'] = np.nan
                    dict_response['new_shipping_cost'] = np.nan
                    dict_response['used_price'] = float(result.text.split('\n')[0][1:])
                    if re.search('\d',result.text.split('\n')[1]):
                        dict_response['used_shipping_cost'] = float((re.sub('\+','',re.sub('Delivery','',result.text.split('\n')[1]))).strip()[1:])
                    else:
                        dict_response['used_shipping_cost'] = 0
                    dict_response['used_total'] = dict_response['used_price'] + dict_response['used_shipping_cost']
                    dict_response['new_total'] = np.nan
                    dict_response['urlPurchase'] = url
                    df_tmp= pd.concat([df_tmp,pd.DataFrame(dict_response,index=[1])])
                if df_tmp.shape[0]!=0:
                    min_idx = pd.to_numeric(df_tmp['used_total']).argmin()
                    df_tmp = pd.DataFrame(df_tmp.iloc[min_idx]).T
                df_response = pd.concat([df_response,df_tmp])        
    return df_response
    
    
    
    
    
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
    df_final = pd.DataFrame()
    isbns = {}
    number_marketplaces = len(df_response.marketplace.value_counts().index)

    for i in reversed(range(1,number_marketplaces+1)):
        isbns['appear_'+str(i)] = df_response.isbn.value_counts()[df_response.isbn.value_counts()==i].index.values
        if i<2:
            break
        df_blank = df_response[df_response.isbn.isin(isbns['appear_'+str(i)])].reset_index(drop=True).sort_values(by=['isbn'])
        keep_index = []
        for start in range(0,df_blank.shape[0],i):
            end=start+i
            keep_index.append(df_blank[start:end].best_price.idxmin())
        drop_index = [index for index in df_blank.index if index not in keep_index]
        df_final = pd.concat([df_final,df_blank.drop(drop_index)])
    return df_final


def populate(response,marketplace,df_response,isbn):
    dict_response = {}
    _ = pd.DataFrame()
    
    # abebooks
    if marketplace=='abebooks':
        dict_response['title'] = ''
        dict_response['isbn'] = response['isbn']
        dict_response['author'] = ''
        dict_response['publisher'] = ''
        dict_response['marketplace'] = marketplace
        if response['pricingInfoForBestUsed'] is None:
            used_shipping_cost = np.nan
            dict_response['used_shipping_cost'] = np.nan
            dict_response['used_price'] = np.nan
        else:
            used_shipping_cost = response['pricingInfoForBestUsed']['domesticShippingPriceInPurchaseCurrencyWithCurrencySymbol'] if response['pricingInfoForBestUsed']['vendorCountryNameInSurferLanguage'] =='United Kingdom' else response['pricingInfoForBestUsed']['shippingToDestinationPriceInPurchaseCurrencyWithCurrencySymbol']
            dict_response['used_shipping_cost'] = float((re.compile(r'[^\d.,]+').sub('', used_shipping_cost)).replace(',','.'))
            dict_response['used_price'] = float(response['pricingInfoForBestUsed']['bestPriceInPurchaseCurrencyValueOnly'])
        if response['pricingInfoForBestNew'] is None:
            new_shipping_cost = np.nan
            dict_response['new_shipping_cost'] = np.nan
            dict_response['new_price'] = np.nan
        else:
            new_shipping_cost = response['pricingInfoForBestNew']['domesticShippingPriceInPurchaseCurrencyWithCurrencySymbol'] if response['pricingInfoForBestNew']['vendorCountryNameInSurferLanguage'] =='United Kingdom' else response['pricingInfoForBestNew']['shippingToDestinationPriceInPurchaseCurrencyWithCurrencySymbol']
            dict_response['new_shipping_cost'] = float((re.compile(r'[^\d.,]+').sub('', new_shipping_cost)).replace(',','.'))
            dict_response['new_price'] = float(response['pricingInfoForBestNew']['bestPriceInPurchaseCurrencyValueOnly'])
        dict_response['urlPurchase'] = 'https://www.abebooks.co.uk/servlet/SearchResults?bi=0&bx=off&cm_sp=SearchF-_-Advtab1-_-Results&fe=off&ds=30&{}'.format(response['refinementList'][0]['url']) if response['success']==True else ''
    # boook depository
    
    if marketplace=='bookdepository':
        dict_response['title'] = response['book_title']
        dict_response['isbn'] = isbn
        dict_response['author'] = str(response['author'])
        dict_response['publisher'] = response['publisher']
        dict_response['marketplace'] = marketplace
        dict_response['new_price'] = response['price']
        dict_response['new_shipping_cost'] =  0
        dict_response['used_price'] =  np.nan
        dict_response['used_shipping_cost'] = 0
        dict_response['urlPurchase'] = response['urlPurchase']
    
    
    # ebay_search
    if marketplace=='ebay':
        skeleton = pd.DataFrame()
        if (response['findItemsByProductResponse'][0]['ack'][0]!='Failure' and int(response['findItemsByProductResponse'][0]['searchResult'][0]['@count'])>0):
            idx_result_counts = response['findItemsByProductResponse'][0]['searchResult'][0]['@count']
            
            for idx in range(int(idx_result_counts)):
                if response['findItemsByProductResponse'][0]['searchResult'][0]['item'][idx]['listingInfo'][0]['listingType'][0]!='Auction':
                    dict_response['title'] = response['findItemsByProductResponse'][0]['searchResult'][0]['item'][idx]['title'][0]
                    dict_response['isbn'] = isbn
                    dict_response['author'] = ''
                    dict_response['publisher'] = ''
                    dict_response['marketplace'] = marketplace
                    dict_response['new_price'] = np.nan
                    dict_response['new_shipping_cost'] = np.nan
                    dict_response['used_shipping_cost'] = float(response['findItemsByProductResponse'][0]['searchResult'][0]['item'][idx]['shippingInfo'][0]['shippingServiceCost'][0]['__value__'])
                    dict_response['used_price'] = float(response['findItemsByProductResponse'][0]['searchResult'][0]['item'][idx]['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__'])
                    dict_response['used_total'] = dict_response['used_price'] + dict_response['used_shipping_cost']
                    dict_response['new_total'] = dict_response['new_price'] + dict_response['new_shipping_cost'] 
                    
                    dict_response['urlPurchase'] = response['findItemsByProductResponse'][0]['searchResult'][0]['item'][idx]['viewItemURL'][0]
                    skeleton = pd.concat([skeleton,pd.DataFrame(dict_response,index=[1])])
#                    print(skeleton)
        # here we have to drop all the ones that are not minimum total cost
            try:
                min_idx = skeleton['totalCost'].argmin()
            except:
                min_idx = 0
                pass
            df_response = pd.concat([df_response,pd.DataFrame(skeleton.iloc[min_idx]).T]) if len(skeleton)> 0 else df_response
    
        
    if (marketplace!='ebay' and marketplace!='amazon'):
        dict_response['new_total'] = dict_response['new_price'] + dict_response['new_shipping_cost'] 
        dict_response['used_total'] = dict_response['used_price'] + dict_response['used_shipping_cost'] 
        _ = pd.DataFrame(dict_response,index=[1])
        df_response = pd.concat([df_response,_])
    if marketplace=='amazon':
        df_response = amazon_data_extraction(isbn,marketplace,df_response)
    df_response = df_response.reset_index(drop=True)
    return df_response

def scraper(book,isbn,marketplace,df_response):
    if marketplace=='abebooks':
        payload = book.get_payload(isbn)
        response = book.get_price_abebooks(payload)
    elif marketplace=='bookdepository':
        response = book.get_price_bookdepository(isbn)
    elif marketplace=='ebay':
        response = book.get_price_ebay(isbn)
    df_response = populate(response,marketplace,df_response,isbn)
    #except Exception as e:
     #   print(isbn,marketplace)
       # print(e)
    #df_response = df_response.reset_index(drop=True)
    return df_response
