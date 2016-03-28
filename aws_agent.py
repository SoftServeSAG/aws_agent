#!/usr/bin/env python3

import sys
import utils
import aws_api


if __name__ == '__main__':
    parser = utils.get_argparser()
    options = parser.parse_args()

    config = utils.read_config(options.configPath)
    aws_client = aws_api.Client(config)

    if options.subparser_name == 'listProfiles':
        aws_client.list_profiles()

    elif options.subparser_name == 'listAvailabilityZones':
        print('\n'.join(aws_client.get_availability_zones()))

    elif options.subparser_name == 'listRequests':
        aws_client.list_spot_instance_requests()

    elif options.subparser_name == 'listInstances':
        aws_client.list_spot_instances()

    elif options.subparser_name == 'listVolumes':
        aws_client.list_volumes()

    elif options.subparser_name == 'attachVolume':
        volume_id = input('Enter volume id to attach: ')
        instance_id = input('Enter instance id to attach to: ')
        device = input('Enter device name to use (e.g. /dev/sdh): ')
        aws_client.attach_volume(instance_id, volume_id, device)

    elif options.subparser_name == 'detachVolume':
        volume_id = input('Enter volume id to detach: ')
        force = input('Force detachment (y/n): ')
        aws_client.detach_volume(volume_id, True if force == 'y' else False)

    elif options.subparser_name == 'deleteVolume':
        aws_client.delete_volume(options.id)

    elif options.subparser_name == 'rebootInstances':
        aws_client.reboot_instances(options.id)

    elif options.subparser_name == 'terminateInstances':
        aws_client.terminate_instances(options.id)

    elif options.subparser_name == 'terminateAllInstances':
        aws_client.terminate_all_instances()

    elif options.subparser_name == 'printPriceHistory':
        profile = input('Enter profile name: ')
        zone = input('Enter availability zone name (default: all): ')
        period = input('Enter period in days to analyze: ')
        availability_zones = aws_client.get_availability_zones() if len(zone) == 0 else [zone]
        price_history = aws_client.get_price_history(profile, availability_zones, int(period))
        utils.print_price_history(price_history)

    elif options.subparser_name == 'plotPriceHistory':
        profile = input('Enter profile name: ')
        zone = input('Enter availability zone name (default: all): ')
        period = input('Enter period in days to analyze: ')
        plot_histogram = input('Do you want to plan a histogram (y/n): ')
        availability_zones = aws_client.get_availability_zones() if len(zone) == 0 else [zone]
        price_history = aws_client.get_price_history(profile, availability_zones, int(period))
        utils.plot_price_history(price_history, True if plot_histogram == 'y' else False)
        input('Price history plot for profile %s created...' % profile)

    elif options.subparser_name == 'recommendPricing':
        profile = options.profile
        availability_zones = aws_client.get_availability_zones()
        price_history = aws_client.get_price_history(profile, availability_zones)
        rec_zone, rec_price = utils.get_recommended_pricing(price_history)
        print('RECOMMENDED BIDDING (ZONE: {}, PRICE: {:.2f})'.format(rec_zone, rec_price))

    elif options.subparser_name == 'requestInstances':
        profile = input('Enter profile name: ')
        availability_zone = input('Enter availability zone name: ')
        price = input('Enter bid price: ')
        instance_count = input('Enter number of instances to request: ')
        valid_hours = input('Enter expiration time in hours (default: permanent): ')
        kwargs = {'profile': profile,
                  'availability_zone': availability_zone,
                  'price': price,
                  'instance_count': instance_count}
        if len(valid_hours) > 0:
            kwargs['valid_hours'] = valid_hours
        response = aws_client.request_spot_instances(**kwargs)

    elif options.subparser_name == 'smartSpotRequest':
        profile = input('Enter profile name: ')
        instance_count = input('Enter number of instances to request: ')
        valid_hours = input('Enter expiration time in hours (default: permanent): ')
        if len(valid_hours) > 0:
            kwargs['valid_hours'] = valid_hours
        # Get recommended pricing and resource allocation options
        availability_zones = aws_client.get_availability_zones()
        price_history = aws_client.get_price_history(profile, availability_zones)
        zone, price = utils.get_recommended_pricing(price_history)
        # Request spot instance(s)
        print("Creating {} Spot request(s) in zone '{}' and bidding price {:<.2}".format(
            instance_count, zone, price))
        response = aws_client.request_spot_instances(
            profile, zone, price, instance_count, valid_hours)

    else:
        parser.print_usage()
        sys.exit(1)
