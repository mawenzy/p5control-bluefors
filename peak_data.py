import itertools
import time

import numpy as np

from p5control import DataGateway, InstrumentGateway

gw = InstrumentGateway()
dgw = DataGateway()

gw.connect()
dgw.connect()

counter = itertools.count()

m = gw.measure()
stop_measurement = False
if not m.running:
    stop_measurement = True
    m.start()

# parameters
freqs = np.logspace(-1, 1, base=10, num=5)
counts = [1,2,5,10]

def _get_dataset(tic, toc, tic_ndx, path, multi_keyword):
    path = f"{path}/multi_{multi_keyword}/"
    while True:
        try:
            test = dgw.get_data(path, indices=slice(-1, None, None), field='time')[0]
            if test > toc:
                break
        except KeyError:
            time.sleep(0.1)

    multi = dgw.get_data(path, indices=slice(tic_ndx, None, None))
    t, V = multi['time'], multi['V']
    indices = (np.argmin(np.abs(t-tic)), 
                np.argmin(np.abs(t-toc)))
    return t[indices[0]:indices[1]], V[indices[0]:indices[1]]

for _,f,c in itertools.product(range(4), freqs, counts):

    # setup bias_source to sweep mode        
    gw.source_bias.set_amplitude(.33)
    gw.source_bias.set_frequency(f)
    gw.source_bias.set_sweep_count(c)

    # wait for measurement
    tic_ndx = []
    for s in ['source']:
        # if measurement just started, dataset doen't exist => Keyerror
        try:
            tic_ndx.append(int(dgw.get(f'{m.path}/multi_{s}').shape[0])-1)
        except KeyError:
            tic_ndx.append(0)

    tic = time.time()
    time.sleep(0.1)
    
    gw.source_bias.trigger()

    toc = tic + c / f + 0.2

    # get data from dgw
    t, s_V = _get_dataset(tic, toc, tic_ndx[0], m.path, multi_keyword='source')

    dgw.append(
        f"test/{str(next(counter))}",
        {"time": t, "V": s_V, "count": c, "freq": f}
    )

    time.sleep(1)

if stop_measurement:
    m.stop()

gw.disconnect()
dgw.disconnect()