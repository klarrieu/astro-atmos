"""
Handles download and caching of RDPS meteorological model data.
"""
import os
import io
import requests
import urllib.request
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import xarray as xr


# TODO: get this fully working and allow option for grabbing met data from NWS or RDPS?

class RDPS_met:
    def __init__(self, met_dir):
        """
        Note: this is currently not fully implemented. Could be used to get met data for Canada,
        since currently we only use NWS.

        Args:
            met_dir (str): directory to cache RDPS meteorological model grids
        """
        self.met_endpoint = 'https://dd.weather.gc.ca/model_gem_regional/10km/grib2/'
        self.met_dir = met_dir
        self.met_data = {}

    def get_latest_RDPS_met(self):
        """Get latest RDPS run for meteorological parameters (cloud cover, RH, wind)"""
        print('Getting met data...')
        # files pulled from here: https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/
        # get endpoint for latest model run
        model_time_endpoints = [os.path.join(self.met_endpoint, f'{s:02d}/') for s in np.arange(0, 24, 6)]
        update_times = []
        model_dates = []
        for model_time_endpoint in model_time_endpoints:
            t0_endpoint = os.path.join(model_time_endpoint, '000/')
            res = requests.get(t0_endpoint)
            soup = BeautifulSoup(res.text, 'html.parser')
            df = pd.read_csv(io.StringIO(soup.find_all('pre')[0].text), sep=r"[ ]{2,}", engine='python')
            df = df[['Name', 'Last modified']]
            update_time = pd.to_datetime(df['Last modified'].iloc[0])
            model_date = df['Name'].iloc[0].split('_')[-2]
            update_times.append(update_time)
            model_dates.append(model_date)
        latest_endpoint = model_time_endpoints[np.argmax(update_times)]
        model_date = model_dates[np.argmax(update_times)]
        # get number of timestep endpoints (could potentially just assume its always 000-084?)
        res = requests.get(latest_endpoint)
        soup = BeautifulSoup(res.text, 'html.parser')
        timestep_endpoints = soup.find_all('pre')[0].find_all('a')[5:]
        timestep_endpoints = [os.path.join(latest_endpoint, a.get('href')) for a in timestep_endpoints]

        # variable/level names for each desired parameter
        par_strs = {'cloud_cover': 'TCDC_SFC_0',
                    #'rh': 'RH_TGL_2',
                    #'wind_speed': 'WIND_TGL_10',
                    #'wind_dir': 'WDIR_TGL_10'
                    }
        # populate with list of server paths of each timestep for each parameter
        met_paths = {'cloud_cover': [],
                     # 'rh': [],
                     # 'wind_speed': [],
                     # 'wind_dir': []
                     }
        for par, par_str in par_strs.items():
            met_paths[par] = [f'CMC_reg_{par_str}_ps10km_{model_date}_P{i:03d}.grib2'
                                for i in range(len(timestep_endpoints))]
        print('Downloading...')
        for par, files in met_paths.items():
            for i, f in enumerate(files):
                out_path = os.path.join(self.met_dir, f)
                if os.path.exists(out_path):
                    continue
                urllib.request.urlretrieve(os.path.join(latest_endpoint, f'{i:03d}', f), out_path)
        # remove old data files
        all_met_files = []
        for par, paths in met_paths.items():
            all_met_files.extend(paths)
        for f in os.listdir(self.met_dir):
            if f not in all_met_files:
                os.remove(os.path.join(self.met_dir, f))
        print('Making xr datasets...')
        for par in par_strs.keys():
            ds = xr.concat([xr.load_dataset(os.path.join(self.met_dir, f)) for f in met_paths[par]],
                           dim='step')
            var = list(ds.data_vars)[0]
            ds = ds.rename({var: par})
            ds['time'] = ds.time + ds.step
            ds = ds.sortby('time')
            self.met_data[par] = ds
        return self.met_data
