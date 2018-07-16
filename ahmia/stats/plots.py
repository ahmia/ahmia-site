import matplotlib
from matplotlib.ticker import MaxNLocator

matplotlib.use('agg')   # server no need to display graphics
import matplotlib.pyplot as plt


def _select_xticks(x):
    """
    Heuristically decide how many x-axis labels will be printed, in
    order to avoid obfuscating each other, due to figure's fixed width.
    """

    if len(x) < 19:
        # print all
        return x
    else:
        # print every two
        return x[0:-1:2]


def generate_figure(x, y1, y2, image_path, metric_str):
    """
    Generate all figures for stats model, normally 4 plots in 2 figures

    :param x A list with dates
    :param y1 A list with integers for bottom line plot
    :param y2 A list with integers for upper line plot
    :param image_path The directory path to store pictures
    :param metric_str: A suffix to plot title, e.g 'Queries'
    """

    # 2 subplots, the axes array is 1-d
    fig, axis = plt.subplots(2, sharex=True)
    x_labels = _select_xticks(x)

    axis[0].set_title("Unique %s" % metric_str)
    axis[0].bar(x, y2, edgecolor="k")
    axis[0].set_xticks(x_labels)
    axis[0].set_xticklabels(x_labels)
    axis[0].yaxis.set_major_locator(MaxNLocator(integer=True))  # int ylabels

    axis[1].set_title(metric_str)
    axis[1].bar(x, y1, edgecolor="k")
    axis[1].yaxis.set_major_locator(MaxNLocator(integer=True))  # int ylabels

    # save the figure
    plt.savefig(image_path, bbox_inches='tight', transparent=True)
