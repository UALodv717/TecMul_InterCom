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



class advancedThreshold(Threshold):
    def __init__(self):
        ''' Create a advancedThreshold object'''
        super().__init__()
        logging.info(__doc__)
        
        logging.info(f"wavelet name = {minimal.args.wavelet_name}")
        logging.info(f"analysis filters's length = {self.wavelet.dec_len}")
        logging.info(f"synthesis filters's length = {self.wavelet.rec_len}")
        logging.info(f"DWT levels = {self.dwt_levels}")

    def calculate_quantization_steps(self, max_q):

        def calc(f):
            return freq_to_db(f)

        f=22050
        average_SPLs = []
        q_per_subband=[]

        # Calculate average SPL[dB] for each frequency subband
        for i in range(self.dwt_levels):
            mean = 0
            for j in np.arange(f/2,f,1):
                mean += calc(j)
            f = f/2
            average_SPLs.insert(0,mean/f)
        mean = 0
        for j in np.arange(1,f,1):
            mean += calc(j)
        average_SPLs.insert(0,mean/f)

        # Map the SPL values to quantization steps, from 1 to max_q
        # https://stackoverflow.com/questions/345187/math-mapping-numbers
        quantization_steps = []
        min_SPL = np.min(average_SPLs)
        max_SPL = np.max(average_SPLs)
        for i in range(len(average_SPLs)):
            quantization_steps.append( round((average_SPLs[i]-min_SPL)/(max_SPL-min_SPL)*(max_q-1)+1) )
            
        print(quantization_steps)
        return quantization_steps



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
        argcomplete.autocomplete(minimal.parser)
    except Exception:
        logging.warning("argcomplete not working :-/")
    minimal.args = minimal.parser.parse_known_args()[0]

    if minimal.args.show_stats or minimal.args.show_samples:
        intercom = advancedThreshold_verbose()
    else:
        intercom =  advancedThreshold()

    if minimal.args.createToH or minimal.args.createToHCumulative:
       print( create_ToH_curve_data()) 
        
    exit()
    try:
        intercom.run()
    except KeyboardInterrupt:
        minimal.parser.exit("\nSIGINT received")
    finally:
        intercom.print_final_averages()