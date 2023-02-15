import signal

from p5control import DataServer, await_close

dserv = DataServer(filename="testsweeps.hdf5")

dserv.start()

def close(_):
    dserv.stop()

signal.signal(signal.SIGINT, close)
signal.signal(signal.SIGTERM, close)

await_close(dserv)