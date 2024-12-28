#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

'''Echo cancellation (template).'''

import logging
import numpy as np
import minimal
import buffer
import sys
import threading
import time
from scipy.signal import correlate  # Make sure to import correlate
import matplotlib.pyplot as plt

class Echo_Cancellation(buffer.Buffering):
    def __init__(self):
        super().__init__()
        self.delay_estimation = 0.5  # d: estimated delay of the echo
        self.alpha_estimation = 1.2  # a: estimated attenuation factor
        self.i = 0
        self.pulse_sent = None
        logging.info(__doc__)

    def send_pulse(self):
        """
        Generate and send a single pulse signal at the start of execution.
        """
        pulse = np.zeros((1024, 2), int)
        pulse[8:20, :] = 32000
        self.pulse_sent = pulse
        print("Pulse sent:", pulse)
        return pulse

    def estimate_delay_and_attenuation(self, sent_signal, received_signal):
        """
        Estimate the delay (d) and attenuation (a) between sent and received signals.
        """
        if sent_signal is None or received_signal is None:
            return 0, 1
        
        plt.figure()
        plt.subplot(2, 1, 1)
        plt.title("Sent Signal")
        plt.plot(sent_signal[:, 0])
        plt.subplot(2, 1, 2)
        plt.title("Received Signal")
        plt.plot(received_signal[:, 0])
        plt.show()
        # Compute cross-correlation
        correlation = correlate(received_signal, sent_signal, mode='full')
        center = len(sent_signal) - 1
        plausible_range = correlation[center-100:center+100]  # Focus on a reasonable range
        delay_index = np.argmax(plausible_range) - 100

        # Compute attenuation factor
        if np.max(np.abs(sent_signal)) > 1e-6:
            attenuation = np.max(np.abs(received_signal)) / (np.max(np.abs(sent_signal)) + 1e-6)
        else:
            attenuation = 1

        return 0.5, 1.2


    def _record_IO_and_play(self, ADC, DAC, frames, time, status):
        """
        Extend the method _record_IO_and_play to include echo cancellation.
        """
        if self.i == 0:
            # Send and play the pulse
            pulse = self.send_pulse()
            self.buffer_chunk(0,pulse)
            self.i += 1
            return
        chunk_from_buffer = self.unbuffer_next_chunk()
        
        # Regular processing
        self.chunk_number = (self.chunk_number + 1) % self.CHUNK_NUMBERS
        packed_chunk = self.pack(self.chunk_number, ADC)
        self.send(packed_chunk)

        
            # Estimate delay and attenuation
        self.delay_estimation, self.alpha_estimation = self.estimate_delay_and_attenuation(
            self.pulse_sent, chunk_from_buffer
        )
        print(f"Estimated delay (d): {self.delay_estimation}, attenuation (a): {self.alpha_estimation}")
            
        
        echo_length = len(self.pulse_sent)
        start_idx = self.delay_estimation
        end_idx = start_idx + echo_length

        if start_idx >= 0 and end_idx <= len(chunk_from_buffer):
            # Extract the portion of the received signal that contains the echo
            echo_portion = chunk_from_buffer[start_idx:end_idx]

            # Estimate the echo using the sent signal
            estimated_echo = self.alpha_estimation * self.pulse_sent[:len(echo_portion)]

            # Subtract the estimated echo from the received signal
            chunk_from_buffer[start_idx:end_idx] -= estimated_echo

            print(f"Echo canceled in range: {start_idx} to {end_idx}")

        # Play the processed chunk
        self.play_chunk(DAC, chunk_from_buffer)

    
    def _read_IO_and_play(self, DAC, frames, time, status):
        self.chunk_number = (self.chunk_number + 1) % self.CHUNK_NUMBERS
        read_chunk = self.read_chunk_from_file()
        packed_chunk = self.pack(self.chunk_number, read_chunk)
        self.send(packed_chunk)
        chunk = self.unbuffer_next_chunk()
        self.play_chunk(DAC, chunk)
        return read_chunk
        
class Echo_Cancellation__verbose(Echo_Cancellation, buffer.Buffering__verbose):
    def __init__(self):
        super().__init__()
        
    def _record_IO_and_play(self, ADC, DAC, frames, time, status):
        if minimal.args.show_samples:
            self.show_recorded_chunk(ADC)

        super()._record_IO_and_play(ADC, DAC, frames, time, status)

        if minimal.args.show_samples:
            self.show_played_chunk(DAC)

        self.recorded_chunk = DAC
        self.played_chunk = ADC
        
    def _read_IO_and_play(self, DAC, frames, time, status):
        read_chunk = super()._read_IO_and_play(DAC, frames, time, status)

        if minimal.args.show_samples:
            self.show_recorded_chunk(read_chunk)
            self.show_played_chunk(DAC)

        self.recorded_chunk = DAC

        return read_chunk

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

    if minimal.args.show_stats or minimal.args.show_samples or minimal.args.show_spectrum:
        try:
            intercom = Echo_Cancellation__verbose()
        except Exception as e:
            print(e)
            sys.exit(-1)
    else:
        intercom = Echo_Cancellation()
    try:
        intercom.run()
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
       intercom.print_final_averages()
