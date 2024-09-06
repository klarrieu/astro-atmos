"""
Handles parsing and caching of RDPS astronomy model grids (seeing and transparency).
"""
import io
import os
import pandas as pd
import xarray as xr
import requests
import urllib.request
from bs4 import BeautifulSoup


class RDPS_astro:
    def __init__(self, forecast_dir):
        """
        Class to handle parsing and caching of RDPS astronomy model grids (seeing and transparency).

        Attributes:
            forecast_dir (str): directory to cache forecast grids
        """
        self.astro_endpoint = 'https://dd.alpha.meteo.gc.ca/model_gem_regional/astronomy/grib2/'
        self.forecast_dir = forecast_dir
        self.seeing_ds = None
        self.trsp_ds = None
        return

    def get_latest_RDPS_astro(self):
        '''
        Get latest RDPS run for astronomy parameters (seeing, transparency). This will download the most recent model
        run if not already cached. Data are loaded into xarray datasets self.seeing_ds and self.trsp_ds.
        '''
        # TODO: implement updating procedure using AMQP: https://eccc-msc.github.io/open-data/msc-datamart/amqp_en/
        print('Getting astro data...')
        res = requests.get(self.astro_endpoint)
        # parse file directory to table
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.find_all('pre')[0].text.split('\n')
        df = pd.read_csv(io.StringIO(soup.find_all('pre')[0].text), sep=r"[ ]{2,}", engine='python')
        df = df[['Name', 'Last modified']]
        df['Last modified'] = pd.to_datetime(df['Last modified'])

        # get most recent run and go to that endpoint
        most_recent_run = df[df['Last modified'] == df['Last modified'].max()]['Name'].values[0]
        self.astro_run_endpoint = self.astro_endpoint + most_recent_run
        res = requests.get(self.astro_run_endpoint)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('pre')[0].find_all('a')
        links = [a.get('href') for a in links if a.get('href').endswith('.grib2')]
        for i, link in enumerate(links):
            url = self.astro_run_endpoint + link
            out_filename = f'./forecast_maps/{link}'
            if os.path.exists(out_filename):
                continue
            print(f'{(i + 1) / len(links) * 100:.0f}%')
            urllib.request.urlretrieve(url, filename=out_filename)
        for f in os.listdir(self.forecast_dir):
            if f.split('.')[0] + '.grib2' not in links:
                os.remove(os.path.join(self.forecast_dir, f))
        print('Making xr datasets...')
        seeing_ds = xr.concat(
            [xr.load_dataset(os.path.join(self.forecast_dir, f), engine="cfgrib") for f in os.listdir(self.forecast_dir)
             if f.endswith('.grib2') and '_SEEI_' in f],
            dim='step').rename({'unknown': 'seeing'})
        self.seeing_ds = self.parse_grib_ds(seeing_ds)

        trsp_ds = xr.concat(
            [xr.load_dataset(os.path.join(self.forecast_dir, f), engine="cfgrib") for f in os.listdir(self.forecast_dir)
             if f.endswith('.grib2') and '_TRSP_' in f],
            dim='step').rename({'unknown': 'transparency'})
        self.trsp_ds = self.parse_grib_ds(trsp_ds)

        return self.seeing_ds, self.trsp_ds

    def parse_grib_ds(self, ds):
        """
        Parse grib2 dataset in xarray from the RDPS astro model. Calculates time from model start time and timestep, and
        converts longitude from (0, 360) to (-180, +180) range

        Args:
            ds (xarray.Dataset): xarray dataset from RDPS atro model

        Returns:
            ds (xarray.Dataset): parsed xarray dataset
        """
        ds['time'] = ds.time + ds.step
        ds = ds.sortby('time')
        ds.coords['longitude'] = (ds.coords['longitude'] + 180) % 360 - 180
        return ds
