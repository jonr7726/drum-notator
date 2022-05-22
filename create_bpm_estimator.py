import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from dynamic_bpm import ESTIMATOR_TRAINING, ESTIMATOR, BATCH_SIZE, MASK_VAL

import pickle
import matplotlib.pyplot as plt

# Read data set
data_file = open(ESTIMATOR_TRAINING, "rb")
data = pickle.load(data_file)
data_file.close()

train_inputs = data[0]
train_outputs = data[1]

# Create model
model = tf.keras.models.Sequential([
    tf.keras.layers.Masking(mask_value=MASK_VAL, batch_input_shape=(1, BATCH_SIZE, 1)),
    tf.keras.layers.LSTM(30, stateful=True, return_sequences=True),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10, activation="relu"),
    tf.keras.layers.Dense(5, activation="relu"),
    tf.keras.layers.Dense(1)
])

# Compile model ready for training
model.compile(
    optimizer=tf.keras.optimizers.Adam(),
    loss=tf.keras.losses.MeanSquaredError(),
    metrics=["mean_absolute_error"]
)

# Train model on file
def train_file(file_inputs, file_outputs):
    file_loss = 0
    file_absolute_error = 0

    # Add masking values to end to ensure fixed batch size
    if len(file_inputs) % BATCH_SIZE != 0:
        padding = [MASK_VAL for i in range(BATCH_SIZE - (len(file_inputs) % BATCH_SIZE))]
        file_inputs.extend(padding)
        file_outputs.extend(padding)

    for batch in range(0, len(file_inputs), BATCH_SIZE):
        # Format training data batch
        batch_in = tf.constant(file_inputs[batch:(batch + BATCH_SIZE)], shape=(1, BATCH_SIZE, 1), dtype=tf.float32)
        batch_out = tf.constant(file_outputs[batch:(batch + BATCH_SIZE)], shape=(1, BATCH_SIZE, 1), dtype=tf.float32)
        # Train model with batch
        loss, absolute_error = model.train_on_batch(batch_in, batch_out)
        file_loss += loss
        file_absolute_error += absolute_error

    return file_loss / (len(file_inputs) / BATCH_SIZE), file_absolute_error / (len(file_inputs) / BATCH_SIZE)

# Train model
losses = []
accuracies = []
for epoch in range(20):
    total_loss = 0
    total_absolute_error = 0
    for file_inputs, file_outputs in zip(train_inputs, train_outputs):
        file_loss, file_absolute_error = train_file(file_inputs, file_outputs)

        total_loss += file_loss
        total_absolute_error += file_absolute_error

        # Reset states for next file
        model.reset_states()
    losses.append(total_loss / len(train_inputs))
    accuracies.append(total_absolute_error / len(train_inputs))
    print(f"Loss: {losses[-1]} Absolute Error: {accuracies[-1]}")

# Print loss / accuracy graphs
plt.title('Loss and Absolute Error Over Time')
plt.xlabel('Epoch')
plt.plot(range(len(losses)), losses, label = "Loss")
plt.plot(range(len(accuracies)), accuracies, label = "Absolute Error")
plt.legend()
plt.show()

# Save model
model.save(ESTIMATOR)

# Print out the structure of the model
model.summary()