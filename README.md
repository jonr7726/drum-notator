# Drum Notator
Program to create drum notation (as pdf or png), given an audio input (as mp3).

## Dependencies
- TensorFlow
- Mingus (and LilyPond)
- MatPlotLib
- SciPy
- Pickle

## Running Code

First ensure audio training data is populated in 'dat/training/...'

Generate data to train neural networks
```
> generate_data.py
```

Train and export neural networks
```
> create_bpm_estimator.py
> create_instrument_classifier.py
```

Next, place input files to 'dat/testing/' and run main program
```
> main.py
```

Outputs will be placed in 'dat/notation_output/' folder, and will contain text and pdf files. Text files can be edited and recompiled with
```
> compile_string.py
> <desired file, or folder of files>
```

## Known Issues
Using dynamic BPMs (that fluctuate throughout playing) is currently not very accurate due to vanishing gradient in RNN training for moving BPM estimator.