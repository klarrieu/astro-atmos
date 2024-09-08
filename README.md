# astro-atmos

### Tools to make local weather forecasts for terrestrial astronomical observations.

- ### [Get Started](#installation)
- ### [Documentation](https://klarrieu.github.io/astro-atmos)

Example forecast:
![Example forecast](./astroatmos/icons/example_forecast.jpg)


> [!NOTE] 
> Because of the models/data sources currently implemented, this can only forecast locations within the United States. I have partially developed support for Canada too, but it is currently incomplete.


## Forecast parameters

- **Cloud Cover**:
  ![cloud cover scale](./astroatmos/icons/cloud_cover_scale.png)
- **Probability of Precipitation**: dark grey bars are shown on top of the cloud cover plot. Height of the bar corresponds to probability of precipitation from 0% (no bar) to 100% (bar fills full plot height). For example, in the example forecast above, we see a maximuim precipitation probability of ~30% on Wednesday afternoon.
- **Transparency**: 1-5 scale representing the overall transparency of the atmosphere. Transparency is indicated using the same color scale as Seeing (below).
- [**Seeing**](https://www.canada.ca/en/environment-climate-change/services/weather-general-tools-resources/astronomy/seeing-forecast.html): 1-5 scale representing how clearly objects can be resolved for astronomical observation due to the effects of atmospheric turbulence. Poor seeing corresponds to "boiling" images and poor angular resolution. Seeing is indicated using the same color scale as Transparency.
   ![seeing/transparency scale](./astroatmos/icons/seeing_transparency_scale.png)
- [**Planetary k-index (Kp)**](https://www.swpc.noaa.gov/products/planetary-k-index): Represents the overall variance in Earth's magnetic fields due to solar flares/CMEs. High values of Kp correspond to geomagnetic storm levels (G-scale) and probability of auroras. Consistent with how Kp is displayed by NOAA's SWPC, the height of bars correspond to the value of Kp, and bars are also colored and labeled to indicate the geomagnetic storm level.
   ![k index scale](./astroatmos/icons/kp_scale.png)
- **Sun/moon altitudes, lunar phase, and astronomical twilight/night times**: Time series of the sun (gold line) and moon (blue line) altitudes for the forecast location are indicated in the Altitude plot. Icons of the sun and moon are shown at their current altitudes. The icon used to represent the moon also corresponds to the current lunar phase. The horizon is indicated by a horizontal black line. Astronomical twilight and night times are indicated by light and dark grey shading, respectively.
- **Temperature/Dewpoint**: Time series of temperature and dewpoint temperature are shown in blue and purple, respectively. Daily high and low temperatures are also annotated.
- **Wind Speed/Gusts**: Time series of average wind speed and wind gusts are shown in blue and red (dotted), respectively.


## Installation

1. Clone this git repository:

   ```commandline
   git clone https://github.com/klarrieu/astro-atmos.git
   cd astro-atmos
   ```

2. Install the required packages:

   ### Option 1: Using `mamba`/`conda` (current environment):

   [`mamba`](https://mamba.readthedocs.io/) is preferred over `conda` since it resolves much faster, but these commands also work by replacing `mamba` with `conda`.

   ```commandline
   mamba env update
   ```

   ### Option 2: Using `mamba`/`conda` (creating new environment):

   ```commandline
   mamba create -n <env-name> --file environment.yml
   mamba activate <env-name>
   ```

   ### Option 3: Using `pip`:

   ```commandline
   pip install -r requirements.txt
   ```

## Making Forecasts

1. Enter desired forecast location by editing `forecast_location.txt`:

    ```editorconfig
    [Location]
    # latitude, decimal degrees
    lat = 39.2
    # longitude, decimal degrees
    lon = -120.4
    # timezone name, see reference: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    timezone = US/Pacific
    # elevation in meters
    elevation = 0
    ```
    
    Units of measurement for temperature and wind speed can also be adjusted in this file.


2. Generate a forecast:

    ```commandline
    python make_forecast.py
    ```

   After processing, an interactive plot will be generated. An image file for the forecast will also be saved.


3. To further customize your forecast plots or grab the raw data from your forecast, [check out the Docs](https://klarrieu.github.io/astro-atmos).


## Additional work-in-progress:
- add smoke data source
- add weather forecasts for Canada
- lowpass filter temp for low/high annotation
- add options for 12/24 hr times, light/dark styles
- make subplots modular (separate method per subplot)


## Data sources

- [Candian Meteorological Centre (CMC) RDPS model](https://weather.gc.ca/astro/index_e.html): seeing, transparency. Other parameters such as cloud cover, dewpoint, etc. can be extracted from these models as well but it has not been fully implemented.
- [National Oceanic and Atmospheric Administration (NOAA)](https://www.swpc.noaa.gov/products/planetary-k-index): planetary k-index.
- [National Weather Service (NWS)](https://www.weather.gov/documentation/services-web-api): cloud cover, probability of precipitation, temperature, dewpoint, wind speed/gusts.
- Sun/moon: All celestial body data is calculated using [`astropy`](https://www.astropy.org/). See [the documentation](https://klarrieu.github.io/astro-atmos/bodies.html) for more details.

## Troubleshooting

Please [submit an issue](https://github.com/klarrieu/astro-atmos/issues/new) if you have any trouble using this code.

## Contributing

Contributions are welcome and encouraged! [Submit a PR.](https://github.com/klarrieu/astro-atmos/pulls)
