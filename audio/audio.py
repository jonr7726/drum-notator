import tensorflow as tf
import tensorflow_io as tfio

from audio import utils
from audio import bpm_functions
from audio import MIN_DISTANCE, MIN_PROMINENCE, SMOOTH_DISTANCE

def audio_to_peaks(file, visualise=True):
    tensor = utils.get_tensor(file)
    return utils.get_peaks(tensor, file, MIN_DISTANCE, MIN_PROMINENCE, SMOOTH_DISTANCE, visualise)
      
# Returns just Mel-spectrograms
def audio_to_images(file, visualise=True, peaks=[]):
    tensor = utils.get_tensor(file)
    if peaks == []:
        peaks = utils.get_peaks(tensor, file, MIN_DISTANCE, MIN_PROMINENCE, SMOOTH_DISTANCE, visualise)
    
    return utils.get_images(tensor, peaks, MIN_DISTANCE)
    
# Returns Mel-spectrograms, peaks, and bpm
def audio_to_images_notation(file, visualise=False, clicks=4, cut_clicks=True, bpm_rounding=True):
    tensor = utils.get_tensor(file)
    peaks = utils.get_peaks(tensor, file, MIN_DISTANCE, MIN_PROMINENCE, SMOOTH_DISTANCE, visualise)
    
    bpm = bpm_functions.get_bpm(peaks, clicks, bpm_rounding)
    if cut_clicks:
        peaks = peaks[clicks:]

    return utils.get_images(tensor, peaks, MIN_DISTANCE), peaks, bpm