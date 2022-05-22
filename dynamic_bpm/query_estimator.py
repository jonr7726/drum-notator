import tensorflow as tf

from dynamic_bpm import ESTIMATOR, BATCH_SIZE, MASK_VAL

# Import model
model = tf.keras.models.load_model(ESTIMATOR)

# Gets durations of peaks (as fraction of beat)
def get_durations_static(spb, peaks):
	durations = []

	# Find durations with distances between peaks
	for i in range(len(peaks) - 1):
		durations.append((peaks[i + 1] - peaks[i]) / spb)

	# Fill remaining bar (no next peak to distance off)
	durations.append(4 - (sum(durations) % 4))

	return durations

def get_durations_dynamic(initial_spb, peaks):
	distances = []

	# Normalise peaks to initial samples per beat
	for i in range(len(peaks) - 1):
		distances.append(peaks[i] / initial_spb)

	# Add masking values to end to ensure fixed batch size
	padding = [MASK_VAL for i in range(BATCH_SIZE - (len(distances) % BATCH_SIZE))]
	distances.extend(padding)

	durations = []
	for batch in range(int((len(peaks) - 1) / BATCH_SIZE)):
		spbs = model(tf.constant(distances[batch:(batch + BATCH_SIZE)], shape=(1, BATCH_SIZE, 1), dtype=tf.float32)).numpy()
		for i in range(BATCH_SIZE):
			# Find durations with distances between peaks and spb at each peak
			durations.append((peaks[i + 1 + (BATCH_SIZE * batch)] - peaks[i + (BATCH_SIZE * batch)]) * (spbs[0][i][0]/ initial_spb))
	# Fill remaining bar (no next peak to distance off)
	durations.append(4 - (sum(durations) % 4))

	return durations



