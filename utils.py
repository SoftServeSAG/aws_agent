import argparse
import json
from collections import OrderedDict
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator, HourLocator
from matplotlib import mlab


# https://bugs.python.org/issue25297
class Formatter(argparse.HelpFormatter):

    def __init__(self, prog):
        super(Formatter, self).__init__(prog, max_help_position=60, width=120)

    # Corrected _max_action_length for the indenting of subactions
    def add_argument(self, action):
        if action.help is not argparse.SUPPRESS:
            # find all invocations
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            current_indent = self._current_indent
            for subaction in self._iter_indented_subactions(action):
                # compensate for the indent that will be added
                indent_chg = self._current_indent - current_indent
                added_indent = 'x' * indent_chg
                invocations.append(added_indent + get_invocation(subaction))
            # update the maximum item length
            invocation_length = max([len(s) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length,
                                          action_length)
            # add the item to the list
            self._add_item(self._format_action, [action])


def get_argparser():
    # General section
    parser = argparse.ArgumentParser(formatter_class=Formatter,
                                     description='Simple AWS EC2 Spot Instance manager')
    parser.add_argument('--configPath', default='config.json', metavar='FILEPATH',
                        help='path to the config file (default: %(default)s)')

    # Agent's commands section
    subparsers = parser.add_subparsers(dest='subparser_name', metavar="", title='commands')

    subparsers.add_parser('listProfiles', formatter_class=Formatter, help='show instance profiles')

    subparsers.add_parser('listAvailabilityZones', formatter_class=Formatter,
                          help='show availability zones in a current region')

    subparsers.add_parser('listVolumes', formatter_class=Formatter,
                          help='show block device volumes')

    subparsers.add_parser('attachVolume', formatter_class=Formatter,
                          help='Attach a block device to an instance')

    subparsers.add_parser('detachVolume', formatter_class=Formatter,
                          help='Detach a block device from an instance')

    subparsers.add_parser('printPriceHistory', formatter_class=Formatter,
                          help='print price history statistics')

    subparsers.add_parser('plotPriceHistory', formatter_class=Formatter,
                          help='plot price history statistics')

    get_recommended_pricing = subparsers.add_parser(
        'recommendPricing', formatter_class=Formatter, help='show recommended pricing and allocation oprions')
    get_recommended_pricing.add_argument('profile', help='name of instance profile')

    subparsers.add_parser('requestInstances', formatter_class=Formatter,
                          help='create spot instance requests')

    subparsers.add_parser('smartSpotRequest', formatter_class=Formatter,
                          help="automated 'single shot' spot instance request")

    subparsers.add_parser('listRequests', formatter_class=Formatter, help='show instance requests')

    subparsers.add_parser('listInstances', formatter_class=Formatter, help='show active instances')

    reboot_instances_parser = subparsers.add_parser(
        'rebootInstances', formatter_class=Formatter, help='reboot specified instance(s)')
    reboot_instances_parser.add_argument('id', nargs='+', help='instance ID(s)')

    terminate_instances_parser = subparsers.add_parser(
        'terminateInstances', formatter_class=Formatter, help='terminate specified instance(s), spot requests will be closed resp')
    terminate_instances_parser.add_argument('id', nargs='+', help='instance ID(s)')

    subparsers.add_parser('terminateAllInstances', formatter_class=Formatter,
                          help='terminate all instances, spot requests will be closed resp')

    return parser


def read_config(file_path):
    with open(file_path, 'r') as file:
        config = json.load(file, object_pairs_hook=OrderedDict)
    return config


def print_price_history(price_history, recommend=True):
    fields = ['Zone', 'Current', 'Min', 'Max', 'Mean', 'Std']
    print('{:13}{:9}{:8}{:8}{:8}{:8}'.format(*fields))
    for zone in sorted(price_history.keys()):
        price_arr = mlab.rec_groupby(
            price_history[zone], ('timestamp',), (('price', np.max, 'max_price'),))['max_price']
        row = [zone, price_arr[-1], np.min(price_arr), np.max(price_arr),
               np.mean(price_arr), np.std(price_arr)]
        print('{:13}${:<8.2f}${:<7.2f}${:<7.2f}${:<7.2f}${:<7.2f}'.format(*row))
    if recommend:
        rec_zone, rec_price = get_recommended_pricing(price_history)
        print('RECOMMENDED BIDDING (ZONE: {}, PRICE: {:.2f})'.format(rec_zone, rec_price))


def plot_price_history(price_history, plot_hist=False):
    num_zones = len(price_history.keys())

    plt.ion()
    fig_price = plt.figure(figsize=(15, 8))
    ax_price = fig_price.add_subplot(111)
    ax_price.xaxis.set_major_locator(DayLocator())
    ax_price.xaxis.set_minor_locator(HourLocator())
    ax_price.xaxis.set_major_formatter(DateFormatter('%b %d'))
    ax_price.autoscale_view()
    ax_price.grid(True)

    if plot_hist:
        num_rows = int(num_zones / 2) + (num_zones % 2)
        fig_hist = plt.figure(figsize=(15, 8))
        fig_hist.set_tight_layout(True)

    colors = plt.cm.Spectral(np.linspace(0, 1, num_zones))
    min_date, max_date = datetime.today(), datetime(1970, 1, 1)
    for zone, color, i in zip(sorted(price_history.keys()), colors, range(1, num_zones + 1)):
        # Plot price history curves
        grouped = mlab.rec_groupby(
            price_history[zone], ('timestamp',), (('price', np.max, 'max_price'),))
        price_arr, date_arr = grouped['max_price'], [
            x.astype(datetime) for x in grouped['timestamp']]
        price_stats = [zone, price_arr[-1],
                       np.min(price_arr), np.max(price_arr), np.mean(price_arr), np.std(price_arr)]
        label = '{:14}current: ${:<6.2f}min: ${:<6.2f}max: ${:<6.2f}mean: ${:<6.2f}std: ${:<6.2f}'.format(
            *price_stats)
        ax_price.plot_date(date_arr, price_arr, '-', color=color, linewidth=1.5, label=label)
        # Plot price history histogram
        if plot_hist:
            ax_hist = fig_hist.add_subplot(num_rows, 2, i)
            ax_hist.hist(price_arr, 200, range=(0, np.max(price_arr) + 0.5), color=color, alpha=0.7)
            ax_hist.set_title('{} (examples: {})'.format(zone, price_arr.size))
            ax_hist.set_xlabel("Price")
            ax_hist.set_ylabel("Frequency")
        # Calculating time boundaries
        min_date, max_date = min(min_date, np.min(date_arr)), max(max_date, np.max(date_arr))

    rec_zone, rec_price = get_recommended_pricing(price_history)
    label = 'RECOMMENDED BIDDING (ZONE: {}, PRICE: {:.2f})'.format(rec_zone, rec_price)
    ax_price.plot_date([min_date, max_date], [rec_price, rec_price], 'r-', linewidth=2, label=label)

    ax_price.legend(loc='upper center', fancybox=True, shadow=True, ncol=1).draggable()

    return fig_price, ax_price, fig_hist if plot_hist else None


def get_recommended_pricing(price_history):
    # Get recommended availability zone
    zones_stats = []
    for zone in price_history:
        price_arr = mlab.rec_groupby(
            price_history[zone], ('timestamp',), (('price', np.max, 'max_price'),))['max_price']
        three_sigma = np.mean(price_arr) + (3 * np.std(price_arr))
        percentile = np.percentile(price_arr, 99)
        zones_stats.append((zone, max(three_sigma, percentile)))
    zone, stat = sorted(zones_stats, key=lambda x: x[1])[0]

    price_arr = mlab.rec_groupby(
        price_history[zone], ('timestamp',), (('price', np.max, 'max_price'),))['max_price']

    n = len(price_arr)
    base = np.arange(n, dtype=np.float) / n
    weights = np.tanh((base - 0.7) / 0.2)
    weights = (weights - np.min(weights)) / (np.max(weights) - np.min(weights)) + 1
    weights /= np.sum(weights)

    weighted = np.multiply(weights, price_arr)

    price = np.max(
        price_arr[np.where(weighted >= np.percentile(weighted, 99, interpolation='nearest'))])

    return (zone, price)
