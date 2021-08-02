import logging
from abc import ABC, abstractmethod

import pandas as pd

class DataCleaner(ABC):
    """
    Clean the original joined dataframe by applying imputation strategies on relevant columns
    This abstract class will enable different implementations based on the experiment
    """
    @abstractmethod
    def __init__(self):
        pass
    @abstractmethod
    def clean(self):
        pass
    
class DataCleanerSimple(DataCleaner):
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.info('hello from dataset cleaner')
        
    def clean(self, df: pd.DataFrame):
        self.logger.info('cleaning')