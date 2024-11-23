import matplotlib
import matplotlib.pyplot as plt
import matplotlib.axes as ax
import math
import numpy as np
import sounddevice as sd
import soundfile
from scipy import signal

def quantizer(x, quantization_step):
    k = (x / quantization_step).astype(np.int16)
    return k

def dequantizer(k, quantization_step):
    y = quantization_step * k
    return y

def plot(x, y, xlabel='', ylabel='', title=''):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title(title)
    ax.grid()
    ax.xaxis.set_label_text(xlabel)
    ax.yaxis.set_label_text(ylabel)
    ax.plot(x, y)
    plt.show(block=False)
    
x = np.linspace(-8, 8, 500) # Input samples
k2 = quantizer(x, quantization_step = 2)
y2 = dequantizer(k2, quantization_step = 2)
k3 = quantizer(x, quantization_step = 3)
y3 = dequantizer(k3, quantization_step = 3)

plot(x, y2, "Input Sample", "Reconstructed Sample", "Dead-zone Quantizer ($\Delta={}$)".format(2))
plot(x, y3, "Input Sample", "Reconstructed Sample", "Dead-zone Quantizer ($\Delta={}$)".format(3))

def q_deq(x, quantization_step):
    k = quantizer(x, quantization_step)
    y = dequantizer(k, quantization_step)
    return k, y

x = np.arange(start = -8, stop = 9, step = 1)
k, y = q_deq(x, quantization_step = 3)
print("    Original samples =", x)
print("Quantization indexes =", k)
print(" Dequantized samples =", y)

x, sampling_rate = soundfile.read(r"C:\Users\blaf2\git\TecMul_InterCom\data\AviadorDro_LaZonaFantasma_8000Hz.oga")
x = x[0:65536*2] * 32768
x = x.astype(np.int16)

sd.play(x)
plot(np.linspace(0, len(x)-1, len(x)), x, "Sample", "Amplitude", "Original Signal")

# Effect of quantization
quantization_step = 2048
k, y = q_deq(x, quantization_step)
sd.play(y)
plot(np.linspace(0, len(y)-1, len(y)), y, "Sample", "Amplitude", "Quantized Signal ($\Delta={}$)".format(quantization_step))

# RD curve

def average_energy(x):
    return np.sum(x.astype(np.double)*x.astype(np.double))/len(x)

def RMSE(x, y):
    error_signal = x - y
    return math.sqrt(average_energy(error_signal))

def entropy_in_bits_per_symbol(sequence_of_symbols):
    value, counts = np.unique(sequence_of_symbols, return_counts = True)
    probs = counts / len(sequence_of_symbols)
    n_classes = np.count_nonzero(probs)

    if n_classes <= 1:
        return 0

    entropy = 0.
    for i in probs:
        entropy -= i * math.log(i, 2)

    return entropy

def RD_curve(x):
    points = []
    for q_step in range(128, 4096, 128):
        k, y = q_deq(x, q_step)
        #print(np.unique(k))
        rate = entropy_in_bits_per_symbol(k)
        distortion = RMSE(x, y)
        points.append((rate, distortion))
    return points
RD_points = RD_curve(x)

plt.title("RD Tradeoff")
plt.xlabel("R (Estimated Bits per Sample) [Entropy]")
plt.ylabel("D (Root Mean Square Error)")
plt.scatter(*zip(*RD_points), s=2, c='b', marker="o")
plt.show()