import tensorflow as tf

from classifier import MODEL_PATH

# Import model
model = tf.keras.models.load_model(MODEL_PATH)

# Gets all instruments classified in each note, given the minimum confidence threshold for a classification to be valid
def get_instruments(peak_spectograms, min_confidence):
	instruments = []

	for classification_labels in model(peak_spectograms).numpy():
		print(output_bits.round(2))

		# Find instruments in each peak
		peak_instruments = []
		for i in range(0, len(classification_labels)):
			if classification_labels[i] > min_confidence:
				peak_instruments.append(constants.instruments[i])

			# If no instruments are above threshold, choose instrument with highest confidence
			if len(peak_instruments) == 0:
				peak_instruments = [constants.instruments[argmax(classification_labels)]]

		# Add peak's instruments to list
		instruments.append(peak_instruments)

	return instruments

# Gets durations of peaks (as fraction of beat)
def get_durations(peaks, samples_per_beat):
	durations = []

	# Find durations with distances between peaks
	for i in range(len(peaks) - 1):
		durations.append((peaks[i + 1] - peaks[i]) / samples_per_beat)

	# Fill remaining bar (no next peak to distance off)
	durations.append(4 - (sum(durations) % 4))

	return durations