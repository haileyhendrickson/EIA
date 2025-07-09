import requests
import pandas as pd
import datetime
from datetime import datetime, timedelta
import tkinter as tk
from customtkinter import *
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import *
from tkcalendar import Calendar
import time


def backend(startdate, enddate):      
    
    # ba=ba_var.get()
    startyr = datetime.strptime(startyr, '%m/%d/%y').date() # formats it to work with datetime package
    endyr = datetime.strptime(endyr, '%m/%d/%y').date()

    difference = endyr - startyr # counts days in between
    yr_count = difference.days # making a number I can work with
    totalrows = 10 * units.count * yr_count # for each selected unit, get 10 rows

    # setting up for pull
    counter = 0
    offset = 0
    files = [] # empty list to store all files
    df_list = [] # place to store rows
    timestamp = datetime.now() # using for filename
    timestamp = timestamp.strftime('%m-%d-%Y %H%M')
    while totalrows > 0:
        try:
            url = 'https://api.eia.gov/v2/electricity/facility-fuel/data/?' # main URL for natural gas, prices for a futures exchange
            params = {'api_key': 'h6SzHD7npQ0r1YVfC7HZHEMu7LZ74yx2m9EcbSHD',
                        'frequency': 'annual', # like interval
                        'data[0]': 'gross-generation', # specifying what columns I want?
                        'facets[state][]': 'CA', # specifies balancing authority
                        'facets[plantCode][]': 10005,  # 5 Digit number. Will probably need to make a map
                        'start': f'{startdate}', # start year
                        'end': f'{enddate}', 
                        'sort[0][column]': 'period',
                        'sort[0][direction]': 'asc',
                        'offset': offset, # if I want to skip any rows. try offsetting by 5000 rows when I need large chunks
                        'length': 5000
                    }

            response = requests.get(url, params=params)
            data = response.json()
            df = pd.DataFrame(data['response']['data'])
            print(df.head())
        except Exception as e:
            print(f'error: {e}')
            # status_lbl.configure(text='Error. Try again.') # updating status label if it fails
            # root.update() 
        totalrows -=5000 # take off rows that just printed
        offset +=5000 # offsets so I can pull the next chunk of data next time
        files.append(f'test{counter}.csv') # adding files to list    
        counter +=1

    for file in files: # if tabbed over, it cleans each pull before combining, but is bad at error handling
        df_list.append(pd.read_csv(file)) # adding individual rows to df.list

    df_combined = pd.concat(df_list, ignore_index=True) # combining 30 day chunks
    df_combined.to_csv('test.csv')