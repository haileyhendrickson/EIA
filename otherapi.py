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


def B_backend(startyr, endyr):          
    totalrows = 100000  # Setting as a very large number for now, might want to change later.  # totalrows = 10 * units.count * yr_count # for each selected unit, get 10 rows
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
                        # 'facets[state][]': 'CA', # specifies balancing authority
                        'facets[plantCode][]': (10005,10003),  # (10005,10003)  5 Digit number. Will probably need to make a map?
                        'start': startyr, # start year
                        'end': endyr, 
                        'sort[0][column]': 'period',
                        'sort[0][direction]': 'asc',
                        'offset': offset, # if I want to skip any rows. try offsetting by 5000 rows when I need large chunks
                        'length': 5000
                    }

            response = requests.get(url, params=params)
            data = response.json()
            df = pd.DataFrame(data['response']['data'])
            print(df.head())
            df.to_csv('test.csv')
        except Exception as e:
            print(f'error: {e}')
            # status_lbl.configure(text='Error. Try again.') # updating status label if it fails
            # root.update() 
        totalrows -=5000 # take off rows that just printed
        offset +=5000 # offsets so I can pull the next chunk of data next time
        files.append(f'test{counter}.csv') # adding files to list    
        counter +=1




startyr = 2022
endyr = 2022
state = 'UT' # input('Select a state: ')

backend(startyr,endyr)

