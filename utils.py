import argparse
import configparser
from statistics import mean, stdev


def get_options():
    def formatter(prog):
        return argparse.HelpFormatter(prog, max_help_position=200, width=150)

    parser = argparse.ArgumentParser(formatter_class=formatter, description='Simple AWS EC2 Spot Instance manager')

    parser.add_argument('--profilesPath', nargs=1, default='profiles.ini', metavar='FILEPATH', help='set the path to the profile config file (default: %(default)s)')
    parser.add_argument('--listProfiles', action='store_true', help='show instance profiles')
    parser.add_argument('--listAvailabilityZones', action='store_true', help='show availability zones in a current region')
    parser.add_argument('--printPriceHistory', nargs=1, metavar='PROFILE', help='show price history statistics for PROFILE')
    parser.add_argument('--plotPriceHistory', nargs=1, metavar='PROFILE', help='plot price history statistics for PROFILE (requires MATPLOTLIB)')
    # parser.add_argument('--requestInstance', nargs=3, metavar=('PROFILE', 'ZONE', 'PRICE'), help='create a spot instance request for PROFILE specified')
    parser.add_argument('--requestInstances', nargs=4, metavar=('PROFILE', 'ZONE', 'BID_PRICE', 'N'), help='create N permanent spot instance requests using PROFILE')
    parser.add_argument('--requestTempInstances', nargs=5, metavar=('PROFILE', 'ZONE', 'BID_PRICE', 'N', 'VALID_HOURS'), help='create N temporary spot instance requests using PROFILE (expire after VALID_HOURS)')
    parser.add_argument('--listRequests', action='store_true', help='show instance requests')
    parser.add_argument('--listInstances', action='store_true', help='show active instances')
    parser.add_argument('--rebootInstances', nargs='+', metavar='ID', help='reboot specified instance(s)')
    parser.add_argument('--terminateInstances', nargs='+', metavar='ID', help='terminate specified instance(s), spot requests will be closed resp')
    parser.add_argument('--terminateAllInstances', action='store_true', help='terminate all instances, spot requests will be closed resp')

    return parser, parser.parse_args()


def read_profiles(file_path):
    profiles = configparser.ConfigParser()
    profiles.read(file_path)
    return profiles


def list_profiles(profiles):
    for profile in profiles.sections():
        print('Profile: ' + profile)
        for key in profiles[profile]:
            print('\t{:23} {:20}'.format(key.upper(), profiles[profile][key]))


def print_price_history(price_history):
    print('{:13}{:9}{:8}{:8}{:8}{:8}'.format('Zone', 'Current', 'Min', 'Max', 'Mean', 'Std'))
    for zone in sorted(price_history.keys()):
        price_list = price_history[zone][0]
        print('{:13}${:<8.2f}${:<7.2f}${:<7.2f}${:<7.2f}${:<7.2f}'.format(zone, price_list[-1], min(price_list), max(price_list), mean(price_list), stdev(price_list)))


def plot_price_history(price_history):
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter, DayLocator, HourLocator
    plt.ion()

    num_plots = len(price_history.keys())
    num_rows = int(num_plots / 2) + (num_plots % 2)

    days, hours, dayFormatter = DayLocator(), HourLocator(), DateFormatter('%b %d')

    axes = []
    fig = plt.figure()
    for zone, i in zip(sorted(price_history.keys()), range(1, num_plots + 1)):
        price_list, date_list = price_history[zone]
        ax = fig.add_subplot(num_rows, 2, i)
        ax.plot_date(date_list, price_list, '-')
        ax.xaxis.set_major_locator(days)
        ax.xaxis.set_major_formatter(dayFormatter)
        ax.xaxis.set_minor_locator(hours)
        ax.fmt_xdata = DateFormatter('%Y-%m-%d')
        ax.fmt_ydata = lambda y: '\${:.2f}'.format(y)
        ax.set_title('{}\n current price: \${:.2f}\n min: \${:.2f},  max: \${:.2f}\n mean: \${:.2f},  std: \${:.2f}'.format(zone.upper(), price_list[-1], min(price_list), max(price_list), mean(price_list), stdev(price_list)), fontsize=9)
        ax.grid(True)
        ax.autoscale_view()
        axes.append(ax)
    fig.set_tight_layout(True)
    return fig, axes
