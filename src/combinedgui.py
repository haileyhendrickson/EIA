'''
This is a GUI program desined to pull 2 reports: Hourly Natural Gas Prices
and Electric Power Operations Generation, cleaned and organized into an excel spreadsheet.
'''
import os
import sys
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import filedialog, ttk

import pandas as pd
import requests

import openpyxl

from customtkinter import (CTk, CTkButton, CTkLabel, CTkComboBox, CTkEntry, set_appearance_mode)
from tkcalendar import Calendar

from state_units import state_options  # File containing list of all units, grouped by state

# FUNCTIONS, including backend for both report types and cleaning function
# Formats all numbers in called rows to have two decimal places
def format_excel_cells(file, sheet, min_col, max_col):
    '''
    This method formats the numerical values to two decimal places.
    '''
    wb = openpyxl.load_workbook(file)
    sheet = wb[sheet]
    for row in sheet.iter_rows(min_col=min_col, max_col=max_col, min_row=2):
        for cell in row:
            cell.number_format = '0.00'
    wb.save(file)

API_KEY = os.getenv('EIA_API_KEY', 'h6SzHD7npQ0r1YVfC7HZHEMu7LZ74yx2m9EcbSHD')
# Natural Gas Prices Code
def natural_gas_report(startdate, enddate, timezone):
    '''
    This method pulls the EIA Natural Gas Report and cleans it mildly.
    '''
    map = {  # Finds UTC difference and associated time code, based on 24 major timezones
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
    }

    hours, timecode, operand = map.get((timezone), ('unknown'))
    ba=ba_var.get()

    # Finding how many expected rows. One month = about 3000 rows.
    startdate = datetime.strptime(startdate, '%m/%d/%y').date()  # Formats to work with datetime
    enddate = datetime.strptime(enddate, '%m/%d/%y').date()
    if operand == '+':
        enddate = enddate + timedelta(days=1)  # Adding one day to pull so it gets full last day
        startdate = startdate - timedelta(days=1)
    else:
        enddate = enddate + timedelta(days=2)  # Adding two days to pull so it gets full last day
    difference = enddate - startdate
    days = difference.days
    totalrows = (days*24)*4  # 4 Rows of data per hour

    # Setting up for data pull
    counter = 0
    offset = 0
    files = []  # To store all files
    df_list = []  # Place to store rows
    timestamp = datetime.now()  # Using for filename
    timestamp = timestamp.strftime('%m-%d-%Y %H%M')
    while totalrows > 0:
        try:
            url = 'https://api.eia.gov/v2/electricity/rto/region-data/data/?'
            params = {'api_key': API_KEY,
                        'frequency' : 'hourly',
                        'data[0]' : 'value',  # Specifying what columns to include
                        'facets[respondent][]' : ba,  # Specifies balancing authority
                        'start' : f'{startdate}T00',
                        'end' : f'{enddate}T00',
                        'sort[0][column]' : 'period',
                        'sort[0][direction]' : 'asc',
                        'offset' : offset,  # Using to skip rows for pulls larger than 5000 rows
                        'length' : '5000'
                    }

            response = requests.get(url, params=params)
            data = response.json()
            df = pd.DataFrame(data['response']['data'])
            # Fixing timezone
            hours = int(hours)
            df['period'] = pd.to_datetime(df['period'])  # Changing period column to datetime
            if operand == '+':  # Shifting hours forward or back depending on difference from UTC
                df['period'] = df['period'] + timedelta(hours=hours)
            else:
                df['period'] = df['period'] - timedelta(hours=hours)
            df.to_csv(f'test{counter}.csv')  # Saving chunks to csvs to combine later
        except Exception as e:
            print(f'error: {e}')
            status_lbl.configure(text='Error. Try again.')  # Updating label if API pull fails
            root.update()
        totalrows -= 5000  # Take off rows that just printed
        offset += 5000  # Offsets so I can pull the next chunk of data next time
        files.append(f'test{counter}.csv')  # Adding pulled files to list
        counter +=1

    for file in files:
        df_list.append(pd.read_csv(file))  # Adding individual rows to df.list

    df_combined = pd.concat(df_list, ignore_index=True)
    df_combined = df_combined.drop(columns=['Unnamed: 0', 'value-units', 'type',
                                            'respondent-name'])
    df_combined.rename(columns={'period':f'Timestamp {timecode}','respondent':'BA Code'},
                                inplace=True)
    # Breaking out generation columns, keeping the other indexed columns
    df_combined = pd.pivot_table(df_combined, values='value',
                                 index=[f'Timestamp {timecode}','BA Code'],
                                 columns='type-name').reset_index()
    df_combined.rename(columns={'Day-ahead demand forecast':'Demand Forecast (MWh)',
                                'Demand':'Demand (MWh)','Net generation':'Net Generation (MWh)',
                                'Total interchange':'Total Interchange (MWh)'},inplace=True)

    if operand =='+':  # Trimming end by hours, trimming start by 24-hrs
        df_combined = df_combined.iloc[(24-hours):-(hours+1)]
    else:
        df_combined = df_combined.iloc[hours:-(25-hours)]

    df_combined.to_excel(f'{output_file_path}/{ba} Data {timestamp}.xlsx', index=False)

    if getattr(sys, 'frozen', False):  # Finding path to GUI location and deleting csv file chunks
        application_path = os.path.dirname(sys.executable)
    for csv in files:
        filepath = os.path.join(application_path, csv)
        os.remove(filepath)

    status_lbl.configure(text='Finished!')  # Updating status label
    root.update()

