import numpy as np
import math
import minimal
import logging
import pywt
import time
from basic_ToH import Treshold, Treshold__verbose

class Threshold(Treshold):
    def __init__(self):
        super().__init__()
        logging.info(__doc__)
        self.wavelet = pywt.WaveletPacket(minimal.args.wavelet_name)

        # Default dwt_levels is based on the length of the chunk and the length of the filter
        self.max_filters_length = max(self.wavelet.dec_len, self.wavelet.rec_len)
        self.dwt_levels = pywt.dwt_max_level(data_len=minimal.args.frames_per_chunk//4, filter_len=self.max_filters_length)
        if minimal.args.levels:
            self.dwt_levels = int(minimal.args.levels)

        # Structure used during the decoding
        zero_array = np.zeros(shape=minimal.args.frames_per_chunk)
        coeffs = pywt.wavedec(zero_array, wavelet=self.wavelet, level=self.dwt_levels, mode="per")
        self.slices = pywt.coeffs_to_array(coeffs)[1]

        logging.info(f"wavelet name = {minimal.args.wavelet_name}")
        logging.info(f"analysis filters's length = {self.wavelet.dec_len}")
        logging.info(f"synthesis filters's length = {self.wavelet.rec_len}")
        logging.info(f"DWT levels = {self.dwt_levels}")

        self.qss = self.determine_user_specific_qss()

    def calculate_quantization_steps(self, max_q):
        def calc(f):
            return 3.64 * (f / 1000)**(-0.8) - 6.5 * math.exp((-0.6) * (f / 1000 - 3.3)**2) + 10**(-3) * (f / 1000)**4

        f = 22050
        average_SPLs = []

        for i in range(self.dwt_levels):
            mean = sum(calc(j) for j in np.arange(f / 2, f, 1))
            f /= 2
            average_SPLs.insert(0, mean / f)
        mean = sum(calc(j) for j in np.arange(1, f, 1))
        average_SPLs.insert(0, mean / f)

        min_SPL, max_SPL = np.min(average_SPLs), np.max(average_SPLs)
        return [round((spl - min_SPL) / (max_SPL - min_SPL) * (max_q - 1) + 1) for spl in average_SPLs]

    def determine_user_specific_qss(self):
        logging.info("Determining user-specific QSS...")
        qss = []
        for level in range(self.dwt_levels):
            noise_amplitude = 1
            while True:
                chunk = self.generate_test_chunk(level, noise_amplitude)
                self.play_chunk(chunk)
                user_input = input(f"Is the noise in subband {level} perceptible? (y/n): ").strip().lower()
                if user_input == 'n':
                    noise_amplitude += 1
                else:
                    break
            qss.append(noise_amplitude - 1)
        return qss

    def generate_test_chunk(self, level, noise_amplitude):
        chunk_DWT = np.zeros(self.slices[-1][-1][-1].stop)
        chunk_DWT[self.slices[level]['d'][0]] = np.random.uniform(-noise_amplitude, noise_amplitude, self.slices[level]['d'][0].stop - self.slices[level]['d'][0].start)
        return pywt.waverec(pywt.array_to_coeffs(chunk_DWT, self.slices, output_format='wavedec'), wavelet=self.wavelet)

    def play_chunk(self, chunk):
        logging.info("Playing chunk with alternating silence...")
        # Here, you'd implement playback logic for the chunk and alternating silence

    def analyze(self, chunk):
        chunk_DWT = super().analyze(chunk)
        for i, level in enumerate(range(self.dwt_levels)):
            chunk_DWT[self.slices[level]['d'][0]] = (chunk_DWT[self.slices[level]['d'][0]] / self.qss[i]).astype(np.int32)
        return chunk_DWT

    def synthesize(self, chunk_DWT):
        for i, level in enumerate(range(self.dwt_levels)):
            chunk_DWT[self.slices[level]['d'][0]] = chunk_DWT[self.slices[level]['d'][0]] * self.qss[i]
        return super().synthesize(chunk_DWT)

class Threshold_verbose(Treshold__verbose, Threshold):
    pass

try:
    import argcomplete  # <tab> completion for argparse.
except ImportError:
    logging.warning("Unable to import argcomplete (optional)")

if __name__ == "__main__":
    minimal.parser.description = __doc__
    try:
        argcomplete.autocomplete(minimal.parser)
    except Exception:
        logging.warning("argcomplete not working :-/")
    minimal.args = minimal.parser.parse_known_args()[0]
    if minimal.args.show_stats or minimal.args.show_samples:
        intercom = Threshold_verbose()
    else:
        intercom = Threshold()
    try:
        intercom.run()
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
        intercom.print_final_averages()