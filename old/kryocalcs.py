# uncompyle6 version 3.7.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 3.8.5 (default, Jul 28 2020, 12:59:40) 
# [GCC 9.3.0]
# Embedded file name: kryocalcs.py
# Compiled at: 2015-12-08 15:57:51
import numpy as np, gc, matplotlib.pyplot as plt, matplotlib as mpl

def clearall():
    """manually remove global variables for garbage collection"""
    import gc
    coll = []
    coll = [ var for var in globals() if (var[:2], var[-2:]) != ('__', '__') ]
    for var in coll:
        del globals()[var]

    del coll
    gc.collect()


def movaver(data, window_len):
    """a moving averager function"""
    wd = window_len
    d = data
    weightings = np.repeat(1.0, wd) / wd
    return np.convolve(d, weightings)[wd - 1:-(wd - 1)]


def smooth(data, window_len=11, window='hanning'):
    """Smooth the data using a window with requested size.

        This method is based on the convolution of a scaled window with the
        signal.  The signal is prepared by introducing reflected copies of the
        signal (with the window size) in both ends so that transient parts are
        minimized in the begining and end part of the output signal.

        Parameters
        ----------
        data : ndarray
            The 1D numpy array to be smoothed
        window_len : int>2, optional
            The dimension of the smoothing window; should be an odd integer
        window : str, optional
            The type of window from 'flat', 'hanning', 'hamming', 'bartlett',
            'blackman' flat window will produce a moving average smoothing.

        See also
        --------
            smooth, numpy.hanning, numpy.hamming, numpy.bartlett,
            numpy.blackman, numpy.convolve, scipy.signal.lfilter

        Notes
        -----
            1) This was modified from http://wiki.scipy.org/Cookbook/SignalSmooth.
            2) length(output) != length(input), to correct this:
               return y[(window_len/2-1):-(window_len/2)] instead of just y.

        """
    if window_len < 3:
        return
    if window not in ('flat', 'hanning', 'hamming', 'bartlett', 'blackman'):
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming'," + "'bartlett', 'blackman'"
    xData = data
    s = np.r_[(xData[window_len - 1:0:-1], xData, xData[-1:-window_len:-1])]
    if window == 'flat':
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.' + window + '(window_len)')
    y = np.convolve(w / w.sum(), s, mode='valid')
    return y[window_len / 2:-window_len / 2 + 1]


def resample_XY(x, y, NPoints, binrange=None):
    """
    resample irregluarly spaced data
    returns:
    --------
    x2  new regularly spaced axis with NPoints data points
    y2  resampled y axis

    """
    import scipy.stats as scistat
    y2, edges, nr = scistat.binned_statistic(x, y, bins=NPoints, statistic='median', range=binrange)
    x2 = edges[:-1] + np.diff(edges) / 2
    return (x2, y2)


def resample_XYZ(x, y, z, NPoints=(11, 11), binrange=[[None, None], [None, None]]):
    """
    resample irregluarly spaced data
    returns:
    --------
    x2  new regularly spaced axis with NPoints data points
    y2  resampled y axis

    """
    import scipy.stats as scistat
    z2, xedges, yedges, nr = scistat.binned_statistic_2d(x, y, z, bins=NPoints, statistic='median', range=binrange)
    x2 = xedges[:-1] + np.diff(xedges) / 2
    y2 = yedges[:-1] + np.diff(yedges) / 2
    return (x2, y2, z2)


def resample(data, NPoints):
    """resample irregluarly spaced data, using binned statistics
       noise is reduced by bin averaging (median)
    returns:
    --------
    data_2  new regularly spaced axis with NPoints data points
    """
    import scipy.stats as scistat
    x = np.arange(len(data))
    y2, edges, nr = scistat.binned_statistic(x, data, bins=NPoints, statistic='median')
    return y2


def resample_2step(data, NPoints, prereduction=3):
    """resample irregluarly spaced data, using binned statistics
    noise is reduced by bin averaging (median). Data is smoothed and reduced in length by a factor before binned statistics are applied
    to reduce computational load for large datasets
    returns:
    --------
    data_2  new regularly spaced axis with NPoints data points
    """
    preNPoints = np.rint(len(data) / prereduction)
    preData = interpolate_linear(data, int(preNPoints), smooth_window=prereduction)
    redData = resample(preData, NPoints)
    return redData


def interpolate_linear(data, NPoints, smooth_window=None):
    """!!! does not reduce noise """
    from scipy.interpolate import interp1d
    x = np.arange(len(data))
    if smooth_window:
        ds = smooth(data, smooth_window)
    else:
        ds = data
    f = interp1d(x, ds, bounds_error=False)
    xnew = np.linspace(0, len(data) - 1, num=NPoints + 1, endpoint=True)
    ynew = f(xnew)
    return ynew


