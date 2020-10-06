#!/usr/bin/env python
# coding: utf-8

# In[12]:


import pandas as pd
from email.message import EmailMessage
import smtplib
from datetime import datetime
from PARAMETERS import GMAIL_PASSWORD, GMAIL_EMAIL


def send_email(df_response):
    df_top_deals = df_response[['title', 'isbn', 'marketplace', 'best_price', 'urlPurchase']].sort_values(by=['best_price']).head(10)
    msg = EmailMessage()
    msg['Subject'] = 'BookScraper - {}'.format(datetime.now())
    msg['From'] = 'camilloshady@gmail.com'
    msg['To'] = 'camilloshady@gmail.com'
    msg.set_content('')


    table = ""
    for i in range(df_top_deals.shape[0]):
        table+='<tr>'
        table +="<th>"+df_top_deals.iloc[i]['title']+"</th>"
        table +="<th>"+df_top_deals.iloc[i]['isbn']+"</th>"
        table +="<th>"+str(df_top_deals.iloc[i]['best_price'])+"</th>"
        table +="<th>"+df_top_deals.iloc[i]['urlPurchase']+"</th>"
        table+='</tr>'



    msg.add_alternative("""    <!DOCTYPE html>
    <html>
    <head>
    <style>
    table {
      font-family: arial, sans-serif;
      border-collapse: collapse;
      width: 100%;
    }

    td, th {
      border: 1px solid #dddddd;
      text-align: left;
      padding: 8px;
    }

    tr:nth-child(even) {
      background-color: #dddddd;
    }
    </style>
    </head>
    <body>
    <h2>Book deals</h2>
    <table>
      <tr>
        <th>Title</th>
        <th>ISBN</th>
        <th>Best Price</th>
        <th>url Purchase</th>
      </tr>
      """+table+"""

                        </table>
                        </body>
                        </html>
    """,subtype='html')

    # add codice fiscale - carta identita
    files = ['book_list.html']
    for file in files:
        with open(file,'rb') as f:
            file_data = f.read()
            file_name = f.name
        msg.add_attachment(file_data,maintype='application',subtype='octet-stream',filename=file_name)
    # add resume - messa a disposizione


    with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
        smtp.ehlo()

        smtp.login(GMAIL_EMAIL,GMAIL_PASSWORD)
        smtp.send_message(msg)

        smtp.quit()
    print('Email sent...')

