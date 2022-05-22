import tensorflow as tf

from classifier import CLASSIFIER
from classifier import MIN_CONFIDENCE

# Import model
model = tf.keras.models.load_model(CLASSIFIER)

# Gets all instruments classified in each note, given the minimum confidence threshold for a classification to be valid
# Instruments is returned as a 2D list where each element is a list of integers, representing each index in labels for valid instruements in that peak
def get_instruments(peak_spectograms):
	instruments = []

	for classification_labels in model(peak_spectograms).numpy():
		print(classification_labels.round(2))

		# Find instruments in each peak
		peak_instruments = []
		for i in range(0, len(classification_labels)):
			if classification_labels[i] > MIN_CONFIDENCE:
				peak_instruments.append(i)

		# If no instruments are above threshold, choose instrument with highest confidence
		if len(peak_instruments) == 0:
			peak_instruments = [tf.argmax(classification_labels).numpy()]

		# Add peak's instruments to list
		instruments.append(peak_instruments)

	return instruments