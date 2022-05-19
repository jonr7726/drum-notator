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

            print(spb_peaks, rhythm_peaks)

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
                    print(rhythm_index)
                    spb_count += 1
                    spb_index += 1
                    spb_sum += spb_peaks[spb_index]
                    total_spb_duration += spb_peaks[spb_index]

                if spb_count == 0:
                    spb = spb_peaks[spb_index]
                else:
                    spb = spb_sum / spb_count

                train_inputs[-1][1].append(rhythm_peaks[rhythm_index])
                train_outputs[-1].append(spb)

from dynamic_bpm import query_bpm_estimator
from notation import notation

train_outputs[0].insert(0, train_inputs[0][0])

print(train_inputs)
print(train_outputs)

duration_adjustments = query_bpm_estimator.get_duration_adjustments(train_inputs[0][0], train_outputs[0])
durations = query_bpm_estimator.get_durations(train_inputs[0][0], train_inputs[0][1])
instrument_indexs = [[1] for i in range(len(durations))]

score = notation.Score(instrument_indexs, durations, True, True, duration_adjustments)

score.create_score("test")

input(": ")

# Create model
model = tf.keras.models.Sequential([
    tf.keras.layers.LSTM(10, return_sequences=True),
    #tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(1)
])

# Compile model ready for training
model.compile(
    optimizer=tf.keras.optimizers.Adam(),
    loss=tf.keras.losses.MeanSquaredError(),
    metrics=['accuracy']
)

model.summary()

# Create training dataset
train_dataset = tf.data.Dataset.from_tensor_slices(train_inputs, train_outputs)

# Train model
model.fit(
    train_dataset, # Expected Inputs and Outputs
    epochs=5 # Number of times to iterate over data
)

# Save model
model.save(MODEL_PATH)

# Print out the structure of the model
model.summary()

print(model.states)