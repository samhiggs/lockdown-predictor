# lockdown-predictor

A multivariate time series classifier that aims to predict when lockdown will change. 

## Usage

automated pipeline entrypoint is [src/pipeline.py](src/pipeline.py)

notebook with exploratory work is in [lockdown_analysis.ipynb](lockdown_analysis.ipynb)


## Modelling Pipeline

The modelling pipeline is joined, and visualisations are created in the lockdown analysis for the purpose of reporting, whilst a python script will eventually combine the pipeline to be an end to end solution. Each step in the pipeline contains it's own abstract class which sets the interface for each step. the input and output schema is defined using pandera ensuring that there are no weird changes whilst preprocessing. The data is maintained in a dataframe with the date as the index as this is a time-series classification problem.

At each stage the 

### 1. Data loader

### 2. Data cleaner