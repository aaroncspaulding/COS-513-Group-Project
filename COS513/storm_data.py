import os
import logging
from urllib.error import HTTPError

import numpy as np
import pandas as pd
from tqdm.contrib.concurrent import thread_map

from COS513.cache import get_cache_dir

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/'
FILE_TEMPLATE = 'StormEvents_details-ftp_v1.0_d{year}_c20250401.csv.gz'

CACHE_DIRECTORY = get_cache_dir('COS513_CACHE_DIRECTORY', 'data')


def load_year_of_noaa_storm_data(year: int | str) -> pd.DataFrame:
    filename = FILE_TEMPLATE.format(year=year)

    # The most recent version for 2020 is missing ig, so override
    if str(year) == '2020':
        filename = 'StormEvents_details-ftp_v1.0_d2020_c20240620.csv.gz'

    cache_directory_for_noaa_storm_data = CACHE_DIRECTORY / 'NOAA_STORM_DATA'
    cache_directory_for_noaa_storm_data.mkdir(parents=True, exist_ok=True)
    local_path = cache_directory_for_noaa_storm_data / filename

    if not local_path.exists():
        url = BASE_URL + filename
        logger.info(f'Downloading: {url}')

        try:
            df = pd.read_csv(url, compression='gzip', low_memory=False)
        except HTTPError:
            logger.error(f'Error downloading {url}')
            raise HTTPError
        df.to_csv(local_path, index=False, compression='gzip')
    else:
        logger.info(f'Loading cached file for year {year}')
        df = pd.read_csv(local_path, compression='gzip', low_memory=False)

    return df


def _load_all_years_of_noaa_storm_data(
    years: list[int],
    verbose: bool = True,
    max_workers: int = 12,
) -> pd.DataFrame:
    max_workers = int(os.getenv('WORKERS', max_workers))

    dfs = thread_map(
        load_year_of_noaa_storm_data,
        years,
        max_workers=max_workers,
        desc='Loading NOAA storm data' if verbose else None,
        disable=not verbose,
    )
    return pd.concat(dfs, ignore_index=True)


def load_all_years_of_noaa_storm_data(
    start_year: int = 1950, end_year: int = 2024, *args, **kwargs
) -> pd.DataFrame:
    return _load_all_years_of_noaa_storm_data(
        list(range(start_year, end_year + 1)), *args, **kwargs
    )


def decode_damage_property(value: str) -> float:
    if pd.isna(value) or value == '':
        return np.nan
    value = str(value).strip().upper()
    if value.endswith('K'):
        try:
            return float(value[:-1]) * 1_000
        except ValueError:
            # there's a single 'k'
            return np.nan
    elif value.endswith('M'):
        try:
            return float(value[:-1]) * 1_000_000
        except ValueError:
            # there's a single 'M'
            return np.nan

    elif value.endswith('B'):
        return float(value[:-1]) * 1_000_000_000
    else:
        try:
            return float(value)
        except ValueError:
            return 0.0


if __name__ == '__main__':
    data = load_all_years_of_noaa_storm_data()
