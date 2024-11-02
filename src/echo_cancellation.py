#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

'''Echo cancellation (template).'''

import logging
import numpy as np
import minimal
import buffer
from scipy.signal import correlate  # Make sure to import correlate

class Echo_Cancellation(buffer.Buffering):
    def __init__(self):
        super().__init__()
        self.delay_estimation = 0  # τ, tiempo de retraso del eco
        self.alpha_estimation = 1  # α, factor de atenuación del eco
        logging.info(__doc__)

    def estimate_echo_parameters(self, speaker_chunk, mic_chunk):
        # Estima los parámetros de eco (τ y α) usando correlación cruzada entre
        # la señal de altavoz (speaker_chunk) y la señal del micrófono (mic_chunk).

        # Usamos correlación cruzada para estimar el delay entre las señales.
        correlation = correlate(mic_chunk[:, 0], speaker_chunk, mode='full')
        delay_idx = np.argmax(np.abs(correlation)) - len(speaker_chunk) + 1
        self.delay_estimation = abs(delay_idx)

        # Estimamos α como la relación de energía entre ambas señales.
        energy_speaker = np.sum(speaker_chunk ** 2)
        energy_mic = np.sum(mic_chunk ** 2)
        if energy_speaker > 0:
            self.alpha_estimation = energy_mic / energy_speaker
        logging.info(f"Estimation - Delay: {self.delay_estimation}, Alpha: {self.alpha_estimation}")

    def cancel_echo(self, mic_chunk, speaker_chunk):
        """
        Realiza la cancelación del eco restando la señal retrasada del altavoz
        de la señal capturada por el micrófono.
        """
        logging.debug("Performing echo cancellation...")
        
        # Retrasamos la señal del altavoz según τ
        delayed_speaker_chunk = np.roll(speaker_chunk, self.delay_estimation, axis=0)

        # Clipping to avoid strange noises
        if delayed_speaker_chunk.ndim == 1:
            delayed_speaker_chunk = np.expand_dims(delayed_speaker_chunk, axis=1)
        
        # Calculamos el eco estimado
        estimated_echo = self.alpha_estimation * delayed_speaker_chunk

        # Ensure the arrays have compatible shapes for broadcasting
        min_len = min(mic_chunk.shape[0], estimated_echo.shape[0])
        mic_chunk = mic_chunk[:min_len]
        estimated_echo = estimated_echo[:min_len]

        # Restamos el eco estimado de la señal del micrófono
        clean_chunk = mic_chunk - estimated_echo
        
        # Clipping to avoid distortion
        clean_chunk = np.clip(clean_chunk, -1.0, 1.0)

        return clean_chunk

    def _record_IO_and_play(self, ADC, DAC, frames, time, status):
        """
        Extiende el método _record_IO_and_play para incluir la cancelación de eco.
        """
        # Obtenemos el número del chunk actual
        self.chunk_number = (self.chunk_number + 1) % self.CHUNK_NUMBERS
        
        # Empaquetar el chunk del ADC (lo que grabamos del micrófono)
        packed_chunk = self.pack(self.chunk_number, ADC)
        
        # Enviar el chunk empaquetado
        self.send(packed_chunk)
        
        # Recuperar el siguiente chunk del buffer (lo que se reprodujo)
        chunk_from_buffer = self.unbuffer_next_chunk()
        
        # Realizar la cancelación de eco si tenemos señales válidas
        clean_chunk = self.cancel_echo(ADC, chunk_from_buffer)
         
        # Reproducir el chunk limpio en el DAC
        self.play_chunk(DAC, clean_chunk)
    
    def _read_IO_and_play(self, DAC, frames, time, status):
        self.chunk_number = (self.chunk_number + 1) % self.CHUNK_NUMBERS
        read_chunk = self.read_chunk_from_file()
        packed_chunk = self.pack(self.chunk_number, read_chunk)
        self.send(packed_chunk)
        chunk = self.unbuffer_next_chunk()
        clean_chunk = self.cancel_echo(DAC, chunk)
        self.play_chunk(DAC, clean_chunk)
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
        intercom = Echo_Cancellation__verbose()
    else:
        intercom = Echo_Cancellation()
    try:
        intercom.run()
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
       intercom.print_final_averages()
