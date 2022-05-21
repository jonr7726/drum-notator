import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Removes warning messages from tensorflow (due to my computer not having a GPU)

import tensorflow as tf

from audio import audio

from dynamic_bpm import TRAINING_PATH, MODEL_PATH, SMALLEST_ERROR
from audio import EXTENSIONS

train_inputs = []
train_outputs = []

for directory in os.listdir(TRAINING_PATH):
    if os.path.isdir(TRAINING_PATH + directory):
        # Get files of appropriate extensions
        files = [file for file in os.listdir(TRAINING_PATH + directory) if file.split(".")[-1] in EXTENSIONS]
        
        if len(files) == 2:
            for file in files:
                peaks = audio.audio_to_peaks(TRAINING_PATH + directory + "/" + file, False)

                # Calculate peak distances
                for i in range(len(peaks) - 1):
                    peaks[i] = peaks[i + 1] - peaks[i]

                if file.split(".")[0][-4:].lower() == " spb":
                    # Samples per beat file (samples per beat)
                    spb_peaks = peaks[:-1]
                else:
                    # Rhythm file
                    initial_spb = (peaks[0] + peaks[1] + peaks[2] + peaks[3]) / 4
                    rhythm_peaks = peaks[4:-1]

            train_inputs.append([initial_spb, []])
            train_outputs.append([])

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

                train_inputs[-1][1].append(rhythm_peaks[rhythm_index] / initial_spb)
                train_outputs[-1].append(spb / initial_spb)

# Create model
class BPM_Estimator(tf.keras.Sequential):

    def __init__(self):
        super(BPM_Estimator, self).__init__()
        self.lstm_1 = tf.keras.layers.LSTM(512, stateful=True, return_sequences=True)
        self.dropout_1 = tf.keras.layers.Dropout(0.2)
        self.lstm_2 = tf.keras.layers.LSTM(5, stateful=True, return_sequences=True)
        self.dropout_2 = tf.keras.layers.Dropout(0.2)
        self.dense_1 = tf.keras.layers.Dense(16, activation="linear")
        self.dense_2 = tf.keras.layers.Dense(8, activation="linear")
        self.dense_3 = tf.keras.layers.Dense(1)
    
    @tf.function
    def call(self, x, training=False):
        #x = self.lstm_1(x, training=training)
        #x = self.dropout_1(x, training=training)
        #x = self.lstm_2(x, training=training)
        #x = self.dropout_2(x, training=training)
        x = self.dense_1(x, training=training)
        x = self.dense_2(x, training=training)
        x = self.dense_3(x, training=training)
        return x

    def call_file(self, inputs, training=False):
        outputs = []
        spb = tf.constant(1, shape=[1,1,1])  # (Initial spb is always 1)
        for i in range(inputs.shape[0]):
            # Run model on sample, store result to pass into next
            spb = self(tf.constant([inputs[i].numpy(), spb[0][0][0].numpy()], shape=[1, 1, 2]), training=training)
            # Add result to outputs
            outputs.append(spb)

        # Reset states for next file
        self.reset_states()

        return outputs

    def train_file_old(self, inputs, expected_outputs, sample_weight=None):
        # Forward pass (calculate loss)
        with tf.GradientTape() as tape:
            # Run model on sample, store result to pass into next
            outputs = self.call_file(inputs, training=True)
            # Calculate loss
            loss = self.compute_loss(inputs, expected_outputs, outputs, sample_weight)

        # Backwards pass (train values)
        self.optimizer.minimize(loss, self.trainable_variables, tape=tape)

        # Return metrics
        metrics = self.compute_metrics(inputs, expected_outputs, outputs, sample_weight)
        metrics["distance"] = tf.math.reduce_sum(tf.abs(expected_outputs - outputs))
        return metrics

    def train_file_test(self, inputs, expected_outputs, sample_weight=None):
        # Unpack the data. Its structure depends on your model and
        # on what you pass to `fit()`.
        x, y = data

        with tf.GradientTape() as tape:
            y_pred = self(x, training=True)  # Forward pass
            # Compute the loss value
            # (the loss function is configured in `compile()`)
            loss = self.compiled_loss(y, y_pred, regularization_losses=self.losses)

        # Compute gradients
        trainable_vars = self.trainable_variables
        gradients = tape.gradient(loss, trainable_vars)
        # Update weights
        self.optimizer.apply_gradients(zip(gradients, trainable_vars))
        # Update metrics (includes the metric that tracks the loss)
        self.compiled_metrics.update_state(y, y_pred)
        # Return a dict mapping metric names to current value
        return {m.name: m.result() for m in self.metrics}

    def train_file(self, inputs, expected_outputs, sample_weight=None):
        outputs = []
        metrics = []
        total_loss = 0
        for i in range(inputs.shape[0]):
            # Forward pass (calculate loss)
            with tf.GradientTape() as tape:
                # Run model on sample, store result to pass into next
                output = self(tf.constant(inputs[i], shape=[1, 1, 1]), training=True)
                # Calculate loss
                loss = self.compute_loss(tf.constant(inputs[i], shape=[1,1,1]), tf.constant(expected_outputs[i], shape=[1,1,1]), spb, sample_weight)

            # Backwards pass (train values)
            self.optimizer.minimize(loss, self.trainable_variables, tape=tape)

            # Calculate metrics
            metric = self.compute_metrics(tf.constant(inputs[i], shape=[1,1,1]), tf.constant(expected_outputs[i], shape=[1,1,1]), spb, sample_weight)

            # Add result to outputs
            outputs.append(spb)
            metrics.append(metric)
            total_loss += loss
        
        self.reset_states()
        return total_loss, tf.math.reduce_sum(tf.abs(expected_outputs - outputs))

model = BPM_Estimator()

# Compile model ready for training
model.compile(
    optimizer=tf.keras.optimizers.Adam(),
    loss=tf.keras.losses.MeanSquaredError(),
    metrics=["accuracy"]
)

def train_model(epochs):
    # Train model
    for epoch in range(epochs):
        metrics = []
        for file in range(len(train_inputs)):
            metrics = model.train_file_old(tf.constant(train_inputs[file][1], dtype=tf.float32), tf.constant(train_outputs[file], dtype=tf.float32))
            total_loss = metrics["loss"]
            average_loss = total_loss / len(train_inputs[file][1])
            average_distance = metrics["distance"] / len(train_inputs[file][1])
            print(f"Total Loss: {total_loss} Average Loss: {average_loss} Average Distance: {average_distance}")
            """
            total_loss, total_distance = model.train_file(tf.constant(train_inputs[file][1], dtype=tf.float32), tf.constant(train_outputs[file], dtype=tf.float32))
            average_loss = total_loss / len(train_inputs[file][1])
            average_distance = total_distance / len(train_inputs[file][1])
            print(f"Total Loss: {total_loss} Average Loss: {average_loss} Average Distance: {average_distance}")
            """

train_model(200)

# Save model
model.save(MODEL_PATH)

# Print out the structure of the model
model.summary()