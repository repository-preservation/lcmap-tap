
import datetime as dt
from matplotlib import pyplot as plt
import numpy as np


def draw(data, items):

    def get_plot_items():
        if len(items) is 1:
            if items[0] is "all":
                return data.all_lookup

            elif items[0] is "all bands":
                return data.band_lookup

            elif items[0] is "all indices":
                return data.index_lookup

        elif len(items) is 0:
            return data.all_lookup

        else:
            try:
                return {i: data.all_lookup[i] for i in items if i in data.all_lookup.keys()}

            except KeyError:
                pass

    plt.style.use('ggplot')

    # ****X-Axis Ticks and Labels****

    # get year values for labeling plots
    year1 = str(dt.datetime.fromordinal(data.dates[0]))[:4]
    year2 = str(dt.datetime.fromordinal(data.dates[-1]))[:4]
    years = np.arange(int(year1), int(year2) + 2, 2)

    # list of datetime objects with YYYY-MM-dd pattern
    t = [dt.datetime(yx, 7, 1) for yx in years]

    # list of ordinal time objects
    ord_time = [dt.datetime.toordinal(tx) for tx in t]

    # list of datetime formatted strings
    x_labels = [str(dt.datetime.fromordinal(int(L)))[:10] if L != "0.0" and L != "" else "0" for L in ord_time]

    total_mask = np.logical_and(data.mask, data.qa_in)

    plot_data = get_plot_items()

    fig, axes = plt.subplots(nrows=len(plot_data), ncols=1, figsize=(16, len(plot_data) * 9), dpi=200)

    for num, b in enumerate(plot_data.keys()):
        # fg = plt.figure(figsize=(16, 9), dpi=300)
        # ax = fg.add_subplot(2, 1, 1, xlim=(min(data.dates) - 100, max(data.dates) + 500),
        #                   ylim=(min(data.data_in[num, total_mask]) - 500, max(data.data_in[num, total_mask]) + 500))

        # Observed values in PyCCD time range
        axes[num].plot(data.dates_in[total_mask], plot_data[b][0][data.dates_mask][total_mask], 'go', ms=7, mec='k',
                       mew=0.5, label="Observations used by PyCCD")

        # Observed values outside PyCCD time range
        axes[num].plot(data.dates_out[data.qa_out],  plot_data[b][0][~data.dates_mask][data.qa_out], 'ro', ms=5,
                       mec='k', mew=0.5, label="Observations not used by PyCCD")

        # Observed values masked out
        axes[num].plot(data.dates_in[~data.mask], plot_data[b][0][data.dates_mask][~data.mask], color="0.65",
                       marker="o", linewidth=0, ms=3, label="Observations masked by PyCCD")

        axes[num].set_title(f'{b}')

        # plot model break and start dates
        match_dates = [b for b in data.break_dates for s in data.start_dates if b == s]

        for ind, e in enumerate(data.end_dates):
            if ind == 0:
                axes[num].axvline(e, color="black", label="End dates")

            else:
                # Plot without a label to remove duplicates in the legend
                axes[num].axvline(e, color="black")

        for ind, br in enumerate(data.break_dates):
            if ind == 0:
                axes[num].axvline(br, color='r', label="Break dates")

            else:
                axes[num].axvline(br, color='r')

        for ind, s in enumerate(data.start_dates):
            if ind == 0:
                axes[num].axvline(s, color='b', label="Start dates")

            else:
                axes[num].axvline(s, color='b')

        for ind, m in enumerate(match_dates):
            if ind == 0:
                axes[num].axvline(m, color="magenta", label="Break date = Start date")

            else:
                axes[num].axvline(m, color="magenta")

        # Predicted curves
        for c in range(0, len(data.results["change_models"])):
            if c == 0:
                axes[num].plot(data.prediction_dates[c * len(data.bands)],  plot_data[b][1][c], "orange", linewidth=2,
                               label="PyCCD model fit")

            else:
                axes[num].plot(data.prediction_dates[c * len(data.bands)], plot_data[b][1][c], "orange", linewidth=2)

        # Add legend
        axes[num].legend(mode="expand", ncol=4, loc="lower center")

        # Add x-ticks and x-tick_labels
        axes[num].set_xticks(ord_time)

        axes[num].set_xticklabels(x_labels, rotation=70, horizontalalignment="right")

    return fig
