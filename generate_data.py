import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2" # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from audio import audio

import pickle

from audio import EXTENSIONS
from classifier import LABELS, HI_HAT_LABEL, OPEN_HI_HAT_LABEL, CLASSIFIER_TRAINING
from dynamic_bpm import ESTIMATOR_TRAINING

TRAINING_INSTRUMENTS = "dat/training/instruments/"
TRAINING_RHYTHMS = "dat/training/rhythms/"
TRAINING_JAMS = "dat/training/jams/"

def boolean_input(prompt_string):
    return input(prompt_string + " (Y/N) ").strip().lower() in ["yes", "y", "true", "t"]

generate_instruments = boolean_input("Generate instrument data?")
generate_rhythms = boolean_input("Generate rhythm data?")
generate_jams = boolean_input("Generate jam data?")

overwrite = boolean_input("Overwrite existing data?")

if generate_instruments or generate_jams:
    # Generate classification labels
    labels = {} # Dictionary of labels used to classify instruments

    # Add single instrument labels (as 1D tensor with a 1 in the index repesenting the corresponding label)
    for i in range(0, len(LABELS)):
        labels[LABELS[i]] = tf.one_hot(i, len(LABELS))

if generate_instruments:
    # Add each audio file in training sub-directories to data
    for directory in os.listdir(TRAINING_INSTRUMENTS):
        if os.path.isdir(TRAINING_INSTRUMENTS + directory):
        
            open_hh = False
            # Compute all present labels in the folder (1 for present, 0 for absent)
            classification_label = tf.zeros(len(LABELS))
            for label in directory.split(" "):
                if label == OPEN_HI_HAT_LABEL:
                    open_hh = True
                else:
                    classification_label += labels[label]
                
            # Get data from all audio files in directory
            files = os.listdir(TRAINING_INSTRUMENTS + directory)
            for file in files:
                file, extension = file.split(".")

                # Ensure file is of valid type, and has not already been processed (unless overwriting)
                if extension.lower() in EXTENSIONS and (file + ".p" not in files or overwrite):
                    file = TRAINING_INSTRUMENTS + directory + "/" + file
            
                    train_inputs = [] # Mel-spectrograms from audio file
                    train_outputs = [] # Corresponding labels for each data_image
                
                    # Retrieve Mel-spectrograms from file
                    spectrograms = audio.audio_to_images(file + "." + extension, True)

                    if open_hh:
                        # If this data is open hi-hats, then every second note is a closed hi-hat
                        closed = False
                        for spectrogram in spectrograms:
                            train_inputs.append(spectrogram)
                            if closed:
                                # Only closed hi-hat
                                train_outputs.append(labels[HI_HAT_LABEL])
                            else:
                                # Open hi-hat + all other labels present
                                train_outputs.append(classification_label + labels[OPEN_HI_HAT_LABEL])
                    else:
                        # Otherwise add Mel-spectrograms and classification labels as usual
                        for spectrogram in spectrograms:
                            train_inputs.append(spectrogram)
                            train_outputs.append(classification_label)
                            
                    # Export data to pickle file for later use
                    save_file = open(file + ".p", "wb")
                    pickle.dump([train_inputs, train_outputs], save_file)
                    save_file.close()

if generate_rhythms:
    # Add each file pair in rhythms to data
    for directory in os.listdir(TRAINING_RHYTHMS):
        if os.path.isdir(TRAINING_RHYTHMS + directory):
            files = os.listdir(TRAINING_RHYTHMS + directory)
            if directory + ".p" not in files or overwrite:
                # Get files of appropriate extensions
                files = [file for file in files if file.split(".")[-1].lower() in EXTENSIONS]

                if len(files) == 2:
                    for file in files:
                        peaks = audio.audio_to_peaks(TRAINING_RHYTHMS + directory + "/" + file, True)

                        # Calculate peak distances
                        for i in range(len(peaks) - 1):
                            peaks[i] = peaks[i + 1] - peaks[i]

                        if file.split(".")[0][-4:].lower() == " bpm":
                            # Samples per beat file (samples per beat)
                            spb_peaks = peaks[:-1]
                        else:
                            # Rhythm file
                            initial_spb = (peaks[0] + peaks[1] + peaks[2] + peaks[3]) / 4
                            rhythm_peaks = peaks[4:-1]

                    train_inputs = []
                    train_outputs = []

                    total_rhythm_duration = 0
                    total_spb_duration = spb_peaks[0]
                    spb_index = 0
                    for rhythm_index in range(len(rhythm_peaks)):
                        total_rhythm_duration += rhythm_peaks[rhythm_index]
                        spb_sum = 0
                        spb_count = 0
                        while spb_index + 1 < len(spb_peaks) and total_spb_duration < total_rhythm_duration:
                            spb_count += 1
                            spb_index += 1
                            spb_sum += spb_peaks[spb_index]
                            total_spb_duration += spb_peaks[spb_index]

                        if spb_count == 0:
                            spb = spb_peaks[spb_index]
                        else:
                            spb = spb_sum / spb_count

                        train_inputs.append(rhythm_peaks[rhythm_index] / initial_spb)
                        train_outputs.append(spb / initial_spb)

                    # Export data to pickle file for later use
                    save_file = open(TRAINING_RHYTHMS + directory + "/" + directory + ".p", "wb")
                    pickle.dump([train_inputs, train_outputs], save_file)
                    save_file.close()

