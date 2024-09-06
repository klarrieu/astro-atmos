"""
Get weather forecasts for a location in the United States from National Weather Service (NWS).
"""
import requests
import pandas as pd


def c_to_f(temp):
    """
    Convert degrees Celsius to Fahrenheit
    """
    return 9/5 * temp + 32


def kmph_to_mph(speed):
    """
    Convert km/hr to mph
    """
    return 0.6213712 * speed


class NWS_met:
    def __init__(self, lat, lon, temp_unit='F', wind_unit='mph'):
        """
        Class for retrieving NWS weather forecast for a given location

        Args:
            lat (float): forecast latitude (decimal degrees)
            lon (float): forecast longitude (decimal degrees)
            temp_unit (str): 'F' or 'C', temperature unit
            wind_unit (str): 'mph' or 'km/hr', wind speed unit
        """
        self.lat = lat
        self.lon = lon
        self.temp_unit = temp_unit
        self.wind_unit = wind_unit

    @property
    def temp_unit(self):
        return self._temp_unit

    @temp_unit.setter
    def temp_unit(self, temp_unit):
        if temp_unit not in ['C', 'F']:
            raise ValueError(f'Invalid temp_unit: {temp_unit}. Must be "C" or "F".')
        self._temp_unit = temp_unit

    @property
    def wind_unit(self):
        return self._wind_unit

    @wind_unit.setter
    def wind_unit(self, wind_unit):
        if wind_unit not in ['km/hr', 'mph']:
            raise ValueError(f'Invalid wind_unit: {wind_unit}. Must be "km/hr" or "mph".')
        self._wind_unit = wind_unit

    def get_nws_met(self):
        """
        Get forecast from NWS at given location
        e.g. temperature, dewpoint, skyCover, probabilityOfPrecipitation

        Returns:
            nws_data (dict): dict of pandas.DataFrame objects for each forecast parameter
        """
        # TODO: localize times to self.timezone? Should be local time for location already though...
        # get gridpoint forecast endpoint
        res = requests.get(f'https://api.weather.gov/points/{self.lat},{self.lon}/')
        properties = res.json()['properties']
        nws_forecast_endpoint = properties['forecastGridData']
        nws_timezone = properties['timeZone']
        # call gridpoint forecast
        res = requests.get(nws_forecast_endpoint)
        nws_forecast = res.json()
        # parse variables we care about
        pars = {'cloud_cover': 'skyCover',
                'dewpoint': 'dewpoint',
                'temperature': 'temperature',
                'precip': 'probabilityOfPrecipitation',
                'wind_speed': 'windSpeed',
                'wind_gust': 'windGust',
                'wind_dir': 'windDirection'}
        nws_data = {par: [] for par in pars.keys()}
        for par, nws_name in pars.items():
            ts = nws_forecast['properties'][nws_name]
            unit = ts['uom']
            ts = ts['values']
            df = pd.DataFrame(ts)
            df[['time', 'duration']] = df.validTime.str.split('/', expand=True)
            df['time'] = pd.to_datetime(df['time'])
            df['duration'] = pd.to_timedelta(df['duration'])
            df.index = df['time']
            df.index = df.index.tz_convert(nws_timezone)
            df['time'] = df.index
            nws_data[par] = df

        if self.temp_unit == 'F':
            # convert C to F
            nws_data['temperature'].value = c_to_f(nws_data['temperature'].value)
            nws_data['dewpoint'].value = c_to_f(nws_data['dewpoint'].value)
        if self.wind_unit == 'mph':
            # convert km/hr to mph
            nws_data['wind_speed'].value = kmph_to_mph(nws_data['wind_speed'].value)
            nws_data['wind_gust'].value = kmph_to_mph(nws_data['wind_gust'].value)

        return nws_data
