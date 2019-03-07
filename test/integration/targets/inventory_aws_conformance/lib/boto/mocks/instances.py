import sys
if sys.version_info[0] >= 3:
    unicode = str

DNSDOMAIN="ansible.amazon.com"

class Tag(object):
    res_id = None
    name = None
    value = None

    def __init__(self, res_id, name, value):
        self.res_id = res_id
        self.name = name
        self.value = value


class BotoInstance(object):
    id = None
    owner_id = None
    instances = None
    region = None
    state = None
    subnet_id = None
    public_dns_name = None
    private_dns_name = None
    placement = None
    image_id = None
    instance_type = None
    platform = None
    key_name = None
    vpc_id = None
    groups = None

    _in_monitoring_element = False
    account_id = 100000
    owner_id = 100000
    ami_launch_index = 0
    architecture = "x86_64"
    block_devices = {
      "sda1": "vol-000000"
    }
    client_token = "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
    ebs_optimized = False
    eventsSet = ""
    group_name = ""
    hypervisor = "xen"
    instance_profile = ""
    instance_type = "m5.large"
    item = ""
    kernel = ""
    key_name = "mykey"
    launch_time = "2019-02-28T13:31:41.000Z"
    monitored = False
    monitoring = ""
    monitoring_state = "disabled"
    ec2_persistent = False
    placement = None
    platform = "mockplatform"
    previous_state = ""
    previous_state_code = 0
    ramdisk = ""
    reason = ""
    requester_id = ""
    root_device_name = "/dev/sda1"
    root_device_type = "ebs",
    security_group_ids = "sg-000000"
    security_group_names = "myappsg"
    sourceDestCheck = True
    spot_instance_request_id = ""
    state = "running"
    state_code = 16
    state_reason = ""
    virtualization_type = "hvm"
    vpc_id = "vpc-00000"

    # This breaks the inv script ...
    #subnet_id = "subnet-100000"
    #subnet_id = "subnet-9cdddbb0"

    #tags = {
    #    'TAG1': "TAG1_VAL"
    #}
    #tags = [
    #    {'TAG1': 'TAG1val'}
    #]

    #_tags = {'TAG1': 'TAG1val'}
    #_tags = [
    #    Tag('TAG1', 'TAG1val')
    #]

    def __init__(self, id=None, owner_id=None, region=None):
        self.id = 'i-%s' % id
        self.region = region
        self.placement = region
        self.groups = []
        self.image_id = 'ami-%s' % self.id
        self.instance_type = 't1.micro'
        self.owner_id = owner_id
        self.instances = [self]
        self.state = 'running'
        self.public_dns_name = 'ec2-dhcp-%s.%s.%s' \
            % (self.id, self.region, DNSDOMAIN)
        self.private_dns_name = 'ec2-internal-%s.%s.%s' \
            % (self.id, self.region, DNSDOMAIN)
        self._tags = [
            Tag(self.id, 'TAG1', 'TAG1val')
        ]


class Boto3Instance(BotoInstance):

    InstanceId = None
    PublicDnsName = None
    PrivateDnsName = None
    placement = None

    def __init__(self, *args, **kwargs):
        super(Boto3Instance, self).__init__(*args, **kwargs)

        self.InstanceId = self.id
        self.PublicDnsName = self.public_dns_name
        self.PrivateDnsName = self.private_dns_name
        self.placement = {
            'availability_zone': [self.region]
        }
        self._tags = [
            Tag(self.id, 'TAG1', 'TAG1val')
        ]

    def to_dict(self):
        data = {}
        for attr in dir(self):
            if attr.startswith('__'):
                continue
            val = getattr(self, attr)
            if type(val) in [str, bool, unicode, int, float, dict, None]:
                data[attr] = val
        return data