if generate_jams:
    # Add each file pair in jams to data
    for directory in os.listdir(TRAINING_JAMS):
        if os.path.isdir(TRAINING_JAMS + directory):
            files = os.listdir(TRAINING_JAMS + directory)
            if directory + ".p" not in files or overwrite:
                # Get files of appropriate extensions
                files = [file for file in files if file.split(".")[-1].lower() in EXTENSIONS]

                # Get classification labels
                instrument_file = TRAINING_JAMS + directory + "/" + directory + ".txt"
                with open(instrument_file, "r") as file:
                    instruments = file.read().strip().split("\n")
                    classification_labels = []
                    for i in range(len(instruments)):
                        current_instruments = instruments[i].split(" ")
                        classification_labels.append(tf.zeros(len(LABELS)))
                        for instrument in instruments[i].strip().split(" "):
                            classification_labels[i] += labels[instrument]

                # Get images and rhythm data
                if len(files) == 2:
                    for file in files:
                        file = TRAINING_JAMS + directory + "/" + file
                        peaks = audio.audio_to_peaks(file, True)

                        # Calculate peak distances
                        distances = []
                        for i in range(len(peaks) - 1):
                            distances.append(peaks[i + 1] - peaks[i])

                        if file.split(".")[0][-4:].lower() == " bpm":
                            # Samples per beat file (samples per beat)
                            spb_peaks = distances
                        else:
                            # Rhythm file
                            initial_spb = (distances[0] + distances[1] + distances[2] + distances[3]) / 4
                            rhythm_peaks = distances[4:]
                            spectograms = audio.audio_to_images(file, peaks=peaks[4:])
                            images = []
                            for spectogram in spectograms:
                                images.append(spectogram)

                    rhythm_inputs = []
                    rhythm_outputs = []

                    total_rhythm_duration = 0
                    total_spb_duration = spb_peaks[0]
                    spb_index = 0
                    for rhythm_index in range(len(rhythm_peaks)):
                        total_rhythm_duration += rhythm_peaks[rhythm_index]
                        spb_sum = 0
                        spb_count = 0
                        while spb_index + 1 < len(spb_peaks) and total_spb_duration < total_rhythm_duration:
                            spb_count += 1
                            spb_index += 1
                            spb_sum += spb_peaks[spb_index]
                            total_spb_duration += spb_peaks[spb_index]

                        if spb_count == 0:
                            spb = spb_peaks[spb_index]
                        else:
                            spb = spb_sum / spb_count

                        rhythm_inputs.append(rhythm_peaks[rhythm_index] / initial_spb)
                        rhythm_outputs.append(spb / initial_spb)

                    # Export data to pickle file for later use
                    save_file = open(TRAINING_JAMS + directory + "/" + directory + ".p", "wb")
                    pickle.dump([[images, classification_labels], [rhythm_inputs, rhythm_outputs]], save_file)
                    save_file.close()

# Generate data sets
instrument_inputs = []
instrument_outputs = []
rhythm_inputs = []
rhythm_outputs = []
for training_path in [TRAINING_INSTRUMENTS, TRAINING_RHYTHMS, TRAINING_JAMS]:
    for directory in os.listdir(training_path):
        if os.path.isdir(training_path + directory):
            for file in os.listdir(training_path + directory):
                if file.split(".")[-1] == "p":
                    data_file = open(training_path + directory + "/" + file, "rb")
                    data = pickle.load(data_file)
                    data_file.close()
                    
                    if training_path == TRAINING_INSTRUMENTS:
                        instrument_inputs += data[0]
                        instrument_outputs += data[1]
                    elif training_path == TRAINING_RHYTHMS:
                        rhythm_inputs.append(data[0])
                        rhythm_outputs.append(data[1])
                    else:
                        instrument_inputs += data[0][0]
                        instrument_outputs += data[0][1]
                        rhythm_inputs.append(data[1][0])
                        rhythm_outputs.append(data[1][1])

# Save data sets
save_file = open(CLASSIFIER_TRAINING, "wb")
pickle.dump([instrument_inputs, instrument_outputs], save_file)
save_file.close()

save_file = open(ESTIMATOR_TRAINING, "wb")
pickle.dump([rhythm_inputs, rhythm_outputs], save_file)
save_file.close()