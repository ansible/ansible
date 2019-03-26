from ansible.module_utils.common._collections_compat import MutableMapping

import datetime
from dateutil.tz import tzutc
import sys

try:
    from ansible.parsing.yaml.objects import AnsibleUnicode
except ImportError:
    AnsibleUnicode = str


if sys.version_info[0] >= 3:
    unicode = str

DNSDOMAIN = "ansible.amazon.com"


class Reservation(object):
    def __init__(self, owner_id, instance_ids, region):
        if len(instance_ids) > 1:
            stopped_instance = instance_ids[-1]
        self.instances = []
        for instance_id in instance_ids:
            stopped = bool(instance_id == stopped_instance)
            self.instances.append(BotoInstance(instance_id=instance_id, owner_id=owner_id, region=region, stopped=stopped))
        self.owner_id = owner_id


class Tag(object):
    res_id = None
    name = None
    value = None

    def __init__(self, res_id, name, value):
        self.res_id = res_id
        self.name = name
        self.value = value


class SecurityGroup(object):
    name = 'sg_default'
    group_id = 'sg-00000'
    id = 'sg-00000'

    def __init__(self, group_id, group_name):
        self.name = group_name
        self.group_id = group_id
        self.id = self.group_id

    def __str__(self):
        return self.name


class NetworkInterfaceBase(list):

    def __init__(self, owner_id=None, private_ip=None, subnet_id=None, vpc_id=None):
        self.description = 'Primary network interface'
        self.mac_address = '06:32:7e:30:3a:20'
        self.owner_id = owner_id
        self.private_ip_address = private_ip
        self.status = 'in-use'
        self.subnet_id = subnet_id
        self.vpc_id = vpc_id

        super(NetworkInterfaceBase, self).__init__([self.to_dict()])

    def to_dict(self):

        data = {}
        for attr in dir(self):
            if attr.startswith('__') or attr == 'boto3':
                continue

            val = getattr(self, attr)

            if callable(val):
                continue

            if self.boto3:
                attr = ''.join(x.capitalize() or '_' for x in attr.split('_'))

            data[attr] = val

        return data


class Boto3NetworkInterface(NetworkInterfaceBase):

    boto3 = True

    def __init__(self, owner_id=None, public_ip=None, public_dns=None, private_ip=None, security_groups=None, subnet_id=None, vpc_id=None):
        self.association = {
            'IpOwnerId': 'amazon',
            'PublicDnsName': public_dns,
            'PublicIp': public_ip
        }
        self.attachment = {
            'AttachTime': datetime.datetime(2019, 2, 27, 19, 41, 49, tzinfo=tzutc()),
            'AttachmentId': 'eni-attach-008fda539bfd1877d',
            'DeleteOnTermination': True,
            'DeviceIndex': 0,
            'Status': 'attached'
        }
        self.groups = security_groups
        self.ipv6_addresses = [{'Ipv6Address': '2600:1f18:1af:f6a1:2c8d:7cf:3d14:1224'}]
        self.network_interface_id = 'eni-00abc58b929197984'
        self.private_ip_addresses = [{
            'Association': {
                'IpOwnerId': 'amazon',
                'PublicDnsName': public_dns,
                'PublicIp': public_ip
            },
            'Primary': True,
            'PrivateIpAddress': private_ip
        }]
        self.source_dest_check = True

        super(Boto3NetworkInterface, self).__init__(
            owner_id=owner_id,
            private_ip=private_ip,
            subnet_id=subnet_id,
            vpc_id=vpc_id
        )


class BotoNetworkInterface(NetworkInterfaceBase):

    boto3 = False

    def __init__(self, owner_id=None, public_ip=None, public_dns=None, private_ip=None, subnet_id=None, vpc_id=None):
        self.tags = {}
        self.id = 'eni-00abc58b929197984'
        self.availability_zone = None
        self.requester_managed = False
        self.publicIp = public_ip
        self.publicDnsName = public_dns
        self.ipOwnerId = 'amazon'
        self.association = '\n                            '
        self.item = '\n                        '

        super(BotoNetworkInterface, self).__init__(
            owner_id=owner_id,
            private_ip=private_ip,
            subnet_id=subnet_id,
            vpc_id=vpc_id
        )


class Volume(object):
    def __init__(self, volume_id):
        self.volume_id = volume_id


class BlockDeviceMapping(MutableMapping):
    devices = {}

    def __init__(self, devices):
        for device, volume_id in devices.items():
            self.devices[device] = Volume(volume_id)

    def __getitem__(self, key):
        return self.devices[key]

    def __setitem__(self, key, value):
        self.devices[key] = Volume(value)

    def __delitem__(self, key):
        del self.devices[key]

    def __iter__(self):
        return iter(self.devices)

    def __len__(self):
        return len(self.devices)


