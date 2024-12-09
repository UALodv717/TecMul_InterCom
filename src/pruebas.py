import numpy as np
print(np.correlate([1, 2, 3], [0, 1, 0.5]))
print(np.correlate([1, 2, 3], [0, 1, 0.5], "same"))
print(np.correlate([1, 2, 3], [0, 1, 0.5], "full"))