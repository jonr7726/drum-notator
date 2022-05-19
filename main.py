import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2" # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from audio import audio
from audio import bpm_functions
from notation import notation
from classifier import query_model

from audio import EXTENSIONS
PATH_INPUT = "dat/testing/"
PATH_OUTPUT = "dat/notation_output/"

def get_boolean_input(prompt_string):
    return input(prompt_string).strip().lower() in ["yes", "y", "true", "t"]

# Notate each file in testing directory, send output to notation directory
for file in os.listdir(PATH_INPUT):
    if file.split(".")[-1].lower() in EXTENSIONS:
    
        print("---", file, "---")
        visualise = get_boolean_input("Enable volume sentitivity tuning for note detection? (Y/N) ")
    
        # Get images, peaks and bpm from file
        print("Reading file...")
        data_images, peaks, bpm = audio.audio_to_images_notation(PATH_INPUT+file, visualise=visualise)
        
        # Get instruments
        print("Classifying drums...")
        instrument_indexs = query_model.get_instruments(data_images)

        # Get custom options
        try:
            bpm = float(input(f"BPM: {bpm}\nBPM: "))
            print(f"using BPM of {bpm}")
        except ValueError:
            print("Invalid input, continuing.")

        dynamic_bpm = get_boolean_input("Use dynamic BPM (use if not playing to a click)? (Y/N) ")

        # Get durations
        durations = query_model.get_durations(peaks, bpm_functions.convert_spb_bpm(bpm))

        # Initialise score
        score = notation.Score(instrument_indexs, durations, True, dynamic_bpm, True)
        
        # Convert score to notation and save file
        score.create_score(PATH_OUTPUT + file.split(".")[0])
        