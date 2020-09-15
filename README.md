# Automating-booksearch
> Do you spend hours at the time in search of the best book deals out there? This might be the app for you.

## Table of contents
* [General info](#general-info)
* [Screenshots](#screenshots)
* [Technologies](#technologies)
* [Setup](#setup)
* [Features](#features)
* [Status](#status)
* [Inspiration](#inspiration)
* [Contact](#contact)

## General info
I consider myself to be an avid reader. When I am not working, studying, exercising or writing, then I am spending my time reading a book. This means that if I was to buy every single book I have read or own, I'd in debt big times by now. For this reason, I always try to buy my books in charity shops or online second-hand marketplaces.<br>
Usually, I would spend couple of hours every few weeks checking for the books in my current 'to-buy' reading list. When your current list comprises over 100 books, this manual process becomes, incredible inefficient and boring.<br>
What if we can make python this machine task for us? <br>
Meet <b>Automating-booksearch</b>. <br> 
All you have to do is provide it with the list of isbns books you're looking for (i.e. the script, automatically extracts them for your current 'to-read' list in your Goodreads profile), and the bookscraper will do the rest. It will check <b>abebooks</b> and <b>Book Depository</b>, compare them, and report back for each book in which marketplace we can get the best deal price.

In this way, we can check for book deals every single day without having to burn out all the few brain neurons we're left with (and use them in more interesting things) :). 

## Screenshots
![Example screenshot](./img/screenshot.png)

## Technologies
The code is written in python comprinsing a collection of API calls, Beautifulsoup, and python requests.

## Setup
- After cloning the repo. pip install the requirements.txt.
- You will need to modify GOODREADS_KEY key and add your user key. This can be obtained from Goodreads website. Furthermore, you will also need to modify load_isbns_goodreads from the bookscraper file to include the url corresponding to your own reading list. More info can be found on Goodreads API website here: https://www.goodreads.com/api (Get the books on a members shelf)
- Following the above changes, you can execute the script via terminal: python main.py

## Code Examples
Show examples of usage:
`put-your-code-here`

## Features
List of features ready and TODOs for future development
* Awesome feature 1
* Awesome feature 2
* Awesome feature 3

To-do list:
* Add eBay and Amazon marketplace search
* Deploy on webserver and run it with crons
* email alerting for books when they lowered the their price

## Status
Project is: _in progress_

## Inspiration
Add here credits. Project inspired by..., based on...
