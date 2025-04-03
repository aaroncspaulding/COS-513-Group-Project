import logging
from urllib.error import HTTPError

import pandas as pd

from COS513.cache import get_cache_dir

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/'
FILE_TEMPLATE = 'StormEvents_details-ftp_v1.0_d{year}_c20250401.csv.gz'

CACHE_DIR = get_cache_dir('COS513_CACHE_DIRECTORY', 'data')


def load_year_of_noaa_storm_data(year: int | str) -> pd.DataFrame:
    filename = FILE_TEMPLATE.format(year=year)

    # The most recent version for 2020 is missing ig, so override
    if str(year) == '2020':
        filename = 'StormEvents_details-ftp_v1.0_d2020_c20240620.csv.gz'

    local_path = CACHE_DIR / filename
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


def _load_all_years_of_noaa_storm_data(years: list[int]) -> pd.DataFrame:
    return pd.concat([load_year_of_noaa_storm_data(y) for y in years], ignore_index=True)


def load_all_years_of_noaa_storm_data(start_year: int = 1950, end_year: int = 2024) -> pd.DataFrame:
    return _load_all_years_of_noaa_storm_data(list(range(start_year, end_year + 1)))


if __name__ == '__main__':
    data = load_all_years_of_noaa_storm_data()
