from audio import AUDIO_RATE

# (works both ways)
def convert_spb_bpm(spb_or_bpm):
    return (AUDIO_RATE / spb_or_bpm) * 60
    
# Rounds to nearest bpm
def round_samples_per_beat(samples_per_beat):
    bpm = round(convert_spb_bpm(samples_per_beat)) # Round to nearest bpm
    samples_per_beat = convert_spb_bpm(bpm) # convert back to samples_per_beat
    print(f"BPM: {bpm}") # (debugging)
    return samples_per_beat
    
def get_bpm(peaks, clicks=4, bpm_rounding=True):
    # Calculate bpm with 4 clicks before start
    samples_per_beat = (peaks[clicks] - peaks[0]) / clicks
    bpm = convert_spb_bpm(samples_per_beat)
    
    if bpm_rounding:
        return round(bpm)
    else:
        return bpm