import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2" # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from classifier import CLASSIFIER_TRAINING, CLASSIFIER, BUFFER_SIZE

import pickle

# Read data set
data_file = open(CLASSIFIER_TRAINING, "rb")
data = pickle.load(data_file)
data_file.close()

data_images = data[0] # Mel-spectrograms from audio files 
data_labels = data[1] # Corresponding label for each data_image
        
# Create model
model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(6, (3, 3), activation="relu", input_shape=(24, 128, 1)),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Conv2D(6, (3, 3), activation="relu"),
    tf.keras.layers.MaxPooling2D((2, 2)),
    tf.keras.layers.Conv2D(6, (3, 3), activation="relu"),
    tf.keras.layers.Flatten(),

    tf.keras.layers.Dense(96, activation="relu"),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(10, activation="sigmoid")
])

# Create shuffled training dataset
train_dataset = tf.data.Dataset.from_tensor_slices((data_images, data_labels))
train_dataset = train_dataset.shuffle(buffer_size=BUFFER_SIZE).batch(20)

# Compile model ready for training
model.compile(
    optimizer=tf.keras.optimizers.Adam(),
    loss=tf.keras.losses.BinaryCrossentropy(),
    metrics=["accuracy", "mean_absolute_error"]
)

# Train model
model.fit(
    train_dataset,
    epochs=10
)

# Save model
model.save(CLASSIFIER)

# Print out the structure of the model
model.summary()