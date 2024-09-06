"""
Methods for generating and plotting a forecast.
"""
import os
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator
from matplotlib import dates as mdates
import datetime as dt
import pytz
from astroatmos.RDPS_astro import RDPS_astro
from astroatmos.RDPS_met import RDPS_met
from astroatmos.NWS_met import NWS_met
from astroatmos.bodies import get_body_alt, get_moon_illumination, moon_icons, sun_icon
from astroatmos.k_index import KIndex, bar_color
from scipy.signal import argrelextrema
from astroatmos.forecast_plot_style import astropy_mpl_style

plt.style.use(astropy_mpl_style)


class Forecast:
    """
    Class for downloading data from various sources, generating a forecast for a given location,
    and plotting a forecast.
    For downloading site data, see `self.get_latest_RDPS_astro`, `self.get_latest_RDPS_met`.
    For generating forecast at a location, see `self.forecast_location`.
    For plotting, see `self.plot_forecast`.

    Attributes:
        forecast_dir (str): directory to store RDPS model astro outputs
        met_dir (str): directory to store RDPS model meteorology outputs
        temp_unit (str): 'F' or 'C', indicating unit for temperature measurements
        wind_unit (str): 'mph' or 'km/hr', indicating unit for wind speed measurements
    """
    def __init__(self, forecast_dir='./forecast_maps', met_dir='./met_maps', temp_unit='F', wind_unit='mph'):
        self.forecast_dir = forecast_dir
        self.met_dir = met_dir
        self.forecast = None
        self.lat = None
        self.lon = None
        self.elevation = 0
        self.timezone = pytz.UTC
        self.temp_unit = temp_unit
        self.wind_unit = wind_unit

    @property
    def forecast_dir(self):
        return self._forecast_dir

    @forecast_dir.setter
    def forecast_dir(self, forecast_dir):
        if not os.path.exists(forecast_dir):
            os.mkdir(forecast_dir)
        self._forecast_dir = forecast_dir

    @property
    def met_dir(self):
        return self._met_dir

    @met_dir.setter
    def met_dir(self, met_dir):
        if not os.path.exists(met_dir):
            os.mkdir(met_dir)
        self._met_dir = met_dir

    @property
    def lat(self):
        return self._lat

    @lat.setter
    def lat(self, lat):
        if lat is None:
            self._lat = lat
            return
        if not -90 <= lat <= 90:
            raise ValueError(f'Invalid latitude entered: {lat}')
        self._lat = lat

    @property
    def lon(self):
        return self._lon

    @lon.setter
    def lon(self, lon):
        if lon is None:
            self._lon = lon
            return
        if not -180 <= lon <= 180:
            raise ValueError(f'Invalid longitude entered: {lon}')
        self._lon = lon

    @property
    def timezone(self):
        return self._timezone

    @timezone.setter
    def timezone(self, timezone):
        if isinstance(timezone, str):
            timezone = pytz.timezone(timezone)
        self._timezone = timezone

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

    @staticmethod
    def get_closest_grid_point(ds, lat, lon):
        """
        Get data at closest point on model grid to given lat/lon (calculated in EPSG 3857 Web Mercator) for xarray ds

        Args:
            ds (xarray.Dataset): xarray dataset with 'latitude' and 'longitude' coordinates
            lat (float): latitude of desired point
            lon (float): longitude of desired point
        Returns:
            xarray.Dataset: dataset subset to the grid cell closest to the given lat/lon point.
        """
        df = ds[['latitude', 'longitude']].to_dataframe().reset_index()
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']), crs="EPSG:4326")
        gdf = gdf.to_crs("EPSG:3857")
        point = gpd.GeoSeries(gpd.points_from_xy([lon], [lat], crs="EPSG:4326").to_crs("EPSG:3857")).iloc[0]
        closest_pt = gdf.loc[np.argmin(gdf.distance(point))]
        closest_dist = closest_pt.geometry.distance(point)
        closest_x, closest_y = closest_pt[['x', 'y']]
        point_ds = ds.sel(x=closest_x, y=closest_y)
        print(f'Closest grid point: ({point_ds.latitude:.4f}, {point_ds.longitude:.4f})\n'
              f'Distance: {closest_dist:.0f} m')
        return point_ds

    def forecast_location(self, lat, lon, timezone, elevation=0):
        # TODO: split into different files/classes for pulling data from each source
        """
        Generate forecast for a given location

        Args:
            lat (float): latitude of forecast location
            lon (float): longitude of forecast location
            timezone (str or pytz.timezone: timezone for location
            elevation (float): elevation of location in meters (default: 0)
        Returns:
            self.forecast (dict): Forecast data for the given location/timezone
        """
        print('Getting forecast for location...')
        self.lat = lat
        self.lon = lon
        self.timezone = timezone
        self.elevation = elevation

        # get RDPS astro data (seeing, transparency) and extract data at forecast location
        rdps = RDPS_astro(forecast_dir=self.forecast_dir)
        seeing_ds, trsp_ds = rdps.get_latest_RDPS_astro()
        # get closest point to desired coordinates
        point_seeing = self.get_closest_grid_point(seeing_ds, self.lat, self.lon)
        point_transparency = self.get_closest_grid_point(trsp_ds, self.lat, self.lon)

        # get met data from RDPS (need to finish this module to have as a met data source)
        #rdps_met = RDPS_met(met_dir=self.met_dir)
        #rdps_met_data = rdps_met.get_latest_RDPS_met()
        #point_cloud_cover = self.get_closest_grid_point(rdps_met_data['cloud_cover'], self.lat, self.lon)

        # get NWS forecast at location
        nws = NWS_met(lat=self.lat, lon=self.lon, temp_unit=self.temp_unit, wind_unit=self.wind_unit)
        nws_forecast = nws.get_nws_met()

        # total forecast
        self.forecast = {'lat': self.lat,
                         'lon': self.lon,
                         'timezone': self.timezone,
                         'elevation': self.elevation,
                         'seeing': point_seeing,
                         'transparency': point_transparency,
                         'cloud_cover': nws_forecast['cloud_cover'],
                         'kp': KIndex().get_pred(),
                         'temperature': nws_forecast['temperature'],
                         'dewpoint': nws_forecast['dewpoint'],
                         'precip': nws_forecast['precip'],
                         'wind_speed': nws_forecast['wind_speed'],
                         'wind_gust': nws_forecast['wind_gust'],
                         'wind_dir': nws_forecast['wind_dir']}
        return self.forecast

    def plot_forecast(self):
        """
        Plot forecast using matplotlib (must have already run self.forecast_location).
        """
        print('Plotting forecast...')
        if self.forecast is None:
            raise ValueError("Get forecast before plotting.")
        # TODO: add smoke, RH, wind direction?
        # get current datetime for indicating on plot
        now = dt.datetime.now(tz=self.timezone)
        # initialize figure
        fig, axes = plt.subplots(7, figsize=(14, 4), sharex=True)
        # TODO: currently assuming NW hemisphere
        fig.suptitle(fr'Stargazing Forecast for ({self.forecast["lat"]:.3f}$^{{\circ}}$N, '
                     fr'{abs(self.forecast["lon"]):.3f}$^{{\circ}}$W)'
                     f'\n{now.strftime("%B %-d, %Y")}')
        axes[0].set(xlim=(self.forecast['seeing'].time.values[0],
                          self.forecast['seeing'].time.values[-1] + np.timedelta64(1, 'h')))
        labelpad = 45

        # plot cloud cover and precip
        ax = axes[0]
        ax.bar(self.forecast['cloud_cover'].time, 1,
               color=plt.get_cmap('coolwarm')(self.forecast['cloud_cover'].value / 100),
               align='edge', width=self.forecast['cloud_cover'].duration, zorder=0)
        ax.bar(self.forecast['precip'].time, self.forecast['precip'].value / 100,
               color='grey', edgecolor='black', align='edge', width=self.forecast['precip'].duration, zorder=1)
        ax.set(ylim=(0, 1))
        ax.set_ylabel("Cloud cover", rotation=0, fontsize=10, labelpad=labelpad)
        ax.axvline(now, linestyle='dashed', color='black')
        ax.get_yaxis().set_ticks([])
        ax.grid(zorder=1)

        # plot transparency
        ax = axes[1]
        dts = self.forecast['transparency'].time.values.astype('datetime64[s]').astype(dt.datetime).tolist()
        dts = [self.timezone.fromutc(t) for t in dts]
        trsp_freq = np.median([t2 - t1 for t1, t2 in zip(dts[:-1], dts[1:])])
        ax.bar(dts, 1, color=plt.get_cmap('coolwarm_r')((self.forecast['transparency'].transparency - 1) / 4),
               align='edge', width=trsp_freq, zorder=0)
        ax.set(ylim=(0, 1))
        ax.set_ylabel("Transparency", rotation=0, fontsize=10, labelpad=labelpad)
        ax.axvline(now, linestyle='dashed', color='black')
        ax.get_yaxis().set_ticks([])
        ax.grid(zorder=1)

        # plot seeing
        ax = axes[2]
        dts = self.forecast['seeing'].time.values.astype('datetime64[s]').astype(dt.datetime).tolist()
        dts = [self.timezone.fromutc(t) for t in dts]
        seeing_freq = np.median([t2 - t1 for t1, t2 in zip(dts[:-1], dts[1:])])
        ax.bar(dts, 1, color=plt.get_cmap('coolwarm_r')((self.forecast['seeing'].seeing - 1) / 4),
               align='edge', width=seeing_freq, zorder=0)
        ax.set(ylim=(0, 1))
        ax.set_ylabel("Seeing", rotation=0, fontsize=10, labelpad=labelpad)
        ax.axvline(now, linestyle='dashed', color='black')
        ax.get_yaxis().set_ticks([])
        ax.grid(zorder=1)

        # plot kp
        ax = axes[3]
        k_ts = [self.timezone.fromutc(t) for t in self.forecast['kp'].index]
        k_vals = [float(k.split(' ')[0]) for k in self.forecast['kp'].values]
        k_storms = [k.split(' ')[1] if len(k.split(' ')) > 1 else '' for k in self.forecast['kp'].values]
        kp_freq = np.median([t2 - t1 for t1, t2 in zip(k_ts[:-1], k_ts[1:])])
        ax.bar(k_ts, k_vals, color=[bar_color(k) for k in k_vals],
               align='edge', edgecolor='black', width=kp_freq, zorder=0)
        ax.set(ylim=(0, 9))
        # overlay text with geomagnetic storm level if storm predicted
        for t, storm_level in zip(k_ts, k_storms):
            if storm_level and ax.get_xlim()[0] <= mdates.date2num(t) <= ax.get_xlim()[1]:
                ax.text(t + kp_freq / 4, 0.5, storm_level.replace('(', '').replace(')', ''), c='k')
        ax.set_ylabel('Kp', rotation=0, fontsize=10, labelpad=labelpad)
        ax.axvline(now, linestyle='dashed', color='black')
        ax.get_yaxis().set_ticks([])
        ax.grid(zorder=1)

        ######################################
        # get alt/az of sun/moon/planets
        times = np.linspace(self.forecast['seeing'].time.values[0].astype('float64'),
                            (self.forecast['seeing'].time.values[-1] + np.timedelta64(1, 'h')).astype('float64'),
                            1000).astype('datetime64[ns]')
        sun_alts = get_body_alt(times, self.lat, self.lon, self.elevation, 'sun')
        moon_alts = get_body_alt(times, self.lat, self.lon, self.elevation, 'moon')

        # plot sun/moon paths, day/night
        ax = axes[4]
        plot_times = [self.timezone.fromutc(t)
                      for t in times.astype('datetime64[s]').astype(dt.datetime).tolist()]
        # plot sun
        ax.plot(plot_times, sun_alts, color='gold', label='sun', zorder=1)
        sun_alt = get_body_alt(now, self.lat, self.lon, self.elevation, 'sun')
        ax.scatter([now], [sun_alt], marker=sun_icon,
                   s=200, zorder=2, c='gold')
        # plot moon
        ax.plot(plot_times, moon_alts, label='moon', zorder=1)
        moon_alt = get_body_alt(now, self.lat, self.lon, self.elevation, 'moon')
        moon_phase, moon_illum_percent = get_moon_illumination(now)
        ax.scatter([now], [moon_alt], marker=moon_icons[moon_phase],
                   s=200, zorder=2, edgecolors='black')
        # plot night/astronomical twilight
        ax.fill_between(plot_times, -90, 90, sun_alts < 0, color='0.5', zorder=0)
        ax.fill_between(plot_times, -90, 90, sun_alts < -18, color='0.2', zorder=0)
        # plot horizon
        ax.axhline(0, c='black', zorder=0)
        # format plot
        ax.set(ylim=(-90, 90))
        ax.set_ylabel('Altitude', rotation=0, fontsize=10, labelpad=labelpad)
        ax.axvline(now, linestyle='dashed', color='black', zorder=1)
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 3, 6, 9, 12, 15, 18, 21],
                                                      tz=self.timezone))
        ax.yaxis.set_major_locator(FixedLocator([-90, -45, 0, 45, 90]))
        ax.yaxis.set_major_formatter(lambda x, _: fr'{x}$^{{\circ}}$')
        ax.get_yaxis().set_ticks([])

        # plot temp/dewpoint
        # TODO: lowpass temp for calculating lows/highs
        ax = axes[5]
        temp = self.forecast['temperature']
        dewpoint = self.forecast['dewpoint']
        ax.plot(temp.time, temp.value, label='temperature')
        high_is = argrelextrema(temp.value.values, np.greater)[0]
        low_is = argrelextrema(temp.value.values, np.less)[0]
        for i in high_is:
            if temp.time.iloc[i] > now and mdates.date2num(temp.time.iloc[i].to_numpy()) < ax.get_xlim()[1]:
                ax.text(temp.time.iloc[i], temp.value.iloc[i] - 5,
                        fr'{temp.value.iloc[i]:.0f} $^{{\circ}}${self.temp_unit}',
                        ha='center', va='top', size='x-small', c='k')
        for i in low_is:
            if temp.time.iloc[i] > now and mdates.date2num(temp.time.iloc[i].to_numpy()) < ax.get_xlim()[1]:
                ax.text(temp.time.iloc[i], temp.value.iloc[i],
                        fr'{temp.value.iloc[i]:.0f}$^{{\circ}}${self.temp_unit}',
                        ha='center', va='bottom', size='x-small', c='k')
        ax.plot(dewpoint.time, dewpoint.value, label='dewpoint')
        ax.set_ylabel('Temp/Dewpoint', rotation=0, fontsize=10, labelpad=labelpad)
        ax.yaxis.set_major_formatter(lambda x, _: fr'{x}$^{{\circ}}$')
        ax.get_yaxis().set_ticks([])
        ax.axvline(now, linestyle='dashed', color='black', zorder=1)

        # plot wind/gusts
        ax = axes[6]
        wind_speed = self.forecast['wind_speed']
        wind_gust = self.forecast['wind_gust']
        wind_dir = self.forecast['wind_dir']
        ax.plot(wind_speed.time, wind_speed.value)
        ax.plot(wind_gust.time, wind_gust.value, c='crimson', linestyle='dotted')
        ax.set(ylim=(0, 1.1 * wind_gust.value.max()))
        ax.set_ylabel(f'Wind ({self.wind_unit})', rotation=0, fontsize=10, labelpad=labelpad - 5)
        ax.axvline(now, linestyle='dashed', color='black', zorder=1)

        # format figure
        def date_formatter(x, _):
            x = mdates.num2date(x, tz=self.timezone)
            if x.hour == 12:
                return f"{x.strftime('%-I')}\n{x.strftime('%a')}"
            elif x.hour == 0:
                return f"{x.strftime('%-I')}\n|"
            else:
                return x.strftime('%-I')
        ax.xaxis.set_major_formatter(date_formatter)
        fig.tight_layout()
        fig.subplots_adjust(hspace=0, top=0.85)
        fig.savefig('forecast.jpg', dpi=800)
        plt.show()
        return


if __name__ == "__main__":
    # enter location information
    lat, lon = 39.236, -120.026  # decimal degrees
    timezone = 'US/Pacific'  # timezone name reference: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    elevation = 1980.0  # meters (optional, default: 0)

    # make forecast
    forecast = Forecast()
    forecast.forecast_location(lat, lon, timezone=timezone, elevation=elevation)
    forecast.plot_forecast()