# Electric Power Operations Code
def electric_power_operations_report(startyr, endyr):
    '''
    This method pulls the EIA Electric Power Operations report and cleans it slightly.
    '''
    try:
        unit_count = unit_count_var.get()
        startyr = int(startyr)
        endyr = int(endyr)
        total_years =  (endyr - startyr) + 1
        totalrows = (total_years *10)*unit_count  # Allowing for 10 rows per year per unit
        # Setting up for pull
        units = units_var.get()
        units = tuple(units.split(","))
        print(units)
        unit_display_names = unit_display_names_var.get()
        counter = 0
        offset = 0
        files = []  # To store all files
        df_list = []  # Place to store rows
        timestamp = datetime.now()
        timestamp = timestamp.strftime('%m-%d-%Y %H%M')
        while totalrows > 0:
            try:
                url = 'https://api.eia.gov/v2/electricity/facility-fuel/data/?'
                params = {'api_key': API_KEY,
                            'frequency': 'annual',
                            'data[0]': 'gross-generation',
                            'data[1]': 'generation',
                            'facets[plantCode][]': units,
                            'start': startyr,
                            'end': endyr,
                            'sort[0][column]': 'period',
                            'sort[0][direction]': 'asc',
                            'offset': offset,
                            'length': 5000
                        }
                print(f'url: {url}, params: {params}')
                response = requests.get(url, params=params, timeout=100000)
                data = response.json()
                df = pd.DataFrame(data['response']['data'])
                df.to_csv(f'test{counter}.csv')
            except Exception as e:
                print(f'error: {e}')
                status_lbl.configure(text='Error with Inputs. Check Dates and Unit Selections.')
                root.update()
            totalrows -= 5000  # Take off rows that just printed
            offset += 5000  # Offsets so I can pull the next chunk of data next time
            files.append(f'test{counter}.csv')
            counter += 1

        if counter > 1:  # Combining files if there is more than one to be combined
            for file in files:
                df_list.append(pd.read_csv(file))
            df_combined = pd.concat(df_list, ignore_index=True)
        else:
            df_combined = pd.read_csv('test0.csv')

        drop_cols = ['Unnamed: 0', 'stateDescription', 'fuel2002', 'primeMover',
                    'gross-generation-units', 'generation-units']
        drop_cols = [col for col in drop_cols if col in df_combined.columns]
        df_combined = df_combined.drop(columns=drop_cols)
        df_combined = df_combined.drop_duplicates()  # Dropping duplicate rows
        df_combined = df_combined.rename(columns={'period':'Year',
                                                'gross-generation':'gross generation (MWh)',
                                                'generation':'generation (MWh)'})
        df_combined = df_combined.sort_values(by='plantName')
        filename = f'{output_file_path}/{unit_display_names} {startyr}-{endyr}.xlsx'
    except NameError as e:
        print(f'Error: {e}')
        status_lbl.configure(text='Please Select an output path')
        root.update()
    df_combined.to_excel(filename, index=False)
    format_excel_cells(filename, 'Sheet1', 6, 7)
    # Finding path to GUI location and deleting csv file chunks
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    for csv in files:
        filepath = os.path.join(application_path, csv)
        os.remove(filepath)
    status_lbl.configure(text='Finished!')
    root.update()

# Tkinter program
root = CTk()
root.geometry('800x600')
set_appearance_mode('light')
report_var=tk.StringVar()
ba_var=tk.StringVar()  # Needed for natural gas report
units_var=tk.StringVar()  # Needed for electric power operations report
startyr_var=tk.IntVar()
endyr_var=tk.IntVar()
unit_count_var=tk.IntVar()
codes_var=tk.StringVar()
unit_name_var=tk.StringVar()

