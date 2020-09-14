import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
import matplotlib.colors as colors
from geopy.geocoders import Nominatim
import vincent as v
v.core.initialize_notebook()
from folium import (plugins, FeatureGroup, Map, Circle, Marker,
                    LayerControl, Popup, CircleMarker, Vega)
from tslearn.clustering import TimeSeriesKMeans

def get_coordinates(address):    
    try:
        geolocator = Nominatim(user_agent="http")
        location = geolocator.geocode(address)
        return [location[-1][0], location[-1][1]]
    except:
        print(f'Oops! No coordinates found for: {address}')
        return [None, None]
def change_col_dt(df):
    new_df = df.T.copy()
    new_df.index =  pd.to_datetime(new_df.index)
    return new_df.T.copy()

def import_data_JHU():
    # url to the data 'Novel Coronavirus (COVID-19) Cases', provided by JHU CSSE
    url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'

    # confirmed cases and deaths worldwide for each country
    cases = pd.read_csv(url + 'time_series_covid19_confirmed_global.csv')
    deaths = pd.read_csv(url + 'time_series_covid19_deaths_global.csv')

    # we sum over Province/State for countries (US = Alabama, Alaska,..)
    cases = cases.groupby('Country/Region', axis=0).sum()
    deaths = deaths.groupby('Country/Region', axis=0).sum()
    #group Italy and San Marino:
    cases.loc['Italy'] = cases.loc['Italy'] + cases.loc['San Marino']
    cases.drop(['San Marino'],inplace=True)
    cases.rename(index={'United Kingdom': 'UK'}, inplace=True)
    deaths.loc['Italy'] = deaths.loc['Italy'] + deaths.loc['San Marino']
    deaths.drop(['San Marino'],inplace=True)
    deaths.rename(index={'United Kingdom': 'UK'}, inplace=True)

    # Some cleaning of the data:
    last_day = cases.columns[-1]
    cases.sort_values( [last_day], ascending=False,
                       axis=0, inplace=True)      # ordering by total number of latest point
    deaths = deaths.reindex(index=cases.index)    # same ordering as cases

    cases.index.name = None                       # delete the name of the index
    deaths.index.name = None

    # delete the following rows from the data
    to_del = ['Diamond Princess', 'MS Zaandam', 'Holy See', 'Western Sahara']
    cases = cases.drop(to_del)
    deaths = deaths.drop(to_del)

    new_df = deaths.iloc[:,2:].T.copy()
    new_df.index =  pd.to_datetime(new_df.index)
    deaths = new_df.T.copy()

    new_df = cases.iloc[:,2:].T.copy()
    new_df.index =  pd.to_datetime(new_df.index)
    cases = new_df.T.copy()

    cases.to_csv('data/cases.csv')
    deaths.to_csv('data/deaths.csv')
    return True

# uncomment this line to import the latest data
import_data_JHU()
cases = pd.read_csv('data/cases.csv', index_col=0)
deaths = pd.read_csv('data/deaths.csv', index_col=0)
cases = change_col_dt(cases)
deaths = change_col_dt(deaths)
last_day = cases.columns[-1]
print('The data is from ' +
      str(pd.to_datetime(cases.columns[-1]).strftime('%d/%m/%Y')) + '.')

population_2018 = pd.read_csv('data/population_2018_2.csv', index_col=0)
population_2018.rename(index={'United Kingdom': 'UK'}, inplace=True)
population_2018.loc['Italy'] = population_2018.loc['Italy'] + population_2018.loc['San Marino']
population_2018.drop('San Marino', inplace=True)
# confirmed cases for each 100k inhabitans

cases_pT =  cases / population_2018.loc[cases.index].values * 100000
deaths_pT = deaths / population_2018.loc[deaths.index].values * 100000
cases_pT.sort_values([last_day], ascending=False, axis=0, inplace=True)
cases_pT_new = cases_pT.diff(axis=1)
deaths_pT_new = deaths_pT.diff(axis=1)

# uncomment this to make the lattest plots, takes some while (coordinates):
json_files = {}
dic={}
for name in cases.index:
    coord = get_coordinates(name)
    dic[name] = coord
    df = cases_pT_new.T[name].to_frame(name='cases')
    df['deaths*10'] = deaths_pT_new.T[name]*10
    line = v.Line(df.rolling(7, center=True, min_periods=1).mean())
    line.axis_titles(x='Date', y='per 100k inhabitants')
    line.legend(name)
    line.width = 350
    line.height = 150
    json_files[name] = str(line.to_json())
df = pd.DataFrame(dic,index=['lat','long']).T
df2 = pd.DataFrame(json_files,index=['json']).T
df['json'] = df2
coord = df.copy()
coord.to_csv('data/coord.csv')

coord = pd.read_csv('data/coord.csv', index_col=0)