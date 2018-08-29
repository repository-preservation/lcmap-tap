"""Create a matplotlib figure"""

from lcmap_tap.Plotting.plot_specs import PlotSpecs
from lcmap_tap.Plotting import plot_functions
from lcmap_tap.Plotting import NAMES, COLORS
from lcmap_tap.logger import log, exc_handler

import sys
import traceback
import datetime as dt
from collections import OrderedDict
from typing import Tuple
import numpy as np
from numpy import ndarray

import matplotlib
from matplotlib import pyplot as plt
import matplotlib.lines as mlines
from matplotlib.figure import Figure

sys.excepthook = exc_handler


def get_plot_items(data: PlotSpecs, items: list) -> dict:
    """
    Check to see which bands and/or indices were selected to plot.
    Args:
        data: An instance of the CCDReader class
        items: A dict containing the selected bands/indices to plot

    Returns:
        temp_dict:

    """
    set_lists = [("All Spectral Bands and Indices", data.all_lookup),
                 ("All Spectral Bands", data.band_lookup),
                 ("All Indices", data.index_lookup)]

    set_lists = OrderedDict(set_lists)

    if len(items) > 0:
        temp_dict = [(i, data.all_lookup[i]) for i in items if i in data.all_lookup.keys()]
        temp_dict = OrderedDict(temp_dict)  # Turn list of tuples into an OrderedDict

        for a in set_lists.keys():
            if a in items:
                # Update the dictionary to include the user-specified items
                temp_dict = plot_functions.merge_dicts(temp_dict, set_lists[a])

        return temp_dict

    else:
        # Do this by default if the user hasn't selected anything from the list
        return data.all_lookup


