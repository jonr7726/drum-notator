
# Gets durations of peaks (as fraction of beat)
def get_durations(spb, peak_distances):
	durations = []

	# Find durations with distances between peaks
	for i in range(len(peak_distances)):
		durations.append((peak_distances[i]) / spb)

	# Fill remaining bar (no next peak to distance off)
	durations.append(4 - (sum(durations) % 4))

	return durations

def get_duration_adjustments(initial_spb, spbs):
	for i in range(len(spbs)):
		spbs[i] = initial_spb / spbs[i]

	return spbs