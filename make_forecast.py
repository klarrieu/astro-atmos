from configparser import ConfigParser
from astroatmos.forecast import Forecast
import tzlocal as tzl


def parse_forecast_location():
    """
    Parse `forecast_location.txt` file to get parameters for forecast location, display units, etc.

    Returns:
        tuple:
            - lat (float): forecast location latitude (decimal degrees)
            - lon (float): forecast location longitude (decimal degrees)
            - timezone (str, or pytz.timezone): forecast location timezone
            - elevation (float): forecast location elevation (m)
            - temp_unit (str): 'C' or 'F', temperature units
            - wind_unit (str): 'km/hr' or 'mph', wind units
    """
    config = ConfigParser()
    config.read('forecast_location.txt')
    lat = float(config.get('Location', 'lat'))
    lon = float(config.get('Location', 'lon'))
    timezone = config.get('Location', 'timezone') if config.has_option('Location', 'timezone') \
        else tzl.get_localzone_name()
    print(timezone)
    elevation = float(config.get('Location', 'elevation')) if config.has_option('Location', 'elevation') \
        else 0
    temp_unit = config.get('Units', 'temp_unit') if config.has_option('Units', 'temp_unit') else 'F'
    wind_unit = config.get('Units', 'wind_unit') if config.has_option('Units', 'wind_unit') else 'mph'
    return lat, lon, timezone, elevation, temp_unit, wind_unit

if __name__ == "__main__":
    # read forecast_location.txt
    lat, lon, timezone, elevation, temp_unit, wind_unit = parse_forecast_location()
    # generate forecast
    forecast = Forecast(temp_unit=temp_unit, wind_unit=wind_unit)
    forecast.forecast_location(lat, lon, timezone=timezone, elevation=elevation)
    forecast.plot_forecast()