def interpolate(x, NPoints, DropData, Spline):
    """
    interpolate regulary spaced data
    Inputs: x           data values
            NPoints     desired amount of resulted data points
            DropData    take only every n=DropData value
            Spline      if Spline=1 use univariate spline function, if Spline=0 use linear interpolation
    return: newx        interpolated regulary spaced datapoints

    """
    from scipy.interpolate import interp1d
    from scipy.interpolate import InterpolatedUnivariateSpline
    x = x[::DropData]
    T = np.int32(np.linspace(0, len(x) - 1, num=len(x), endpoint=True))
    if Spline:
        f = InterpolatedUnivariateSpline(T, x)
    else:
        f = interp1d(T, x)
    del x
    Tnew = np.int32(np.linspace(0, NPoints, num=NPoints + 1, endpoint=True))
    xnew = f(Tnew)
    return xnew


def peakdet(v, delta, x=None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    
    Returns two arrays
    
    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %      
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by

    %        DELTA.
    
    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.
    
    """
    import sys
    maxtab = []
    mintab = []
    if x is None:
        x = np.arange(len(v))
    v = np.asarray(v)
    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')
    if not np.isscalar(delta):
        sys.exit('Input argument delta must be a scalar')
    if delta <= 0:
        sys.exit('Input argument delta must be positive')
    mn, mx = np.Inf, -np.Inf
    mnpos, mxpos = np.NaN, np.NaN
    lookformax = True
    for i in np.arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        if lookformax:
            if this < mx - delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        elif this > mn + delta:
            mintab.append((mnpos, mn))
            mx = this
            mxpos = x[i]
            lookformax = True

    return (
     np.array(maxtab), np.array(mintab))


def local_MinMax(data, window):
    """Find the local minima within fits, and return them and their indices.

    Returns a list of indices at which the minima were found, and a list of the
    minima, sorted in order of increasing minimum.  The keyword argument window
    determines how close two local minima are allowed to be to one another.  If
    two local minima are found closer together than that, then the lowest of
    them is taken as the real minimum.  window=1 will return all local minima"""
    from scipy.ndimage.filters import minimum_filter as min_filter
    from scipy.ndimage.filters import maximum_filter as max_filter
    fits = data
    minfits = min_filter(fits, size=window, mode='wrap')
    maxfits = max_filter(fits, size=window, mode='wrap')
    min_indices = np.nonzero(fits == minfits)
    max_indices = np.nonzero(fits == maxfits)
    min_bool = fits == minfits
    max_bool = fits == maxfits
    min_indices = [ i[min_bool] for i in np.indices(fits.shape) ]
    max_indices = [ i[max_bool] for i in np.indices(fits.shape) ]
    return (
     min_indices, max_indices)


def uniquify(seq, idfun=None):
    """ remove douplicate elements from 'seq' (list), order preserving """
    if idfun is None:

        def idfun(x):
            return x

    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)

    return result


def regular_grid2D(X, Y, Z, resolution=(10, 10), extents=None):
    """
    map irregularly spaced x, y and z data on a regular grid defined bins and range.
    The routine is based on numpy.histogram2d

    x, y, z: array_like, shape (N,)

    resolution: [nx, ny] with nx, ny intergers
 
    extents: optional array_like, shape(2,2)
            The leftmost and rightmost edges of the bins along each dimension
            [[xmin, xmax], [ymin, ymax]]. All values outside of this range will be considered outliers and not tallied in the histogram.
            if not specified [[min(x), max(x)],[min(y), max(y)]] is used

    Returns:
    image: ndarray, shape(nx, ny)
           The bi-dimensional histogram of samples x and y with bin values given by sum(z)/bin_count per bin nx, ny. 
        
    format:  format['extent'] = [x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]]
             format['aspect'] = (x_edges[-1]-x_edges[0])/(y_edges[-1]-y_edges[0])
             format['edges'] = [x_edges, y_edges]
    """
    iSUM, x_edges, y_edges = np.histogram2d(X, Y, bins=resolution, range=extents, normed=False, weights=Z)
    iCOUNT, x_edges, y_edges = np.histogram2d(X, Y, bins=resolution, range=extents, normed=False, weights=None)
    format = {}
    format['extent'] = [
     x_edges[0], x_edges[(-1)], y_edges[0], y_edges[(-1)]]
    format['aspect'] = (x_edges[(-1)] - x_edges[0]) / (y_edges[(-1)] - y_edges[0])
    format['edges'] = [x_edges, y_edges]
    return (
     iSUM.T / iCOUNT.T, format)


def integer_grid2D(x, y, z, resolution=(128, 128)):
    """
    calculate a regular grid of irregularly spaced x, y and z data. The x and y coordinates are multplied by a factor and shifted
    to convert the data range to integer bins. The integer values are then used as index to populate the grid with z values.
    Empty cells are filled with NaN, occupied cells with the mean of the occuier (z).
 
    x, y and z  - numpy arrays containing the data
    resolution  - number of bins along the x and y axes

    returns the image array and a formating dictionary

    Example:
    --------
    x=np.linspace(-0.1, 0.5, 124)
    y=np.linspace(-4, 4, 68)
    xx, yy=np.meshgrid(x, y)
    z=np.sin(xx**2) + (xx*yy**2) / (xx**2 + yy**2)

    X= xx.flatten()
    Y= yy.flatten()
    Z= z.flatten()

    im1, form1= integer_grid2D(X, Y, Z, resolution=(12, 12))

    f, (ax1, ax2)=plt.subplots(2)
    ax1.imshow(z, cmap=plt.cm.jet, norm=None, aspect=None, interpolation=None, alpha=None, vmin=None, vmax=None, origin=None, extent=None,
               shape=None, filternorm=1, filterrad=4.0, imlim=None, resample=None, url=None)
    ax2.imshow(im1, cmap=plt.cm.jet, norm=None, aspect=None, interpolation=None, alpha=None, vmin=None, vmax=None, origin=None, extent=None,
               shape=None, filternorm=1, filterrad=4.0, imlim=None, resample=None, url=None)
    plt.show()

    """
    xval = x.astype(float)
    yval = y.astype(float)
    zval = z.astype(float)
    xfact = resolution[0] / (np.nanmax(xval) - np.nanmin(xval))
    yfact = resolution[1] / (np.nanmax(yval) - np.nanmin(yval))
    xi = np.round(np.add(xval * float(xfact), -np.nanmin(xval * float(xfact))), decimals=0).astype(int)
    yi = np.round(np.add(yval * float(yfact), -np.nanmin(yval * float(yfact))), decimals=0).astype(int)
    Zn = np.zeros((np.nanmax(xi) + 1, np.nanmax(yi) + 1))
    Zsum = np.zeros((np.nanmax(xi) + 1, np.nanmax(yi) + 1))
    Zmean = np.zeros((np.nanmax(xi) + 1, np.nanmax(yi) + 1))
    for i in range(len(xi)):
        try:
            Zsum[(int(xi[i]), int(yi[i]))] += zval[i]
            Zn[(int(xi[i]), int(yi[i]))] += 1
        except:
            pass

    Zmean[Zmean == 0] = np.nan
    Zmean = Zsum.astype(float) / Zn.astype(float)
    extent = (
     np.nanmin(xval), np.nanmax(xval), np.nanmin(yval), np.nanmax(yval))
    ar = (extent[1] - extent[0]) / (extent[3] - extent[2])
    format = {}
    format['extent'] = extent
    format['aspect'] = ar
    return (
     Zmean.T, format)


def cmap_intervals(cmap='YlOrBr', length=50, from_interval=(0, 255)):
    """
    Return evenly spaced intervals of a given colormap `cmap`.
        
    cmap - name of a matplotlib colormap (see matplotlib.pyplot.cm)
    length - the number of colors used before cycling back to first color. When
    `length` is large (> ~10), it is difficult to distinguish between
    successive lines because successive colors are very similar.
    from_interval -  tuple (low, high) specifying the start (>=0) and end points (<= 255) of the RGB colorscale along cmap

    Example:
        cols=cmap_intervals(cmap='jet', length=100, from_interval=(120, 230))

        for i in range(100):
            plt.plot(i, i**2, 'o', color=cols[i], markersize=10)

        plt.show()
    """
    cm = getattr(plt.cm, cmap)
    crange = dict(start=from_interval[0], stop=from_interval[1])
    if length > abs(crange['start'] - crange['stop']):
        print 'Warning: the input length is greater than the number of' + 'colors in the colormap; some colors will be repeated'
    idx = np.linspace(crange['start'], crange['stop'], length).astype(np.int)
    return cm(idx)


def cycle_cmap(cmap='YlOrBr', length=50, from_interval=(0, 255)):
    """
    Set default color cycle of matplotlib to a given colormap `cmap`.

    The default color cycle of matplotlib is set to evenly distribute colors in
    color cycle over specified colormap.

    Note: this function must be called before *any* plot commands because it
    changes the default color cycle.

    See ``cmap_intervals`` for input details.
    """
    colcycle = cmap_intervals(cmap, length, from_interval)
    plt.rc('axes', color_cycle=colcycle.tolist())