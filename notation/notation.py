from notation import lilypond_notation

from notation import MAX_REPEATS
from notation import REST, INVISIBLE_REST
from notation import BASS, SNARE, FLOOR_TOM, RIDE, HI_HAT, HI_HAT_FOOT
from notation import CYMBALS, HI_HAT_FOOT_IMPLICATORS

import numpy as np
from math import log2
from tensorflow import argmax

from mingus.extra.lilypond import to_png

# Splits instruments and durations up into each valid note (adds rests)
def get_notes(instruments, durations, triplets_enabled, dynamic_bpm):
    smallest_error = (1/4)/2 # (constant)

    notes = []
    # formated as [bar][beat/s][note/s][0 = instruments, 1 = duration]
    # contains array for every bar, but not necessarily every beat, as notes longer than a beat exist

    accumulated_duration = 0

    peak_instruments = None
    peak_duration = None
    triplet_beat = None

    remainders = []
    accumulated_duration_start = 0

    bpm_adjustment = 1

    def handle_bpm_error(remainder):
        nonlocal accumulated_duration_start, bpm_adjustment

        remainders.append(remainder)

        if accumulated_duration - accumulated_duration_start > 4:
            if len(remainders) >= 3:
                correlation = np.corrcoef(range(len(remainders)), remainders)[0,1]
                adjustment = (remainders[0] - remainders[-1]) / len(remainders)

                if adjustment > 0.005:
                    adjustment = 0.005
                elif adjustment < -0.005:
                    adjustment = -0.005

                if abs(correlation) > 0 and abs(1 - (bpm_adjustment + adjustment)) < 0.02:
                    bpm_adjustment += adjustment
                    print('bpm:', bpm_adjustment)
            remainders.clear()
            accumulated_duration_start = accumulated_duration

    # Adds quavers within a beat or whole note on an on-beat
    def add_note_quaver(note_duration):
        nonlocal peak_instruments, peak_duration, accumulated_duration

        # Round to nearest semiquaver
        note_duration = round(4 * note_duration) / 4
    
        peak_duration -= note_duration

        # Accumulate duration (after rounding)
        accumulated_duration += note_duration

        # Add note
        notes[-1][-1].append([peak_instruments, note_duration])

        peak_instruments = [] # Set preceeding notes in this peak to rests

    def add_note_triplet(note_duration):
        nonlocal peak_instruments, peak_duration, accumulated_duration

        # Round to triplets
        note_duration = round(3 * note_duration) / 3
        if note_duration == 0:
            print('triplet', peak_instruments, accumulated_duration)
            note_duration = 1/3
    
        peak_duration -= note_duration

        # Accumulate duration (after rounding)
        accumulated_duration += note_duration
        # Handle tripplet rounding error
        accumulated_duration = round(3 * accumulated_duration) / 3

        # Add note
        notes[-1][-1].append([peak_instruments, note_duration])

        # Set preceeding notes in this peak to rests
        peak_instruments = []

    def add_bar():
        notes.append([])

    def add_beat():
        nonlocal triplet_beat
        notes[-1].append([])
        triplet_beat = None

    # Determines whether beat is triplet, or quaver
    # TODO add polyrhythm handling
    def set_triplet_beat(index_of_next_peak):
        nonlocal bpm_adjustment

        if not triplets_enabled:
            return False

        assert(int(peak_duration + smallest_error) == 0) # assert no whole beats

        triplets = 3 * peak_duration
        quavers = 4 * peak_duration

        triplet_errors = [abs(triplets - round(triplets))]
        quaver_errors = [abs(quavers - round(quavers))]

        triplet_count = round(triplets)

        while triplet_count < 3:
            if index_of_next_peak >= len(durations) - 1:
                # Next duration goes outside of beat (as end of score)
                break

            next_peak_duration = bpm_adjustment * durations[index_of_next_peak]

            if (triplet_count / 3) + next_peak_duration > (1 + smallest_error):
                # Next duration goes outside of beat
                break

            next_triplets = 3 * next_peak_duration
            next_quavers = 4 * next_peak_duration
            
            triplet_errors.append(abs(next_triplets - round(next_triplets)))
            quaver_errors.append(abs(next_quavers - round(next_quavers)))
            
            triplet_count += round(next_triplets)

            index_of_next_peak += 1

        if sum(triplet_errors) <= sum(quaver_errors):
            return True
        else:
            return False

    i = 0
    last_peak_remainder = 0
    while i < len(instruments): # until no more peaks
        peak_instruments = instruments[i]
        peak_duration = bpm_adjustment * (durations[i] + last_peak_remainder)

        if i == len(instruments) - 1:
            peak_duration = 4 - (accumulated_duration % 4)

        while peak_duration > smallest_error:
            duration_left_in_beat = 1 - (accumulated_duration % 1)
            duration_left_in_bar = 4 - (accumulated_duration % 4)

            if duration_left_in_bar == 4:
                # Down beat
                add_bar()

            if duration_left_in_beat == 1:
                # On-beat
                add_beat()

                # Whole beat/s
                whole_duration = int(peak_duration + smallest_error) # (smallest_error rounds it up if applicable)

                if whole_duration > 0:
                    if whole_duration > duration_left_in_bar:
                        # Spill to next bar
                        add_note_quaver(duration_left_in_bar)
                    else:
                        add_note_quaver(whole_duration)

                else:
                    # Triplet or Quaver start of beat
                    triplet_beat = set_triplet_beat(i)
                    if triplet_beat:
                        add_note_triplet(peak_duration)
                    else:
                        add_note_quaver(peak_duration)

            else:
                # Inside beat
                assert(triplet_beat != None)

                if duration_left_in_beat - peak_duration < smallest_error:
                    # Spill outside of beat
                    if triplet_beat:
                        add_note_triplet(duration_left_in_beat)
                    else:
                        add_note_quaver(duration_left_in_beat)

                else:
                    if triplet_beat:
                        add_note_triplet(peak_duration)
                    else:
                        add_note_quaver(peak_duration)

        i += 1
        last_peak_remainder = peak_duration

        if dynamic_bpm:
            handle_bpm_error(peak_duration)

    # Add crochet triplet groupings in
    '''if triplets_enabled:
        for bar in range(len(notes)):
            for beat in range(len(notes[bar])):
                if beat >= len(notes[bar]):
                    print("---DEBUG: break crochet triplets---")
                    break

                if (
                    # If has 2 notes in beat, and next beat exists in bar and also has 2 notes
                    len(notes[bar][beat]) == 2 and
                    beat + 1 < len(notes[bar]) and len(notes[bar][beat + 1]) == 2 and
                    # and each note is a crochet triplet
                    notes[bar][beat][0][1] == 2/3 and 
                    notes[bar][beat][1][1] == 1/3 and
                    notes[bar][beat + 1][0][1] == 1/3 and notes[bar][beat + 1][0][0] == []
                    and notes[bar][beat + 1][1][1] == 2/3
                ):                    
                    # Merge beats to make crochet triplet
                    notes[bar][beat][1][1] = 2/3
                    notes[bar][beat].append([notes[bar][beat + 1][1][0], 2/3])
                    notes[bar].pop(beat + 1)'''

    return notes

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
        lilypond_string = ' '.join([self.instruments[i] + self.duration[i] for i in range(self.length())])

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
            while note_duration > 0:
                largest_duration = (2**int(log2(sub_division * note_duration))) / sub_division # Represents the largest note that can be formed (rounds off remainder)
                
                if largest_duration * 1.5 <= note_duration:
                    # Dotted note
                    lilypond_beat.duration.append(str(int(sub_division_lilypond / (sub_division * largest_duration))) + '.')

                    largest_duration = largest_duration * 1.5
                else:
                    lilypond_beat.duration.append(str(int(sub_division_lilypond / (sub_division * largest_duration))))

                lilypond_beat.instruments.append(lilypond_notation.get_lilypond_instruments(note_instruments, default=self.rest))

                note_duration -= largest_duration
                note_instruments = []

        self.bars[-1].append(lilypond_beat)

    def get_lilypond_bars(self):
        lilypond_bars = [' '.join([beat.get_lilypond_string() for beat in bar]) for bar in self.bars]

        return lilypond_bars

