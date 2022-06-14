from notation import SMALLEST_ERROR

class Notes:

    def __init__(self, instruments, durations, triplets_enabled=True):
        self.instruments = instruments
        self.durations = durations
        self.triplets_enabled = triplets_enabled

        self.notes = []
        # formated as [bar][beat/s][note/s][0 = instruments, 1 = duration]
        # contains array for every bar, but not necessarily every beat, as notes longer than a beat exist

        self.accumulated_duration = 0

        self.peak_instruments = None
        self.peak_duration = None
        self.triplet_beat = None

    # Adds quavers within a beat or whole note on an on-beat
    def add_note_quaver(self, note_duration):
        # Round to nearest semiquaver
        note_duration = round(4 * note_duration) / 4
    
        self.peak_duration -= note_duration

        # Accumulate duration (after rounding)
        self.accumulated_duration += note_duration

        # Add note
        self.notes[-1][-1].append([self.peak_instruments, note_duration])

        self.peak_instruments = [] # Set preceeding notes in this peak to rests

    def add_note_triplet(self, note_duration):
        # Round to triplets
        note_duration = round(3 * note_duration) / 3
        if note_duration == 0:
            # TODO fix this error
            note_duration = 1/3
    
        self.peak_duration -= note_duration

        # Accumulate duration (after rounding)
        self.accumulated_duration += note_duration
        # Handle tripplet rounding error
        self.accumulated_duration = round(3 * self.accumulated_duration) / 3

        # Add note
        self.notes[-1][-1].append([self.peak_instruments, note_duration])

        # Set preceeding notes in this peak to rests
        self.peak_instruments = []

    def add_bar(self):
        self.notes.append([])

    def add_beat(self):
        self.notes[-1].append([])
        self.triplet_beat = None

    # Determines whether beat is triplet (True), or quaver (False)
    # TODO add polyrhythm handling
    def set_triplet_beat(self, index_of_next_peak):
        if not self.triplets_enabled:
            self.triplet_beat = False
            return

        assert(int(self.peak_duration + SMALLEST_ERROR) == 0) # assert no whole beats

        triplets = 3 * self.peak_duration
        quavers = 4 * self.peak_duration

        triplet_errors = [abs(triplets - round(triplets))]
        quaver_errors = [abs(quavers - round(quavers))]

        triplet_count = round(triplets)

        total_duration = self.peak_duration

        while triplet_count < 3:
            if index_of_next_peak >= len(self.durations) - 1:
                # Next duration goes outside of beat (as end of score)
                break

            next_peak_duration = self.durations[index_of_next_peak]

            total_duration += next_peak_duration

            if total_duration > (1.25):
                # Next duration goes outside of beat
                break

            next_triplets = 3 * next_peak_duration
            next_quavers = 4 * next_peak_duration
            
            triplet_errors.append(abs(next_triplets - round(next_triplets)))
            quaver_errors.append(abs(next_quavers - round(next_quavers)))
            
            triplet_count += round(next_triplets)

            index_of_next_peak += 1

        self.triplet_beat = (sum(triplet_errors) < sum(quaver_errors) and len(triplet_errors) > 1)

    # Splits instruments and durations up into each valid note (adds rests)
    def get_notes(self):
        i = 0
        last_peak_remainder = 0
        while i < len(self.instruments): # until no more peaks
            self.peak_instruments = self.instruments[i]
            self.peak_duration = self.durations[i] + last_peak_remainder

            if i == len(self.instruments) - 1:
                self.peak_duration = 4 - (self.accumulated_duration % 4)

            while self.peak_duration > SMALLEST_ERROR:
                duration_left_in_beat = 1 - (self.accumulated_duration % 1)
                duration_left_in_bar = 4 - (self.accumulated_duration % 4)

                if duration_left_in_bar == 4:
                    # Down beat
                    self.add_bar()

                if duration_left_in_beat == 1:
                    # On-beat
                    self.add_beat()

                    # Whole beat/s
                    whole_duration = int(self.peak_duration + SMALLEST_ERROR) # (smallest_error rounds it up if applicable)

                    if whole_duration > 0:
                        if whole_duration > duration_left_in_bar:
                            # Spill to next bar
                            self.add_note_quaver(duration_left_in_bar)
                        else:
                            self.add_note_quaver(whole_duration)

                    else:
                        # Triplet or Quaver start of beat
                        self.set_triplet_beat(i + 1)
                        if self.triplet_beat:
                            self.add_note_triplet(self.peak_duration)
                        else:
                            self.add_note_quaver(self.peak_duration)

                else:
                    # Inside beat
                    assert(self.triplet_beat != None)

                    if duration_left_in_beat - self.peak_duration < SMALLEST_ERROR:
                        # Spill outside of beat
                        if self.triplet_beat:
                            self.add_note_triplet(duration_left_in_beat)
                        else:
                            self.add_note_quaver(duration_left_in_beat)

                    else:
                        if self.triplet_beat:
                            self.add_note_triplet(self.peak_duration)
                        else:
                            self.add_note_quaver(self.peak_duration)

            i += 1
            last_peak_remainder = self.peak_duration

        return self.notes