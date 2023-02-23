import numpy as np

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

def magic2(time, V, count, freq):
    """
    Takes the indices from magic1_ind and improves them by using fits
    """
    bounds, minima, maxima = magic1_ind(time, V, count, freq)

    ind_soup = [0] + bounds + minima + maxima + [len(V)]
    ind_soup.sort()

    print(ind_soup)

    bounds, maxima, minima = [], [], []

    i = 0
    while i < len(ind_soup) - 2:
        slice1 = slice(
            ind_soup[i] + int(0.05 * (ind_soup[i+1] - ind_soup[i])),
            ind_soup[i+1] - int(0.05 * (ind_soup[i+1] - ind_soup[i])))

        slice2 = slice(
            ind_soup[i+1] + int(0.05 * (ind_soup[i+2] - ind_soup[i+1])),
            ind_soup[i+2] - int(0.05 * (ind_soup[i+2] - ind_soup[i+1])))

        times = np.reshape(time[slice1], (len(time[slice1]),))
        vs = np.reshape(V[slice1], (len(V[slice1]),))

        fit1 = np.polynomial.Polynomial.fit(times, vs, deg=1)

        print(fit1)

        plt.plot(time[slice1], V[slice1])
        plt.plot(time[slice2], V[slice2])

        plt.show()



        i += 1
