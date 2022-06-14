from notation import lilypond_notation
from notation.notes import Notes

from notation import MAX_REPEATS
from notation import REST, INVISIBLE_REST
from notation import BASS, SNARE, FLOOR_TOM, RIDE, HI_HAT, HI_HAT_FOOT
from notation import CYMBALS, HI_HAT_FOOT_IMPLICATORS

from math import log2
from tensorflow import argmax

from mingus.extra.lilypond import to_pdf

class Beat:
    def __init__(self, instruments, duration):
        self.instruments = instruments
        self.duration = duration

    def length(self):
        assert(len(self.instruments) == len(self.duration))
        return len(self.instruments)

class LilypondBeat(Beat):
    def __init__(self, instruments, duration, triplet_beat):
        super().__init__(instruments, duration)
        self.triplet_beat = triplet_beat

    def get_lilypond_string(self):
        lilypond_string = " ".join([self.instruments[i] + self.duration[i] for i in range(self.length())])

        if self.triplet_beat:
            lilypond_string = lilypond_notation.get_tuplet(lilypond_string)

        return lilypond_string

class Voice():
    def __init__(self, rest):
        self.bars = [] # type(bars[bar][beat]) == Beat
        self._beats_left = 0
        self.rest = rest

    def add_beat(self, beat, triplet_beat=False):
        if self._beats_left == 0:
            self._beats_left = 4
            self.bars.append([]) # Add bar

        self._beats_left -= sum(beat.duration) # (Handles beats that span over more than 1 beat, ie. minums, or crochet triplets)

        lilypond_beat = LilypondBeat([], [], triplet_beat=triplet_beat)

        for note in range(beat.length()):
            if lilypond_beat.triplet_beat or ((3 * beat.duration[note]) % 1 == 0 and beat.duration[note] % 1 != 0):
                lilypond_beat.triplet_beat = True
                sub_division = 3 # Quaver triplets (1/3)
                sub_division_lilypond = 8 # What a sub_division maps to (8th notes)
            else:
                sub_division = 4 # Semiquavers (1/4)
                sub_division_lilypond = 16 # What a sub_division maps to (16th notes)

            note_duration = beat.duration[note]
            note_instruments = beat.instruments[note]

            largest_duration = 2**int(log2(sub_division * note_duration)) # Represents the largest note that can be formed (rounds off any dot remainders)
            
            lilypond_beat.duration.append(str(int(sub_division_lilypond / largest_duration)))

            largest_duration /= sub_division # Convert back to regular duration to test if dotted note

            if largest_duration * 1.5 == note_duration:
                # Dotted note
                lilypond_beat.duration[-1] += "."

            lilypond_beat.instruments.append(lilypond_notation.get_lilypond_instruments(note_instruments, default=self.rest))

            assert(note_duration == largest_duration or note_duration == largest_duration * 1.5)

        self.bars[-1].append(lilypond_beat)

    def get_lilypond_bars(self):
        lilypond_bars = [" ".join([beat.get_lilypond_string() for beat in bar]) for bar in self.bars]

        return lilypond_bars

