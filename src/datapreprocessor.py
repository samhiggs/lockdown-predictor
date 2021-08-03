import logging
from abc import ABC, abstractmethod

import pandas as pd

class DataPreprocessor(ABC):
    """
    Class designed to preprocess COVID table. Each method will act on a speecific column or apply a specific technique.
    Where necessary, the pattern will allow for a single operation that can be used with pandas apply
    """
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def clean(self, df: pd.DataFrame):
        pass
    
    
class DataPreprocessorSimple(DataPreprocessor):
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.info('hello from dataset cleaner')
        
    def clean(self, df: pd.DataFrame):
        self.logger.info('cleaning')
        
    def _text_columns(self, df: pd.DataFrame, cols: list) -> pd.DataFrame:
        pass
    