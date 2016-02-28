from datetime import datetime, timedelta
import pytz

# Initialize timezone value
TIME_ZONE = 'Europe/Kiev'
tz = pytz.timezone(TIME_ZONE)


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_availability_zones
def get_availability_zones(client):
    response = client.describe_availability_zones()
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return sorted([zone['ZoneName'] for zone in response['AvailabilityZones'] if zone['State'] == 'available'])
    else:
        print(response['ResponseMetadata'])
        return []


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_spot_price_history
def get_price_history(client, profile, availability_zones, time_delta_days=2):
    instance_type, product = profile['instance_type'], profile['product']
    end_time = tz.localize(datetime.today())
    start_time = end_time - timedelta(days=time_delta_days)
    price_history = {}
    for zone in availability_zones:
        response = client.describe_spot_price_history(StartTime=start_time,
                                                      EndTime=end_time,
                                                      InstanceTypes=[instance_type],
                                                      ProductDescriptions=[product],
                                                      AvailabilityZone=zone)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            price_list = [float(x['SpotPrice']) for x in response['SpotPriceHistory']]
            date_list = [x['Timestamp'] for x in response['SpotPriceHistory']]
            price_history[zone] = [price_list, date_list]
        else:
            print(response['ResponseMetadata'])
    return price_history


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.request_spot_instances
def request_spot_instances(client, profile, availability_zone, price, instance_count=1):
    response = client.request_spot_instances(SpotPrice=str(price),
                                             Type='one-time',
                                             InstanceCount=int(instance_count),
                                             LaunchSpecification={'ImageId': profile['image_id'],
                                             'KeyName': profile['key_name'],
                                             'SecurityGroups': [profile['security_group_name']],
                                             'InstanceType': profile['instance_type'],
                                             'Placement': {'AvailabilityZone': availability_zone},
                                             'SecurityGroupIds': [profile['security_group_id']]}
                                             )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return [request['Status']['Message'] for request in response['SpotInstanceRequests']]
    else:
        print(response['ResponseMetadata'])
        return []


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.request_spot_instances
def request_temp_spot_instances(client, profile, availability_zone, price, valid_hours, instance_count=1):
    valid_until=tz.localize(datetime.today()) + timedelta(hours=int(valid_hours))
    response = client.request_spot_instances(SpotPrice=str(price),
                                             Type='one-time',
                                             InstanceCount=int(instance_count),
                                             ValidUntil=valid_until,
                                             LaunchSpecification={'ImageId': profile['image_id'],
                                             'KeyName': profile['key_name'],
                                             'SecurityGroups': [profile['security_group_name']],
                                             'InstanceType': profile['instance_type'],
                                             'Placement': {'AvailabilityZone': availability_zone},
                                             'SecurityGroupIds': [profile['security_group_id']]}
                                             )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return [request['Status']['Message'] for request in response['SpotInstanceRequests']]
    else:
        print(response['ResponseMetadata'])
        return []


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_spot_instance_requests
def list_spot_instance_requests(client):
    response = client.describe_spot_instance_requests()
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print('{:21}{:15}{:7}{:13}{:21}{:9}{}'.format('CreateTime', 'RequestID', "Price", 'InstanceID', 'ValidUntill', 'State', 'RequestStatus'))
        for request in sorted(response['SpotInstanceRequests'], key = lambda request: request['CreateTime']):
            create_time = request['CreateTime'].astimezone(tz).strftime("%d-%m-%Y %H:%M:%S") if 'CreateTime' in request else ''
            request_id = request['SpotInstanceRequestId'] if 'SpotInstanceRequestId' in request else ''
            price = float(request['SpotPrice']) if 'SpotPrice' in request else ''
            instance_id = request['InstanceId'] if 'InstanceId' in request else ''
            valid_until = request['ValidUntil'].astimezone(tz).strftime("%d-%m-%Y %H:%M:%S") if 'ValidUntil' in request else ''
            state = request['State'].upper() if 'State' in request else ''
            status = request['Status']['Message'] if 'Status' in request and 'Message' in request['Status'] else ''
            print('{:21}{:15}{:<7.2g}{:13}{:21}{:9}{}'.format(create_time, request_id, price, instance_id, valid_until, state, status))
    else:
        print(response['ResponseMetadata'])


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
def list_spot_instances(client):
    response = client.describe_instances()
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print('{:21}{:13}{:15}{:13}{:14}{:16}{:16}{:15}{:10}'.format('LaunchTime', 'InstanceID', 'ImageID', 'Zone', 'InstanceType', 'PublicIP', 'PrivateIP', 'KeyName', 'State'))
        for reservation in sorted(response['Reservations'], key = lambda reservation: reservation['Instances'][0]['LaunchTime']):
            for instance in reservation['Instances']:
                launch_time = instance['LaunchTime'].astimezone(tz).strftime("%d-%m-%Y %H:%M:%S") if 'LaunchTime' in instance else ''
                instance_id = instance['InstanceId'] if 'InstanceId' in instance else ''
                image_id = instance['ImageId'] if 'ImageId' in instance else ''
                availability_zone = instance['Placement']['AvailabilityZone'] if 'Placement' in instance and 'AvailabilityZone' in instance['Placement'] else ''
                instance_type = instance['InstanceType'] if 'InstanceType' in instance else ''
                public_ip = instance['PublicIpAddress'] if 'PublicIpAddress' in instance else ''
                private_ip = instance['PrivateIpAddress'] if 'PrivateIpAddress' in instance else ''
                key_name = instance['KeyName'] if 'KeyName' in instance else ''
                state = instance['State']['Name'].upper() if 'State' in instance and 'Name' in instance['State'] else ''
                print('{:21}{:13}{:15}{:13}{:14}{:16}{:16}{:15}{:10}'.format(launch_time, instance_id, image_id, availability_zone, instance_type, public_ip, private_ip, key_name, state))
    else:
        print(response['ResponseMetadata'])


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.reboot_instances
def reboot_instances(client, instance_ids):
    response = client.reboot_instances(InstanceIds=instance_ids)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print('Instance(s) [{}] rebooted'.format(', '.join(instance_ids)))
    else:
        print(response['ResponseMetadata'])


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.terminate_instances
def terminate_instances(client, instance_ids):
    response = client.terminate_instances(InstanceIds=instance_ids)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        for instance in response['TerminatingInstances']:
            print('{}: {}'.format(instance['InstanceId'], instance['CurrentState']['Name']))
    else:
        print(response['ResponseMetadata'])


# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
# http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.terminate_instances
def terminate_all_instances(client):
    response = client.describe_instances()
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        all_instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                all_instances.append(instance['InstanceId'])
        terminate_instances(client, all_instances)
    else:
        print(response['ResponseMetadata'])
