import requests
import pandas as pd
import datetime
from datetime import datetime

startdate = input('Please enter start date: (yyyy-mm-dd) ')
enddate = input('Please enter end date: (yyyy-mm-dd) ') 
# find how many expected rows. one month = about 3000 rows.
startdate = datetime.strptime(startdate, '%Y-%m-%d').date() # formats it to work with datetime package
enddate = datetime.strptime(enddate, '%Y-%m-%d').date()
difference = enddate - startdate # counts days in between
days = difference.days # making a counter for my loop bc .days is readonly
totalrows = (days*24)*4 # 4 rows of data per hour
# setting up for pull
ba = 'PACE' # input('Please enter BA code:')
counter = 0
offset = 0
files = [] # empty list to store all files
df_list = [] # place to store rows
while totalrows > 0:
    try:
        url = 'https://api.eia.gov/v2/electricity/rto/region-data/data/?' # main URL for natural gas, prices for a futures exchange
        params = {'api_key': 'h6SzHD7npQ0r1YVfC7HZHEMu7LZ74yx2m9EcbSHD',
                    'frequency' : 'hourly', # like interval
                    'data[0]' : 'value', # specifying what columns I want?
                    'facets[respondent][]' : ba, # specifies balancing authority
                    'start' : f'{startdate}T00-07:00', # start date, in MST
                    'end' : f'{enddate}T23-07:00', # end date, in MST
                    'sort[0][column]' : 'period',
                    'sort[0][direction]' : 'asc',
                    'offset' : offset, # if I want to skip any rows. try offsetting by 5000 rows when I need large chunks OR pull chunks by month?
                    'length' : '5000' # how many rows to give back. almost 3000 rows for a month
                }

        response = requests.get(url, params=params)
        data = response.json()
        df = pd.DataFrame(data['response']['data'])
        df.to_csv(f'test{counter}.csv')
    except Exception as e:
        print(f'error: {e}')
    totalrows -=5000 # take off rows that just printed
    offset +=5000 # offsets so I can pull the next chunk of data next time
    files.append(f'test{counter}.csv') # adding files to list    
    counter +=1

for file in files: # if tabbed over, it cleans each pull before combining, but is bad at error handling
    df_list.append(pd.read_csv(file)) # adding individual rows to df.list

df_combined = pd.concat(df_list, ignore_index=True) # combining 30 day chunks
df_combined = df_combined.drop(columns=['Unnamed: 0', 'value-units', 'type', 'respondent-name']) # bc I'm dropping units, rename columns later
df_combined = pd.pivot_table(df_combined, values='value', index=['period','respondent','respondent-name'], columns='type-name') # breaking out LMP_TYPE columns, keeping the other indexed columns
df.rename(columns={'period':'Timestamp (MST)','respondent':'BA Code','Day-ahead demand forecast':'Demand Forecast (MWh)','Demand':'Demand (MWh)','Net generation':'Net Generation(MWh)','Total interchange':'Total Interchange (MWh)'},inplace=True)

df_combined.to_csv('testfinal.csv') # saving to one completed file