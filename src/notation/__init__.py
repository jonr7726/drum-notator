MAX_REPEATS = 2

# Instrument constants:
BASS = "bd"
SNARE = "sn"
HI_HAT = "hh"
HI_HAT_OPEN = "hho"
CRASH = "cymc"
RIDE = "cymr"
RIDE_BELL = "rb"
TOM_1 = "tommh"
TOM_2 = "tomml"
FLOOR_TOM = "tomfh"

HI_HAT_FOOT = "hhp"
HI_HAT_CLOSED = "hhc"
REST = "r"
INVISIBLE_REST = "s"
# (See http://lilypond.org/doc/v2.22/Documentation/notation/percussion-notes)

CYMBALS = [HI_HAT, HI_HAT_OPEN, HI_HAT_CLOSED, HI_HAT_FOOT, CRASH, RIDE, RIDE_BELL]
HI_HAT_FOOT_IMPLICATORS = [RIDE, RIDE_BELL, FLOOR_TOM] # (Non-hihat instruments that must be played with the right hand)

INSTRUMENTS = [BASS, SNARE, TOM_1, TOM_2, FLOOR_TOM, HI_HAT, HI_HAT_OPEN, RIDE, RIDE_BELL, CRASH] # Used for notation, must be in same order as labels from classifier output

SMALLEST_ERROR = (1/4)/2