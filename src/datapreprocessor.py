import logging
from abc import ABC, abstractmethod

import pandas as pd

class DataPreprocessor(ABC):
    """
    Class designed to preprocess COVID table. Each method will act on a speecific column or apply a specific technique.
    Where necessary, the pattern will allow for a single operation that can be used with pandas apply
    """
    @property
    def name(self):
        raise NotImplementedError
        
    @abstractmethod
    def __init__(self):
        self.logger = None
        pass
    
    @abstractmethod
    def preprocess(self, df: pd.DataFrame):
        pass
    
    
class DataPreprocessorSimple(DataPreprocessor):
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        self.name = 'simple_preprocessor'
        self.logger.info(f'initialised {self.name}')
        
        
    def preprocess(self, df: pd.DataFrame):
        """
        Performs simple transformations on the data
        """
        self.logger.info(f'{self.name} completed preprocessing')
        return df
        
        
    def _text_columns(self, df: pd.DataFrame, cols: list) -> pd.DataFrame:
        pass
    
    
    
from abc import ABC, abstractmethod
from sklearn.preprocessing import MinMaxScaler

class TSTransformer(ABC):
    
    transformer_name = None
    transform_data_path = Path(f'data/transformed_{transformer_name}_data.csv')
        
    @abstractmethod
    def transform_data(self, ts_df: pd.DataFrame, input_dim: int = 0) -> pd.DataFrame:
        pass
    
    def load_transformed_data(self) -> pd.DataFrame:
        
        return pd.read_csv(self.transform_data_path, index_col='date')
    
    def generate_time_lags(self, df, n_lags):
        df_n = df.copy()
        for n in range(1, n_lags + 1):
            df_n[f'lag{n}'] = df_n['count'].shift(n)

        # Remove variables that are represented by the lag
        df_n = df_n.iloc[n_lags:]

        return df_n
    
    def scale_data(self, df, scaler) -> pd.DataFrame():
        df_ = df.copy()
        # TOOO:
        return df_
    
    
class MultiVariateTransformer(TSTransformer):
    
    def __init__(self):
        self.transformer_name = 'multivariate'
#     transform_data_path = Path(f'data/transformed_{self.transformer_name}_data.csv')

    def transform_data(self, ts_df: pd.DataFrame, input_dim: int = 0) -> pd.DataFrame:
        """Encapsulates the transformations done in preparation of the modelling"""
        
        df = ts_df.copy()
    
#         scaler = MinMaxScaler()
#         df = scaler.fit_transform(df)
        
        # Predict out 30 days
        df = self.generate_time_lags(df, 30)

        # Generate features from the date
        df_features = (
                    df
                    .assign(hour = df.index.hour)
                    .assign(day = df.index.day)
                    .assign(month = df.index.month)
                    .assign(day_of_week = df.index.dayofweek)
                    .assign(week_of_year = df.index.week)
                  )

        def onehot_encode_pd(df, col_name):
            """One hot encode the date features"""
            for col in col_name:
                df[col] = df[col].astype('object')
            dummies = pd.get_dummies(df[col_name], prefix=col_name)
            return pd.concat([df, dummies], axis=1).drop(col_name, axis=1)

        df.to_csv(self.transform_data_path)
        return df_features


class ARTransformer(TSTransformer):
    """Performs transformations for an autoregressive model. Particularly excludes extracting date data (day of week, week etc)"""
    def __init__(self):
        self.transformer_name = 'autoregressive'
#     self.transform_data_path = Path(f'data/transformed_{self.transformer_name}_data.csv')
        
    def transform_data(self, ts_df: pd.DataFrame, input_dim: int=0) -> pd.DataFrame:
        
        df_features = pd.DataFrame()
        
        return df_features