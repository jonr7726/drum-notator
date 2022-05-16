import tensorflow as tf
import tensorflow_io as tfio

from audio import utility
from audio import bpm_functions
from audio import MIN_DISTANCE, MIN_PROMINENCE, SMOOTH_DISTANCE
      
# Returns just Mel-spectrograms
def audio_to_images(file, visualise):
    tensor = utility.get_tensor(file)
    peaks = utility.get_peaks(tensor, file, MIN_DISTANCE, MIN_PROMINENCE, SMOOTH_DISTANCE, visualise=visualise)
    
    return utility.get_images(tensor, peaks, MIN_DISTANCE)
    
# Returns Mel-spectrograms, peaks, and bpm
def audio_to_images_notation(file, visualise=False, clicks=4, cut_clicks=True, bpm_rounding=True):
    tensor = utility.get_tensor(file)
    peaks = utility.get_peaks(tensor, file, MIN_DISTANCE, MIN_PROMINENCE, SMOOTH_DISTANCE, visualise)
    
    bpm = bpm_functions.get_bpm(peaks, clicks, bpm_rounding)
    if cut_clicks:
        peaks = peaks[clicks:]

    return utility.get_images(tensor, peaks, MIN_DISTANCE), peaks, bpm