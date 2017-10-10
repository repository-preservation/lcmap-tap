
import datetime as dt
from matplotlib import pyplot as plt


def get_plot_items(data, items):
    """
    Check to see which bands and/or indices were selected to plot.
    :return:
    """
    set_lists = {"All Bands and Indices": data.all_lookup, "All Bands": data.band_lookup,
                 "All Indices": data.index_lookup}

    if len(items) > 0:
        temp_dict = {i: data.all_lookup[i] for i in items if i in data.all_lookup.keys()}

        for a in set_lists.keys():
            if a in items:
                temp_dict =  {**temp_dict, **set_lists[a]}

        return temp_dict


        # temp = {i : data.all_lookup[i] for i in items if i in data.all_lookup.keys()}
    else:
        return data.all_lookup


def draw_figure(data, items, model_on, masked_on):
    """
    Generate a matplotlib figure
    :param masked_on: boolean
    :param model_on: boolean
    :param data: class instance
    :param items: list of strings
    :return: dictionary
    """
    print("Entered draw function")

    plt.style.use('ggplot')

    # ****X-Axis Ticks and Labels****

    # get year values for labeling plots
    year1 = str(dt.datetime.fromordinal(data.dates[0]))[:4]
    year2 = str(dt.datetime.fromordinal(data.dates[-1]))[:4]
    years = range(int(year1), int(year2) + 2, 2)

    # list of datetime objects with YYYY-MM-dd pattern
    t = [dt.datetime(yx, 7, 1) for yx in years]

    # list of ordinal time objects
    ord_time = [dt.datetime.toordinal(tx) for tx in t]

    # list of datetime formatted strings
    x_labels = [str(dt.datetime.fromordinal(int(L)))[:10] if L != "0.0" and L != "" else "0" for L in ord_time]

    print("x_labels generated")

    total_mask = data.total_mask

    plot_data = get_plot_items(data=data, items=items)

    print("plot data dictionary retrieved")
    # print(plot_data)

    # squeeze=False allows for plt.subplots to have a single subplot, must specify the column index as well
    # when calling a subplot e.g. axes[num, 0] for plot number 'num' and column 1
    fig, axes = plt.subplots(nrows=len(plot_data), ncols=1, figsize=(16, len(plot_data) * 7.5), dpi=65, squeeze=False)

    print("created figure and subplots objects")

    for num, b in enumerate(plot_data.keys()):
        print("Working on plot ", b, num)
        # fg = plt.figure(figsize=(16, 9), dpi=300)
        # ax = fg.add_subplot(2, 1, 1, xlim=(min(data.dates) - 100, max(data.dates) + 500),
        #                   ylim=(min(data.data_in[num, total_mask]) - 500, max(data.data_in[num, total_mask]) + 500))


        # Observed values in PyCCD time range
        axes[num, 0].plot(data.dates_in[total_mask], plot_data[b][0][data.date_mask][total_mask], 'go', ms=7, mec='k',
                       mew=0.5, label="Observations used by PyCCD")
        print(f"Observed values for {b} in time range plotted")

        # Observed values outside PyCCD time range
        axes[num, 0].plot(data.dates_out[data.qa_out],  plot_data[b][0][~data.date_mask][data.qa_out], 'ro', ms=5,
                       mec='k', mew=0.5, label="Observations not used by PyCCD")
        print(f"Observed values for {b} outside time range plotted")

        # Observed values masked out
        if masked_on is True:

            # Remove the 0-value masked observations
            if b in data.index_lookup.keys():
                index_plot = plot_data[b][0][data.date_mask][~data.mask]

                axes[num, 0].plot(data.dates_in[~data.mask][index_plot != 0], index_plot[index_plot != 0], color="0.65",
                               marker="o", linewidth=0, ms=3, label="Observations masked by PyCCD")
                print(f"Masked observed values for {b} plotted")

            else:
                axes[num, 0].plot(data.dates_in[~data.mask], plot_data[b][0][data.date_mask][~data.mask], color="0.65",
                               marker="o", linewidth=0, ms=3, label="Observations masked by PyCCD")
                print(f"Masked observed values for {b} plotted")


        axes[num, 0].set_title(f'{b}')
        print("Plot title added")

        # plot model break and start dates
        if model_on is True:
            match_dates = [b for b in data.break_dates for s in data.start_dates if b == s]

            for ind, e in enumerate(data.end_dates):
                if ind == 0:
                    axes[num, 0].axvline(e, color="black", linewidth=1.5, label="End dates")

                else:
                    # Plot without a label to remove duplicates in the legend
                    axes[num, 0].axvline(e, color="black", linewidth=1.5)
            print("End dates plotted")

            for ind, br in enumerate(data.break_dates):
                if ind == 0:
                    axes[num, 0].axvline(br, color='r', linewidth=1.5, label="Break dates")

                else:
                    axes[num, 0].axvline(br, color='r', linewidth=1.5)
            print("break dates plotted")

            for ind, s in enumerate(data.start_dates):
                if ind == 0:
                    axes[num, 0].axvline(s, color='b', linewidth=1.5, label="Start dates")

                else:
                    axes[num, 0].axvline(s, color='b')
            print("start dates plotted")


            for ind, m in enumerate(match_dates):
                if ind == 0:
                    axes[num, 0].axvline(m, color="magenta", linewidth=1.5, label="Break date = Start date")

                else:
                    axes[num, 0].axvline(m, color="magenta", linewidth=1.5)
            print("match dates plotted")


            # Predicted curves
            for c in range(0, len(data.results["change_models"])):
                if c == 0:
                    axes[num, 0].plot(data.prediction_dates[c * len(data.bands)],  plot_data[b][1][c], "orange",
                                      linewidth=2, alpha=0.8, label="PyCCD model fit")

                else:
                    axes[num, 0].plot(data.prediction_dates[c * len(data.bands)], plot_data[b][1][c], "orange",
                                      alpha=0.8, linewidth=2)

            print("predicted curves plotted")

        # Get ymin and ymax values to constrain the plot size
        if b in data.index_lookup.keys():
            ymin = min(plot_data[b][0][data.date_mask][total_mask]) - 0.15
            ymax = max(plot_data[b][0][data.date_mask][total_mask]) + 0.1
        else:
            ymin = min(plot_data[b][0][data.date_mask][total_mask]) - 700
            ymax = max(plot_data[b][0][data.date_mask][total_mask]) + 500

        axes[num, 0].set_ylim([ymin, ymax])

        # Add legend
        axes[num, 0].legend(mode="expand", ncol=4, loc="lower center")

        # Add x-ticks and x-tick_labels
        axes[num, 0].set_xticks(ord_time)

        axes[num, 0].set_xticklabels(x_labels, rotation=70, horizontalalignment="right")

        axes[num, 0].format_coord = lambda x, y: "({0:f}, ".format(y) +  \
                                                 "{0:%Y-%m-%d})".format(dt.datetime.fromordinal(int(x)))

    return fig
