
from notation import INSTRUMENTS, HI_HAT, HI_HAT_OPEN, HI_HAT_CLOSED

# FOR CLOSED HI-HAT SEE:
# https://lilypond.org/doc/v2.22/Documentation/learning/articulations-and-dynamics#articulations

##########################
### Notation Constants ###
##########################

style_table = """
#(define style_table '(
    (hihat cross #f 5)
    (openhihat cross "open" 5)
    (closedhihat cross "stopped" 5)
    (pedalhihat cross #f -3)

    (ridecymbal cross #f 4)
    (ridebell triangle #f 4)
    (crashcymbal xcircle #f 5)

    (snare default #f 1)
    (bassdrum default #f -3)

    (himidtom default #f 3)
    (lowmidtom default #f 2)
    (highfloortom default #f -1)
    (lowfloortom default #f -2)
))
"""
# (See http://lilypond.org/doc/v2.22/Documentation/notation/common-notation-for-percussion#custom-percussion-staves)

up_name = "up"
down_name = "down"

up_voice_options = [
]
down_voice_options = [
    # Prevent tuplets to show
    "\\omit TupletNumber",
    "\\omit TupletBracket"
]

staff = f"""
\\new DrumStaff <<
    \\set DrumStaff.drumStyleTable = #(alist->hash-table style_table)
    \\new DrumVoice {{ \\voiceOne \\{up_name} }}
    \\new DrumVoice {{ \\voiceTwo \\{down_name} }}
>>"""
# See (https://lilypond.org/doc/v2.22/Documentation/notation/multiple-voices#single_002dstaff-polyphony)

repeat_counter_bar_interval = 4




##########################
### Notation Functions ###
##########################

def get_instruments(instrument_indexs):
    instruments = []
    open_hh = False
    for peak in instrument_indexs:
        instruments.append([])
        for instrument_index in peak:
            # Get instrument from index
            instrument = INSTRUMENTS[instrument_index]

            if open_hh and instrument == HI_HAT:
                # Add closed hi-hat if previously had open hi-hat
                instruments[-1].append(HI_HAT_CLOSED)
                open_hh = False
            else:
                # Otherwise, add instrument to list
                instruments[-1].append(instrument)
                if instrument == HI_HAT_OPEN:
                    open_hh = True

    return instruments

def get_tuplet(lilypond_string):
    return "\\tuplet 3/2 { " + lilypond_string + " }"
    # (See https://lilypond.org/doc/v2.22/Documentation/notation/writing-rhythms#tuplets)

def get_lilypond_instruments(note_instruments, default="r"):
    if len(note_instruments) == 0:
        return default
    else:
        return "<" + " ".join(note_instruments) + ">"
        # (See https://lilypond.org/doc/v2.22/Documentation/notation/single-voice#chorded-notes)

# Each arg is an array of lilypond instruments
# Each instruments arg after note is "and", but instruments within the arg are "or"
def note_has_instruments(note, *args):
    for instruments in args:
        has_any = False
        for instrument in instruments:

            if instrument in note:
                has_any = True
                break

        if not has_any:
            return False

    return True

def make_bar(bar):
    return "    " + bar + "\n"

def make_bars(bars):
    return "".join([make_bar(bar) for bar in bars])

def make_repeat_bars(bars, repeat_times):
    # Create bars
    repeat_bars = "".join(["    " + make_bar(bar) for bar in bars])

    # Set nth bar repeat counter
    nth_bar = int(len(bars) / repeat_counter_bar_interval)

    return (
        # Set repeat counter
        make_bar(f"\\set repeatCountVisibility = #(every-nth-repeat-count-visible {nth_bar})") +
        make_bar(f"\\repeat percent {repeat_times + 1} {{") +
            repeat_bars +
        make_bar("}")
        # (See https://lilypond.org/doc/v2.22/Documentation/notation/short-repeats#percent-repeats)
    )

def make_score(up_voice, down_voice):

    def make_voice(name, voice_options, voice):
        return (
            name + " = \\drummode {\n" +
            # (See https://lilypond.org/doc/v2.22/Documentation/notation/common-notation-for-percussion#basic-percussion-notation)
                make_bars(voice_options) +
                voice +
            "}\n"
        )

    up_voice = make_voice(up_name, up_voice_options, up_voice)
    down_voice = make_voice(down_name, down_voice_options, down_voice)

    return (
        style_table + up_voice + down_voice + staff
    )