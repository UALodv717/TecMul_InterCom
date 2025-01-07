#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

''' Considering the threshold of human hearing. '''

'''Changes from basic_toh:
1. Same-sized subbands
2. ToH curve customization
3. Sending and receiving ThO
4. Load and save ToH from a file
'''
import numpy as np
import math
import minimal
import logging
import pywt
import sounddevice as sd
import threading
import os
import pickle
from scipy.interpolate import interp1d
from basic_ToH import Threshold
from basic_ToH import Threshold__verbose

# Añadir argumentos adicionales al parser
minimal.parser.add_argument("-ctoh", "--createToH", action="store_true", help="Allow you to create your custom ToH curve")
minimal.parser.add_argument("-ctohc", "--createToHCumulative", action="store_true", help="Allow you to create your custom cumulative ToH curve")
minimal.parser.add_argument("-tohf", "--ToHfilename", type=str, default=None, help="Load or save custom ToH from a file")
minimal.parser.add_argument("-toha", "--ToHdestination_address", type=minimal.int_or_str, default="localhost", help="Destination (interlocutor's listening) address for ToH")

class advancedThreshold(Threshold):
    def __init__(self):
        ''' Create an advancedThreshold object'''
        super().__init__()
        logging.info(__doc__)

        logging.info(f"wavelet name = {minimal.args.wavelet_name}")
        logging.info(f"analysis filters's length = {self.wavelet.dec_len}")
        logging.info(f"synthesis filters's length = {self.wavelet.rec_len}")
        logging.info(f"DWT levels = {self.dwt_levels}")

    def init(self):
        ''' Initialize advancedThreshold object with Wavelet Packets configuration.'''
        super().init()
        logging.info(__doc__)
        logging.info("Instanciada la clase advancedThreshold.")
        logging.info(f"wavelet name = {minimal.args.wavelet_name if hasattr(minimal.args, 'wavelet_name') else 'default wavelet'}")
        self.wavelet_name = minimal.args.wavelet_name if hasattr(minimal.args, 'wavelet_name') else 'db3'
        self.dwt_levels = 6
        self.wavelet_packet = pywt.WaveletPacket(data=None, wavelet=self.wavelet_name, mode='symmetric', maxlevel=self.dwt_levels)

    def freq_to_db(self, f):
        '''By default, use ThO standard, if create_ToH_from_data is called this function is overwritten.'''
        return 3.64 * (f / 1000) ** (-0.8) - 6.5 * math.exp((-0.6) * (f / 1000 - 3.3) ** 2) + 10 ** (-3) * (f / 1000) ** 4

    def calculate_quantization_steps(self, max_q):
        '''Divide frequency ranges into equal subbands using Wavelet Packets and calculate quantization steps.'''
        f_min, f_max = 20, 22050
        n_subbands = 2 ** self.dwt_levels
        subband_edges = np.linspace(f_min, f_max, n_subbands + 1)
        average_SPLs = []

        # Calculate the average SPL for each subband
        for i in range(n_subbands):
            f_start, f_end = subband_edges[i], subband_edges[i + 1]
            mean_SPL = np.mean([self.freq_to_db(f) for f in np.linspace(f_start, f_end, 100)])
            average_SPLs.append(mean_SPL)

        min_SPL, max_SPL = np.min(average_SPLs), np.max(average_SPLs)

        # Map SPL values to quantization steps
        self.quantization_steps = [
            round((spl - min_SPL) / (max_SPL - min_SPL) * (max_q - 1) + 1)
            for spl in average_SPLs
        ]

        logging.info(f"Quantization step sizes (equal subbands): {self.quantization_steps}")
        return self.quantization_steps

    def save_toh_in_file(self, freq_volume, file="custom_toh.pkl"):
        '''Save freq_volume in a pickle file .'''
        with open(file, "wb") as pickle_file:
            pickle.dump(freq_volume, pickle_file)

    def load_toh_from_file(self, file="custom_toh.pkl"):
        """Carga un diccionario freq_volume desde un archivo utilizando pickle."""
        with open(file, "rb") as pickle_file:
            freq_volume = pickle.load(pickle_file)
        return freq_volume

    def create_ToH_curve_data(self, freq_steps=1000, volume_steps=0.1):
        '''Generate a custom ToH or load from a file.'''

        # si el archivo especificado por parametro ya existe se carga su informacion en lugar degenerarla
        if minimal.args.ToHfilename is not None and os.path.isfile(minimal.args.ToHfilename):
            logging.info(f"Cargando ToH desde el archivo: {minimal.args.ToHfilename}")
            return self.load_toh_from_file(minimal.args.ToHfilename)

        threading_control = {"pressed": False, "alive": True, "lock": True}

        def detect_intro():
            while threading_control["alive"]:
                if not threading_control["lock"]:
                    input("------------------------------------------")
                    threading_control["pressed"] = True
                    threading_control["lock"] = True

        def sound_generator(frecuencia, volumen=0.1, tiempo=1):
            t = np.linspace(0, tiempo, int(44100 * tiempo))
            wave = np.sin(2 * np.pi * frecuencia * t)
            wave *= volumen
            sd.play(wave, samplerate=44100)
            sd.wait()

        def cumulative_sound_generator(frecuencia, volumen=0.1, tiempo=1):
            t = np.linspace(0, tiempo, int(44100 * tiempo))
            wave = np.zeros_like(t)
            for freq in range(20, 22001, frecuencia):
                wave += np.sin(2 * np.pi * freq * t) * (freq_volume[freq] if freq in freq_volume else 1.0)
            wave *= volumen / np.max(np.abs(wave))  # Normalizar para evitar distorsión
            sd.play(wave, samplerate=44100)
            sd.wait()

        logging.info("Bienvenido al Asistente de Personalización de ToH")
        input("Presiona Enter para comenzar")

        if minimal.args.createToHCumulative:
            sound_generator = cumulative_sound_generator

        freq_volume = {}
        thread = threading.Thread(target=detect_intro, daemon=True)
        thread.start()

        for freq in range(20, 22101, freq_steps):
            logging.info(f"Reproduciendo {freq} Hz, presiona Enter cuando lo escuches")
            threading_control["lock"] = False
            for volume in np.arange(0, 1.000001, volume_steps):
                sound_generator(freq, volume)
                if threading_control["pressed"]:
                    threading_control["pressed"] = False
                    logging.info(f"Guardado {freq} Hz al {volume}. \n")
                    freq_volume[freq] = volume
                    break
            else:
                logging.info(f"\nGuardado {freq} Hz al 100% \n")
                freq_volume[freq] = 1.0

        threading_control["alive"] = False

        # Guardar los datos en el archivo si se especifica un nombre
        if minimal.args.ToHfilename is not None:
            logging.info(f"Guardando ToH en el archivo: {minimal.args.ToHfilename}")
            self.save_toh_in_file(freq_volume, minimal.args.ToHfilename)

        return freq_volume

    def send_ToH_data(self, freq_volume):
        '''Sends the ToH data dictionary by TCP connection'''
        pass

    def create_ToH_from_data(self, freq_volume):
        global freq_to_db
        freqs = np.array(sorted(freq_volume.keys()))
        volumes = np.array([freq_volume[f] for f in freqs])
        volumes[volumes == 0] = 1e-6  
        decibels = 20 * np.log10(volumes)
        freq_to_db = interp1d(freqs, decibels, kind='cubic', fill_value="extrapolate")


class advancedThreshold_verbose(Threshold__verbose, Threshold):
    def __init__(self):
        ''' Create an advancedThreshold verbose object'''
        super().__init__()


if __name__ == "__main__":
    minimal.parser.description = __doc__
    intercom = None  # Inicializar intercom como None
    try:
        import argcomplete  # <tab> completion for argparse.
        argcomplete.autocomplete(minimal.parser)
    except ImportError:
        logging.warning("Unable to import argcomplete (optional)")

    minimal.args = minimal.parser.parse_known_args()[0]

    if minimal.args.createToH or minimal.args.createToHCumulative:
        print(advancedThreshold().create_ToH_curve_data())

    try:
        if minimal.args.show_stats or minimal.args.show_samples:
            intercom = advancedThreshold_verbose()
        else:
            intercom = advancedThreshold()

        intercom.run()
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
        if intercom is not None:
            intercom.print_final_averages()