# FUNCTIONS
# Front page functions
def select_output_file():
    '''
    For selecting excel output file path.
    '''
    global output_file_path
    directory = filedialog.askdirectory(title='Select output directory')
    if directory:
        output_file_path = directory
        output_file_label.configure(text=directory)  # Displaying file path
    else:
        output_file_label.configure(text='No directory selected yet')  # If submitting w/o filepath

def submit():
    '''
    After user gives all inputs, runs all of the backend code, depending on report type.
    '''
    report = report_var.get()
    if report == 'Natural Gas Prices':
        timezone=timezoneDropdown.get()
        natural_gas_report(startdate, enddate, timezone)
    if report == 'Electric Power Operations':
        # Filter out state names and get units
        selected_iids = treeview.selection()
        unit_names = [treeview.item(iid)['text'] for iid in selected_iids]
        print(unit_names)
        actual_units = []
        for unit_name in unit_names:
            if len(treeview.selection()) > 0:
                children = treeview.get_children(treeview.selection()[0])
            if not children and '(' in unit_name:
                actual_units.append(unit_name)

        # Extract codes and names
        codes = []
        unit_display_names = []
        for unit in actual_units:
            if '(' in unit:
                code = unit.split('(')[-1].strip(')')
                codes.append(code)
                name = unit.split('(')[0]
                unit_display_names.append(name)

        unit_display_names_var.set(unit_display_names)
        units = ",".join(codes)  # Joining codes with a comma
        units_var.set(units)
        unit_count = len(units)
        unit_count_var.set(unit_count)
        startyr = start_year_dropdown.get()
        endyr = end_year_dropdown.get()
        status_lbl.configure(text='Running...')
        root.update()
        electric_power_operations_report(startyr, endyr)

def show_second_dropdown(choice):
    '''
    This method changes the widgets on the GUI to match up with the desired report type inputs.
    '''
    report_var.set(choice)  # Creating a variable to use later
    if choice == 'Natural Gas Prices':
        title_lbl.configure(text='Natural Gas Prices Report')
        root.update()
        # Forget old labels
        start_year_label.grid_forget()
        start_year_dropdown.grid_forget()
        end_year_dropdown.grid_forget()
        treeview.grid_forget()
        scrollbar.grid_forget()

        # Natural Gas labels here
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

    if choice == 'Electric Power Operations':
        title_lbl.configure(text='Electric Power Operations Report')
        root.update()
        # Forget old labels
        ba_label.grid_forget()
        ba_entry.grid_forget()
        timezone_label.grid_forget()
        timezoneDropdown.grid_forget()
        cal.grid_forget()
        chooseStartDate.grid_forget()
        chooseEndDate.grid_forget()
        startdate_label.grid_forget()
        enddate_label.grid_forget()

        # Electric Power Operations labels here
        start_year_label.grid(row=3,column=0)
        start_year_dropdown.grid(row=4,column=0)
        end_year_dropdown.grid(row=5,column=0)
        sub_btn.grid(row=6,column=0)
        status_lbl.grid(row=7,column=0)
        treeview.grid(row=6,column=2, sticky='nsew')
        scrollbar.grid(row=6,column=3, sticky='ns')


# Natural Gas Report widget functions
def find_start_date():
    '''
    For selecting the start date.
    '''
    global startdate
    startdate = cal.get_date()
    startdate_label.configure(text=f'Start date: {startdate}')

def find_end_date():
    '''
    For selecting the end date
    '''
    global enddate
    enddate = cal.get_date()
    enddate_label.configure(text=f'End date: {enddate}')

# Electric Power Operations Report widget functions
def get_unit_names():
    '''
    IDK, this method is supposed to help me get the actual unit names
    '''
    selected_iids = treeview.selection()
    selected_unit_names = [treeview.item(iid)['text'] for iid in selected_iids]
    return selected_unit_names

def on_row_click(event):
    '''
    This method will help multi-unit selection more intuitive. Users can just click, instead of
    holding the CTRL button to select multiple.
    '''
    item = treeview.identify_row(event.y)
    if item:
        children = treeview.get_children(item)
        if children:
            return
        else:
            global selected_units
            if item in selected_units:
                selected_units.remove(item)
                treeview.selection_remove(item)
            else:
                selected_units.add(item)
                treeview.selection_add(item)
            treeview.selection_set(list(selected_units))
            return 'break'


