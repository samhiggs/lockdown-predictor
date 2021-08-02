import requests, json, logging, errno, os
from typing import List
from datetime import datetime, timedelta
from pathlib import Path
from pprint import pprint
from functools import reduce

import pandas as pd
import numpy as np

from bs4 import BeautifulSoup
# Google unofficial API
from pytrends.request import TrendReq
from pytrends import dailydata

from sagemaker.s3 import S3Downloader, S3Uploader

class DataLoader:
    """Gathers the data from various sources"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
    ###### NSW CASE DATA
    def _get_data_nsw(self, resource_id: str, counts_col: str = None) -> pd.DataFrame:
        """Retrieve json data object and convert to pandas dataframe"""
        # Query API
        url = f'https://data.nsw.gov.au/data/api/3/action/datastore_search?resource_id={resource_id}&limit=100000'  
        res = requests.get(url)
        records = res.json()['result']['records']

        # Convert to dataframe
        df = pd.DataFrame(records)

        # Set date as index and standardise name
        df.iloc[:,0] = pd.to_datetime(df.iloc[:,0])
        df.set_index(df.columns[0], inplace=True)
        df.index.rename('date', inplace=True)

        # Get daily values by either summing counts col or counting rows
        if counts_col in df.columns:
            df = df[counts_col]
            df = df.astype('int')
        else:
            df['count'] = 1
            df = df['count']

        df = df.groupby(pd.Grouper(level='date', freq='D')).sum()

        return df
    
    
    def get_case_data(self, from_csv: bool = True) -> pd.DataFrame:
        """Loads data from data nsw and in future, other data sources."""
        
        cached_path = 'data/case_data.csv'
        if from_csv:
            return self._load_data(cached_path)    
    
        # resource IDS for data nsw APIs 
        resource_ids = {
            'testing': '945c6204-272a-4cad-8e33-dde791f5059a',
            'cases': '21304414-1ff1-4243-a5d2-f52778048b29'
        }

        df = self._get_data_nsw(resource_ids['cases']).to_frame()

        print(f'{df.index.min()} - {df.index.max()}')
        df.to_csv(cached_path)
        return df
    
    def _clean_references(self, x: str) -> str:
        """Converts referencescolumns from aph into multiple columns"""
        split_str = ' '.join(x.split()).split(',')
        # peoples names exist
        if len(split_str) == 5:
            # Concatetenate the first and second
            split_str = [split_str[0] + split_str[1]] + split_str[2:]
        if len(split_str) == 3:
            split_str.append(None)
        return split_str
    
    ####### Vaccinations
    def get_vaccinations_data(self, from_csv: bool = True) -> pd.DataFrame:
        """Gets Australian vaccination rate from Our world in data NOT WORKING"""
        
        cached_path = 'data/aus_vaccination_data.csv'
        
        try:
            return self._load_data(cached_path)
        except:
            self.logger.warning(f'Unable to load file {cached_path}')
            
        url = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv'
        df = pd.read_csv(url)
        df = [df['location'] == 'Australia']
        df[['date', 'people_vaccinated_per_hundred', 'people_fully_vaccinated_per_hundred', 'daily_vaccinations_per_million']]
        df.date = pd.to_datetime(df.date)
        df.set_index('date', inplace=True)
        df.to_csv(cached_path)
        return df
    
    ######## get restructions for all oecd countries
    def _get_oecd_countries(self) -> list:
        try:
            url_oecd = 'https://www.oecd.org/about/document/ratification-oecd-convention.htm'
            dfs = pd.read_html(url_oecd)
            oecd_countries = dfs[1].iloc[:,1].tolist()[1:]
            oecd_countries = [c.capitalize() for c in oecd_countries]
        except Exception as e:
            print(e)

        return oecd_countries

    def _load_oecd_countries(self) -> list:
        oecd_countries = []
        try:
            with open('data/oecd_countries.txt', 'r') as f:
                for line in f:
                    oecd_countries.append(line.strip())
        except Exception as e:
            print(e)

        return oecd_countries

    def get_oecd_restrictions(self, from_csv: bool = True) -> pd.DataFrame:
        """
        Data can be downloaded from ourworldindata, haven't created endpoint for it yet
        https://ourworldindata.org/covid-stay-home-restrictions
        """

        df = pd.read_csv('data/global_restriction_orders.csv')
        try:
            oecd_countries = self._load_oecd_countries()
        except Exception as e:
            print(e)
            oecd_countries = self._get_oecd_countries()

        df = df[df.Entity.isin(oecd_countries)]
        df.rename(columns={'Day': 'date'}, inplace=True)
        df['date'] = pd.to_datetime(df.date)
        df.set_index('date', inplace=True)
        df.columns = ['country', 'country_code', 'stay_home_requirements']
        df = df.iloc[:,[0,2]]
        df = df.pivot_table(index='date', columns='country', values='stay_home_requirements').reset_index()
        # oecd_wide = oecd_wide.drop(columns='country')
        # oecd_wide.set_index('date', inplace=True)
        df = df.ffill()
        df.head()
        df.to_csv('data/global_restrictions.csv', index=False)
        return df

    def _load_oecd_restrictions(self) -> pd.DataFrame:
        df = pd.read_csv('data/global_restrictions.csv')
    #     df.set_index('date', inplace=True)
        return df
    
    
    ####### APH DATA
    def get_news_data(self, from_csv: bool = True) -> pd.DataFrame:
        """Gathers relevant text data from government site"""

        cached_path = 'data/nsw_announcements.csv'
        if from_csv:
            return self._load_data(cached_path)

        url = 'https://www.aph.gov.au/About_Parliament/Parliamentary_Departments/Parliamentary_Library/pubs/rp/rp2021/Chronologies/COVID-19StateTerritoryGovernmentAnnouncements'
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        tables = soup.findAll('table')
        table = tables[4]
        table_rows = table.find_all('tr')

        res = []
        for tr in table_rows:
            td = tr.find_all('td')
            row = [tr.text.strip() for tr in td if tr.text.strip()]
            if row:
                res.append(row)
        clean_res = [r for r in res if len(r) == 3]
        df = pd.DataFrame(clean_res[1:], columns=clean_res[0])
        df.columns = ['date', 'content', 'references']
        df.date = pd.to_datetime(df.date)

        # test_str = nsw_announcements.references.tolist()[7]
        references_list = []
        # for r in nsw_announcements.references.tolist():

        references_df = pd.DataFrame(df.references.apply(self._clean_references).tolist())
        references_df.columns = ['source', 'theme', 'medium', 'date_released']
        df = pd.concat([df.drop(columns='references'), references_df], axis=1, join='inner')
        df.set_index('date', inplace=True)
        df.to_csv(cached_path)
        assert len(df) > 5
        return df
    
    ######## GOOGLE TREND API
    def get_google_trend_data(self, from_csv: bool = True, to_month: int = 7) -> pd.DataFrame:
        """Extract google trend data about the lockdown"""
    
        cached_path = 'data/google_trend_covid.csv'
        if from_csv:
            return self._load_data(cached_path)

        print('This will take a minute or two...')
        df = dailydata.get_daily_data('covid', 2020, 2, 2021, to_month, geo = 'AU-NSW')
        df.to_csv(cached_path)
        print('data saved')
        return df


    def get_restrictions_data(self,from_csv: bool = True) -> pd.DataFrame:
        """Restrictions in place from 
            https://www.theguardian.com/world/2020/may/02/australias-coronavirus-lockdown-the-first-50-days
            https://deborahalupton.medium.com/timeline-of-covid-19-in-australia-1f7df6ca5f23
        """
        cached_path = 'data/restrictions.csv'
        if from_csv:
            return self._load_data(cached_path)


        lockdown_dates_nsw = [
            ['2020-03-16', 500], # gatherings over 500 forbidden
            ['2020-03-18', 100], # gatherings over 100 forbidden
            ['2020-03-19', 50], # gathering over 50 forbidden
            ['2020-03-24', 10], # gatherings over 10 forbidden
            ['2020-03-27', 5], # exercise groups limited to 10 and no seeing others
            ['2020-03-29', 2], # no more then two 
            ['2020-03-30', 1], # $1000 fines enfored and ph orders
            ['2020-04-29', 2], # can visit family
            ['2020-05-01', 10], # restrictions loosen, family picnic and park, 50km radius of home
            ['2020-05-08', 15] # three stage plan announced
        ]
        # Convert to dataframe
        df = pd.DataFrame(lockdown_dates_nsw, columns=['date', 'restriction'])
        df['date'] = pd.to_datetime(df.date)
        df.set_index('date', inplace=True)

        # Impute dates with last date
        df = df.resample('D').mean() # Mean is irrelevant in this case
        df = df.fillna(method='ffill')

        # Invert the restriction value to make higher = worse
        df['severity'] = df.restriction.apply(lambda x: int((1/x)*100))
        df.to_csv(cached_path)
        return df
    
    def _load_data(self, path) -> pd.DataFrame:
        """Loads data that is """
        df = pd.read_csv(path)
        df.set_index('date', inplace=True)
        return df
    
    def get_data(self, from_csv: bool = True) -> pd.DataFrame:
        """
        Builder function to gather all the data and returns it
        giving the user flexibility to do what they want with it.
        """

        cases_df = self.get_case_data(from_csv)
        self.logger.info('cases data loaded')
#         vac_df = self.get_vaccinations_data(from_csv)
#         self.logger.info('vaccination data loaded')
        news_df = self.get_news_data(from_csv)
        self.logger.info('news data loaded')
        trend_df = self.get_google_trend_data(from_csv)
        self.logger.info('google trend data loaded')
        restric_df = self.get_restrictions_data(from_csv)
        self.logger.info('restrictions data loaded')
        # This differs from restric_df as restric_df is manually compiled
        oecd_restric_df = self.get_oecd_restrictions(from_csv)
        self.logger.info('oecd restrictions data loaded')
        # TODO: Write tables to S3
#         s3_uri = 's3://projects/lockdown-predictor/'
#         data_uri = s3_uri + 'data/' 
#         # S3Downloader().download(data_uri, 'data/')

#         S3Uploader().upload(data_uri, 'data/')
        return cases_df, news_df, trend_df, restric_df, oecd_restric_df