"""Author: Kelcy Smith"""

import base64
import yaml
from functools import lru_cache

import requests
import numpy as np


# base_url = 'something'

class LCMAPHTTP:
    def __init__(self, config):
        self.base_url = yaml.load(open(config, 'r'))['merlin']

    def getchips(self, x, y, acquired, ubid):
        """
        Make a request to the HTTP API for some chip data.
        """
        chip_url = f'{self.base_url}/chips'

        data = requests.get(chip_url, params={'x': x,
                                              'y': y,
                                              'acquired': acquired,
                                              'ubid': ubid})
        return data.json()

    @lru_cache()
    def getregistry(self):
        """
        Retrieve the spec registry from the API.
        """
        reg_url = f'{self.base_url}/registry'

        return requests.get(reg_url).json()

    @lru_cache()
    def getgrid(self):
        """
        Retrieve the tile and chip definitions for the grid (geospatial transformation information)
        from the API.
        """
        grid_url = f'{self.base_url}/grid'

        return requests.get(grid_url).json()

    @lru_cache()
    def getspec(self, ubid):
        """
        Retrieve the appropriate spec information for the corresponding ubid.
        """
        registry = self.getregistry()

        return next(filter(lambda x: x['ubid'] == ubid, registry), None)

    def tonumpy(self, chip):
        """
        Convert the data response to a numpy array.
        """
        spec = self.getspec(chip['ubid'])
        data = base64.b64decode(chip['data'])

        chip['data'] = np.frombuffer(data, spec['data_type'].lower()).reshape(*spec['data_shape'])

        return chip

    def requestchips(self, x, y, acquired, ubid):
        """
        Helper func to wrap the data conversion around the http response.
        """
        return [self.tonumpy(c) for c in self.getchips(x, y, acquired, ubid)]
