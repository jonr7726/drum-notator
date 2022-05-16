import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2" # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from audio import audio

import pickle

from audio import EXTENSIONS
from classifier import LABELS, TRAINING_PATH, HI_HAT_LABEL, OPEN_HI_HAT_LABEL

labels = {} # Dictionary of labels used to classify instruments

# Add single instrument labels (as 1D tensor with a 1 in the index repesenting the corresponding label)
for i in range(0, len(LABELS)):
    labels[LABELS[i]] = tf.one_hot(i, len(LABELS))

overwrite = input("Overwrite existing data? (Y/N) ").strip().lower() in ["yes", "y", "true", "t"]
    
# Add each audio file in training sub-directories to data
for directory in os.listdir(TRAINING_PATH):
    if os.path.isdir(TRAINING_PATH + directory):
    
        open_hh = False
        # Compute all present labels in the folder (1 for present, 0 for absent)
        classification_label = tf.zeros(len(LABELS))
        for label in directory.split(" "):
            if label == OPEN_HI_HAT_LABEL:
                open_hh = True
            else:
                classification_label += labels[label]
            
        # Get data from all audio files in directory
        files = os.listdir(TRAINING_PATH + directory)
        for file in files:
            file, extension = file.split(".")

            # Ensure file is of valid type, and has not already been processed (unless overwriting)
            if extension.lower() in EXTENSIONS and (file + ".p" not in files or overwrite):
                file = TRAINING_PATH + directory + "/" + file
        
                data_images = [] # Mel-spectrograms from audio file
                data_labels = [] # Corresponding labels for each data_image
            
                # Retrieve Mel-spectrograms from file
                spectrograms = audio.audio_to_images(file + "." + extension, True)

                if open_hh:
                    # If this data is open hi-hats, then every second note is a closed hi-hat
                    closed = False
                    for spectrogram in spectrograms:
                        data_images.append(spectrogram)
                        if closed:
                            # Only closed hi-hat
                            data_labels.append(labels[HI_HAT_LABEL])
                        else:
                            # Open hi-hat + all other labels present
                            data_labels.append(classification_label + labels[OPEN_HI_HAT_LABEL])
                else:
                    # Otherwise add Mel-spectrograms and classification labels as usual
                    for spectrogram in spectrograms:
                        data_images.append(spectrogram)
                        data_labels.append(classification_label)
                        
                # Export data to pickle file for later use
                save_file = open(file + ".p", "wb")
                pickle.dump([data_images, data_labels], save_file)
                save_file.close()
