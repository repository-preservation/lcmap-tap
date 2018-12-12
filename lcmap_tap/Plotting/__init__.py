
COLORS = {'Developed': (0.933, 0.0, 0.0),
          'Agriculture': (0.671, 0.439, 0.157),
          'Grass/Shrub': (0.890, 0.890, 0.761),
          'Tree Cover': (0.110, 0.388, 0.188),
          'Water': (0.278, 0.420, 0.631),
          'Wetlands': (0.729, 0.851, 0.922),
          'Ice/Snow': (1.0, 1.0, 1.0),
          'Barren': (0.702, 0.682, 0.639),
          'No Model-fit': (0.984, 0.604, 0.6)}

NAMES = {1: 'Developed',
         2: 'Agriculture',
         3: 'Grass/Shrub',
         4: 'Tree Cover',
         5: 'Water',
         6: 'Wetlands',
         7: 'Ice/Snow',
         8: 'Barren',
         9: 'No Model-fit'}

LEG_DEFAULTS = {'highlight_pick': {'marker': 'D', 'ms': 8, 'color': 'none', 'mec': 'lime',  # plot params
                               'mew': 1.75, 'linewidth': 0, 'label': 'Selected', 'picker': 3},

                'clear_obs': {'marker': 'o', 'ms': 8, 'color': "green", 'mec': 'k', 'mew': 0.3, 'linewidth': 0,
                                  'label': 'Clear'},

                'mask_obs': {'marker': 'o', 'ms': 4, 'color': 'silver', 'label': 'Masked', 'linewidth': 0},

                'out_obs': {'marker': 'o', 'ms': 4, 'color': 'red', 'mec': 'k', 'mew': 0.3,
                                            'label': 'Unused', 'linewidth': 0},

                'end_lines': {'color': 'maroon', 'linewidth': 1.5, 'label': 'End Date'},

                'break_lines': {'color': 'red', 'linewidth': 1.5, 'label': 'Break Date'},

                'start_lines': {'color': 'blue', 'linewidth': 1.5, 'label': 'Start Date'},

                'match_lines': {'color': 'magenta', 'linewidth': 1.5, 'label': 'Start Date = Break Date'},

                'model_lines': {'color': 'orange', 'linewidth': 3, 'alpha': 0.8, 'label': 'Model Fit'},

                'date_lines': {'color': 'dimgray', 'linewidth': 1.5, 'label': 'Datelines'}
                }

DEFAULTS = {'highlight_pick': {'marker': 'D', 'ms': 12, 'color': 'none', 'mec': 'lime',  # plot params
                               'mew': 1.75, 'linewidth': 0, 'label': 'Selected', 'picker': 3},

            'clear_obs': {'marker': 'o', 's': 44, 'color': 'green', 'edgecolors': 'black',  # scatter params
                          'label': 'Clear', 'picker': 3},

            'mask_obs': {'marker': 'o', 's': 21, 'color': 'silver', 'label': 'Masked', 'picker': 2},  # scatter params

            'out_obs': {'marker': 'o', 's': 21, 'color': 'red', 'edgecolors': 'black',  # scatter params
                        'label': 'Unused', 'picker': 3},

            'end_lines': {'color': 'maroon', 'linewidth': 1.5, 'label': 'End Date', 'linestyle': '-'},

            'break_lines': {'color': 'red', 'linewidth': 1.5, 'label': 'Break Date', 'linestyle': '-'},

            'start_lines': {'color': 'blue', 'linewidth': 1.5, 'label': 'Start Date', 'linestyle': '-'},

            'match_lines': {'color': 'magenta', 'linewidth': 1.5, 'label': 'Start Date = Break Date', 'linestyle': '-'},

            'model_lines': {'color': 'orange', 'linewidth': 3, 'alpha': 0.8, 'label': 'Model Fit', 'linestyle': '-'},

            'date_lines': {'color': 'dimgray', 'linewidth': 1.5, 'label': 'Datelines', 'linestyle': '-'},

            'background': {'color': 'whitesmoke'}
            }

LOOKUP = {"Selected": 'highlight_pick', "Clear": 'clear_obs',
          "Masked": 'mask_obs', "Unused": 'out_obs',
          "End Date": 'end_lines', "Break Date": 'break_lines', "Start Date": 'start_lines',
          "Start Date = Break Date": 'match_lines', "Model Fit": 'model_lines', "Datelines": 'date_lines'}

POINTS = ['Selected', 'Clear', 'Masked', 'Unused']

LINES = ['End Date', 'Break Date', 'Start Date', 'Start Date = Break Date', 'Model Fit', 'Datelines']

VLINES = ['End Date', 'Break Date', 'Start Date', 'Start Date = Break Date']

PLINES = ['Model Fit']

HLINES = [i for i in NAMES.values()]
