import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2" # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from audio import audio, bpm_functions
from notation.score import Score
from classifier import query_classifier
from dynamic_bpm import query_estimator

from audio import EXTENSIONS
PATH_INPUT = "dat/testing/"
PATH_OUTPUT = "dat/notation_output/"

def boolean_input(prompt_string):
    return input(prompt_string + " (Y/N) ").strip().lower() in ["yes", "y", "true", "t"]

# Notate each file in testing directory, send output to notation directory
for file in os.listdir(PATH_INPUT):
    if file.split(".")[-1].lower() in EXTENSIONS:
    
        print("---", file, "---")
        visualise = boolean_input("Enable volume sentitivity tuning for note detection?")
    
        # Get images, peaks and samples per beat from file
        print("Reading file...")
        data_images, peaks, bpm = audio.audio_to_images_notation(PATH_INPUT+file, visualise=visualise)
        
        # Get instruments
        print("Classifying drums...")
        instrument_indexs = query_classifier.get_instruments(data_images)

        # Get note durations
        if boolean_input("Use dynamic BPM (use if not playing to a click)?"):
            # Get durations
            durations = query_estimator.get_durations_dynamic(bpm_functions.convert_spb_bpm(bpm), peaks)
        else:
            # Allow alternative bpm entry
            try:
                bpm = float(input(f"BPM: {bpm}\nBPM: "))
                print(f"using BPM of {bpm}")
            except ValueError:
                print("Invalid input, continuing.")

            # Get durations
            durations = query_estimator.get_durations_static(bpm_functions.convert_spb_bpm(bpm), peaks)

        #repeats = boolean_input("Use bar repeats? ")
        repeats = False
        # Override repeats to prevent this from running as there are currently errors in that module

        # Initialise score
        score = Score(instrument_indexs, durations, repeats)
        
        # Convert score to notation and save file
        score.create_score(PATH_OUTPUT + file.split(".")[0])
        