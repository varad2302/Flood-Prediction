import pandas as pd
import numpy as np


# Preprocessing of multiple stage height datasets
def stage_preprocessing(*args):
    final = pd.DataFrame()
    for x in args:
        data = pd.read_csv(x, encoding='UTF-8')
        data.iloc[:, 1] = data.iloc[:, 1].apply(pd.to_numeric, errors='coerce')
        data['Date'] = pd.to_datetime(data['Date']).dt.date
        data['Date'] = pd.to_datetime(data['Date'])
        final = final.append(data)
    final = final.groupby('Date').mean()
    final.interpolate(method='time', inplace=True)      # Removes missing/null values by interpolation
    final = final.round(2)
    print("Any null values left? : ", final.isna().values.any())
    return final


# Meteorological data is acquired from multiple datasets and averaged to give average weather conditions over watershed
# Preprocessing of Iowa Mesonet Datasets
def mesonet_preprocessing(*args):
    final = pd.DataFrame()
    for x in args:
        data = pd.read_csv(x, encoding='UTF-8')
        data = data.iloc[:, [1, 2, 3, 6, 7, 8]].copy()
        data['day'] = pd.to_datetime(data['day']).dt.date
        data['day'] = pd.to_datetime(data['day'])
        data.rename({'day': 'Date', 'max_temp_f': 'MaxTemp', 'min_temp_f': 'MinTemp',
                     'precip_in': 'Precip', 'avg_wind_drct': 'WindDir', 'HourlyWindGustSpeed': 'GustSpeed',
                     'avg_wind_speed_kts': 'WindSpeed'}, axis='columns', inplace=True)
        # print(data[['Snowfall', 'SnowDepth']].head(-10))
        data.iloc[:, 1:] = data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        data['Temp'] = data[['MaxTemp', 'MinTemp']].mean(axis=1)        # Mean daily temperature is calculated from min and max temperatures
        data.drop(['MaxTemp', 'MinTemp'], axis=1, inplace=True)
        final = final.append(data)
    final = final.groupby('Date').mean()
    final.interpolate(method='time', inplace=True)          # Removes missing/null values by interpolation
    final = final.round(2)
    print("Any null values left? : ", final.isna().values.any())
    return final


# Preprocessing of NCDC Local Climate Data
def lcd_preprocessing(*args):
    final = pd.DataFrame()
    for x in args:
        data = pd.read_csv(x, encoding='UTF-8')
        print(len(data.index))
        data = data.iloc[:, [1, 41, 42, 43, 48, 49, 51, 52, 53, 54, 55, 56]].copy()
        data['DATE'] = pd.to_datetime(data['DATE']).dt.date
        data["DATE"] = pd.to_datetime(data['DATE'])
        data.rename({'DATE': 'Date', 'HourlyAltimeterSetting': 'Altimeter', 'HourlyDewPointTemperature': 'DPTemp',
                     'HourlyDryBulbTemperature': 'Temperature', 'HourlyRelativeHumidity': 'RelHumidity',
                     'HourlySeaLevelPressure': 'SeaLevelPressure', 'HourlyStationPressure': 'AtmPressure',
                     'HourlyVisibility': 'Visibility', 'HourlyWetBulbTemperature': 'WBTemp',
                     'HourlyWindDirection': 'WindDir', 'HourlyWindGustSpeed': 'GustSpeed',
                     'HourlyWindSpeed': 'WindSpeed'}, axis='columns', inplace=True)
        data.iloc[:, 1:] = data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        final = final.append(data)
    final = final.groupby('Date').mean()
    print(final.head())
    # final.set_index('DATE')
    final.interpolate(method='time', inplace=True).fillna(method='bfill')   # Removes missing/null values by interpolation
    print("Any null values left? : ", final.isna().values.any())
    return final


# Converts wind speed and direction to wind vectors with x and y components
def feature_engineering(data):
    df = data
    # date_time = pd.to_datetime(df.pop('Date'), format='%Y-%m-%d')
    ws = df.pop('WindSpeed')
    wdir = df.pop('WindDir') * np.pi / 180
    df['Wx'] = ws * np.cos(wdir)
    df['Wy'] = ws * np.sin(wdir)
    return df


def plot(data):
    df = data
    date_time = pd.to_datetime(df.pop('Date'), format='%Y-%m-%d')
    plot_cols = ['Precip', 'Temp', 'AtmPressure', 'Visibility', 'StageHeight']
    plot_features = df[plot_cols]
    plot_features.index = date_time
    _ = plot_features.plot(subplots=True)

    plot_features = df[plot_cols][480:700]
    plot_features.index = date_time[480:700]
    _ = plot_features.plot(subplots=True)

# Preprocessing data acquired from Cedar Rapids station from 1980-2020
CR = lcd_preprocessing("/content/Iowa/CR 1980.csv", "/content/Iowa/CR 1985.csv", "/content/Iowa/CR 1994.csv", "/content/Iowa/CR 2003.csv", "/content/Iowa/CR 2012.csv")
# Preprocessing data acquired from Des Moines station from 1980-2020
DM = lcd_preprocessing("/content/Iowa/DM 1980.csv", "/content/Iowa/DM 1989.csv", "/content/Iowa/DM 1998.csv", "/content/Iowa/DM 2007.csv", "/content/Iowa/DM 2016.csv")
# Preprocessing data acquired from Waterloo station from 1980-2020
WL = lcd_preprocessing("/content/Iowa/WL 1980.csv", "/content/Iowa/WL 1989.csv", "/content/Iowa/WL 1998.csv", "/content/Iowa/WL 2007.csv", "/content/Iowa/WL 2016.csv")

lcd = pd.concat((CR, DM, WL), axis=0)
lcd = lcd.groupby(['Date']).mean()    # Hourly records are converted to daily mean records
lcd.interpolate(method='time', inplace=True)

# Preprocessing daily maximum river stage data acquired for Cedar Rapids from USACE
stage = stage_preprocessing("E:/ML/FloodPrediction/Data/CedarStage.csv")

# Preprocessing data acquired from Mesonet station across the watershed from 1980-2020
mesonet = mesonet_preprocessing('Data/CedarRapidsClimate.csv', 'Data/DesMoinesClimate.csv', 'Data/IowaCityClimate.csv', 'Data/OtumwaClimate.csv', 'Data/WaterlooClimate.csv')

# stage.to_csv('E:/ML/FloodPrediction/Data/Stage2.csv')
# lcd.to_csv('E:/ML/FloodPrediction/Data/LCD.csv')
# mesonet.to_csv('Data/Mesonet.csv')

# lcd = pd.read_csv('Data/LCD.csv', parse_dates=['Date'], index_col=['Date'])
# mesonet = pd.read_csv('Data/Mesonet.csv', parse_dates=['Date'], index_col=['Date'])
# stage = pd.read_csv('Data/Stage.csv', parse_dates=['Date'], index_col=['Date'])

# Select required features from lcd and mesonet dataframes to form weather dataset
WeatherData = pd.concat([mesonet[['Precip', 'Temp', 'WindDir', 'WindSpeed']], lcd[['AtmPressure', 'RelHumidity', 'Visibility']], stage], axis=1)
data = feature_engineering(WeatherData)
data.to_csv('Data/WeatherDataVec.csv', index=False)

