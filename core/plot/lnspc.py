import numpy as np
from rpyc.utils.classic import obtain

from p5control import DataGateway
from p5control.gui import BasePlotConfig


class LnSpcPlotConfig(BasePlotConfig):
    """
    Plot config which subscribes to the parent group and plots incoming new datasets
    """
    def __init__(
        self,
        dgw: DataGateway,
        path: str,
        *args,
        **kwargs
    ):
        super().__init__(dgw, path, *args, **kwargs)

        self.dgw = dgw
        node = dgw.get(path)

        compound_names = node.dtype.names
        ndim = node.shape

        self._config["data"] = dgw.get_data(path)
        self._config["attrs"] = node.attrs
        self._config["x_data"] = np.linspace(
                                    float(self._config["attrs"]["start"]),
                                    float(self._config["attrs"]["stop"]),
                                    int(self._config["attrs"]["points"]),
                                    dtype = 'float64'
                                )

        # set defaults for x and y indexing
        self._config["x"] = self._config["attrs"]["x_axis"]
        self._config["y"] = compound_names[1]

        self.callid = self.dgw.register_callback(path, self.callback)

    def callback(self, data):
        data = obtain(data)

        with self._config["lock"]:
            self._config["data"] = data

    def cleanup(self):
        self.dgw.remove_callback(self.callid)

    def update(self):
        with self._config["lock"]:
            data = self._config["data"]
            plotDataItem = self._config["plotDataItem"]

            plotDataItem.setData(
                self._config['x_data'],
                data[self._config["y"]][-1]
            )