class Score:

    def __init__(self, instrument_indexs, durations, use_repeats=True, triplets_enabled=True):
        if use_repeats:
            self.max_repeats = MAX_REPEATS
        else:
            self.max_repeats = 0

        notes = Notes(lilypond_notation.get_instruments(instrument_indexs), durations, triplets_enabled).get_notes()

        self.up = Voice(rest=REST)
        self.down = Voice(rest=INVISIBLE_REST)

        self._split_voice(notes)

    # Sets instruments and durations for each up/down voices by splitting notes
    # Put bass down if down snare or down bass in beat or down snare in bar and cymbal in beat or multiple instruments in note
    # Put snare down if down snare in beat or bass in bar and cymbal in beat
    # Put floor tom down if snare in beat down
    # Put hi-hat down if down hi-hat in beat or a instrument that must be played with the right hand in note
    # Put everything else up
    def _split_voice(self, notes):

        def find_down_notes(bar):
            bar_has_bass = False
            bar_has_snare = False
            for beat in bar:
                for note in beat:
                    if BASS in note[0]:
                        bar_has_bass = True
                    if SNARE in note[0]:
                        bar_has_snare = True

                    if bar_has_bass and bar_has_snare:
                        break

            beat_down_bass = []
            beat_down_snare = []
            beat_down_hi_hat = []
            for beat in bar:
                beat_down_bass.append(False)
                beat_down_snare.append(False)
                beat_down_hi_hat.append(False)

                for note in beat:
                    if (
                        BASS in note[0] and
                        len(note[0]) > 1 or
                        (bar_has_snare and lilypond_notation.note_has_instruments(note[0], CYMBALS))
                    ):
                        beat_down_bass[-1] = True

                    if (
                        SNARE in note[0] and 
                        (bar_has_bass and lilypond_notation.note_has_instruments(note[0], CYMBALS))
                    ):
                        beat_down_snare[-1] = True

                    if (
                        HI_HAT in note[0] and
                        (lilypond_notation.note_has_instruments(note[0], HI_HAT_FOOT_IMPLICATORS))
                    ):
                        beat_down_hi_hat[-1] = True

            return beat_down_bass, beat_down_snare, beat_down_hi_hat

        def split_notes(beat_notes, down_bass, down_snare, down_hi_hat):
            up_beat_notes = Beat([], [])
            down_beat_notes = Beat([], [])

            for note in beat_notes:

                up_instruments = []
                down_instruments = []
                for instrument in note[0]:
                    if (
                        instrument == BASS and (down_bass or down_snare) or
                        instrument == SNARE and down_snare or
                        instrument == FLOOR_TOM and down_snare
                    ):
                        down_instruments.append(instrument)

                    elif instrument == HI_HAT and down_hi_hat:
                        down_instruments.append(HI_HAT_FOOT)

                    else:
                        up_instruments.append(instrument)

                if down_beat_notes.length() > 0 and down_instruments == []:
                    down_beat_notes.duration[-1] += note[1]
                else:
                    down_beat_notes.duration.append(note[1])
                    down_beat_notes.instruments.append(down_instruments)

                # ((down_beat_notes.length() > 0)  =>  (up_beat_notes.length() > 0))
                if up_beat_notes.length() > 0 and up_instruments == []:
                    up_beat_notes.duration[-1] += note[1]
                else:
                    up_beat_notes.duration.append(note[1])
                    up_beat_notes.instruments.append(up_instruments)

            return up_beat_notes, down_beat_notes

        for bar in notes:
            beat_down_bass, beat_down_snare, beat_down_hi_hat = find_down_notes(bar)

            for beat, down_bass, down_snare, down_hi_hat in zip(bar, beat_down_bass, beat_down_snare, beat_down_hi_hat):
                up_beat_notes, down_beat_notes = split_notes(beat, down_bass, down_snare, down_hi_hat)

                self.up.add_beat(up_beat_notes)
                self.down.add_beat(down_beat_notes, triplet_beat=self.up.bars[-1][-1].triplet_beat)
            
    # Will get the lilypond notation, as a string (that can then be compiled to an image)
    def get_notation_string(self):

        up_bars = self.up.get_lilypond_bars()
        down_bars = self.down.get_lilypond_bars()

        if self.max_repeats == 0:
            up_voice = lilypond_notation.make_bars(up_bars)
            down_voice = lilypond_notation.make_bars(down_bars)
        else:
            # Add repeats to notation
            # TODO fix this code

            # (Add ["skip1", "skip2"] to end of list to append final bars in loop)
            up_bars += ["skip1", "skip2"]
            down_bars += ["skip1", "skip2"]

            up_voice = ""
            down_voice = ""

            last_up_bars = ["skip", "skip"]
            last_down_bars = ["skip", "skip"]
            repeating_bars = 0
            repeat = 0
            for up_bar, down_bar in zip(up_bars, down_bars):
                if up_bar == last_up_bars[0] and down_bar == last_down_bars[0] and repeating_bars != 2:
                    # Bar same as last bar
                    repeat += 1
                    repeating_bars = 1
                elif up_bar == last_up_bars[1] and down_bar == last_down_bars[1] and repeating_bars != 1:
                    # 2 Bar repeat (same as bar before last)
                    repeat += 0.5
                    repeating_bars = 2
                else:
                    assert(repeat != 0.5) # TODO fix error when this condition occurs
                    if repeat > 0:
                        if repeating_bars == 2:
                            if repeat % 1 != 0:
                                # Cant repeat half of 2 bars
                                repeat -= 0.5
                                up_voice += lilypond_notation.make_bar(last_up_bars[0])
                                down_voice += lilypond_notation.make_bar(last_down_bars[0])

                        # Add repeat bars
                        up_voice += lilypond_notation.make_repeat_bars(last_up_bars[:repeating_bars], int(repeat))
                        down_voice += lilypond_notation.make_repeat_bars(last_down_bars[:repeating_bars], int(repeat))

                        # Reset repeat variables
                        repeat = 0
                        repeating_bars = 0

                        # Clear last bars so next itterations do not repeat off them
                        last_up_bars[0] = "skip" # (Only need to do it with one)
                    elif last_up_bars[1] != "skip": # (If this is not true, then last_up_bars[1] has already been written in a repeat (or its the original value and thus does not exist))
                        # Add last bar normally
                        up_voice += lilypond_notation.make_bar(last_up_bars[1])
                        down_voice += lilypond_notation.make_bar(last_down_bars[1])

                # Shift last bars across
                last_up_bars.pop()
                last_down_bars.pop()

                last_up_bars.insert(0, up_bar)
                last_down_bars.insert(0, down_bar)

        return lilypond_notation.make_score(up_voice, down_voice)
        
    def create_score(self, file_output_path):
        notation_string = self.get_notation_string()
        
        # Write notation to text file (for editing)
        text_file = open(file_output_path + ".txt", "w")
        text_file.write(notation_string)
        text_file.close()

        # Write notation to pdf
        to_pdf(notation_string, file_output_path)