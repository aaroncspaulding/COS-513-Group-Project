import logging
from pathlib import Path

import pandas as pd
import requests

from COS513.cache import get_cache_dir

logger = logging.getLogger(__name__)

CACHE_DIRECTORY = get_cache_dir('COS513_CACHE_DIRECTORY', 'data')
COUNTY_ZONE_CACHE_DIR = CACHE_DIRECTORY / 'COUNTY_ZONE'
COUNTY_ZONE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

FILE_URL = 'https://www.weather.gov/source/gis/Shapefiles/County/bp05mr24.dbx'
RAW_FILENAME = 'bp05mr24.dbx'
CSV_FILENAME = 'bp05mr24.csv'

COUNTY_ZONE_COLUMNS = ['STATE', 'ZONE', 'CWA', 'NAME', 'STATE_ZONE', 'COUNTY', 'FIPS', 'TIME_ZONE', 'FE_AREA', 'LAT',
                       'LON']


def load_county_zone_mapping() -> pd.DataFrame:
    raw_path = COUNTY_ZONE_CACHE_DIR / RAW_FILENAME
    csv_path = COUNTY_ZONE_CACHE_DIR / CSV_FILENAME

    if csv_path.exists():
        logger.info(f'Using cached county-zone CSV at {csv_path}')
        df = pd.read_csv(csv_path, dtype=str, header=None)
        df.columns = COUNTY_ZONE_COLUMNS
        return df

    logger.info(f'Downloading county-zone file from {FILE_URL}')
    response = requests.get(FILE_URL)
    if response.status_code != 200:
        raise RuntimeError(f'Failed to download file from {FILE_URL} (status {response.status_code})')

    with open(raw_path, 'wb') as f:
        f.write(response.content)
    logger.info(f'Saved raw file to {raw_path}')

    df = pd.read_csv(raw_path, delimiter='|', dtype=str, header=None)
    df.to_csv(csv_path, index=False)
    logger.info(f'Parsed and cached county-zone CSV to {csv_path}')
    df.columns = COUNTY_ZONE_COLUMNS

    return df
