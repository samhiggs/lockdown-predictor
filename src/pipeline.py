from argparse import ArgumentParser

from src.dataloader import DataLoader
from src.datacleaner import DataCleanerSimple
from src.datapreprocessor import DataPreprocessorSimple
from src.trainer import LSTMTrainer


def parse_args(args):
    """Use this if you need to write command line arguments"""
    pass

def main():
    # Load
    data_loader = DataLoader()
    data_frames = data_loader.get_data()
    
    # Clean
    data_cleaner = DataCleanerSimple()
    df = data_cleaner.clean(data_frames)

    # Preprocess
    preprocessor = DataPreprocessorSimple()
    processed_df = preprocessor.preprocess(df)

    # Train
    trainer = LSTMTrainer()
    trainer.train(preprocessed_df)
    

if __name__ == '__main__':
    print('hello from main!')
    main()