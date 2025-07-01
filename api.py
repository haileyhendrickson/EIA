import requests
import pandas as pd

try:
    url = 'https://api.eia.gov/v2/natural-gas/pri/fut/data/?' # main URL for natural gas, prices for a futures exchange
    params = {'api_key': 'h6SzHD7npQ0r1YVfC7HZHEMu7LZ74yx2m9EcbSHD',
                'frequency' : 'monthly', # like interval
                'data[0]' : 'value', # specifying what columns I want?
                # 'facets[series][]' : 'RNGWHHD', # i think this one specifies henry hub or something 
                'start' : '2001-01', # start date 
                'end' : '2025-02', # end date
                'offset' : '0', # if I want to skip any rows. try offsetting by 5000 rows when I need large chunks
                'length' : '5000' # how many rows to give back
            }

    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data['response']['data'])
    print(df.info())
except Exception as e:
    print(f'error: {e}')


# try:
#     url = 'https://api.eia.gov/v2/natrual-gas/data'
#     API_route = 'natural-gas/pri/fut'

#     params = {'api_key': 'h6SzHD7npQ0r1YVfC7HZHEMu7LZ74yx2m9EcbSHD'
#             }

#     response = requests.get(url, params=params)
#     data = response.json()

#     df = pd.DataFrame(data['response']['data'])
#     print(df.head())
# except Exception as e:
#     print(f'error: {e}')

# params = {'frequency': 'monthly', # monthly, weekly, etc. I think justin wants monthly
#           'start': '2024-01', # yyyy-mm format. start month
#           'end': '2024-12', # end month
#           'api_key' : 'h6SzHD7npQ0r1YVfC7HZHEMu7LZ74yx2m9EcbSHD'
#           }

# full_url = f'{url}/{API_route}/data/?{params}api_key={api_key}'