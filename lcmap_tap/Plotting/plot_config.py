"""These are artists on the plot figure that we want to set symbology for"""

from lcmap_tap import HOME
from lcmap_tap.logger import log
from lcmap_tap.Plotting import DEFAULTS, LOOKUP, LEG_DEFAULTS

import os
import yaml

config_file = os.path.join(HOME, 'plot_config.yml')

if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        CONFIG = yaml.load(f)


class PlotConfig:

    def __init__(self):
        if os.path.exists(config_file):
            with open(config_file, 'r') as yaml_file:
                self.opts = yaml.load(yaml_file)

        else:
            self.opts = {'DEFAULTS': DEFAULTS, 'LEG_DEFAULTS': LEG_DEFAULTS}

    def update_config(self, item, params):
        log.debug('PARAMS: {}'.format(params))

        _id = LOOKUP[item]

        if _id is 'highlight_pick':
            # 's' won't work for plots, only for scatters
            params['ms'] = params['s']

            params.pop('s', None)

        temp = self.opts['DEFAULTS'][_id]

        for key, value in params.items():
            temp[key] = value

        self.opts['DEFAULTS'][_id] = temp

        temp = self.opts['LEG_DEFAULTS'][_id]

        for key, value in params.items():
            # Don't want to change symbol size on the legend
            if key is not 's':
                temp[key] = value

        self.opts['LEG_DEFAULTS'][_id] = temp

    def save_config(self):
        with open(config_file, 'w') as f:
            yaml.dump(self.opts, f, default_flow_style=False)
