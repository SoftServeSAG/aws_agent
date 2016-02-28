#!/usr/bin/env python3

import sys
import boto3
import utils
import aws_api


if __name__ == '__main__':
    client = boto3.client('ec2')
    parser, options = utils.get_options()
    profiles = utils.read_profiles(options.profilesPath)

    if options.listProfiles:
        utils.list_profiles(profiles)

    elif options.listAvailabilityZones:
        print('\n'.join(aws_api.get_availability_zones(client)))

    # elif options.requestInstance:
    #     profile, zone, price = options.requestInstance
    #     for response in aws_api.request_spot_instances(client, profiles[profile], zone, price, instance_count=1):
    #         print(response)

    elif options.requestInstances:
        profile, zone, price, count = options.requestInstances
        for response in aws_api.request_spot_instances(client, profiles[profile], zone, price, count):
            print(response)

    elif options.requestTempInstances:
        profile, zone, price, count, valid_hours = options.requestTempInstances
        for response in aws_api.request_temp_spot_instances(client, profiles[profile], zone, price, valid_hours, count):
            print(response)

    elif options.listRequests:
        aws_api.list_spot_instance_requests(client)

    elif options.listInstances:
        aws_api.list_spot_instances(client)

    elif options.rebootInstances:
        ids = options.rebootInstances
        aws_api.reboot_instances(client, ids)

    elif options.terminateInstances:
        ids = options.terminateInstances
        aws_api.terminate_instances(client, ids)

    elif options.terminateAllInstances:
        aws_api.terminate_all_instances(client)

    elif options.printPriceHistory:
        profile = options.printPriceHistory[0]
        availability_zones = aws_api.get_availability_zones(client)
        price_history = aws_api.get_price_history(client, profiles[profile], availability_zones)
        utils.print_price_history(price_history)

    elif options.plotPriceHistory:
        profile = options.plotPriceHistory[0]
        availability_zones = aws_api.get_availability_zones(client)
        price_history = aws_api.get_price_history(client, profiles[profile], availability_zones)
        utils.plot_price_history(price_history)
        input('Price history plot for profile %s created...' % profile)

    else:
        parser.print_usage()
        sys.exit(1)
