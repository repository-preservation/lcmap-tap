"""Create a matplotlib figure"""

import sys
import traceback
import datetime as dt
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from collections import OrderedDict
from typing import Tuple
from numpy import ndarray
from lcmap_tap.RetrieveData.retrieve_data import CCDReader
from lcmap_tap.Plotting import plot_functions
from lcmap_tap.logger import log


def exc_handler(exc_type, exc_value, exc_traceback):
    """
    Customized handling of top-level exceptions
    Args:
        exc_type: exception class
        exc_value: exception instance
        exc_traceback: traceback object

    Returns:
        None

    """
    log.warning("Uncaught Exception Type: {}".format(str(exc_type)))
    log.warning("Uncaught Exception Value: {}".format(str(exc_value)))
    log.warning("Uncaught Exception Traceback: {}".format(traceback.print_tb(exc_traceback)))


sys.excepthook = exc_handler


def get_plot_items(data: CCDReader, items: list) -> dict:
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
                # temp_dict = {**temp_dict, **set_lists[a]}
                temp_dict = plot_functions.merge_dicts(temp_dict, set_lists[a])

        return temp_dict

    else:
        # Do this by default if the user hasn't selected anything from the list
        return data.all_lookup


def draw_figure(data: CCDReader, items: list) -> Tuple[matplotlib.figure.Figure, dict, dict, ndarray]:
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
    plt.style.use('ggplot')

    # get year values for labeling plots
    year1 = str(dt.datetime.fromordinal(data.dates[0]))[:4]
    year2 = str(dt.datetime.fromordinal(data.dates[-1]))[:4]

    # List of every other year
    # years = range(int(year1), int(year2) + 2, 2)

    # List of every single year
    years_ = range(int(year1), int(year2) + 2, 1)

    # list of datetime objects with YYYY-MM-dd pattern using July 1 for month and day
    # t = [dt.datetime(yx, 7, 1) for yx in years]

    # list of datetime objects with YYYY-MM-dd pattern using January 1 for month and day
    t_ = [dt.datetime(yx, 1, 1) for yx in years_]

    # list of ordinal time objects
    # ord_time = [dt.datetime.toordinal(tx) for tx in t]

    # list of datetime formatted strings
    # x_labels = [str(dt.datetime.fromordinal(int(L)))[:10] if L != "0.0" and L != "" else "0" for L in ord_time]

    total_mask = data.total_mask

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

    # squeeze=False allows for plt.subplots to have a single subplot, must specify the column index as well
    # when referencing a subplot because will always return a 2D array
    # e.g. axes[num, 0] for plot number 'num' and column 0
    fig, axes = plt.subplots(nrows=len(plot_data), ncols=1, figsize=(18, len(plot_data) * 5),
                             dpi=65, squeeze=False, sharex='all', sharey='none')

    for num, b in enumerate(plot_data.keys()):
        """Make lists to contain references to the specific artist objects for the current subplot.
        These lists are reset with each iteration, but their current items are stored in the artist_map and
        lines_map dictionaries at the end of the for-loop."""

        end_lines, break_lines, start_lines, match_lines, model_lines, date_lines = [], [], [], [], [], []

        obs_points, out_points, mask_points, empty_point = [], [], [], []

        # ---- Create an empty plot to use for displaying which point is clicked later on ----
        empty_point.append(axes[num, 0].plot([], [],
                                             ms=12,
                                             c="none",
                                             marker="D",
                                             mec="lime",
                                             mew=1.75,
                                             picker=3,
                                             linewidth=0))

        # Generate legend line for the selected observation
        axes[num, 0].plot([], [], marker="D", ms=8, color="none", mec="lime", mew=1.75,
                          linewidth=0, label="Selected")

        # Store a reference to the empty point which will be used to display clicked points on the plot
        artist_map[b] = empty_point[0][0]

        """ ---- Plot the observed values within the PyCCD time range ---- """
        obs_points.append(axes[num, 0].scatter(x=data.dates_in[total_mask],
                                               y=plot_data[b][0][data.date_mask][total_mask], s=44, c="green",
                                               marker="o",
                                               edgecolors="black", picker=3))

        # Generate legend line for the observations used by pyccd
        axes[num, 0].plot([], [], marker="o", ms=8, color="green", mec="k", mew=0.3,
                          linewidth=0, label="Clear")

        # There's only ever one item in the *_points lists-a PathCollection artist-but it makes it easier to use with
        # the 2D Lines because those are lists too.  See the plotwindow.py module.
        artist_map[obs_points[0]] = [data.dates_in[total_mask], plot_data[b][0][data.date_mask][total_mask], b]

        """ ---- Observed values outside of the PyCCD time range ---- """
        out_points.append(axes[num, 0].scatter(x=data.dates_out[data.fill_out],
                                               y=plot_data[b][0][~data.date_mask][data.fill_out], s=21, color="red",
                                               marker="o",
                                               edgecolors="black", picker=3))

        # Generate legend line for the obs. outside time range
        axes[num, 0].plot([], [], marker="o", ms=4, color="red", mec="black", mew=0.3, linewidth=0,
                          label="Unused")

        artist_map[out_points[0]] = [data.dates_out[data.fill_out], plot_data[b][0][~data.date_mask][data.fill_out], b]

        """ ---- Plot the observed values masked out by PyCCD ---- """
        mask_points.append(axes[num, 0].scatter(x=data.dates_in[~data.ccd_mask],
                                                y=plot_data[b][0][data.date_mask][~data.ccd_mask], s=21, color="0.65",
                                                marker="o", picker=2))

        # Generate legend line for the masked observations
        axes[num, 0].plot([], [], marker="o", ms=4, color="0.65", linewidth=0,
                          label="Masked")

        artist_map[mask_points[0]] = [data.dates_in[~data.ccd_mask],
                                      plot_data[b][0][data.date_mask][~data.ccd_mask], b]

        # Give each subplot a title
        axes[num, 0].set_title('{}'.format(b))

        # ---- plot the model start, end, and break dates ----
        match_dates = [b for b in data.break_dates for s in data.start_dates if b == s]

        for ind, e in enumerate(data.end_dates):
            if ind == 0:
                lines1 = axes[num, 0].axvline(e, color="maroon", linewidth=1.5, label="End")

                end_lines.append(lines1)

            else:
                # Plot without a label to remove duplicates in the legend
                lines1 = axes[num, 0].axvline(e, color="maroon", linewidth=1.5)

                end_lines.append(lines1)

        for ind, br in enumerate(data.break_dates):
            if ind == 0:
                lines2 = axes[num, 0].axvline(br, color='r', linewidth=1.5, label="Break")

                break_lines.append(lines2)

            else:
                lines2 = axes[num, 0].axvline(br, color='r', linewidth=1.5)

                break_lines.append(lines2)

        for ind, s in enumerate(data.start_dates):
            if ind == 0:
                lines3 = axes[num, 0].axvline(s, color='b', linewidth=1.5, label="Start")

                start_lines.append(lines3)

            else:
                lines3 = axes[num, 0].axvline(s, color='b')

                start_lines.append(lines3)

        for ind, m in enumerate(match_dates):
            if ind == 0:
                lines4 = axes[num, 0].axvline(m, color="magenta", linewidth=1.5, label="Break = Start")

                match_lines.append(lines4)

            else:
                lines4 = axes[num, 0].axvline(m, color="magenta", linewidth=1.5)

                match_lines.append(lines4)

        # ---- Draw the predicted curves ----
        for c in range(0, len(data.results["change_models"])):
            if c == 0:
                lines5, = axes[num, 0].plot(data.prediction_dates[c * len(data.bands)], plot_data[b][1][c], "orange",
                                            linewidth=3, alpha=0.8, label="Model Fit")

                model_lines.append(lines5)

            else:
                lines5, = axes[num, 0].plot(data.prediction_dates[c * len(data.bands)], plot_data[b][1][c], "orange",
                                            alpha=0.8, linewidth=3)

                model_lines.append(lines5)

        # Set values for the y-axis limits
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

        # ---- Display the x and y values where the cursor is placed on a subplot ----
        axes[num, 0].format_coord = lambda xcoord, ycoord: "({0:%Y-%m-%d}, ".format(
            dt.datetime.fromordinal(int(xcoord))) + "{0:f})".format(ycoord)

        # ---- Plot a vertical line at January 1 of each year on the time series ----
        for y in t_:
            if y == t_[0]:
                lines6 = axes[num, 0].axvline(y, color="dimgray", linewidth=1.5, label="Datelines")

                date_lines.append(lines6)

            else:
                lines6 = axes[num, 0].axvline(y, color="dimgray", linewidth=1.5)

                date_lines.append(lines6)

        # ---- Generate the legend for the current subplot ----
        leg = axes[num, 0].legend(ncol=1, loc="upper left", bbox_to_anchor=(1.00, 1.00),
                                  borderaxespad=0.)

        """Have to check for the possibility that match_lines is empty...might be worth considering not plotting this
        at all"""
        if len(match_lines) == 0:
            lines = [empty_point[0], obs_points, out_points, mask_points, end_lines, break_lines, start_lines,
                     model_lines, date_lines]
        else:
            lines = [empty_point[0], obs_points, out_points, mask_points, end_lines, break_lines, start_lines,
                     match_lines, model_lines, date_lines]

        # Map the legend lines to their original artists so the event picker can interact with them
        for legline, origline in zip(leg.get_lines(), lines):
            # Set a tolerance of 5 pixels
            legline.set_picker(5)

            # Map the artist to the corresponding legend line
            lines_map[legline] = origline

        # With sharex=True, set all x-axis tick labels to visible
        axes[num, 0].tick_params(axis='both', which='both', labelsize=12, labelbottom=True)

    # Fill in the figure canvas
    fig.tight_layout()

    # Make room for the legend
    fig.subplots_adjust(right=0.9)

    return fig, artist_map, lines_map, axes
