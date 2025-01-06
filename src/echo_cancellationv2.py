import logging
import numpy as np
import minimal
import buffer
import sys
import threading
import time
from scipy.signal import correlate

class EchoCancellation(buffer.Buffering):
    def __init__(self):
        super().__init__()
        self.delay_estimation = 0 
        self.alpha_estimation = 1 
        self.i = 0
        self.pulse_sent = None
        self.estimate_thread = None  
        self.lock = threading.Lock()
        logging.info("Echo cancellation initialized")

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
        Moved to a separate thread for performance.
        """
        if sent_signal is None or received_signal is None:
            return

        combined_signal = np.concatenate((sent_signal, received_signal), axis=0)

        correlation = correlate(combined_signal[:, 0], sent_signal[:, 0], mode='full')
        delay_index = np.argmax(correlation) - (len(sent_signal) - 1)

        if np.max(np.abs(sent_signal)) > 1e-6:
            attenuation = np.max(np.abs(received_signal)) / (np.max(np.abs(sent_signal)) + 1e-6)
        else:
            attenuation = 1

        with self.lock:
            self.delay_estimation = delay_index
            self.alpha_estimation = attenuation

        print(f"Estimated delay: {delay_index}, Estimated attenuation: {attenuation}")

    def start_estimation_thread(self, sent_signal, received_signal):
        """
        Start a thread for delay and attenuation estimation.
        """
        self.estimate_thread = threading.Thread(
            target=self.estimate_delay_and_attenuation, args=(sent_signal, received_signal)
        )
        self.estimate_thread.start()

    def _record_IO_and_play(self, ADC, DAC, frames, time, status):
        """
        Extend the method _record_IO_and_play to include echo cancellation.
        """
        if self.i == 0:
            pulse = self.send_pulse()
            self.buffer_chunk(0, pulse)
            self.i += 1

        chunk_from_buffer = self.unbuffer_next_chunk()
        self.chunk_number = (self.chunk_number + 1) % self.CHUNK_NUMBERS
        packed_chunk = self.pack(self.chunk_number, ADC)
        self.send(packed_chunk)

        if self.pulse_sent is not None:
            self.start_estimation_thread(self.pulse_sent, chunk_from_buffer)

        with self.lock:
            self.delay = self.delay_estimation
            self.attenuation = self.alpha_estimation
        
        self.play_chunk(DAC, chunk_from_buffer)

    def _read_IO_and_play(self, DAC, frames, time, status):
        self.chunk_number = (self.chunk_number + 1) % self.CHUNK_NUMBERS
        read_chunk = self.read_chunk_from_file()
        packed_chunk = self.pack(self.chunk_number, read_chunk)
        self.send(packed_chunk)
        chunk = self.unbuffer_next_chunk()
        self.play_chunk(DAC, chunk)
        return read_chunk

class EchoCancellationVerbose(EchoCancellation, buffer.Buffering__verbose):
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

if __name__ == "__main__":
    minimal.parser.description = "Echo Cancellation Program"
    minimal.args = minimal.parser.parse_known_args()[0]

    if minimal.args.show_stats or minimal.args.show_samples or minimal.args.show_spectrum:
        intercom = EchoCancellationVerbose()
    else:
        intercom = EchoCancellation()

    try:
        intercom.run()
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
        intercom.print_final_averages()
