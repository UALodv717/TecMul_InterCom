import threading
import queue
import numpy as np
from scipy.fft import fft, ifft
import struct
import logging
import minimal
import buffer

class EchoCancellation(buffer.Buffering):
    def __init__(self):
        super().__init__()
        logging.info("Echo Cancellation Initialized")
        self.estimated_a = 0.8  # Initial estimate for attenuation factor 'a'
        self.estimated_d = 100  # Initial estimate for delay 'd' in samples

        # Queues for threading
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()

        # Start the processing thread
        self.processing_thread = threading.Thread(target=self.process_echo, daemon=True)
        self.processing_thread.start()

    def estimate_echo(self, sent_signal):
        delayed_signal = np.roll(sent_signal, self.estimated_d)
        return self.estimated_a * delayed_signal

    def subtract_echo(self, mic_signal, estimated_echo):
        return mic_signal - estimated_echo

    def update_estimates(self, mic_signal, sent_signal):
        correlation = np.correlate(mic_signal, sent_signal, "full")
        delay_index = np.argmax(correlation)
        self.estimated_d = delay_index - len(sent_signal) + 1

        estimated_echo = self.estimate_echo(sent_signal)
        energy_echo = np.sum(estimated_echo ** 2)
        energy_mic = np.sum(mic_signal ** 2)
        self.estimated_a = energy_mic / (energy_echo + 1e-10)  # Avoid division by zero

    def process_echo(self):
        """
        Thread worker: processes echo cancellation asynchronously.
        """
        while True:
            # Wait for input from the queue
            mic_signal, sent_signal = self.input_queue.get()

            # Estimate and subtract echo
            estimated_echo = self.estimate_echo(sent_signal)
            echo_cancelled_signal = self.subtract_echo(mic_signal, estimated_echo)

            # Update estimates for a and d
            self.update_estimates(mic_signal, sent_signal)

            # Place the result in the output queue
            self.output_queue.put(echo_cancelled_signal)

    def _record_IO_and_play(self, ADC, DAC, frames, time, status):
        """
        Override to include threading for echo cancellation.
        """
        sent_signal = ADC.copy()  # Capture the outgoing signal

        # Pack and send the original signal
        self.chunk_number = (self.chunk_number + 1) % self.CHUNK_NUMBERS
        packed_chunk = self.pack(self.chunk_number, ADC)
        self.send(packed_chunk)

        # Retrieve the microphone signal (mocked here for simplicity)
        mic_signal = self.unbuffer_next_chunk()

        # Add signals to the processing queue
        self.input_queue.put((mic_signal, sent_signal))

        # Wait for the echo-cancelled signal from the output queue
        echo_cancelled_signal = self.output_queue.get()

        # Play the echo-cancelled signal
        self.play_chunk(DAC, echo_cancelled_signal)

if __name__ == "__main__":
    minimal.parser.description = "Echo Cancellation Implementation with Threading"

    try:
        import argcomplete
        argcomplete.autocomplete(minimal.parser)
    except Exception:
        logging.warning("argcomplete not working")

    minimal.args = minimal.parser.parse_known_args()[0]

    intercom = EchoCancellation()

    try:
        intercom.run()
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
        intercom.print_final_averages()
