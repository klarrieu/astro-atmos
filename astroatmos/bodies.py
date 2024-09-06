"""
Functions for getting the altitude of celestial bodies (e.g. sun, moon) at a given time and location on Earth.
"""
from pathlib import Path
import numpy as np
import datetime as dt
from astropy.time import Time
from astropy.coordinates import get_body
from astropy.coordinates import EarthLocation, AltAz, GeocentricTrueEcliptic
from astropy import units as u
import pickle


def get_body_alt(times, lat, lon, elevation, body_name):
    """
    Get altitude of celestial body at given time(s), lat/lon

    Args:
        times: datetime(s) of observation
        lat (float): latitude (decimal degrees)
        lon (float): longitude (decimal degrees)
        elevation (float): elevation in meters
        body_name (str): name of celestial body, e.g. 'sun', 'moon'

    Returns:
        float: altitude (degrees), same shape as times
    """
    times = Time(times)
    # TODO: set height based on global DEM? Also assuming HAE is ~= MASL
    loc = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)
    body = get_body(body_name, times, loc)
    altazframe = AltAz(obstime=times, location=loc, pressure=0)
    body_trans = body.transform_to(altazframe)
    alts = body_trans.alt.degree
    return alts


def get_moon_illumination(times):
    """
    Get moon phase and percent illuminated from time

    Args:
        times: datetime(s) for desired moon phase

    Returns:
        tuple:
            - phase (str): name of lunar phase
            - illumination percent (float): 0-100 value for percent of moon illuminated
    """
    times = Time(times)
    sun = get_body('sun', times)
    sun_lon = sun.transform_to(GeocentricTrueEcliptic()).lon
    moon = get_body('moon', times)
    moon_lon = moon.transform_to(GeocentricTrueEcliptic()).lon
    elongation = (sun_lon - moon_lon) % (2 * np.pi * u.rad)
    phase_angle = np.arctan2(sun.distance * np.sin(elongation), moon.distance - sun.distance * np.cos(elongation)).value
    illumination = (1 + np.cos(phase_angle)) / 2
    illumination_percent = illumination * 100
    if np.abs(phase_angle - 0) <= np.pi / 28:
        phase = 'Full Moon'
    elif np.abs(np.abs(phase_angle) - np.pi) <= np.pi / 28:
        phase = 'New Moon'
    elif np.abs(phase_angle - np.pi / 2) <= np.pi / 28:
        phase = 'Third Quarter'
    elif np.abs(phase_angle - - np.pi / 2) <= np.pi / 28:
        phase = 'First Quarter'
    elif 0 <= phase_angle <= np.pi / 2:
        phase = 'Waning Gibbous'
    elif np.pi / 2 <= phase_angle:
        phase = 'Waning Crescent'
    elif phase_angle <= -np.pi / 2:
        phase = 'Waxing Crescent'
    elif phase_angle <= 0:
        phase = 'Waxing Gibbous'
    else:
        raise ValueError(f'Could not classify phase angle: {phase_angle}')
    return phase, illumination_percent

def next_time_moon_phase(target_phase):
    """
    Get the next time that the moon is at a given phase

    Args:
        target_phase (str): One of ['Full Moon', 'New Moon', 'First Quarter', 'Third Quarter', 'Waxing Crescent',
            'Waxing Gibbous', 'Waning Crescent', 'Waning Gibbous']

    Returns:
        datetime.datetime: python datetime object for the next date the moon is at the corresponding phase
    """
    if target_phase not in moon_icons.keys():
        raise ValueError(f'Invalid phase: {target_phase}. Must be one of: {moon_icons.keys()}')
    now = Time(dt.datetime.now())
    i = 0
    while True:
        delta_t = dt.timedelta(days=i)
        phase, illum_percent = get_moon_illumination(now + delta_t)
        if phase == target_phase:
            return (now + delta_t).datetime.date()
        i += 1
        if i > 28:
            raise ValueError(f'Cannot find target phase: {target_phase}')

icons_path = Path(__file__).parent / "icons"
moon_icons = pickle.load(open(icons_path / "moon_markers.obj", "rb"))
sun_icon = pickle.load(open(icons_path / "sun_marker.obj", "rb"))
