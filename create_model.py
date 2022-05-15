import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from classifier import TRAINING_PATH, MODEL_PATH, BUFFER_SIZE

import pickle

data_images = [] # Mel-spectrograms from audio files 
data_labels = [] # Corresponding label for each data_image

for directory in os.listdir(TRAINING_PATH):
    if os.path.isdir(TRAINING_PATH + directory):
        for file in os.listdir(TRAINING_PATH + directory):
            if file.split('.')[-1] == 'p':
                
                data_file = open(TRAINING_PATH + directory + '/' + file, 'rb')
                data = pickle.load(data_file)
                data_file.close()
                
                data_images += data[0]
                data_labels += data[1]
        
# Create instance of model
model = tf.keras.Sequential(
    [
        tf.keras.layers.Conv2D(4, (3, 3), activation='relu', input_shape=(24, 128, 1)),
        tf.keras.layers.MaxPooling2D((2,2)),
        tf.keras.layers.Conv2D(4, (3, 3), activation='relu'),
        tf.keras.layers.Conv2D(2, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D((2,2)),
        tf.keras.layers.Flatten(),
        #tf.keras.layers.Dense(96, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(8, activation='sigmoid')
    ]
)

# Create shuffled training dataset
train_dataset = tf.data.Dataset.from_tensor_slices((data_images, data_labels))
train_dataset = train_dataset.shuffle(buffer_size=BUFFER_SIZE).batch(20)

# Compile model ready for training
model.compile(
    optimizer=tf.keras.optimizers.Adam(), # Using Adam optimiser algorithm
    loss=tf.keras.losses.BinaryCrossentropy(), # This loss (opposed to SparseCrossentropy) allows multiple categories to be active at once
    metrics=['accuracy'] # Measure success by how often our output is correct
)

# Train model again, using multiple instruments as well
model.fit(
    train_dataset, # Expected Inputs and Outputs
    epochs=15 # Number of times to iterate over data
)

# Save model
model.save(MODEL_PATH)

# Print out the structure of the model
model.summary()