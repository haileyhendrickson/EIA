# have user choose which type of report: generation by BA or by unit (powerplant)
# switch remaining inputs based off of report type
    # Balancing Authority (Justin's report)
    # Choose BA
    # Choose date range
    # Choose timezone
    # submit!

    # Unit (dad's report)
    # choose year range (just make a dropdown? easier than calendar)
    # choose state to filter units. Base unit dropdown on state
        # select applicable units (option for multiple)
        # submit!

import os
from zipfile import ZipFile
from io import BytesIO
import time
from datetime import timedelta, datetime
import sys

import tkinter as tk
from tkinter import filedialog
import tkinter as tk
from tkinter import filedialog
from customtkinter import (CTk, CTkButton, CTkLabel, CTkComboBox, CTkEntry, set_appearance_mode)
from tkcalendar import Calendar
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

import openpyxl
from openpyxl.styles import Font


# REPORT A CODE
def A_backend(startdate, enddate, timezone):      
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

    df_combined.to_excel(f'{output_file_path}/{ba} Data {timestamp}.xlsx', index=False) # saving to one completed file

    if getattr(sys, 'frozen', False): # finding file path to wherever GUI is stored
        application_path = os.path.dirname(sys.executable)
    for csv in files: # deleting extra files
        filepath = os.path.join(application_path, csv) # creating path to CSV file that will populate in the GUI folder
        os.remove(filepath) # deleting files

    status_lbl.configure(text='Finished!') # updating status label 
    root.update()            

# REPORT B CODE
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

# front page widgets
def select_output_file(): # for selecting excel output file path
    global output_file_path
    directory = filedialog.askdirectory(title='Select output directory')
    if directory:
        output_file_path = directory
        output_file_label.configure(text=directory) # displaying file path
    else:
        output_file_label.configure(text='No directory selected yet') # if they tried to submit without a filepath


# report A widget functions 
def submit(): # after user gives all inputs, runs all of the backend code
    status_lbl.configure(text='Running...')
    root.update() # updating status label
    timezone=timezoneDropdown.get()
    A_backend(startdate, enddate, timezone)

def findStartDate(): # for selecting the start date
    global startdate
    startdate = cal.get_date()
    startdate_label.configure(text=f'Start date: {startdate}')

def findEndDate(): # for selecting the end date
    global enddate
    enddate = cal.get_date()
    enddate_label.configure(text=f'End date: {enddate}')


# tkinter program
root = CTk() # initializing window
root.geometry('600x400') # setting size
set_appearance_mode('light') # can also be light
ba_var=tk.StringVar() # needed for report A

def show_second_dropdown(choice):
    if choice == 'Report A':
        # forget old labels
        start_year_label.grid_forget()
        start_year_dropdown.grid_forget()
        end_year_dropdown.grid_forget()
        state_label.grid_forget()
        state_dropdown.grid_forget()

        # report A labels here
        ba_label.grid(row=3, column=1)
        ba_entry.grid(row=3,column=2)
        timezone_label.grid(row=1, column=1)
        timezoneDropdown.grid(row=1, column=2)
        cal.grid(row=6,column=0)
        chooseStartDate.grid(row=4,column=0) 
        chooseEndDate.grid(row=5,column=0)
        sub_btn.grid(row=6,column=2)
        startdate_label.grid(row=4, column=1)
        enddate_label.grid(row=5, column=1)

    if choice == 'Report B':
        # forget old labels
        ba_label.grid_forget()
        ba_entry.grid_forget()
        timezone_label.grid_forget()
        timezoneDropdown.grid_forget()
        cal.grid_forget()
        chooseStartDate.grid_forget()
        chooseEndDate.grid_forget()
        sub_btn.grid_forget()
        startdate_label.grid_forget()
        enddate_label.grid_forget()

        # report b labels here
        start_year_label.grid()
        start_year_dropdown.grid()
        end_year_dropdown.grid()
        state_label.grid()
        state_dropdown.grid()
    else:
        second_dropdown.pack_forget()
# front page labels/initial dropdown
options1 = ['Select Report Type', 'Report A', 'Report B']
var1 = tk.StringVar(value=options1[0])

dropdown1 = CTkComboBox(root, variable=var1, values=options1, command=show_second_dropdown)
dropdown1.grid(column=0,row=0)

