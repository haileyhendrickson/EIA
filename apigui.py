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

# backend code
def backend(startdate, enddate, timezone):      
    map = { # finds UTC difference and associated time code, based on 24 major timezones
        ('Universal Time'): ('00', '(UTC)', '+'),
        ('Mountain Time'): ('07', '(MST)', '-'), 
        ('Central Time'): ('06', '(CST)', '-'),
        ('Pacific Time'): ('08', '(PST)', '-'),
        ('Eastern Time'): ('05', '(EST)', '-'), 
        ('European Central Time'): ('01', '(ECT)', '+'),
        ('Eastern Eurpoean Time'): ('02', '(EET)', '+'),
        ('Eastern African Time'): ('03', '(EAT)', '+'),
        ('Near East Time'): ('04', '(NET)', '+'),
        ('Pakistan Lahore Time'): ('05', '(PLT)', '+'),
        ('Bangladesh Standard Time'): ('06', '(BST)', '+'),
        ('Vietnam Standard Time'): ('07', '(VST)', '+'),
        ('China Taiwan Time'): ('08', '(CTT)', '+'),
        ('Japan Standard Time'): ('09', '(JST)', '+'),
        ('Australia Eastern Time'): ('10', '(AET)', '+'),
        ('Solomon Standard Time'): ('11', '(SST)', '+'),
        ('New Zealand Standard Time'): ('12', '(NST)', '+'),
        ('Midway Islands Time'): ('11', '(MIT)', '-'),
        ('Hawaii Standard Time'): ('10', '(HST)', '-'),
        ('Alaska Standard Time'): ('09', '(AST)', '-'),
        ('Puerto Rico and US Virtin Islands Time'): ('04', '(PRT)', '-'),
        ('Argentina Standard/Brazil Eastern Time'): ('03', '(AGT/BET)', '-'),
        ('Central African Time'): ('01', 'CAT', '-')
    } # add more timezones later, if needed 
    
    hours, timecode, operand = map.get((timezone), ('unknown')) # getting variables from map based on user input
    ba=ba_var.get()

    # find how many expected rows. one month = about 3000 rows.
    startdate = datetime.strptime(startdate, '%m/%d/%y').date() # formats it to work with datetime package
    enddate = datetime.strptime(enddate, '%m/%d/%y').date()
    if operand == '+':
        enddate = enddate + timedelta(days=1) # adding on one day to the desired pull so it gets the full last day
        startdate = startdate - timedelta(days=1)
    else:
        enddate = enddate + timedelta(days=2) # adding on two days to the desired pull so it gets the full last day

    difference = enddate - startdate # counts days in between
    days = difference.days # making a number I can work with
    totalrows = (days*24)*4 # 4 rows of data per hour

    # setting up for pull
    counter = 0
    offset = 0
    files = [] # empty list to store all files
    df_list = [] # place to store rows
    timestamp = datetime.now() # using for filename
    timestamp = timestamp.strftime('%m-%d-%Y %H%M')
    while totalrows > 0:
        try:
            url = 'https://api.eia.gov/v2/electricity/rto/region-data/data/?' # main URL for natural gas, prices for a futures exchange
            params = {'api_key': 'h6SzHD7npQ0r1YVfC7HZHEMu7LZ74yx2m9EcbSHD',
                        'frequency' : 'hourly', # like interval
                        'data[0]' : 'value', # specifying what columns I want?
                        'facets[respondent][]' : ba, # specifies balancing authority
                        'start' : f'{startdate}T00', # start date, in UTC. Change timezone with dropdown menu and pytz mod? Starting at hours so its cloaser to 0 for most used timezones. timezones that jump ahead will lose hourly data
                        'end' : f'{enddate}T00', # end date, in UTC
                        'sort[0][column]' : 'period',
                        'sort[0][direction]' : 'asc',
                        'offset' : offset, # if I want to skip any rows. try offsetting by 5000 rows when I need large chunks
                        'length' : '5000' # how many rows to give back. almost 3000 rows for a month
                    }

            response = requests.get(url, params=params)
            data = response.json()
            df = pd.DataFrame(data['response']['data'])
            # fixing timezone   
            hours = int(hours)
            df['period'] = pd.to_datetime(df['period']) # changing period column to datetime
            if operand == '+': # separating by adding or subtracting hours to UTC
                df['period'] = df['period'] + timedelta(hours=hours) # shifting timezone dependent on user input
            else:
                df['period'] = df['period'] - timedelta(hours=hours)
            df.to_csv(f'test{counter}.csv') # saving chunks to csvs to combine later
        except Exception as e:
            print(f'error: {e}')
            status_lbl.configure(text='Error. Try again.') # updating status label if it fails
            root.update() 
        totalrows -=5000 # take off rows that just printed
        offset +=5000 # offsets so I can pull the next chunk of data next time
        files.append(f'test{counter}.csv') # adding files to list    
        counter +=1

    for file in files: # if tabbed over, it cleans each pull before combining, but is bad at error handling
        df_list.append(pd.read_csv(file)) # adding individual rows to df.list

    df_combined = pd.concat(df_list, ignore_index=True) # combining 30 day chunks
    df_combined = df_combined.drop(columns=['Unnamed: 0', 'value-units', 'type', 'respondent-name']) # bc I'm dropping units, rename columns later
    df_combined.rename(columns={'period':f'Timestamp {timecode}','respondent':'BA Code'},inplace=True)
    df_combined = pd.pivot_table(df_combined, values='value', index=[f'Timestamp {timecode}','BA Code'], columns='type-name').reset_index() # breaking out LMP_TYPE columns, keeping the other indexed columns
    df_combined.rename(columns={'Day-ahead demand forecast':f'Demand Forecast (MWh)','Demand':'Demand (MWh)','Net generation':'Net Generation (MWh)','Total interchange':'Total Interchange (MWh)'},inplace=True)
    
    if operand =='+': # trimming end by hours, trimming start by 24-hrs
        df_combined = df_combined.iloc[(24-hours):-(hours+1)]
    else:
        df_combined = df_combined.iloc[hours:-(25-hours)] 

    df_combined.to_excel(f'{output_file_path}/{ba} Data {timestamp}.xlsx') # saving to one completed file

    if getattr(sys, 'frozen', False): # finding file path to wherever GUI is stored
        application_path = os.path.dirname(sys.executable)
    for csv in files: # deleting extra files
        filepath = os.path.join(application_path, csv) # creating path to CSV file that will populate in the GUI folder
        os.remove(filepath) # deleting files

    status_lbl.configure(text='Finished!') # updating status label 
    root.update()            


