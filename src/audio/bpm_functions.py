from audio import AUDIO_RATE

# (works both ways)
def convert_spb_bpm(spb_or_bpm):
    return (AUDIO_RATE / spb_or_bpm) * 60
    
# Rounds to nearest bpm
def round_spb(spb):
    bpm = round(convert_spb_bpm(spb)) # Round to nearest bpm
    spb = convert_spb_bpm(bpm) # convert back to samples per beat
    return spb
    
# Calculate bpm with 4 clicks before start
def get_bpm(peaks, clicks=4, bpm_rounding=True):
    spb = (peaks[clicks] - peaks[0]) / clicks
    bpm = convert_spb_bpm(spb)
    
    if bpm_rounding:
        return round(bpm)
    else:
        return bpm