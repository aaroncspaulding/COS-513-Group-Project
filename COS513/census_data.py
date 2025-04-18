import logging
import os

import pandas as pd
import requests
from typing import Union, List

from census import Census
from tqdm.contrib.concurrent import thread_map

from COS513.cache import get_cache_dir

logger = logging.getLogger(__name__)

CACHE_DIRECTORY = get_cache_dir('COS513_CACHE_DIRECTORY', 'data')

STATE_FIPS = ['01', '02', '04', '05', '06', '08', '09', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20',
              '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37',
              '38', '39', '40', '41', '42', '44', '45', '46', '47', '48', '49', '50', '51', '53', '54', '55', '56']

VARIABLES_TO_DOWNLOAD = {
    'B01001_001E': 'TOTAL POPULATION',
    'B19001_001E': 'TOTAL NUMBER OF HOUSEHOLDS',
    'B19013_001E': 'MEDIAN HOUSEHOLD INCOME',
    'B19001_002E': 'Households: Less than $10,000',
    'B19001_003E': 'Households: $10,000 to $14,999',
    'B19001_004E': 'Households: $15,000 to $19,999',
    'B19001_005E': 'Households: $20,000 to $24,999',
    'B19001_006E': 'Households: $25,000 to $29,999',
    'B19001_007E': 'Households: $30,000 to $34,999',
    'B19001_008E': 'Households: $35,000 to $39,999',
    'B19001_009E': 'Households: $40,000 to $44,999',
    'B19001_010E': 'Households: $45,000 to $49,999',
    'B19001_011E': 'Households: $50,000 to $59,999',
    'B19001_012E': 'Households: $60,000 to $74,999',
    'B19001_013E': 'Households: $75,000 to $99,999',
    'B19001_014E': 'Households: $100,000 to $124,999',
    'B19001_015E': 'Households: $125,000 to $149,999',
    'B19001_016E': 'Households: $150,000 to $199,999',
    'B19001_017E': 'Households: $200,000 or more'
}


def read_census_api_key(path='../census_api_key.txt'):
    try:
        with open(path, 'r') as file:
            census_api_key = file.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f'Census API key file not found at: {path}\n')
    return census_api_key


def get_variable_descriptions(year=2020, dataset='acs5'):
    url = f'https://api.census.gov/data/{year}/acs/{dataset}/variables.json'
    resp = requests.get(url)
    return resp.json()['variables']


def get_census_data_for_one_state(
    census_api_key: str,
    fields: Union[List[str], tuple] = tuple(VARIABLES_TO_DOWNLOAD.keys()),
    state_fips: str = '01',
    county_fips: str = '*',
    tract: str = '*',
    year: int = 2020,
    *args,
    **kwargs
) -> List[dict]:
    census_api = Census(census_api_key)

    census_data_ = census_api.acs5.state_county_tract(
        fields=fields,
        state_fips=state_fips,
        county_fips=county_fips,
        tract=tract,
        year=year
    )
    return census_data_


def download_census_data_for_all_states(
    census_api_key: str,
    verbose: bool = True,
    max_workers: int = 12,
    *args,
    **kwargs) -> pd.DataFrame:
    max_workers = int(os.getenv('WORKERS', max_workers))

    def _get_census_data_for_one_state(state_fips):
        return get_census_data_for_one_state(
            state_fips=state_fips,
            census_api_key=census_api_key,
            *args,
            **kwargs
        )

    logger.info('Downloading Census Data')
    dfs = thread_map(
        _get_census_data_for_one_state,
        STATE_FIPS,
        max_workers=max_workers,
        disable=not verbose

    )
    dfs = [pd.DataFrame(df) for df in dfs]
    census_data = pd.concat(dfs, ignore_index=True)

    return census_data


def load_census_data(
    *args,
    **kwargs
) -> pd.DataFrame:
    census_data_cache_directory = CACHE_DIRECTORY / 'CENSUS_DATA'
    census_data_cache_directory.mkdir(parents=True, exist_ok=True)
    census_data_file_path = census_data_cache_directory / 'census_data.csv'

    if census_data_file_path.exists():
        logger.info(f'Loading cached census data from {census_data_cache_directory}')
        return pd.read_csv(census_data_file_path, low_memory=False)

    logger.info('No cached census data found. Downloading...')
    census_api_key = read_census_api_key()
    df = download_census_data_for_all_states(census_api_key, *args, **kwargs)

    df.to_csv(census_data_file_path, index=False)
    logger.info(f'Census data cached at {census_data_cache_directory}')
    return df


if __name__ == '__main__':
    census_api = Census(read_census_api_key())
