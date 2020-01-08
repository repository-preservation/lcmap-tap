
COLORS = {'Developed': (1.0, 0.19607843137254902, 0.19607843137254902),
          'Agriculture': (0.7450980392156863, 0.5490196078431373, 0.35294117647058826),
          'Grass/Shrub': (0.9019607843137255, 0.9411764705882353, 0.8235294117647058),
          'Tree Cover':(0.10980392156862745, 0.38823529411764707, 0.18823529411764706),
          'Water': (0.0, 0.4392156862745098, 1.0),
          'Wetlands': (0.7019607843137254, 0.8509803921568627, 1.0),
          'Ice/Snow': (1.0, 1.0, 1.0),
          'Barren': (0.7019607843137254, 0.6823529411764706, 0.6392156862745098),
          'No Model-fit': (0.6705882352941176, 0.0, 0.8392156862745098)}

NAMES = {1: 'Developed',
         2: 'Agriculture',
         3: 'Grass/Shrub',
         4: 'Tree Cover',
         5: 'Water',
         6: 'Wetlands',
         7: 'Ice/Snow',
         8: 'Barren',
         9: 'No Model-fit'}

LEG_DEFAULTS = {'highlight_pick': {'marker': 'D',  # plot params
                                   'ms': 8,
                                   'color': 'none',
                                   'mec': 'lime',
                                   'mew': 1.75,
                                   'linewidth': 0,
                                   'label': 'Selected',
                                   'picker': 3},

                'clear_obs': {'marker': 'o',
                              'ms': 8,
                              'color': 'lightskyblue',
                              'mec': 'k',
                              'mew': 0.3,
                              'linewidth': 0,
                              'label': 'Clear'},

                'mask_obs': {'marker': 'o',
                             'ms': 4,
                             'color': 'silver',
                             'label': 'Masked',
                             'linewidth': 0},

                'out_obs': {'marker': 'o',
                            'ms': 4,
                            'color': 'red',
                            'mec': 'k',
                            'mew': 0.3,
                            'label': 'Unused',
                            'linewidth': 0},

                'end_lines': {'color': 'red',
                              'linewidth': 2,
                              'label': 'End Date'},

                'break_lines': {'color': 'orange',
                                'linewidth': 2,
                                'linestyle': '--',
                                'label': 'Break Date'},

                'start_lines': {'color': 'green',
                                'linewidth': 2,
                                'label': 'Start Date'},

                'model_lines': {'color': 'black',
                                'linewidth': 3,
                                'label': 'Model Fit'},

                'date_lines': {'color': 'dimgray',
                               'linewidth': 1.5,
                               'label': 'Datelines'}
                }

DEFAULTS = {'highlight_pick': {'marker': 'D',  # plot params
                               'ms': 12,
                               'color': 'none',
                               'mec': 'lime',
                               'mew': 1.75,
                               'linewidth': 0,
                               'label': 'Selected',
                               'picker': 3},

            'clear_obs': {'marker': 'o',
                          's': 44,
                          'color': 'lightskyblue',
                          'edgecolors': 'black',  # scatter params
                          'label': 'Clear',
                          'picker': 3},

            'mask_obs': {'marker': 'o',
                         's': 21,
                         'color': 'silver',
                         'label': 'Masked',
                         'picker': 2},  # scatter params

            'out_obs': {'marker': 'o',
                        's': 21,
                        'color': 'red',
                        'edgecolors': 'black',  # scatter params
                        'label': 'Unused',
                        'picker': 3},

            'end_lines': {'color': 'red',
                          'linewidth': 2,
                          'label': 'End Date',
                          'linestyle': '-'},

            'break_lines': {'color': 'orange',
                            'linewidth': 2,
                            'label': 'Break Date',
                            'linestyle': '--'},

            'start_lines': {'color': 'green',
                            'linewidth': 2,
                            'label': 'Start Date',
                            'linestyle': '-'},

            'model_lines': {'color': 'black',
                            'linewidth': 3,
                            'label': 'Model Fit',
                            'linestyle': '-'},

            'date_lines': {'color': 'dimgray',
                           'linewidth': 2,
                           'label': 'Datelines',
                           'linestyle': '-'},

            'background': {'color': 'whitesmoke'}
            }

LOOKUP = {"Selected": 'highlight_pick',
          "Clear": 'clear_obs',
          "Masked": 'mask_obs',
          "Unused": 'out_obs',
          "End Date": 'end_lines',
          "Break Date": 'break_lines',
          "Start Date": 'start_lines',
          "Model Fit": 'model_lines',
          "Datelines": 'date_lines'}

POINTS = ['Selected',
          'Clear',
          'Masked',
          'Unused']

LINES = ['End Date',
         'Break Date',
         'Start Date',
         'Model Fit',
         'Datelines']

VLINES = ['End Date',
          'Break Date',
          'Start Date']

PLINES = ['Model Fit']

HLINES = [i for i in NAMES.values()]
