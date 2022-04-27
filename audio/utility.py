import tensorflow as tf
import tensorflow_io as tfio

from scipy.signal import find_peaks
import matplotlib.pyplot as plt

from audio import AUDIO_RATE

def get_tensor(file):
    # Get file
    audio = tfio.audio.AudioIOTensor(file)
    assert(audio.rate.numpy() == AUDIO_RATE) # (Important as all image sizes must be the same for network)

    tensor = audio.to_tensor() # Convert to tensor
    tensor = tf.transpose(tensor)[0] # Remove stereo channel, by taking only one

    # Make sure in float format
    if tensor.dtype != tf.float32:
        tensor = tf.cast(tensor, tf.float32)

    # Normalise amplitude to between +-1
    max_amplitude = max(abs(tensor.numpy()))
    tensor = tensor / max_amplitude
    
    return tensor


def get_peaks(tensor, file_name, min_distance, min_prominence, smooth_distance, visualise):
    # Get absolute value of amplitudes (for volume)
    absolute_amplitudes = abs(tensor.numpy())
    
    # Smooth amplitudes with convolution filter (removes noise by essentially averaging points over smooth_distance)
    filter = tf.ones(smooth_distance)/smooth_distance # Set filter to average over smooth distance
    absolute_amplitudes = tf.squeeze(tf.nn.convolution(tf.constant(absolute_amplitudes, shape=(1, len(absolute_amplitudes), 1)), tf.constant(filter, shape=(smooth_distance,1,1)), padding='SAME')).numpy()
    absolute_amplitudes = absolute_amplitudes / max(absolute_amplitudes) # Normalise again
    
    peaks, _ = find_peaks(absolute_amplitudes, distance=min_distance, prominence=min_prominence)

    # Visualize peaks to ensure validity of data
    if visualise:
        plt.plot(absolute_amplitudes)
        plt.plot(peaks, absolute_amplitudes[peaks], 'x')
        plt.title(file_name)
        plt.show()
        
        print(file_name)
        print(f"Found {len(peaks)} points, with prominence threshold of {min_prominence}.")
        try:
            min_prominence = float(input("Enter value to change prominence threshold: "))
            peaks = get_peaks(tensor, file_name, min_distance, min_prominence, smooth_distance, visualise=True)
        except ValueError:
            print("Did not enter valid value, moving to next file.")
        
    return peaks


def get_images(tensor, peaks, min_distance):
    # Make mel-spectograms from peaks
    images = []
    for peak in peaks:
        # Get audio slice at peak
        peak_slice = tensor[peak:peak+min_distance]

        # Convert to spectrogram
        spectrogram = tfio.audio.spectrogram(peak_slice, nfft=1024, window=512, stride=256)

        # Convert to mel-spectrogram and add to list
        images.append(tfio.audio.melscale(spectrogram, rate=AUDIO_RATE, mels=128, fmin=0, fmax=AUDIO_RATE/2))
    
    # Add empty channel dimention to image data
    images = tf.expand_dims(images, axis=-1)
    
    return images