options2 = ["Option A", "Option B"]
var2 = tk.StringVar(value=options2[0])

second_dropdown = CTkComboBox(root, variable=var2, values=options2)

# report A widgets
timezone_label = CTkLabel(root, text = 'Timezone:', font=('Arial',15), text_color='#04033A')
timezoneDropdown = CTkComboBox(master=root, values=['Universal Time', 'Mountain Time', 'Pacific Time', 'Central Time', 'Eastern Time', 'European Central Time',
                                                    'Eastern Eurpoean Time','Eastern African Time','Near East Time','Pakistan Lahore Time','Bangladesh Standard Time',
                                                    'Vietnam Standard Time','China Taiwan Time','Japan Standard Time','Australia Eastern Time','Solomon Standard Time',
                                                    'New Zealand Standard Time','Midway Islands Time','Hawaii Standard Time','Alaska Standard Time',
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


# report b widgets
start_year_label = CTkLabel(root, text='Choose Start and End year:')
start_year_dropdown = CTkComboBox(root, values=['2000', '2000', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2000', '2010','2011',
                                                '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023',
                                                '2024', '2025', '2027', '2028', '2029', '2030'])
end_year_dropdown = CTkComboBox(root, values=['2000', '2000', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2000', '2010','2011',
                                              '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023',
                                              '2024', '2025', '2027', '2028', '2029', '2030'])
state_label = CTkLabel(root, text='Choose State of Unit: ')
state_dropdown = CTkComboBox(root, values=['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                                           'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                                           'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                                           'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                                           'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'])

state_options = {
    'AL': [
    'Sand Point (1)',
    'Dillingham (109)',
    'Green Lake (313)',
    'Solomon Gulch (390)',
    'Tok (406)',
    'Craig (AK) (421)',
    'Hydaburg (423)',
    'Utility Plants Section (50308)',
    'Eielson AFB Central Heat & Power Plant (50392)',
    'University of Alaska Fairbanks (50711)',
    'Tesoro Kenai Cogeneration Plant (52184)',
    'Westward Seafoods (54305)',
    'Unisea G 2 (54422)',
    'Fort Greely Power Plant (54834)',
    'Nikiski Combined Cycle (55966)',
    'False Island (56146)',
    'Viking (56147)',
    'South Fork (56265)',
    'Delta Power (56325)',
    'Kasidaya Creek Hydro (56542)',
    'Southcentral Power Project (57036)',
    'Noatak (57051)',
    'Savoonga (57052)',
    'Alakanuk (57053)',
    'Upper Kalskag (57054)',
    'Stebbins (57055)',
    'Scammon Bay (57056)',
    'Quinhagak (57057)',
    'Pilot Station (57058)',
    'Koyuk (57059)',
    'Elim (57060)',
    'Gambell (57062)',
    'Shungnak (57063)',
    'Kotlik (57064)',
    'Kivalina (57065)',
    'Kasigluk (57066)',
    'Toksook Bay (57067)',
    'Lake Dorothy Hydroelectric Project (57085)',
    'Pillar Mountain Wind Project Microgrid (57187)',
    'Soldotna (57206)',
    'Battery Energy Storage System (57583)',
    'Eva Creek Wind (57935)',
    'TNSG South Plant (58117)',
    'TNSG North Plant (58278)',
    'JBER Landfill Gas Power Plant (58380)',
    'ESS Battery Microgrid (58405)',
    'Fire Island Wind (58425)',
    'Delta Wind Farm (58511)',
    'Whitman (58977)',
    'Allison Creek Hydro (58982)',
    'Eklutna Generation Station (58989)',
    'Hiilangaay Hydro (59037)',
    'Industrial Plant (59793)',
    'Ambler (60243)',
    'Marshall (60244)',
    'New Stuyahok (60245)',
    'Swampy Acres Microgrid (60250)',
    'Brevig Mission (60260)',
    'Flywheel Energy Storage System Microgrid (60563)',
    'Tyee Lake Hydroelectric Facility (61166)',
    'Klawock Power Generation Station (61684)',
    'Slana Generating Station (61685)',
    'Annex Creek (62)',
    'Eyak Service Center BESS (62714)',
    'Kodiak Microgrid (6281)',
    'Seldovia (6283)',
    'North Pole (6285)',
    'Fairbanks (6286)',
    'Healy (6288)',
    'Cooper Lake (6291)',
    'Bernice Lake (6292)',
    'International (6293)',
    'Unalakleet (6299)',
    'Gold Creek (63)',
    'Naknek (6301)',
    'Purple Lake (6302)',
    'Kotzebue Hybrid (6304)',
    'Glennallen (6305)',
    'Valdez (6306)',
    'Chevak (6311)',
    'Emmonak (6314)',
    'Hooper Bay (6319)',
    'Kiana (6323)',
    'Mountain Village (6329)',
    'Noorvik (6330)',
    'St Marys IC (6338)',
    'Selawik (6341)',
    'Shishmaref (6345)',
    'Togiak (6348)',
    'Lemon Creek (64)',
    'Salmon Creek 1 (65)',
    'McGrath (6555)',
    'George M Sullivan Generation Plant 2 (6559)',
    'Bethel (6566)',
    'Gustavus (65767)',
    'Beaver Falls (6580)',
    'Silvis (6581)',
    'Skagway (66)',
    'Yakutat (6637)',
    'Pelican (6702)',
    'Jarvis Street (6801)',
    'Haines (69)',
    'Swan Lake (70)',
    'Humpback Creek (7042)',
    'Terror Lake Microgrid (71)',
    'Centennial (7112)',
    'Chester Lake (7168)',
    'Northway (7169)',
    'Barrow (7173)',
    'Gwitchyaa Zhee (7174)',
    'Aniak (7182)',
    'Newhalen (7183)',
    'Auke Bay (7250)',
    'Bradley Lake (7367)',
    'Thorne Bay Plant (7414)',
    'Galena Electric Utility (7437)',
    'Angoon (7462)',
    'Hoonah (7463)',
    'Kake (7464)',
    'NSB Atqasuk Utility (7482)',
    'NSB Kaktovik Utility (7483)',
    'NSB Nuiqsut Utility (7484)',
    'NSB Point Hope Utility (7485)',
    'NSB Point Lay Utility (7486)',
    'NSB Anaktuvuk Pass (7487)',
    'NSB Wainwright Utility (7488)',
    'King Cove (7493)',
    'Hank Nikkels Plant 1 (75)',
    'Anchorage 1 (75)',
    'Dutch Harbor (7502)',
    'Unalaska Power Module (7503)',
    'Eklutna Hydro Project (77)',
    'Nymans Plant Microgrid (7723)',
    'Goat Lake Hydro (7751)',
    'Black Bear Lake (7752)',
    'Snettisham (78)',
    'Valdez Cogen (7841)',
    'Power Creek (7862)',
    'Orca (789)',
    'Aurora Energy LLC Chena (79)',
    'Ketchikan (84)',
    'S W Bailey (85)',
    'Snake River (90)',
    'Petersburg (91)',
    'Seward (AK) (92)',
    'Blue Lake Hydro (93)',
    'Wrangell (95)',
    'Beluga (96)'],
    'AK': [],
    'AZ': [],
    'AR': 
    'CA': 
    'CO': 
    'CT': 
    'DE':
    'FL':
    'GA':
    'HI':
    'ID':
    'IL':
    'IN':
    'IA': 
    'KS': 
    'KY': 
    'LA': 
    'ME': 
    'MD':
    'MA': 
    'MI': 
    'MN': 
    'MS': 
    'MO': 
    'MT': 
    'NE': 
    'NV': 
    'NH': 
    'NJ':
    'NM': 
    'NY': 
    'NC': 
    'ND': 
    'OH': 
    'OK': 
    'OR': 
    'PA': 
    'RI': 
    'SC':
    'SD': 
    'TN': 
    'TX': 
    'UT': 
    'VT': 
    'VA': 
    'WA': 
    'WV': 
    'WI':
    'WY':
}


# all other widgets
status_lbl = CTkLabel(root, text='', font=('Arial',15), text_color='#04033A')
title_lbl = CTkLabel(root, text='EIA Generation Data', font=('Arial',20, 'bold'), text_color='#04033A')



# grid- first page
output_file_button.grid(row=1, column=0)
output_file_label.grid(row=2, column=0)
title_lbl.grid(row=0, column=2)
status_lbl.grid(row=7,column=2) 

# grid- report A

# grid- report B
root.mainloop()