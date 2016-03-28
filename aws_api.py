import sys
import time
import pytz
from datetime import datetime, timedelta
import boto3
import botocore
import numpy as np


class Client:

    def __init__(self, config, time_zone='Europe/Kiev', retry_timeout=5, retry_tries=5):
        """Peform config checking and initialize Client's global variables."""
        # Ensure config contains 'instance_profiles' section
        assert 'instance_profiles' in config, "config does not have 'instance_profiles' section"
        # Ensure config contains 'user_profile' section
        assert 'user_profile' in config, "config does not have 'user_profile' section"
        # Ensure 'user_profile' contain "User" tag ('Key' and 'Value')
        assert sum([tag["Key"] == 'User' and len(tag["Value"]) > 0 for tag in config[
                   'user_profile']['tags']]) == 1, "config does not contain username information"

        self.ec2 = boto3.client('ec2')

        self.inst_profiles = config["instance_profiles"]
        self.user_profile = config["user_profile"]

        self.retry_timeout = retry_timeout
        self.retry_tries = retry_tries
        self.tz = pytz.timezone(time_zone)

    def safe_api_call(self, func, kwargs={}):
        """Boto3 API function call wrapper.

        Handle Client and AWS API errors by performing 'self.retry_tries' attempts.
        """
        for i in range(self.retry_tries):
            try:
                response = func(**kwargs)
            except botocore.exceptions.ClientError as err:
                err_name, error_desc = type(err).__name__, err
            else:
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    return response
                else:
                    err_name, error_desc = 'AWS Client', response[
                        'ResponseMetadata']['HTTPStatusCode']
            print('[Try #{}] {}: {}'.format(i + 1, err_name, error_desc))
            time.sleep(self.retry_timeout)
        sys.exit(1)

    def get_user_filter(self):
        """Create a list of dicts containing user's tags to be passed as a filter."""
        return [{'Name': 'tag:' + tag['Key'], 'Values': [tag['Value']]} for tag in self.user_profile['tags']]

    def get_profile_tags(self, profile):
        return [*self.inst_profiles[profile]['tags'], *self.user_profile['tags']]

    def list_profiles(self):
        for profile in self.inst_profiles:
            print('Profile: ' + profile)
            for key in self.inst_profiles[profile]:
                print('\t{:23} {}'.format(key.upper(), self.inst_profiles[profile][key]))

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_availability_zones
    def get_availability_zones(self):
        response = self.safe_api_call(self.ec2.describe_availability_zones)
        return sorted([zone['ZoneName'] for zone in response['AvailabilityZones'] if zone['State'] == 'available'])

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_spot_instance_requests
    def list_spot_instance_requests(self):
        response = self.safe_api_call(self.ec2.describe_spot_instance_requests, {
                                      'Filters': self.get_user_filter()})
        fields = ['CreateTime', 'RequestID', "Price",
                  'InstanceID', 'ValidUntill', 'State', 'RequestStatus']
        print('{:21}{:15}{:7}{:13}{:21}{:9}{}'.format(*fields))
        for request in sorted(response['SpotInstanceRequests'], key=lambda request: request['CreateTime']):
            # row = [request.get('CreateTime', datetime(1970, 1,
            # 1)).astimezone(self.tz).strftime("%d-%m-%Y %H:%M:%S"),
            row = [request.get('CreateTime', datetime(1970, 1, 1, tzinfo=self.tz)).astimezone(self.tz).strftime("%d-%m-%Y %H:%M:%S"),
                   request.get('SpotInstanceRequestId', ''),
                   float(request.get('SpotPrice', 'inf')),
                   request.get('InstanceId', ''),
                   request.get('ValidUntil', datetime(1970, 1, 1, tzinfo=self.tz)
                               ).astimezone(self.tz).strftime("%d-%m-%Y %H:%M:%S"),
                   request.get('State', '').upper(),
                   request.get('Status', {}).get('Message', '')]
            print('{:21}{:15}{:<7.2g}{:13}{:21}{:9}{}'.format(*row))
        return response

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
    def list_spot_instances(self):
        response = self.safe_api_call(self.ec2.describe_instances, {
                                      'Filters': self.get_user_filter()})
        fields = ['LaunchTime', 'InstanceID', 'ImageID', 'Zone',
                  'InstanceType', 'PublicIP', 'PrivateIP', 'KeyName', 'State']
        print('{:21}{:13}{:15}{:13}{:14}{:16}{:16}{:15}{:10}'.format(*fields))
        for reservation in sorted(response['Reservations'], key=lambda reservation: reservation['Instances'][0]['LaunchTime']):
            for instance in reservation['Instances']:
                row = [instance.get('LaunchTime', datetime(1970, 1, 1, tzinfo=self.tz)).astimezone(self.tz).strftime("%d-%m-%Y %H:%M:%S"),
                       instance.get('InstanceId', ''),
                       instance.get('ImageId', ''),
                       instance.get('Placement', {}).get('AvailabilityZone', ''),
                       instance.get('InstanceType', ''),
                       instance.get('PublicIpAddress', ''),
                       instance.get('PrivateIpAddress', ''),
                       instance.get('KeyName', ''),
                       instance.get('State', {}).get('Name', '').upper()]
                print('{:21}{:13}{:15}{:13}{:14}{:16}{:16}{:15}{:10}'.format(*row))
        return response

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_volumes
    def list_volumes(self):
        response = self.safe_api_call(self.ec2.describe_volumes, {
            'Filters': self.get_user_filter()})
        fields = ['CreateTime', 'VolumeId', "Size", 'Type', 'Iops', 'Zone', 'InstanceId', 'State']
        print('{:21}{:15}{:6}{:6}{:6}{:13}{:15}{:10}'.format(*fields))
        for volume in sorted(response['Volumes'], key=lambda volume: volume['CreateTime']):
            row = [volume.get('CreateTime', datetime(1970, 1, 1, tzinfo=self.tz)).astimezone(self.tz).strftime("%d-%m-%Y %H:%M:%S"),
                   volume.get('VolumeId', ''),
                   volume.get('Size', ''),
                   volume.get('VolumeType', ''),
                   volume.get('Iops', ''),
                   volume.get('AvailabilityZone', ''),
                   ','.join([attch.get('InstanceId', '')
                             for attch in volume.get('Attachments', [])]),
                   volume.get('State', '')]
            print('{:21}{:15}{:<6}{:6}{:<6}{:13}{:15}{:10}'.format(*row))
        return response

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.attach_volume
    def attach_volume(self, instance_id, volume_id, device):
        kwargs = {'InstanceId': instance_id,
                  'VolumeId': volume_id,
                  'Device': device}
        response = self.safe_api_call(self.ec2.attach_volume, kwargs)
        print('State: {}'.format(response['State']))
        return response

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.detach_volume
    def detach_volume(self, volume_id, force):
        kwargs = {'VolumeId': volume_id,
                  'Force': force}
        response = self.safe_api_call(self.ec2.detach_volume, kwargs)
        print('State: {}'.format(response['State']))
        return response

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_spot_price_history
    def get_price_history(self, profile, availability_zones, time_delta_days=7):
        instance_type = self.inst_profiles[profile]['instance_type']
        product = self.inst_profiles[profile]['product']

        end_time = self.tz.localize(datetime.today())
        start_time = end_time - timedelta(days=time_delta_days)

        price_history = {}
        # TODO: to be rewritten using 'safe_api_call'
        paginator = self.ec2.get_paginator('describe_spot_price_history')
        for zone in availability_zones:
            price_list = []
            for page in paginator.paginate(StartTime=start_time,
                                           EndTime=end_time,
                                           InstanceTypes=[instance_type],
                                           ProductDescriptions=[product],
                                           AvailabilityZone=zone):
                price_list += [(float(i['SpotPrice']), i['Timestamp'])
                               for i in page['SpotPriceHistory']]
                price_list = [(price_list[0][0], end_time)] + \
                    price_list  # set last available price as current
            price_history[zone] = np.array(
                price_list, dtype=[('price', np.float), ('timestamp', 'datetime64[h]')])
        return price_history

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.create_tags
    def create_tags(self, resource_ids, tags):
        return self.safe_api_call(self.ec2.create_tags, {'Resources': resource_ids, 'Tags': tags})

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.request_spot_instances
    def request_spot_instances(self, profile, availability_zone, price, instance_count=1, valid_hours=None):
        kwargs = {'SpotPrice': str(price),
                  'Type': 'one-time',
                  'InstanceCount': int(instance_count),
                  'LaunchSpecification': {'ImageId': self.inst_profiles[profile]['image_id'],
                                          'KeyName': self.inst_profiles[profile]['key_name'],
                                          'SecurityGroups': [self.inst_profiles[profile]['security_group_name']],
                                          'InstanceType': self.inst_profiles[profile]['instance_type'],
                                          'Placement': {'AvailabilityZone': availability_zone},
                                          'SecurityGroupIds': [self.inst_profiles[profile]['security_group_id']]
                                          }
                  }
        if valid_hours:
            kwargs['ValidUntil'] = datetime.today() + timedelta(hours=int(valid_hours))

        response = self.safe_api_call(self.ec2.request_spot_instances, kwargs)

        # Tag spot request(s)
        request_ids = [request['SpotInstanceRequestId']
                       for request in response['SpotInstanceRequests']]
        tags = self.get_profile_tags(profile)
        self.create_tags(request_ids, tags)

        # Wait for all Spot request(s) to be processed by Amazon
        print('Waiting for your Spot request(s) to be evaluated')
        states_list = ['open']
        while 'open' in states_list:
            sys.stdout.write("."), time.sleep(self.retry_timeout)
            response = self.safe_api_call(self.ec2.describe_spot_instance_requests, {
                                          'SpotInstanceRequestIds': request_ids})
            states_list = [request['State'] for request in response['SpotInstanceRequests']]
        print('done')

        # Get spot instance id(s)
        instance_ids = []
        for request in response['SpotInstanceRequests']:
            print(request['Status']['Message'])
            if request['State'] == 'active':
                instance_ids.append(request['InstanceId'])

        # Get EBS volumes id(s)
        volume_ids = []
        response = self.safe_api_call(self.ec2.describe_instances, {
            'InstanceIds': instance_ids})
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                for mapping in instance['BlockDeviceMappings']:
                    if 'Ebs' in mapping:
                        volume_ids.append(mapping['Ebs']['VolumeId'])

        # Tag spot instance(s)
        if len(instance_ids) > 0:
            tags = self.get_profile_tags(profile)
            self.create_tags([*instance_ids, *volume_ids], tags)

        return response

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.terminate_instances
    def terminate_instances(self, instance_ids):
        response = self.safe_api_call(self.ec2.terminate_instances, {'InstanceIds': instance_ids})
        for instance in response['TerminatingInstances']:
            print('{}: {}'.format(instance['InstanceId'], instance['CurrentState']['Name']))
        return response

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.terminate_instances
    def terminate_all_instances(self):
        response = self.safe_api_call(self.ec2.describe_instances, {
                                      'Filters': self.get_user_filter()})
        all_instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                all_instances.append(instance['InstanceId'])
        response = self.terminate_instances(all_instances)
        return response

    # http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.reboot_instances
    def reboot_instances(self, instance_ids):
        response = self.safe_api_call(self.ec2.reboot_instances, {'InstanceIds': instance_ids})
        print('Instance(s) [{}] rebooted'.format(', '.join(instance_ids)))
        return response