class InstanceBase(object):
    def __init__(self, stopped=False):
        # set common ignored attribute to make sure instances have identical tags and security groups
        self._ignore_security_groups = {
            'sg-0e1d2bd02b45b712e': 'a-sgname-with-hyphens',
            'sg-ae5c262eb5c4d712e': 'name@with?invalid!chars'
        }
        self._ignore_tags = {
            'tag-with-hyphens': 'value:with:colons',
            b'\xec\xaa\xb4'.decode('utf'): 'value1with@invalid:characters',
            'tag;me': 'value@noplez',
            'tag!notit': 'value<=ohwhy?'
        }
        if not stopped:
            self._ignore_state = {'Code': 16, 'Name': 'running'}
        else:
            self._ignore_state = {'Code': 80, 'Name': 'stopped'}

        # common attributes
        self.ami_launch_index = '0'
        self.architecture = 'x86_64'
        self.client_token = ''
        self.ebs_optimized = False
        self.hypervisor = 'xen'
        self.image_id = 'ami-0ac019f4fcb7cb7e6'
        self.instance_type = 't2.micro'
        self.key_name = 'k!y:2/-n@me'
        self.private_dns_name = 'ip-20-0-0-20.ec2.internal'
        self.private_ip_address = '20.0.0.20'
        self.product_codes = []
        if not stopped:
            self.public_dns_name = 'ec2-12-3-456-78.compute-1.amazonaws.com'
        else:
            self.public_dns_name = ''
        self.root_device_name = '/dev/sda1'
        self.root_device_type = 'ebs'
        self.subnet_id = 'subnet-09564ba2121bca7bd'
        self.virtualization_type = 'hvm'
        self.vpc_id = 'vpc-01ae527fabc81dd04'

    def to_dict(self):

        data = {}
        for attr in dir(self):
            if attr.startswith(('__', '_ignore')) or attr in ['to_dict', 'boto3']:
                continue

            val = getattr(self, attr)

            if self.boto3:
                attr = ''.join(x.capitalize() or '_' for x in attr.split('_'))

            data[attr] = val

        return data


class BotoInstance(InstanceBase):

    boto3 = False

    def __init__(self, instance_id=None, owner_id=None, region=None, stopped=False):
        super(BotoInstance, self).__init__(stopped=stopped)

        self._in_monitoring_element = False
        self._tags = [Tag(instance_id, k, v) for k, v in self._ignore_tags.items()]
        self.block_device_mapping = BlockDeviceMapping({'/dev/sda1': 'vol-044a646a9292c82af'})
        self.dns_name = 'ec2-12-3-456-78.compute-1.amazonaws.com'
        self.eventsSet = None
        self.group_name = None
        self.groups = [SecurityGroup(k, v) for k, v in sorted(self._ignore_security_groups.items())]
        self.id = instance_id
        self.instance_profile = {
            'arn': 'arn:aws:iam::{0}:instance-profile/developer'.format(owner_id),
            'id': 'ABCDE2GHIJKLMN8PQRSTU'
        }
        if not stopped:
            self.ip_address = '12.3.456.7'
        else:
            self.ip_address = ''  # variable is returned as empty by boto if the instance is stopped
        self.item = '\n                '
        self.kernel = None
        self.launch_time = '2019-02-27T19:41:49.000Z'
        self.monitored = False
        self.monitoring = '\n                    '
        self.monitoring_state = 'disabled'
        self.persistent = False
        self.placement = region + 'e'
        self.platform = None
        self.ramdisk = None
        self.reason = ''
        self.region = region
        self.requester_id = None
        self.sourceDestCheck = 'true'
        self.spot_instance_request_id = None
        self.state = self._ignore_state['Name']
        self.state_code = self._ignore_state['Code']
        if not stopped:
            self.state_reason = None
        else:
            self.state_reason = {
                'code': 'Client.UserInitiatedShutdown',
                'message': 'Client.UserInitiatedShutdown: User initiated shutdown'
            }
        self.tags = dict(self._ignore_tags)

        self.interfaces = BotoNetworkInterface(
            owner_id=owner_id,
            public_ip=self.ip_address,
            public_dns=self.public_dns_name,
            private_ip=self.private_ip_address,
            subnet_id=self.subnet_id,
            vpc_id=self.vpc_id,
        )


class Boto3Instance(InstanceBase):

    boto3 = True

    def __init__(self, instance_id=None, owner_id=None, region=None, stopped=False):
        super(Boto3Instance, self).__init__(stopped=stopped)

        self.block_device_mappings = [{
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'AttachTime': datetime.datetime(2019, 2, 27, 19, 41, 50, tzinfo=tzutc()),
                'DeleteOnTermination': True,
                'Status': 'attached',
                'VolumeId': 'vol-044a646a9292c82af'
            }
        }]
        self.capacity_reservation_specification = {'CapacityReservationPreference': 'open'}
        self.cpu_options = {'CoreCount': 1, 'ThreadsPerCore': 1}
        self.ena_support = True
        self.hibernation_options = {'Configured': False}
        self.iam_instance_profile = {
            'Arn': 'arn:aws:iam::{0}:instance-profile/developer'.format(owner_id),
            'Id': 'ABCDE2GHIJKLMN8PQRSTU'
        }
        self.instance_id = instance_id
        self.launch_time = datetime.datetime(2019, 2, 27, 19, 41, 49, tzinfo=tzutc())
        self.monitoring = {'State': 'disabled'}
        self.placement = {'AvailabilityZone': region + 'e', 'GroupName': '', 'Tenancy': 'default'}
        if not stopped:
            self.public_ip_address = '12.3.456.7'  # variable is not returned by boto3 if the instance is stopped
        self.security_groups = [{'GroupId': key, 'GroupName': value} for key, value in self._ignore_security_groups.items()]
        self.source_dest_check = True
        self.state = dict(self._ignore_state)
        if not stopped:
            self.state_transition_reason = ''
        else:
            self.state_transition_reason = 'User initiated (2019-02-11 12:49:13 GMT)'
            self.state_reason = {  # this variable is only returned by AWS if the instance is stopped
                'Code': 'Client.UserInitiatedShutdown',
                'Message': 'Client.UserInitiatedShutdown: User initiated shutdown'
            }
        self.tags = [{'Key': k, 'Value': v} for k, v in self._ignore_tags.items()]

        self.network_interfaces = Boto3NetworkInterface(
            owner_id=owner_id,
            public_ip=getattr(self, 'public_ip_address', ''),
            public_dns=self.public_dns_name,
            private_ip=self.private_ip_address,
            security_groups=self.security_groups,
            subnet_id=self.subnet_id,
            vpc_id=self.vpc_id
        )
