import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from audio import EXTENSIONS
from classifier import LABELS

from audio import audio

import pickle

labels = {} # Dictionary of labels used to classify instruments

# Add single instrument labels (as 1D tensor with a 1 in the index repesenting the corresponding label)
for i in range(0, len(LABELS)):
    labels[LABELS[i]] = tf.one_hot(i, len(LABELS))
    
# Add each audio file in training sub-directories to data
for directory in os.listdir(TRAINING_PATH):
    if os.path.isdir(TRAINING_PATH + directory):
    
        classification_label = 0
        for label in directory.split(' '):
            classification_label += labels[label]
            
        for file in os.listdir(TRAINING_PATH + directory):
            if file.split('.')[-1] in EXTENSIONS:
                file = TRAINING_PATH + directory + '/' + file
        
                data_images = [] # Mel-spectrograms from audio file
                data_labels = [] # Corresponding labels for each data_image
            
                spectrograms, _ = audio_to_images(file, True)

                for image in spectrograms:
                    data_images.append(image)
                    data_labels.append(classification_label)
                        
                save_file = open(file.split('.')[0]+'.p', 'wb')
                pickle.dump([data_images, data_labels], save_file)
                save_file.close()
