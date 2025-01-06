#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

''' Considering the threshold of human hearing. '''

'''Changes from basic_toh:
1. Same-sized subbands
2. ToH curve customization
3. Sending and receiving ThO
'''
import numpy as np
import math
import minimal
import logging
import pywt
import sounddevice as sd
import threading 

from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

from basic_ToH import Threshold
from basic_ToH import Threshold__verbose

#A new arg to select if we want to create a ToH curve
minimal.parser.add_argument("-ctoh","--createToH", action="store_true", help="Allow you to create your custom ToH curve")
#A new arg to select if we want to create a ToH curve 
minimal.parser.add_argument("-ctohc","--createToHCumulative", action="store_true", help="Allow you to create your custom cumulative ToH curve")

def create_ToH_curve_data(freq_steps=1000, volume_steps=0.1):
    '''Stars a user-dependent process to obtain a frequency dictionary - volume (volume is a value between 0.0 and 1.0)'''

    threading_control = {"pressed": False , "alive":True,"lock":True}  

    #ERROR CONOCIDO: si se pulsa repetidamente intro se almacena en el buffer del SO y marca las siguientes frecuencias con volumen minimo, se puede arreglar borrando dicho buffer antes de cada frecuencia pero no se implementa por simplicidad/compativilidad entre SOs
    def detect_intro():
        while threading_control["alive"]:
            if not threading_control["lock"]:
                input("------------------------------------------")

                threading_control["pressed"] = True
                threading_control["lock"] = True #Por desgracia no ayuda con el error conocido


    def sound_generator(frecuencia,volumen=0.1,tiempo=1):
        #logging.info("sonido de " + str(frecuencia) + "hz al " + str(volumen))
        t = np.linspace(0, tiempo, int(44100 * tiempo))
        wave = np.sin(2 * np.pi * frecuencia * t)
        wave *= volumen
        sd.play(wave, samplerate=44100)
        sd.wait()

    def cumulative_sound_generator(frecuencia,volumen=0.1,tiempo=1):
       #En ocasiones se bloquea, de momento desconozco la causa
        t = np.linspace(0, tiempo, int(44100 * tiempo))
        wave = np.zeros_like(t)
        for freq in range(20, 22001, frecuencia):
            wave += np.sin(2 * np.pi * freq * t) * (freq_volume[freq] if freq in freq_volume else 1.0)

        wave *= volumen / np.max(np.abs(wave))  # Normalizar para evitar distorsión
        sd.play(wave, samplerate=44100)
        sd.wait()

        

    logging.info("Welcome to the TOH Customization Wizard ")
    input("Pulsa intro para comenzar")

    if minimal.args.createToHCumulative:
        sound_generator = cumulative_sound_generator
        


    freq_volume={}
    thread = threading.Thread(target=detect_intro, daemon=True)
    thread.start()
    
    for freq in range(20,22101,freq_steps):
        logging.info(f"Reproduciendo {freq} hz, pulsa intro cuando lo escuches")
        threading_control["lock"] = False
        for volume in np.arange(0,1.000001,volume_steps):
            

            sound_generator(freq,volume)
            #si durante el wait de sd se presiona intro
            if threading_control["pressed"]:
                threading_control["pressed"] = False
                logging.info(f"Guardado {freq} Hz al {volume}. \n")
                freq_volume[freq] = volume
                break

        else:
            #si el usuario no pulsa nunca significa que no escucha el sonido y se debe guardar como valor 1 a esa frecuencia 
            logging.info(f"\nGuardado {freq} Hz al 100% \n")
            freq_volume[freq] = 1.0
    
    threading_control["alive"]=False

    return freq_volume 
  
def send_ToH_data(freq_volume):
    '''Sends the ToH data diccionary by TCP conexion'''
    pass

def freq_to_db(f):
    '''By default, use ThO standar, if create_ToH_from_data is called this function is overwriten with another formula'''
    return 3.64*(f/1000)**(-0.8) - 6.5*math.exp((-0.6)*(f/1000-3.3)**2) + 10**(-3)*(f/1000)**4

