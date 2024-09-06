"""
Gets Planetary k-index and geomagnetic storm levels from NOAA SWPC.
"""
import datetime as dt
import requests
import re
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use('bmh')


def g_level(k):
    """
    Get geomagnetic storm level (G-scale) and plot color corresponding to k-index value
    Args:
        k (float): Planetary k-index value

    Returns:
        tuple:
            - g_scale (str): Geomagnetic storm level, e.g. 'G1', 'G2', etc.
            - short_desc (str): Description of storm level, e.g. 'Minor', 'Moderate', etc.
            - color (str): hex color corresponding to NOAA SWPC color palette for storm level
    """
    if k < 4.5:
        g_scale = ''
        short_desc = 'None'
        color = '#92d050'
    elif k < 5.5:
        g_scale = 'G1'
        short_desc = 'Minor'
        color = '#f6eb14'
    elif k < 6.5:
        g_scale = 'G2'
        short_desc = 'Moderate'
        color = '#ffc800'
    elif k < 7.5:
        g_scale = 'G3'
        short_desc = 'Strong'
        color = '#ff9600'
    elif k < 9:
        g_scale = 'G4'
        short_desc = 'Severe'
        color = '#ff0000'
    else:
        g_scale = 'G5'
        short_desc = 'Extreme'
        color = '#c80000'
    return g_scale, short_desc, color


def bar_color(k):
    """
    Get color for bar plot of k-index corresponding to NOAA SWPC palette
    Args:
        k (float): planetary k-index value

    Returns:
        str: hex code for corresponding color
    """
    _, _, color = g_level(k)
    return color


class KIndex:
    def __init__(self):
        """
        Class for getting Planetary k-index data from NOAA SWPC
        """
        self.k_obs_endpoint = 'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
        self.k_pred_endpoint = 'https://services.swpc.noaa.gov/text/3-day-forecast.txt'
        self.k_data = None

    def run(self):
        """
        Get observed and predicted k-index values and make a plot of them
        """
        self.get_obs()
        self.get_pred()
        self.make_plot()
        storm, header, msg = self.make_summary()
        print(header, msg)
        return header, msg

    def get_obs(self):
        """
        Get observed k-index values

        Returns:
            pandas.DataFrame: table of observed k-index time series
        """
        res = requests.get(self.k_obs_endpoint)
        k_data = json.loads(res.text)
        k_data = pd.DataFrame(k_data[1:], columns=k_data[0])
        k_data['time'] = pd.to_datetime(k_data['time_tag'])
        k_data['Kp'] = pd.to_numeric(k_data['Kp'])
        k_data.index = k_data['time']
        k_data = k_data[k_data['time'] > k_data['time'].iloc[-1] - dt.timedelta(days=2)]
        self.k_data = k_data
        return k_data

    def get_pred(self):
        """
        Get predicted k-index values

        Returns:
            pandas.DataFrame: table of predicted k-index time series
        """
        res = requests.get(self.k_pred_endpoint)
        all_lines = res.text.split('\n')
        data_lines = []
        hit_data = False
        for line in all_lines:
            if line.startswith('Rationale:'):
                break
            if hit_data and len(line):
                data_lines.append(line)
            if line.startswith('NOAA Kp index breakdown'):
                hit_data = True
        lines = [re.split(r' {2,}', l) for l in data_lines]
        df = pd.DataFrame(lines[1:])
        df.columns = ['time_range'] + lines[0][1:] + ['null']
        df = df.drop('null', axis=1)
        now = dt.datetime.now()
        datetimes = []
        ks = []
        for i, row in df.iterrows():
            for colname in df.columns[1:]:
                date = colname
                time_range = row['time_range']
                datetime = dt.datetime.strptime(f'{now.year} {date} {time_range.split("-")[0]}', '%Y %b %d %H')
                if now - datetime > dt.timedelta(days=2):
                    datetime = dt.datetime.strptime(f'{now.year + 1} {date} {time_range.split("-")[0]}', '%Y %b %d %H')
                datetimes.append(datetime)
                ks.append(row[colname])
        pred_ks = pd.Series(ks, datetimes).sort_index()
        self.pred_ks = pred_ks
        return self.pred_ks

    def make_summary(self):
        """
        Make a text summary of the recent k-index observations
        """
        current_k = self.k_data['Kp'].iloc[-1]
        storm = True if current_k >= 5 else False
        g, short_desc, color = g_level(current_k)
        header = f'Geomagnetic Storm Alert: {g} ({short_desc})'
        msg = f'Current Kp: {current_k} ({g}: {short_desc})'
        max_k = self.k_data['Kp'].max()
        g, short_desc, color = g_level(max_k)
        msg += f'\nRecent Maximum Kp: {max_k} ({g}: {short_desc})'
        msg += '\n\nSource: https://www.swpc.noaa.gov/products/planetary-k-index'
        msg += '\nAurora forecast: https://www.swpc.noaa.gov/products/aurora-30-minute-forecast'
        return storm, header, msg

    def make_plot(self):
        """
        Make a plot of the k-index
        """
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.grid(zorder=0)
        timestep = np.median(self.k_data['time'].diff().iloc[1:])
        ax.bar(self.k_data.index, self.k_data['Kp'], color=[bar_color(k) for k in self.k_data['Kp']],
               width=timestep, align='edge', edgecolor='black', zorder=3)
        ax.set(xlabel='Time (UTC)', ylabel='Kp', title='Planetary K-index',
               ylim=(0, max(9, self.k_data['Kp'].max())),
               xlim=(self.k_data['time'].iloc[0], self.k_data['time'].iloc[-1] + 5 * timestep))
        for k, g in zip([4.5, 5.5, 6.5, 7.5, 9], [1, 2, 3, 4, 5]):
            ax.axhline(k, c=bar_color(k), label=f'G{g}')
            ax.text(self.k_data['time'].iloc[-1] + timestep, k + 0.05, f'G{g}')
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig('Kp_plot.png', dpi=400)
        plt.close(fig)


if __name__ == '__main__':
    KIndex().run()