# tkinter widgets
def submit(): # after user gives all inputs, runs all of the backend code
    status_lbl.configure(text='Running...')
    root.update() # updating status label
    timezone=timezoneDropdown.get()
    backend(startdate, enddate, timezone)

def findStartDate(): # for selecting the start date
    global startdate
    startdate = cal.get_date()
    startdate_label.configure(text=f'Start date: {startdate}')

def findEndDate(): # for selecting the end date
    global enddate
    enddate = cal.get_date()
    enddate_label.configure(text=f'End date: {enddate}')

def select_output_file(): # for selecting excel output file path
    global output_file_path
    directory = filedialog.askdirectory(title='Select output directory')
    if directory:
        output_file_path = directory
        output_file_label.configure(text=directory) # displaying file path
    else:
        output_file_label.configure(text='No directory selected yet') # if they tried to submit without a filepath


# tkinter program
root = CTk() # initializing window
root.geometry('600x400') # setting size
set_appearance_mode('light') # can also be light
ba_var=tk.StringVar()

startdate = None # initializing
enddate = None

# widgets
timezone_label = CTkLabel(root, text = 'Timezone:', font=('Arial',15), text_color='#04033A')
timezoneDropdown = CTkComboBox(master=root, values=['Universal Time', 'Mountain Time', 'Pacific Time', 'Central Time', 'Eastern Time', 'European Central Time',
        'Eastern Eurpoean Time','Eastern African Time','Near East Time','Pakistan Lahore Time','Bangladesh Standard Time','Vietnam Standard Time','China Taiwan Time',
        'Japan Standard Time','Australia Eastern Time','Solomon Standard Time','New Zealand Standard Time','Midway Islands Time','Hawaii Standard Time','Alaska Standard Time',
        'Puerto Rico and US Virtin Islands Time','Argentina Standard/Brazil Eastern Time','Central African Time'])

cal = Calendar(root, selectmode ='day',
            year=2024, month =1, # defaults
            day = 1, font=('Arial', 15))

chooseStartDate = CTkButton(root, text='Choose Start Date', command=findStartDate, corner_radius=26,fg_color='#162157', hover_color='#6D7DCF')
chooseEndDate = CTkButton(root, text='Choose End Date', command=findEndDate, corner_radius=26,fg_color='#162157', hover_color='#6D7DCF')

startdate_label = CTkLabel(root, text= 'Start Date: ', font=('Arial',15), text_color='#04033A') 
enddate_label = CTkLabel(root, text='End Date: ', font=('Arial',15), text_color='#04033A')

sub_btn=CTkButton(master=root,text = 'Submit', command = submit, corner_radius=32,fg_color='#162157', hover_color='#6D7DCF') 

output_file_button = CTkButton(root, text='Select Output File Path', command=select_output_file, corner_radius=32,fg_color='#162157', hover_color='#6D7DCF')
output_file_label = CTkLabel(root, text='No path selected', font=('Arial',10), text_color='#04033A')

ba_label = CTkLabel(root, text='BA Code:', font=('Arial',15), text_color='#04033A')
ba_entry = CTkEntry(root, textvariable = ba_var, font=('Arial',15), text_color='#04033A')

status_lbl = CTkLabel(root, text='', font=('Arial',15), text_color='#04033A')

title_lbl = CTkLabel(root, text='EIA DATA', font=('Arial',20, 'bold'), text_color='#04033A')

# grid
cal.grid(row=6,column=0)
chooseStartDate.grid(row=4,column=0) 
chooseEndDate.grid(row=5,column=0)
sub_btn.grid(row=6,column=2)
startdate_label.grid(row=4, column=1)
enddate_label.grid(row=5, column=1)
output_file_button.grid(row=1, column=0)
output_file_label.grid(row=2, column=0)
title_lbl.grid(row=0, column=2)
status_lbl.grid(row=7,column=2) 
ba_label.grid(row=3, column=1)
ba_entry.grid(row=3,column=2)
timezone_label.grid(row=1, column=1)
timezoneDropdown.grid(row=1, column=2)

root.mainloop() # performing an infinite loop for the window to display