def create_ToH_from_data(freq_volume):
    global freq_to_db
    freqs = np.array(sorted(freq_volume.keys()))
    volumes = np.array([freq_volume[f] for f in freqs])
    volumes[volumes == 0] = 1e-6  # Un valor muy pequeño para simular 0
    decibels = 20 * np.log10(volumes)        
    freq_to_db = interp1d(freqs, decibels, kind='cubic', fill_value="extrapolate")

# AQUÍ EMPEZÓ A MODIFICAR GIO, NO FUNCIONA :)

class advancedThreshold(Threshold):
    def __init__(self):
        ''' Create a advancedThreshold object'''
        super().__init__()
        logging.info(__doc__)
        logging.info("Instanciada la clase advancedThreshold.")
        logging.info(f"wavelet name = {minimal.args.wavelet_name if hasattr(minimal.args, 'wavelet_name') else 'default wavelet'}")
        self.wavelet_name = minimal.args.wavelet_name if hasattr(minimal.args, 'wavelet_name') else 'db3'
        self.dwt_levels = 6
        self.wavelet_packet = pywt.WaveletPacket(data=None, wavelet=self.wavelet_name, mode='symmetric', maxlevel=self.dwt_levels)

    def calculate_quantization_steps(self, max_q):
        f_min, f_max = 20, 22050
        n_subbands = 2 ** self.dwt_levels
        subband_edges = np.linspace(f_min, f_max, n_subbands + 1)
        average_SPLs = []

        for i in range(n_subbands):
            f_start, f_end = subband_edges[i], subband_edges[i + 1]
            mean_SPL = np.mean([freq_to_db(f) for f in np.linspace(f_start, f_end, 100)])
            average_SPLs.append(mean_SPL)

        min_SPL, max_SPL = np.min(average_SPLs), np.max(average_SPLs)
    
        # Usar una lista para los pasos de cuantización
        self.quantization_steps = [
            round((spl - min_SPL) / (max_SPL - min_SPL) * (max_q - 1) + 1) 
            for spl in average_SPLs
        ]

        logging.info(f"Quantization step sizes: {self.quantization_steps}")
        return self.quantization_steps
    
    def analyze(self, chunk):
        chunk_DWT = super().analyze(chunk)

        # Quantize the subbands
        chunk_DWT[self.slices[0][0]] = (chunk_DWT[self.slices[0][0]] / self.quantization_steps[0]).astype(np.int32)
        for i in range (self.dwt_levels):
            chunk_DWT[self.slices[i+1]['d'][0]] = (chunk_DWT[self.slices[i+1]['d'][0]] / self.quantization_steps[i+1]).astype(np.int32)

        return chunk_DWT


    def synthesize(self, chunk_DWT):

        # Dequantize the subbands
        chunk_DWT[self.slices[0][0]] = chunk_DWT[self.slices[0][0]] * self.quantization_steps[0]
        for i in range (self.dwt_levels):
            chunk_DWT[self.slices[i+1]['d'][0]] = chunk_DWT[self.slices[i+1]['d'][0]] * self.quantization_steps[i+1]

        return super().synthesize(chunk_DWT)

   

# --------------------------------------------------------------------------------------------------------------------------------------

class advancedThreshold_verbose(Threshold__verbose, Threshold):
         def __init__():
            ''' Create a advancedThreshold verbose object'''
            super().__init__()
        
pass

try:
    import argcomplete  # <tab> completion for argparse.
except ImportError:
    logging.warning("Unable to import argcomplete (optional)")

if __name__ == "__main__":
    minimal.parser.description = __doc__
    
    try:
        # Habilitar autocompletar argumentos
        import argcomplete  
        argcomplete.autocomplete(minimal.parser)
    except ImportError:
        logging.warning("argcomplete not working :-/")
    
    # Parsear argumentos
    minimal.args = minimal.parser.parse_known_args()[0]

    # Crear instancia de Threshold avanzado
    if minimal.args.show_stats or minimal.args.show_samples:
        intercom = advancedThreshold_verbose()
    else:
        intercom = advancedThreshold()

    # Crear curvas ToH personalizadas si se especifica
    if minimal.args.createToH or minimal.args.createToHCumulative:
        print(create_ToH_curve_data())

    try:
        intercom.run()  # Ejecutar el programa principal
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
        intercom.print_final_averages()