def draw_figure(data: PlotSpecs, items: list) -> Tuple[matplotlib.figure.Figure, dict, dict, ndarray]:
    """

    Args:
        data: an instance of the CCDReader class, contains all of the plotting attributes and data
        items: A list of strings representing the subplots to be plotted

    Returns:
        fig: A matplotlib.figure.Figure object
        artist_map: A dictionary mapping the data series to plot artists, used for referencing and interactivity
        lines_map: A dictionary mapping the legend lines to the plot artists they represent, used for interactivity
        axes: Using squeeze=False, returns a 2D numpy array of matplotlib.axes.Axes objects

    """

    def check_for_matches(starts: list, breaks: list):
        """
        Check if there are any instances of start date equalling break date

        Args:
            starts: list of ints: start dates in ordinal time
            breaks: list of ints: break dates in ordinal time

        Returns:
            Either a list of match dates or None

        """
        matches = [b_ for b_ in breaks for s_ in starts if s_ == b_]

        if len(matches) == 0:
            return None

        else:
            return matches

    def get_legend_handle(**kwargs):
        """
        A helper function to generate legend handles

        Args:
            **kwargs: Line2D keyword arguments

        Returns:

        """
        return mlines.Line2D([], [], **kwargs)

    plt.style.use('ggplot')

    # get year values for labeling plots
    year1 = str(dt.datetime.fromordinal(data.dates[-1]))[:4]
    year2 = str(dt.datetime.fromordinal(data.dates[0]))[:4]

    # List of years in time series
    years = range(int(year1), int(year2) + 2, 1)

    # list of datetime objects with YYYY-MM-dd pattern using January 1 for month and day
    datetimes = [dt.datetime(yx, 1, 1) for yx in years]

    total_mask = data.qa_mask

    fill_out = data.fill_mask[~data.date_mask]

    class_results = dict()

    for ind, result in enumerate(data.segment_classes):
        if len(result['class_probs']) == 9:
            class_ind = np.argmax(result['class_probs'])

        else:
            # The older classification results have an additional class '0' so indices are off by 1
            class_ind = np.argmax(result['class_probs']) + 1

        class_label = NAMES[class_ind]

        if class_label not in class_results:
            class_results[class_label] = {'starts': [result['start_day']],
                                          'ends': [result['end_day']]}

        else:
            class_results[class_label]['starts'].append(result['start_day'])
            class_results[class_label]['ends'].append(result['end_day'])

    """plot_data is a dict whose keys are band names, index names, or a combination of both

    plot_data[key][0] contains the observed values

    plot_data[key][1] contains the model predicted values
    """
    plot_data = get_plot_items(data=data, items=items)

    """Create an empty dict to contain the mapping of data series to artists

    artist_map[key][0] contains the x-series

    artist_map[key][1] contains the y-series

    artist_map[key][2] contains the subplot name

    The keys that are subplot names will contain an empty point used for displaying which point is selected on the plot

    All other keys are the PathCollections returned by matplotlib.axes.Axes.scatter

    """
    artist_map = {}

    """Create an empty dict to contain the mapping of legend lines to plot artists"""
    lines_map = {}

    """squeeze=False allows for plt.subplots to have a single subplot, must specify the column index as well
    when referencing a subplot because will always return a 2D array
    e.g. axes[num, 0] for subplot 'num'"""
    fig, axes = plt.subplots(nrows=len(plot_data), ncols=1, figsize=(18, len(plot_data) * 5),
                             dpi=65, squeeze=False, sharex='all', sharey='none')

    """Define list objects that will contain the matplotlib artist objects within all subplots"""
    end_lines = list()
    break_lines = list()
    start_lines = list()
    match_lines = list()
    model_lines = list()
    date_lines = list()

    all_obs_points = list()
    all_out_points = list()
    all_mask_points = list()
    empty_point = None

    match_dates = None

    class_lines = dict()
    class_handles = None

    for num, b in enumerate(plot_data.keys()):
        """Make lists to contain references to the specific artist objects for the current subplot."""
        obs_points = list()
        out_points = list()
        mask_points = list()
        empty_point = list()
        class_handles = list()

        # Give each subplot a title
        axes[num, 0].set_title('{}'.format(b))

        """ ---- Create an empty plot to use for displaying which point is clicked later on ---- """
        empty_point.append(axes[num, 0].plot([], [],
                                             ms=12,
                                             c="none",
                                             marker="D",
                                             mec="lime",
                                             mew=1.75,
                                             picker=3,
                                             linewidth=0))

        # log.debug("empty_point created")
        # log.debug("empty_point=%s" % str(empty_point))

        # Store a reference to the empty point which will be used to display clicked points on the plot
        artist_map[b] = empty_point[0]

        # log.debug("Referencing empty_point[0] which is %s for subplot %s" % (str(empty_point[0]), b))

        """ ---- Plot the observed values within the PyCCD time range ---- """
        #: class matplotlib.collections.PathCollection:
        obs = axes[num, 0].scatter(x=data.dates_in[total_mask[data.date_mask]],
                                   y=plot_data[b][0][data.date_mask][total_mask[data.date_mask]],
                                   s=44,
                                   c="green",
                                   marker="o",
                                   edgecolors="black",
                                   picker=3,
                                   )

        obs_points.append(obs)
        all_obs_points.append(obs)

        # There's only ever one item in the *_points lists-a PathCollection artist-but it makes it easier to use with
        # the 2D Lines because those are lists too.  See the plotwindow.py module.
        artist_map[obs_points[0]] = [data.dates_in[total_mask[data.date_mask]],
                                     plot_data[b][0][data.date_mask][total_mask[data.date_mask]], b]

        """ ---- Observed values outside of the PyCCD time range ---- """
        #: class matplotlib.collections.PathCollection:
        out = axes[num, 0].scatter(x=data.dates_out[fill_out],
                                   y=plot_data[b][0][~data.date_mask][fill_out],
                                   s=21,
                                   color="red",
                                   marker="o",
                                   edgecolors="black",
                                   picker=3,
                                   )

        out_points.append(out)
        all_out_points.append(out)

        artist_map[out_points[0]] = [data.dates_out[fill_out], plot_data[b][0][~data.date_mask][fill_out], b]

        """ ---- Plot the observed values masked out by PyCCD ---- """
        #: class matplotlib.collections.PathCollection:
        mask = axes[num, 0].scatter(x=data.dates_in[~total_mask[data.date_mask]],
                                    y=plot_data[b][0][data.date_mask][~total_mask[data.date_mask]],
                                    s=21,
                                    color="0.65",
                                    marker="o",
                                    picker=2,
                                    )

        mask_points.append(mask)
        all_mask_points.append(mask)

        artist_map[mask_points[0]] = [data.dates_in[~total_mask[data.date_mask]],
                                      plot_data[b][0][data.date_mask][~total_mask[data.date_mask]], b]

        """ # ---- plot the model start, end, and break dates ---- """
        match_dates = check_for_matches(data.start_dates, data.break_dates)

        for ind, e in enumerate(data.end_dates):
            lines1 = axes[num, 0].axvline(e, color="maroon", linewidth=1.5)

            end_lines.append(lines1)

        for ind, br in enumerate(data.break_dates):
            lines2 = axes[num, 0].axvline(br, color='r', linewidth=1.5)

            break_lines.append(lines2)

        for ind, s in enumerate(data.start_dates):
            lines3 = axes[num, 0].axvline(s, color='b', linewidth=1.5)

            start_lines.append(lines3)

        if match_dates is not None:

            for ind, m in enumerate(match_dates):
                lines4 = axes[num, 0].axvline(m, color="magenta", linewidth=1.5)

                match_lines.append(lines4)

        """ ---- Draw the predicted curves ---- """
        for c in range(0, len(data.results["change_models"])):
            lines5, = axes[num, 0].plot(data.prediction_dates[c * len(data.bands)],
                                        plot_data[b][1][c],
                                        "orange",
                                        linewidth=3,
                                        alpha=0.8)

            model_lines.append(lines5)

        """ ---- Draw horizontal color bars representing class assignments ---- """

        for key in class_results.keys():
            if key not in class_lines:
                class_lines[key] = list()

            for ind, item in enumerate(class_results[key]['starts']):
                lines6 = axes[num, 0].hlines(y=0,
                                             xmin=item,
                                             xmax=class_results[key]['ends'][ind],
                                             linewidth=6,
                                             colors=COLORS[key])

                class_lines[key].append(lines6)

            class_handles.append(get_legend_handle(linewidth=6,
                                                   color=COLORS[key], label=key))

        """ ---- Set values for the y-axis limits ---- """
        if b in data.index_lookup.keys():
            # Potential dynamic range values
            # ymin = min(plot_data[b][0][data.date_mask][total_mask]) - 0.15
            # ymax = max(plot_data[b][0][data.date_mask][total_mask]) + 0.1

            # Preferred static range values
            ymin = -1.01
            ymax = 1.01

        elif b == "Thermal":
            ymin = -2500
            ymax = 6500

        else:
            # Potential dynamic range values
            # ymin = min(plot_data[b][0][data.date_mask][total_mask]) - 700
            # ymax = max(plot_data[b][0][data.date_mask][total_mask]) + 500

            # Preferred static range values
            ymin = -100
            ymax = 6500

        # Set the y-axis limits
        axes[num, 0].set_ylim([ymin, ymax])

        """ ---- Display the x and y values where the cursor is placed on a subplot ---- """
        axes[num, 0].format_coord = lambda xcoord, ycoord: "({0:%Y-%m-%d}, ".format(
            dt.datetime.fromordinal(int(xcoord))) + "{0:f})".format(ycoord)

        """ ---- Plot a vertical line at January 1 of each year on the time series ---- """
        for date in datetimes:
            lines7 = axes[num, 0].axvline(date, color='dimgray', linewidth=1.5, visible=False)

            date_lines.append(lines7)

        # With sharex=True, set all x-axis tick labels to visible
        axes[num, 0].tick_params(axis='both', which='both', labelsize=12, labelbottom=True)

    """Create custom legend handles"""
    empty_leg = get_legend_handle(marker="D", ms=8, color="none", mec="lime", mew=1.75, linewidth=0,
                                  label="Selected")

    obs_leg = get_legend_handle(marker="o", ms=8, color="green", mec="k", mew=0.3, linewidth=0,
                                label="Clear")

    mask_leg = get_legend_handle(marker="o", ms=4, color="0.65", linewidth=0,
                                 label="Masked")

    out_leg = get_legend_handle(marker="o", ms=4, color="red", mec="black", mew=0.3, linewidth=0,
                                label="Unused")

    end_leg = get_legend_handle(color="maroon", linewidth=1.5, label="End Date")

    break_leg = get_legend_handle(color='r', linewidth=1.5, label="Break Date")

    start_leg = get_legend_handle(color='b', linewidth=1.5, label="Start Date")

    match_leg = get_legend_handle(color='magenta', linewidth=1.5, label="Start Date = Break Date")

    model_leg = get_legend_handle(color="orange", linewidth=3, alpha=0.8, label="Model Fit")

    date_leg = get_legend_handle(color='dimgray', linewidth=1.5, label="Datelines")

    if match_dates is not None:

        handles = [empty_leg, obs_leg, mask_leg, out_leg, end_leg, break_leg, start_leg,
                   match_leg, model_leg, date_leg]

        labels = ["Selected", "Clear", "Masked", "Unused", "End Date", "Break Date", "Start Date",
                  "Start Date = Break Date", "Model Fit", "Datelines"]

        lines = [empty_point[0], all_obs_points, all_mask_points, all_out_points, end_lines, break_lines, start_lines,
                 match_lines, model_lines, date_lines]

    else:
        handles = [empty_leg, obs_leg, mask_leg, out_leg, end_leg, break_leg, start_leg,
                   model_leg, date_leg]

        labels = ["Selected", "Clear", "Masked", "Unused", "End Date", "Break Date", "Start Date",
                  "Model Fit", "Datelines"]

        lines = [empty_point[0], all_obs_points, all_mask_points, all_out_points, end_lines, break_lines, start_lines,
                 model_lines, date_lines]

    """Add whichever land cover classes are present to the legend handles and labels"""
    for c in class_handles:
        handles.append(c)

    for cl in class_results.keys():
        labels.append(cl)

    leg = axes[0, 0].legend(handles=handles, labels=labels,
                            ncol=1,
                            loc="upper left",
                            bbox_to_anchor=(1.00, 1.00),
                            borderaxespad=0.)

    for key in class_lines.keys():
        lines.append(class_lines[key])

    for legline, origline in zip(leg.get_lines(), lines):
        # Set a tolerance of 5 pixels
        legline.set_picker(5)

        # Map the artist to the corresponding legend line
        lines_map[legline] = origline

    # Fill in the figure canvas
    fig.tight_layout()

    # Make room for the legend
    fig.subplots_adjust(right=0.9)

    return fig, artist_map, lines_map, axes
