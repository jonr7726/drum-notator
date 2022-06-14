AUDIO_RATE = 48000 # Must be constant so that input size to network is the same
MAX_BPM = 480 # Max bpm for audio detection -not max bpm for metronome (i.e. semiquavers at 50 bpm would be 200 max_bpm)
MIN_PROMINENCE = 0.025 # Minimum amplitude from peak to lowest contour line for peak to count
SMOOTH_DISTANCE = 2500 # Distance in samples to average datapoints over for finding peaks

MIN_DISTANCE =  int(AUDIO_RATE / (MAX_BPM / 60))

EXTENSIONS = ["mp3"]