class Score:

    def __init__(self, instrument_indexs, durations, triplets_enabled, dynamic_bpm, use_repeats):
        if use_repeats:
            self.max_repeats = MAX_REPEATS
        else:
            self.max_repeats = 0

        notes = get_notes(lilypond_notation.get_instruments(instrument_indexs), durations, triplets_enabled, dynamic_bpm)

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
                        HI_HAT_FOOT = True

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
            # (Add ['skip1', 'skip2'] to end of list to append final bars in loop)
            up_bars += ['skip1', 'skip2']
            down_bars += ['skip1', 'skip2']

            up_voice = ''
            down_voice = ''

            last_up_bars = ['skip', 'skip']
            last_down_bars = ['skip', 'skip']
            repeating_bars = 0
            repeat = 0
            for up_bar, down_bar in zip(up_bars, down_bars):
                print(up_bar, last_up_bars[1])
                if up_bar == last_up_bars[0] and down_bar == last_down_bars[0] and repeating_bars != 2:
                    # Bar same as last bar
                    repeat += 1
                    repeating_bars = 1
                elif up_bar == last_up_bars[1] and down_bar == last_down_bars[1] and repeating_bars != 1:
                    # 2 Bar repeat (same as bar before last)
                    repeat += 0.5
                    repeating_bars = 2
                else:
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
                        last_up_bars[0] = 'skip' # (Only need to do it with one)
                    elif last_up_bars[1] != 'skip': # (If this is not true, then last_up_bars[1] has already been written in a repeat (or its the original value and thus does not exist))
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
        n = self.get_notation_string()
        print(n)
        to_png(n, file_output_path)