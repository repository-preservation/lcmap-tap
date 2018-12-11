"""These are artists on the plot figure that we want to set symbology for"""

from lcmap_tap import HOME
from lcmap_tap.Plotting import DEFAULTS, LOOKUP

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
            self.opts = DEFAULTS

    def update_config(self, item, params):
        _id = LOOKUP[item]

        temp = self.opts[_id]

        for key in temp.keys():
            if key in params.keys():
                temp[key] = params[key]

        self.opts[item] = temp

    def save_config(self):
        with open(config_file, 'w') as f:
            yaml.dump(self.opts, f, default_flow_style=False)
