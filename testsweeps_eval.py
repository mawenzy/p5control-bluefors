import matplotlib.pyplot as plt
import numpy as np

from p5control import DataGateway

dgw = DataGateway()

dgw.connect()

def magic(time, V, count, freq):
    return (
        (time[0], time[-1]),
        (time[10]),
        (time[20])
    )

calc_time = []
for name in dgw.get("test").keys():

    time = dgw.get_data(f"test/{name}", field="time").T
    V = dgw.get_data(f"test/{name}", field="V").T
    count = dgw.get_data(f"test/{name}", field="count")
    freq = dgw.get_data(f"test/{name}", field="freq")

    tic = time.time()
    bounds, minima, maxima = magic(time, V, count, freq)
    toc = time.time()
    print(toc-tic)
    calc_time.append(toc-tic)

    plt.plot(time, V)

    line_min = min(V)
    line_max = max(V)

    for b in bounds:
        plt.vlines(b, line_min, line_max, 'r')
    for b in minima:
        plt.vlines(b, line_min, line_max, 'g')
    for b in maxima:
        plt.vlines(b, line_min, line_max, 'b')

    plt.show()

dgw.disconnect()

plt.plot(calc_time)
print(np.mean(calc_time))