# ConvLSTM model for Weather Forecasting

PyTorch Lightning implementation of drought forecasting (classification) model (Convolutional LSTM). Classification is based on [PDSI index](https://en.wikipedia.org/wiki/Palmer_drought_index), and its corresponding bins. 

<img src="https://raw.githubusercontent.com/makboard/Droughts/master/docs/pdsi_bins.png" width="400" height="250">

We solve binary classification problem, where threshold for a drought could be adjusted in config file.

## Preprocessing ##

Input is geospatial monthly data, downloaded as .tif from public sources (e.g. from Google Earth Engine) and put into "data/raw" folder. Naming convention is "region_feature.tif". Please run

```
python preprocess.py --region region_name --band feature_name
```

Results (both as .csv and .npy files) could be found in 

## Training ##

To train model - first, change configs of datamodule and network (if necessary) - and then run
```
python train.py --config==train.yaml
```

Experiments results can be tracked via Comet ML (please add your token to logger config file or export it as enviromental variable)

## Inference ##

To run model on test dataset, calculate metrics and save predictions - first, change configs of datamodule and network (if necessary), add path to model checkpoint - and then run
```
python test.py --config==test.yaml

