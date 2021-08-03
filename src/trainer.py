from abc import ABC, abstractmethod

class Trainer(ABC):
        
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod:
    def train(self):
        pass

class LSTMTrainer(Trainer):
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        self.name = 'lstm_trainer'
        self.logger.info(f'initialised {self.name}')
        
        
    def train(self, df: pd.DataFrame, checkpoint: int = None):
        """
        Trains an LSTM saving n checkpoints, if none it only saves the final model
        """
        self.logger.info(f'{self.name} completed training')
        return model