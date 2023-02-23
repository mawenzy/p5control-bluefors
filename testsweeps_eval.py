import matplotlib.pyplot as plt
import numpy as np
import time

from p5control import DataGateway
def magic1_ind(time, V, count, freq):
    """
    Gives a rough estimation of in the indices
    """
    mid = (np.max(V) + np.min(V)) / 2

    start = np.argmax(V>mid)
    Vrev = V[::-1]
    end = len(V) - np.argmax(Vrev>mid)

    indices = np.linspace(start, end, int(2*count), dtype=int)

    maxima, minima = [], []

    i = 0
    while i < len(indices) - 1:
        view = V[indices[i]:indices[i+1]]

        if i % 2 == 0:
            # max
            maxima.append(indices[i] + np.argmax(view))
        else:
            # min
            minima.append(indices[i] + np.argmin(view))

        i += 1

    return (
        [start - (maxima[0] - start), end + (end-maxima[-1])],
        minima,
        maxima
    )

def magic1(time, V, count, freq):
    """
    Return the times associated with the indices returned from magic1_ind
    """
    bounds, minima, maxima = magic1_ind(time, V, count, freq)

    return (
        map(lambda x: time[x], bounds),
        map(lambda x: time[x], minima),
        map(lambda x: time[x], maxima),
        )

dgw = DataGateway()

dgw.connect()



from scipy.signal import find_peaks, peak_prominences
from scipy.signal import savgol_filter as sg
from scipy.signal import find_peaks as fp

def magic(t, V, count, freq):
    t = np.ravel(((t.T)[0]).T)
    V = np.ravel(((V.T)[0]).T)
    
    max_V=np.max(np.abs(V))
    V = V / max_V
    length = (len(V))-200
    min_peaks = fp(
        V, 
        height=.25, 
        distance=length/(count+1),
        )[0]
    max_peaks = fp(
        -V, 
        height=.25, 
        distance=length/(count),
        prominence=1,
        )[0]

    return (
        [],
        t[(min_peaks)],
        t[(max_peaks)]
    )

calc_time = []
for name in dgw.get("test").keys():

    
    t = dgw.get_data(f"test/{name}", field="time").T
    V = dgw.get_data(f"test/{name}", field="V").T
    print(t.shape, V.shape)
    count = dgw.get_data(f"test/{name}", field="count")
    freq = dgw.get_data(f"test/{name}", field="freq")


    tic = time.time()
    bounds, minima, maxima = magic1(t, V, count, freq)
    toc = time.time()
    print(toc-tic)
    calc_time.append(toc-tic)


    line_min = min(V)
    line_max = max(V)


    plt.plot(t, V)
    plt.title(f'freq: {freq}, count: {count}')
    for b in bounds:
        plt.vlines(b, line_min, line_max, 'r')
    for b in minima:
        plt.vlines(b, line_min, line_max, 'g')
    for b in maxima:
        plt.vlines(b, line_min, line_max, 'b')

    plt.show()

dgw.disconnect()

# plt.plot(calc_time)
print(np.mean(calc_time))