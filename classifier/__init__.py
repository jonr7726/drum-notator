TRAINING_PATH = "dat/training/"
MODEL_PATH = "classifier/drum_classifier_model"
MIN_CONFIDENCE = 0.5

BUFFER_SIZE = 4096

OPEN_HI_HAT_LABEL = "hi-hat_open"
HI_HAT_LABEL = "hi-hat"

LABELS = [ # Equivilent to folder names in path_training
	"bass",
	"snare",
	"tom_1",
	"tom_2",
	"floor_tom",
	HI_HAT_LABEL,
	OPEN_HI_HAT_LABEL,
	"ride",
	"ride_bell",
	"crash"
]