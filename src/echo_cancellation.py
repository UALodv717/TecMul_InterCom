import logging
import numpy as np
import minimal
import buffer
import sys
import threading
import time
from scipy.signal import correlate, butter, lfilter

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
        Generate and send a sinusoidal pulse signal.
        """
        pulse = np.zeros((1024, 2), int)
        t = np.arange(0, 12)  # Duration of pulse in samples
        sine_wave = (32000 * np.sin(2 * np.pi * t / len(t))).astype(int)
        pulse[8:20, :] = sine_wave[:, None]
        self.pulse_sent = pulse
        print("Pulse sent:", pulse)
        return pulse

    def lowpass_filter(self, data, cutoff, fs, order=5):
        """
        Apply a lowpass filter to reduce noise.
        """
        nyquist = 0.5 * fs
        normal_cutoff = cutoff / nyquist
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return lfilter(b, a, data)

    def estimate_delay_and_attenuation(self, sent_signal, received_signal):
        """
        Estimate the delay (d) and attenuation (a) between sent and received signals.
        Moved to a separate thread for performance.
        """
        if sent_signal is None or received_signal is None:
            return

        # Ensure received_signal has the same shape as sent_signal
        if received_signal.ndim == 1:
            received_signal = np.expand_dims(received_signal, axis=-1)  # Convert to 2D: (N,) -> (N, 1)

        if received_signal.shape[1] < sent_signal.shape[1]:
            # If received_signal has fewer channels, repeat the channel
            received_signal = np.tile(received_signal, (1, sent_signal.shape[1]))

        if received_signal.shape[1] > sent_signal.shape[1]:
            # If received_signal has more channels, truncate extra channels
            received_signal = received_signal[:, :sent_signal.shape[1]]

        # Apply lowpass filter to reduce noise
        for col in range(received_signal.shape[1]):
            received_signal[:, col] = self.lowpass_filter(received_signal[:, col], cutoff=1000, fs=48000)

        try:
            delays = []
            correlations = []

            for col in range(sent_signal.shape[1]):
                correlation = correlate(received_signal[:, col], sent_signal[:, col], mode='full')
                delay_index = np.argmax(correlation) - (len(sent_signal) - 1)
                delays.append(max(0, delay_index))  # Ensure non-negative delay
                correlations.append(correlation)

            average_delay = int(np.mean(delays))

        except ValueError as e:
            print("Error in signal concatenation:", e)
            return

        if np.max(np.abs(sent_signal)) > 1e-6:
            attenuation = min(1, np.max(np.abs(received_signal)) / (np.max(np.abs(sent_signal)) + 1e-6))
        else:
            attenuation = 1

        with self.lock:
            self.delay_estimation = average_delay + minimal.args.buffering_time
            self.alpha_estimation = attenuation


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