# WIDGETS
# First page widgets
options1 = ['Select Report Type', 'Natural Gas Prices', 'Electric Power Operations']
var1 = tk.StringVar(value=options1[0])
dropdown1 = CTkComboBox(root, variable=var1, values=options1, command=show_second_dropdown,
                        font=('Arial',20))
dropdown1.grid(column=0,row=0)
output_file_button = CTkButton(root, text='Select Output File Path', command=select_output_file,
                               corner_radius=32,fg_color='#162157', hover_color='#6D7DCF')
output_file_label = CTkLabel(root, text='No path selected', font=('Arial',15),
                             text_color='#04033A')
title_lbl = CTkLabel(root, text='EIA Generation Data', font=('Arial',25,'bold'),
                     text_color='#04033A')

# Natural Gas widgets
timezone_label = CTkLabel(root, text = 'Timezone:', font=('Arial',20), text_color='#04033A')
timezoneDropdown = CTkComboBox(master=root, values=['Universal Time', 'Mountain Time',
                               'Pacific Time', 'Central Time', 'Eastern Time',
                               'European Central Time', 'Eastern Eurpoean Time',
                               'Eastern African Time','Near East Time','Pakistan Lahore Time',
                               'Bangladesh Standard Time','Vietnam Standard Time',
                               'China Taiwan Time','Japan Standard Time','Australia Eastern Time',
                               'Solomon Standard Time','New Zealand Standard Time',
                               'Midway Islands Time','Hawaii Standard Time',
                               'Alaska Standard Time','Puerto Rico and US Virtin Islands Time',
                               'Argentina Standard/Brazil Eastern Time','Central African Time'],
                               font=('Arial',20))
cal = Calendar(root, selectmode ='day', year=2024, month =1, day = 1, font=('Arial',10))
chooseStartDate = CTkButton(root, text='Choose Start Date', command=find_start_date,
                            corner_radius=26,fg_color='#162157', hover_color='#6D7DCF')
chooseEndDate = CTkButton(root, text='Choose End Date', command=find_end_date, corner_radius=26,
                          fg_color='#162157', hover_color='#6D7DCF')
startdate_label = CTkLabel(root, text= 'Start Date: ', font=('Arial',20), text_color='#04033A')
enddate_label = CTkLabel(root, text='End Date: ', font=('Arial',20), text_color='#04033A')
ba_label = CTkLabel(root, text='BA Code:', font=('Arial',20), text_color='#04033A')
ba_entry = CTkEntry(root, textvariable = ba_var, font=('Arial',20), text_color='#04033A')

# Electric Power Operations widgets
unit_display_names_var = tk.StringVar()
selected_units=set()
start_year_label = CTkLabel(root, text='Choose Start and End year:', font=('Arial',20))
start_year_dropdown = CTkComboBox(root, values=['2001', '2002', '2003', '2004', '2005', '2006',
                                                '2007', '2008', '2009', '2010','2011','2012',
                                                '2013', '2014', '2015', '2016', '2017', '2018',
                                                '2019', '2020', '2021', '2022', '2023', '2024',
                                                '2025'], font=('Arial',20))
end_year_dropdown = CTkComboBox(root, values=['2001', '2002', '2003', '2004', '2005', '2006',
                                              '2007', '2008', '2009', '2010','2011', '2012',
                                              '2013', '2014', '2015', '2016', '2017', '2018',
                                              '2019', '2020', '2021', '2022', '2023', '2024',
                                              '2025'], font=('Arial',20))

treeview = ttk.Treeview(root, selectmode='extended')
treeview.heading('#0', text='Select Units:', anchor='w')
style = ttk.Style()
style.configure('treeview.heading', font=(None,100))

for state in state_options:
    parent_id = treeview.insert('', tk.END, text=state, open=False)
    for unit in state_options[state]:
        treeview.insert(parent_id, tk.END, text=unit)

scrollbar = ttk.Scrollbar(root, orient='vertical', command=treeview.yview)
treeview.configure(yscrollcommand=scrollbar.set)
treeview.bind('<ButtonRelease-1>', on_row_click)

# All other widgets
status_lbl = CTkLabel(root, text='', font=('Arial',20), text_color='#04033A')
sub_btn=CTkButton(master=root,text = 'Submit', command = submit, corner_radius=32,
                  fg_color='#162157', hover_color='#6D7DCF')


# Grid- first page
output_file_button.grid(row=1, column=0)
output_file_label.grid(row=2, column=0)
title_lbl.grid(row=0, column=2)
status_lbl.grid(row=7,column=2)

root.mainloop()
