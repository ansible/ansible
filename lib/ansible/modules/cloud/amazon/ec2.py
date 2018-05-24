#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: ec2
short_description: create, terminate, start or stop an instance in ec2
description:
    - Creates or terminates ec2 instances.
version_added: "0.9"
options:
  key_name:
    description:
      - key pair to use on the instance
    aliases: ['keypair']
  id:
    version_added: "1.1"
    description:
      - identifier for this instance or set of instances, so that the module will be idempotent with respect to EC2 instances.
        This identifier is valid for at least 24 hours after the termination of the instance, and should not be reused for another call later on.
        For details, see the description of client token at U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Run_Instance_Idempotency.html).
  group:
    description:
      - security group (or list of groups) to use with the instance
    aliases: [ 'groups' ]
  group_id:
    version_added: "1.1"
    description:
      - security group id (or list of ids) to use with the instance
  region:
    version_added: "1.2"
    description:
      - The AWS region to use.  Must be specified if ec2_url is not used.
        If not specified then the value of the EC2_REGION environment variable, if any, is used.
        See U(http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region)
    aliases: [ 'aws_region', 'ec2_region' ]
  zone:
    version_added: "1.2"
    description:
      - AWS availability zone in which to launch the instance
    aliases: [ 'aws_zone', 'ec2_zone' ]
  instance_type:
    description:
      - instance type to use for the instance, see U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html)
    required: true
  tenancy:
    version_added: "1.9"
    description:
      - An instance with a tenancy of "dedicated" runs on single-tenant hardware and can only be launched into a VPC.
        Note that to use dedicated tenancy you MUST specify a vpc_subnet_id as well. Dedicated tenancy is not available for EC2 "micro" instances.
    default: default
    choices: [ "default", "dedicated" ]
  spot_price:
    version_added: "1.5"
    description:
      - Maximum spot price to bid, If not set a regular on-demand instance is requested. A spot request is made with this maximum bid.
        When it is filled, the instance is started.
  spot_type:
    version_added: "2.0"
    description:
      - Type of spot request; one of "one-time" or "persistent". Defaults to "one-time" if not supplied.
    default: "one-time"
    choices: [ "one-time", "persistent" ]
  image:
    description:
       - I(ami) ID to use for the instance
    required: true
  kernel:
    description:
      - kernel I(eki) to use for the instance
  ramdisk:
    description:
      - ramdisk I(eri) to use for the instance
  wait:
    description:
      - wait for the instance to reach its desired state before returning.  Does not wait for SSH, see 'wait_for_connection' example for details.
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
  spot_wait_timeout:
    version_added: "1.5"
    description:
      - how long to wait for the spot instance request to be fulfilled
    default: 600
  count:
    description:
      - number of instances to launch
    default: 1
  monitoring:
    version_added: "1.1"
    description:
      - enable detailed monitoring (CloudWatch) for instance
    type: bool
    default: 'no'
  user_data:
    version_added: "0.9"
    description:
      - opaque blob of data which is made available to the ec2 instance
  instance_tags:
    version_added: "1.0"
    description:
      - a hash/dictionary of tags to add to the new instance or for starting/stopping instance by tag; '{"key":"value"}' and '{"key":"value","key":"value"}'
  placement_group:
    version_added: "1.3"
    description:
      - placement group for the instance when using EC2 Clustered Compute
  vpc_subnet_id:
    version_added: "1.1"
    description:
      - the subnet ID in which to launch the instance (VPC)
  assign_public_ip:
    version_added: "1.5"
    description:
      - when provisioning within vpc, assign a public IP address. Boto library must be 2.13.0+
    type: bool
  private_ip:
    version_added: "1.2"
    description:
      - the private ip address to assign the instance (from the vpc subnet)
  instance_profile_name:
    version_added: "1.3"
    description:
      - Name of the IAM instance profile to use. Boto library must be 2.5.0+
  instance_ids:
    version_added: "1.3"
    description:
      - "list of instance ids, currently used for states: absent, running, stopped"
    aliases: ['instance_id']
  source_dest_check:
    version_added: "1.6"
    description:
      - Enable or Disable the Source/Destination checks (for NAT instances and Virtual Routers)
    type: bool
    default: 'yes'
  termination_protection:
    version_added: "2.0"
    description:
      - Enable or Disable the Termination Protection
    type: bool
    default: 'no'
  instance_initiated_shutdown_behavior:
    version_added: "2.2"
    description:
    - Set whether AWS will Stop or Terminate an instance on shutdown. This parameter is ignored when using instance-store
      images (which require termination on shutdown).
    default: 'stop'
    choices: [ "stop", "terminate" ]
  state:
    version_added: "1.3"
    description:
      - create, terminate, start, stop or restart instances.
        The state 'restarted' was added in 2.2
    required: false
    default: 'present'
    choices: ['present', 'absent', 'running', 'restarted', 'stopped']
  volumes:
    version_added: "1.5"
    description:
      - a list of hash/dictionaries of volumes to add to the new instance; '[{"key":"value", "key":"value"}]'; keys allowed
        are - device_name (str; required), delete_on_termination (bool; False), device_type (deprecated), ephemeral (str),
        encrypted (bool; False), snapshot (str), volume_type (str), volume_size (int, GB), iops (int) - device_type
        is deprecated use volume_type, iops must be set when volume_type='io1', ephemeral and snapshot are mutually exclusive.
  ebs_optimized:
    version_added: "1.6"
    description:
      - whether instance is using optimized EBS volumes, see U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSOptimized.html)
    default: 'no'
  exact_count:
    version_added: "1.5"
    description:
      - An integer value which indicates how many instances that match the 'count_tag' parameter should be running.
        Instances are either created or terminated based on this value.
  count_tag:
    version_added: "1.5"
    description:
      - Used with 'exact_count' to determine how many nodes based on a specific tag criteria should be running.
        This can be expressed in multiple ways and is shown in the EXAMPLES section.  For instance, one can request 25 servers
        that are tagged with "class=webserver". The specified tag must already exist or be passed in as the 'instance_tags' option.
  network_interfaces:
    version_added: "2.0"
    description:
      - A list of existing network interfaces to attach to the instance at launch. When specifying existing network interfaces,
        none of the assign_public_ip, private_ip, vpc_subnet_id, group, or group_id parameters may be used. (Those parameters are
        for creating a new network interface at launch.)
    aliases: ['network_interface']
  spot_launch_group:
    version_added: "2.1"
    description:
      - Launch group for spot request, see U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-spot-instances-work.html#spot-launch-group)

author:
    - "Tim Gerla (@tgerla)"
    - "Lester Wade (@lwade)"
    - "Seth Vidal"
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic provisioning example
- ec2:
    key_name: mykey
    instance_type: t2.micro
    image: ami-123456
    wait: yes
    group: webserver
    count: 3
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Advanced example with tagging and CloudWatch
- ec2:
    key_name: mykey
    group: databases
    instance_type: t2.micro
    image: ami-123456
    wait: yes
    wait_timeout: 500
    count: 5
    instance_tags:
       db: postgres
    monitoring: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Single instance with additional IOPS volume from snapshot and volume delete on termination
- ec2:
    key_name: mykey
    group: webserver
    instance_type: c3.medium
    image: ami-123456
    wait: yes
    wait_timeout: 500
    volumes:
      - device_name: /dev/sdb
        snapshot: snap-abcdef12
        volume_type: io1
        iops: 1000
        volume_size: 100
        delete_on_termination: true
    monitoring: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Single instance with ssd gp2 root volume
- ec2:
    key_name: mykey
    group: webserver
    instance_type: c3.medium
    image: ami-123456
    wait: yes
    wait_timeout: 500
    volumes:
      - device_name: /dev/xvda
        volume_type: gp2
        volume_size: 8
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes
    count_tag:
      Name: dbserver
    exact_count: 1

# Multiple groups example
- ec2:
    key_name: mykey
    group: ['databases', 'internal-services', 'sshable', 'and-so-forth']
    instance_type: m1.large
    image: ami-6e649707
    wait: yes
    wait_timeout: 500
    count: 5
    instance_tags:
        db: postgres
    monitoring: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Multiple instances with additional volume from snapshot
- ec2:
    key_name: mykey
    group: webserver
    instance_type: m1.large
    image: ami-6e649707
    wait: yes
    wait_timeout: 500
    count: 5
    volumes:
    - device_name: /dev/sdb
      snapshot: snap-abcdef12
      volume_size: 10
    monitoring: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Dedicated tenancy example
- local_action:
    module: ec2
    assign_public_ip: yes
    group_id: sg-1dc53f72
    key_name: mykey
    image: ami-6e649707
    instance_type: m1.small
    tenancy: dedicated
    vpc_subnet_id: subnet-29e63245
    wait: yes

# Spot instance example
- ec2:
    spot_price: 0.24
    spot_wait_timeout: 600
    keypair: mykey
    group_id: sg-1dc53f72
    instance_type: m1.small
    image: ami-6e649707
    wait: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes
    spot_launch_group: report_generators

# Examples using pre-existing network interfaces
- ec2:
    key_name: mykey
    instance_type: t2.small
    image: ami-f005ba11
    network_interface: eni-deadbeef

- ec2:
    key_name: mykey
    instance_type: t2.small
    image: ami-f005ba11
    network_interfaces: ['eni-deadbeef', 'eni-5ca1ab1e']

# Launch instances, runs some tasks
# and then terminate them

- name: Create a sandbox instance
  hosts: localhost
  gather_facts: False
  vars:
    key_name: my_keypair
    instance_type: m1.small
    security_group: my_securitygroup
    image: my_ami_id
    region: us-east-1
  tasks:
    - name: Launch instance
      ec2:
         key_name: "{{ keypair }}"
         group: "{{ security_group }}"
         instance_type: "{{ instance_type }}"
         image: "{{ image }}"
         wait: true
         region: "{{ region }}"
         vpc_subnet_id: subnet-29e63245
         assign_public_ip: yes
      register: ec2

    - name: Add new instance to host group
      add_host:
        hostname: "{{ item.public_ip }}"
        groupname: launched
      with_items: "{{ ec2.instances }}"

    - name: Wait for SSH to come up
      delegate_to: "{{ item.public_dns_name }}"
      wait_for_connection:
        delay: 60
        timeout: 320
      with_items: "{{ ec2.instances }}"

- name: Configure instance(s)
  hosts: launched
  become: True
  gather_facts: True
  roles:
    - my_awesome_role
    - my_awesome_test

- name: Terminate instances
  hosts: localhost
  connection: local
  tasks:
    - name: Terminate instances that were previously launched
      ec2:
        state: 'absent'
        instance_ids: '{{ ec2.instance_ids }}'

# Start a few existing instances, run some tasks
# and stop the instances

- name: Start sandbox instances
  hosts: localhost
  gather_facts: false
  connection: local
  vars:
    instance_ids:
      - 'i-xxxxxx'
      - 'i-xxxxxx'
      - 'i-xxxxxx'
    region: us-east-1
  tasks:
    - name: Start the sandbox instances
      ec2:
        instance_ids: '{{ instance_ids }}'
        region: '{{ region }}'
        state: running
        wait: True
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes
  roles:
    - do_neat_stuff
    - do_more_neat_stuff

- name: Stop sandbox instances
  hosts: localhost
  gather_facts: false
  connection: local
  vars:
    instance_ids:
      - 'i-xxxxxx'
      - 'i-xxxxxx'
      - 'i-xxxxxx'
    region: us-east-1
  tasks:
    - name: Stop the sandbox instances
      ec2:
        instance_ids: '{{ instance_ids }}'
        region: '{{ region }}'
        state: stopped
        wait: True
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

#
# Start stopped instances specified by tag
#
- local_action:
    module: ec2
    instance_tags:
        Name: ExtraPower
    state: running

#
# Restart instances specified by tag
#
- local_action:
    module: ec2
    instance_tags:
        Name: ExtraPower
    state: restarted

#
# Enforce that 5 instances with a tag "foo" are running
# (Highly recommended!)
#

- ec2:
    key_name: mykey
    instance_type: c1.medium
    image: ami-40603AD1
    wait: yes
    group: webserver
    instance_tags:
        foo: bar
    exact_count: 5
    count_tag: foo
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

#
# Enforce that 5 running instances named "database" with a "dbtype" of "postgres"
#

- ec2:
    key_name: mykey
    instance_type: c1.medium
    image: ami-40603AD1
    wait: yes
    group: webserver
    instance_tags:
        Name: database
        dbtype: postgres
    exact_count: 5
    count_tag:
        Name: database
        dbtype: postgres
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

#
# count_tag complex argument examples
#

    # instances with tag foo
- ec2:
    count_tag:
        foo:

    # instances with tag foo=bar
- ec2:
    count_tag:
        foo: bar

    # instances with tags foo=bar & baz
- ec2:
    count_tag:
        foo: bar
        baz:

    # instances with tags foo & bar & baz=bang
- ec2:
    count_tag:
        - foo
        - bar
        - baz: bang

'''

import time
import traceback
from ast import literal_eval
from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import get_aws_connection_info, ec2_argument_spec, ec2_connect
from ansible.module_utils.six import get_function_code, string_types
from ansible.module_utils._text import to_bytes, to_text

try:
    import boto.ec2
    from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping
    from boto.exception import EC2ResponseError
    from boto import connect_ec2_endpoint
    from boto import connect_vpc
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def find_running_instances_by_count_tag(module, ec2, vpc, count_tag, zone=None):

    # get reservations for instances that match tag(s) and are in the desired state
    state = module.params.get('state')
    if state not in ['running', 'stopped']:
        state = None
    reservations = get_reservations(module, ec2, vpc, tags=count_tag, state=state, zone=zone)

    instances = []
    for res in reservations:
        if hasattr(res, 'instances'):
            for inst in res.instances:
                if inst.state == 'terminated':
                    continue
                instances.append(inst)

    return reservations, instances


def _set_none_to_blank(dictionary):
    result = dictionary
    for k in result:
        if isinstance(result[k], dict):
            result[k] = _set_none_to_blank(result[k])
        elif not result[k]:
            result[k] = ""
    return result


def get_reservations(module, ec2, vpc, tags=None, state=None, zone=None):
    # TODO: filters do not work with tags that have underscores
    filters = dict()

    vpc_subnet_id = module.params.get('vpc_subnet_id')
    vpc_id = None
    if vpc_subnet_id:
        filters.update({"subnet-id": vpc_subnet_id})
        if vpc:
            vpc_id = vpc.get_all_subnets(subnet_ids=[vpc_subnet_id])[0].vpc_id

    if vpc_id:
        filters.update({"vpc-id": vpc_id})

    if tags is not None:

        if isinstance(tags, str):
            try:
                tags = literal_eval(tags)
            except:
                pass

        # if not a string type, convert and make sure it's a text string
        if isinstance(tags, int):
            tags = to_text(tags)

        # if string, we only care that a tag of that name exists
        if isinstance(tags, str):
            filters.update({"tag-key": tags})

        # if list, append each item to filters
        if isinstance(tags, list):
            for x in tags:
                if isinstance(x, dict):
                    x = _set_none_to_blank(x)
                    filters.update(dict(("tag:" + tn, tv) for (tn, tv) in x.items()))
                else:
                    filters.update({"tag-key": x})

        # if dict, add the key and value to the filter
        if isinstance(tags, dict):
            tags = _set_none_to_blank(tags)
            filters.update(dict(("tag:" + tn, tv) for (tn, tv) in tags.items()))

        # lets check to see if the filters dict is empty, if so then stop
        if not filters:
            module.fail_json(msg="Filters based on tag is empty => tags: %s" % (tags))

    if state:
        # http://stackoverflow.com/questions/437511/what-are-the-valid-instancestates-for-the-amazon-ec2-api
        filters.update({'instance-state-name': state})

    if zone:
        filters.update({'availability-zone': zone})

    if module.params.get('id'):
        filters['client-token'] = module.params['id']

    results = ec2.get_all_instances(filters=filters)

    return results


def get_instance_info(inst):
    """
    Retrieves instance information from an instance
    ID and returns it as a dictionary
    """
    instance_info = {'id': inst.id,
                     'ami_launch_index': inst.ami_launch_index,
                     'private_ip': inst.private_ip_address,
                     'private_dns_name': inst.private_dns_name,
                     'public_ip': inst.ip_address,
                     'dns_name': inst.dns_name,
                     'public_dns_name': inst.public_dns_name,
                     'state_code': inst.state_code,
                     'architecture': inst.architecture,
                     'image_id': inst.image_id,
                     'key_name': inst.key_name,
                     'placement': inst.placement,
                     'region': inst.placement[:-1],
                     'kernel': inst.kernel,
                     'ramdisk': inst.ramdisk,
                     'launch_time': inst.launch_time,
                     'instance_type': inst.instance_type,
                     'root_device_type': inst.root_device_type,
                     'root_device_name': inst.root_device_name,
                     'state': inst.state,
                     'hypervisor': inst.hypervisor,
                     'tags': inst.tags,
                     'groups': dict((group.id, group.name) for group in inst.groups),
                     }
    try:
        instance_info['virtualization_type'] = getattr(inst, 'virtualization_type')
    except AttributeError:
        instance_info['virtualization_type'] = None

    try:
        instance_info['ebs_optimized'] = getattr(inst, 'ebs_optimized')
    except AttributeError:
        instance_info['ebs_optimized'] = False

    try:
        bdm_dict = {}
        bdm = getattr(inst, 'block_device_mapping')
        for device_name in bdm.keys():
            bdm_dict[device_name] = {
                'status': bdm[device_name].status,
                'volume_id': bdm[device_name].volume_id,
                'delete_on_termination': bdm[device_name].delete_on_termination
            }
        instance_info['block_device_mapping'] = bdm_dict
    except AttributeError:
        instance_info['block_device_mapping'] = False

    try:
        instance_info['tenancy'] = getattr(inst, 'placement_tenancy')
    except AttributeError:
        instance_info['tenancy'] = 'default'

    return instance_info


def boto_supports_associate_public_ip_address(ec2):
    """
    Check if Boto library has associate_public_ip_address in the NetworkInterfaceSpecification
    class. Added in Boto 2.13.0

    ec2: authenticated ec2 connection object

    Returns:
        True if Boto library accepts associate_public_ip_address argument, else false
    """

    try:
        network_interface = boto.ec2.networkinterface.NetworkInterfaceSpecification()
        getattr(network_interface, "associate_public_ip_address")
        return True
    except AttributeError:
        return False


def boto_supports_profile_name_arg(ec2):
    """
    Check if Boto library has instance_profile_name argument. instance_profile_name has been added in Boto 2.5.0

    ec2: authenticated ec2 connection object

    Returns:
        True if Boto library accept instance_profile_name argument, else false
    """
    run_instances_method = getattr(ec2, 'run_instances')
    return 'instance_profile_name' in get_function_code(run_instances_method).co_varnames


def boto_supports_volume_encryption():
    """
    Check if Boto library supports encryption of EBS volumes (added in 2.29.0)

    Returns:
        True if boto library has the named param as an argument on the request_spot_instances method, else False
    """
    return hasattr(boto, 'Version') and LooseVersion(boto.Version) >= LooseVersion('2.29.0')


def create_block_device(module, ec2, volume):
    # Not aware of a way to determine this programatically
    # http://aws.amazon.com/about-aws/whats-new/2013/10/09/ebs-provisioned-iops-maximum-iops-gb-ratio-increased-to-30-1/
    MAX_IOPS_TO_SIZE_RATIO = 30

    # device_type has been used historically to represent volume_type,
    # however ec2_vol uses volume_type, as does the BlockDeviceType, so
    # we add handling for either/or but not both
    if all(key in volume for key in ['device_type', 'volume_type']):
        module.fail_json(msg='device_type is a deprecated name for volume_type. Do not use both device_type and volume_type')
    if 'device_type' in volume:
        module.deprecate('device_type is deprecated for block devices - use volume_type instead',
                         version=2.9)

    # get whichever one is set, or NoneType if neither are set
    volume_type = volume.get('device_type') or volume.get('volume_type')

    if 'snapshot' not in volume and 'ephemeral' not in volume:
        if 'volume_size' not in volume:
            module.fail_json(msg='Size must be specified when creating a new volume or modifying the root volume')
    if 'snapshot' in volume:
        if volume_type == 'io1' and 'iops' not in volume:
            module.fail_json(msg='io1 volumes must have an iops value set')
        if 'iops' in volume:
            snapshot = ec2.get_all_snapshots(snapshot_ids=[volume['snapshot']])[0]
            size = volume.get('volume_size', snapshot.volume_size)
            if int(volume['iops']) > MAX_IOPS_TO_SIZE_RATIO * size:
                module.fail_json(msg='IOPS must be at most %d times greater than size' % MAX_IOPS_TO_SIZE_RATIO)
        if 'encrypted' in volume:
            module.fail_json(msg='You can not set encryption when creating a volume from a snapshot')
    if 'ephemeral' in volume:
        if 'snapshot' in volume:
            module.fail_json(msg='Cannot set both ephemeral and snapshot')
    if boto_supports_volume_encryption():
        return BlockDeviceType(snapshot_id=volume.get('snapshot'),
                               ephemeral_name=volume.get('ephemeral'),
                               size=volume.get('volume_size'),
                               volume_type=volume_type,
                               delete_on_termination=volume.get('delete_on_termination', False),
                               iops=volume.get('iops'),
                               encrypted=volume.get('encrypted', None))
    else:
        return BlockDeviceType(snapshot_id=volume.get('snapshot'),
                               ephemeral_name=volume.get('ephemeral'),
                               size=volume.get('volume_size'),
                               volume_type=volume_type,
                               delete_on_termination=volume.get('delete_on_termination', False),
                               iops=volume.get('iops'))


def boto_supports_param_in_spot_request(ec2, param):
    """
    Check if Boto library has a <param> in its request_spot_instances() method. For example, the placement_group parameter wasn't added until 2.3.0.

    ec2: authenticated ec2 connection object

    Returns:
        True if boto library has the named param as an argument on the request_spot_instances method, else False
    """
    method = getattr(ec2, 'request_spot_instances')
    return param in get_function_code(method).co_varnames


def await_spot_requests(module, ec2, spot_requests, count):
    """
    Wait for a group of spot requests to be fulfilled, or fail.

    module: Ansible module object
    ec2: authenticated ec2 connection object
    spot_requests: boto.ec2.spotinstancerequest.SpotInstanceRequest object returned by ec2.request_spot_instances
    count: Total number of instances to be created by the spot requests

    Returns:
        list of instance ID's created by the spot request(s)
    """
    spot_wait_timeout = int(module.params.get('spot_wait_timeout'))
    wait_complete = time.time() + spot_wait_timeout

    spot_req_inst_ids = dict()
    while time.time() < wait_complete:
        reqs = ec2.get_all_spot_instance_requests()
        for sirb in spot_requests:
            if sirb.id in spot_req_inst_ids:
                continue
            for sir in reqs:
                if sir.id != sirb.id:
                    continue  # this is not our spot instance
                if sir.instance_id is not None:
                    spot_req_inst_ids[sirb.id] = sir.instance_id
                elif sir.state == 'open':
                    continue  # still waiting, nothing to do here
                elif sir.state == 'active':
                    continue  # Instance is created already, nothing to do here
                elif sir.state == 'failed':
                    module.fail_json(msg="Spot instance request %s failed with status %s and fault %s:%s" % (
                        sir.id, sir.status.code, sir.fault.code, sir.fault.message))
                elif sir.state == 'cancelled':
                    module.fail_json(msg="Spot instance request %s was cancelled before it could be fulfilled." % sir.id)
                elif sir.state == 'closed':
                    # instance is terminating or marked for termination
                    # this may be intentional on the part of the operator,
                    # or it may have been terminated by AWS due to capacity,
                    # price, or group constraints in this case, we'll fail
                    # the module if the reason for the state is anything
                    # other than termination by user. Codes are documented at
                    # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-bid-status.html
                    if sir.status.code == 'instance-terminated-by-user':
                        # do nothing, since the user likely did this on purpose
                        pass
                    else:
                        spot_msg = "Spot instance request %s was closed by AWS with the status %s and fault %s:%s"
                        module.fail_json(msg=spot_msg % (sir.id, sir.status.code, sir.fault.code, sir.fault.message))

        if len(spot_req_inst_ids) < count:
            time.sleep(5)
        else:
            return list(spot_req_inst_ids.values())
    module.fail_json(msg="wait for spot requests timeout on %s" % time.asctime())


def enforce_count(module, ec2, vpc):

    exact_count = module.params.get('exact_count')
    count_tag = module.params.get('count_tag')
    zone = module.params.get('zone')

    # fail here if the exact count was specified without filtering
    # on a tag, as this may lead to a undesired removal of instances
    if exact_count and count_tag is None:
        module.fail_json(msg="you must use the 'count_tag' option with exact_count")

    reservations, instances = find_running_instances_by_count_tag(module, ec2, vpc, count_tag, zone)

    changed = None
    checkmode = False
    instance_dict_array = []
    changed_instance_ids = None

    if len(instances) == exact_count:
        changed = False
    elif len(instances) < exact_count:
        changed = True
        to_create = exact_count - len(instances)
        if not checkmode:
            (instance_dict_array, changed_instance_ids, changed) \
                = create_instances(module, ec2, vpc, override_count=to_create)

            for inst in instance_dict_array:
                instances.append(inst)
    elif len(instances) > exact_count:
        changed = True
        to_remove = len(instances) - exact_count
        if not checkmode:
            all_instance_ids = sorted([x.id for x in instances])
            remove_ids = all_instance_ids[0:to_remove]

            instances = [x for x in instances if x.id not in remove_ids]

            (changed, instance_dict_array, changed_instance_ids) \
                = terminate_instances(module, ec2, remove_ids)
            terminated_list = []
            for inst in instance_dict_array:
                inst['state'] = "terminated"
                terminated_list.append(inst)
            instance_dict_array = terminated_list

    # ensure all instances are dictionaries
    all_instances = []
    for inst in instances:

        if not isinstance(inst, dict):
            warn_if_public_ip_assignment_changed(module, inst)
            inst = get_instance_info(inst)
        all_instances.append(inst)

    return (all_instances, instance_dict_array, changed_instance_ids, changed)


def create_instances(module, ec2, vpc, override_count=None):
    """
    Creates new instances

    module : AnsibleModule object
    ec2: authenticated ec2 connection object

    Returns:
        A list of dictionaries with instance information
        about the instances that were launched
    """

    key_name = module.params.get('key_name')
    id = module.params.get('id')
    group_name = module.params.get('group')
    group_id = module.params.get('group_id')
    zone = module.params.get('zone')
    instance_type = module.params.get('instance_type')
    tenancy = module.params.get('tenancy')
    spot_price = module.params.get('spot_price')
    spot_type = module.params.get('spot_type')
    image = module.params.get('image')
    if override_count:
        count = override_count
    else:
        count = module.params.get('count')
    monitoring = module.params.get('monitoring')
    kernel = module.params.get('kernel')
    ramdisk = module.params.get('ramdisk')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    spot_wait_timeout = int(module.params.get('spot_wait_timeout'))
    placement_group = module.params.get('placement_group')
    user_data = module.params.get('user_data')
    instance_tags = module.params.get('instance_tags')
    vpc_subnet_id = module.params.get('vpc_subnet_id')
    assign_public_ip = module.boolean(module.params.get('assign_public_ip'))
    private_ip = module.params.get('private_ip')
    instance_profile_name = module.params.get('instance_profile_name')
    volumes = module.params.get('volumes')
    ebs_optimized = module.params.get('ebs_optimized')
    exact_count = module.params.get('exact_count')
    count_tag = module.params.get('count_tag')
    source_dest_check = module.boolean(module.params.get('source_dest_check'))
    termination_protection = module.boolean(module.params.get('termination_protection'))
    network_interfaces = module.params.get('network_interfaces')
    spot_launch_group = module.params.get('spot_launch_group')
    instance_initiated_shutdown_behavior = module.params.get('instance_initiated_shutdown_behavior')

    vpc_id = None
    if vpc_subnet_id:
        if not vpc:
            module.fail_json(msg="region must be specified")
        else:
            vpc_id = vpc.get_all_subnets(subnet_ids=[vpc_subnet_id])[0].vpc_id
    else:
        vpc_id = None

    try:
        # Here we try to lookup the group id from the security group name - if group is set.
        if group_name:
            if vpc_id:
                grp_details = ec2.get_all_security_groups(filters={'vpc_id': vpc_id})
            else:
                grp_details = ec2.get_all_security_groups()
            if isinstance(group_name, string_types):
                group_name = [group_name]
            unmatched = set(group_name).difference(str(grp.name) for grp in grp_details)
            if len(unmatched) > 0:
                module.fail_json(msg="The following group names are not valid: %s" % ', '.join(unmatched))
            group_id = [str(grp.id) for grp in grp_details if str(grp.name) in group_name]
        # Now we try to lookup the group id testing if group exists.
        elif group_id:
            # wrap the group_id in a list if it's not one already
            if isinstance(group_id, string_types):
                group_id = [group_id]
            grp_details = ec2.get_all_security_groups(group_ids=group_id)
            group_name = [grp_item.name for grp_item in grp_details]
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=str(e))

    # Lookup any instances that much our run id.

    running_instances = []
    count_remaining = int(count)

    if id is not None:
        filter_dict = {'client-token': id, 'instance-state-name': 'running'}
        previous_reservations = ec2.get_all_instances(None, filter_dict)
        for res in previous_reservations:
            for prev_instance in res.instances:
                running_instances.append(prev_instance)
        count_remaining = count_remaining - len(running_instances)

    # Both min_count and max_count equal count parameter. This means the launch request is explicit (we want count, or fail) in how many instances we want.

    if count_remaining == 0:
        changed = False
    else:
        changed = True
        try:
            params = {'image_id': image,
                      'key_name': key_name,
                      'monitoring_enabled': monitoring,
                      'placement': zone,
                      'instance_type': instance_type,
                      'kernel_id': kernel,
                      'ramdisk_id': ramdisk,
                      'user_data': to_bytes(user_data, errors='surrogate_or_strict')}

            if ebs_optimized:
                params['ebs_optimized'] = ebs_optimized

            # 'tenancy' always has a default value, but it is not a valid parameter for spot instance request
            if not spot_price:
                params['tenancy'] = tenancy

            if boto_supports_profile_name_arg(ec2):
                params['instance_profile_name'] = instance_profile_name
            else:
                if instance_profile_name is not None:
                    module.fail_json(
                        msg="instance_profile_name parameter requires Boto version 2.5.0 or higher")

            if assign_public_ip:
                if not boto_supports_associate_public_ip_address(ec2):
                    module.fail_json(
                        msg="assign_public_ip parameter requires Boto version 2.13.0 or higher.")
                elif not vpc_subnet_id:
                    module.fail_json(
                        msg="assign_public_ip only available with vpc_subnet_id")

                else:
                    if private_ip:
                        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
                            subnet_id=vpc_subnet_id,
                            private_ip_address=private_ip,
                            groups=group_id,
                            associate_public_ip_address=assign_public_ip)
                    else:
                        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
                            subnet_id=vpc_subnet_id,
                            groups=group_id,
                            associate_public_ip_address=assign_public_ip)
                    interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface)
                    params['network_interfaces'] = interfaces
            else:
                if network_interfaces:
                    if isinstance(network_interfaces, string_types):
                        network_interfaces = [network_interfaces]
                    interfaces = []
                    for i, network_interface_id in enumerate(network_interfaces):
                        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
                            network_interface_id=network_interface_id,
                            device_index=i)
                        interfaces.append(interface)
                    params['network_interfaces'] = \
                        boto.ec2.networkinterface.NetworkInterfaceCollection(*interfaces)
                else:
                    params['subnet_id'] = vpc_subnet_id
                    if vpc_subnet_id:
                        params['security_group_ids'] = group_id
                    else:
                        params['security_groups'] = group_name

            if volumes:
                bdm = BlockDeviceMapping()
                for volume in volumes:
                    if 'device_name' not in volume:
                        module.fail_json(msg='Device name must be set for volume')
                    # Minimum volume size is 1GB. We'll use volume size explicitly set to 0
                    # to be a signal not to create this volume
                    if 'volume_size' not in volume or int(volume['volume_size']) > 0:
                        bdm[volume['device_name']] = create_block_device(module, ec2, volume)

                params['block_device_map'] = bdm

            # check to see if we're using spot pricing first before starting instances
            if not spot_price:
                if assign_public_ip and private_ip:
                    params.update(
                        dict(
                            min_count=count_remaining,
                            max_count=count_remaining,
                            client_token=id,
                            placement_group=placement_group,
                        )
                    )
                else:
                    params.update(
                        dict(
                            min_count=count_remaining,
                            max_count=count_remaining,
                            client_token=id,
                            placement_group=placement_group,
                            private_ip_address=private_ip,
                        )
                    )

                # For ordinary (not spot) instances, we can select 'stop'
                # (the default) or 'terminate' here.
                params['instance_initiated_shutdown_behavior'] = instance_initiated_shutdown_behavior or 'stop'

                try:
                    res = ec2.run_instances(**params)
                except boto.exception.EC2ResponseError as e:
                    if (params['instance_initiated_shutdown_behavior'] != 'terminate' and
                            "InvalidParameterCombination" == e.error_code):
                        params['instance_initiated_shutdown_behavior'] = 'terminate'
                        res = ec2.run_instances(**params)
                    else:
                        raise

                instids = [i.id for i in res.instances]
                while True:
                    try:
                        ec2.get_all_instances(instids)
                        break
                    except boto.exception.EC2ResponseError as e:
                        if "<Code>InvalidInstanceID.NotFound</Code>" in str(e):
                            # there's a race between start and get an instance
                            continue
                        else:
                            module.fail_json(msg=str(e))

                # The instances returned through ec2.run_instances above can be in
                # terminated state due to idempotency. See commit 7f11c3d for a complete
                # explanation.
                terminated_instances = [
                    str(instance.id) for instance in res.instances if instance.state == 'terminated'
                ]
                if terminated_instances:
                    module.fail_json(msg="Instances with id(s) %s " % terminated_instances +
                                     "were created previously but have since been terminated - " +
                                     "use a (possibly different) 'instanceid' parameter")

            else:
                if private_ip:
                    module.fail_json(
                        msg='private_ip only available with on-demand (non-spot) instances')
                if boto_supports_param_in_spot_request(ec2, 'placement_group'):
                    params['placement_group'] = placement_group
                elif placement_group:
                    module.fail_json(
                        msg="placement_group parameter requires Boto version 2.3.0 or higher.")

                # You can't tell spot instances to 'stop'; they will always be
                # 'terminate'd. For convenience, we'll ignore the latter value.
                if instance_initiated_shutdown_behavior and instance_initiated_shutdown_behavior != 'terminate':
                    module.fail_json(
                        msg="instance_initiated_shutdown_behavior=stop is not supported for spot instances.")

                if spot_launch_group and isinstance(spot_launch_group, string_types):
                    params['launch_group'] = spot_launch_group

                params.update(dict(
                    count=count_remaining,
                    type=spot_type,
                ))
                res = ec2.request_spot_instances(spot_price, **params)

                # Now we have to do the intermediate waiting
                if wait:
                    instids = await_spot_requests(module, ec2, res, count)
                else:
                    instids = []
        except boto.exception.BotoServerError as e:
            module.fail_json(msg="Instance creation failed => %s: %s" % (e.error_code, e.error_message))

        # wait here until the instances are up
        num_running = 0
        wait_timeout = time.time() + wait_timeout
        res_list = ()
        while wait_timeout > time.time() and num_running < len(instids):
            try:
                res_list = ec2.get_all_instances(instids)
            except boto.exception.BotoServerError as e:
                if e.error_code == 'InvalidInstanceID.NotFound':
                    time.sleep(1)
                    continue
                else:
                    raise

            num_running = 0
            for res in res_list:
                num_running += len([i for i in res.instances if i.state == 'running'])
            if len(res_list) <= 0:
                # got a bad response of some sort, possibly due to
                # stale/cached data. Wait a second and then try again
                time.sleep(1)
                continue
            if wait and num_running < len(instids):
                time.sleep(5)
            else:
                break

        if wait and wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg="wait for instances running timeout on %s" % time.asctime())

        # We do this after the loop ends so that we end up with one list
        for res in res_list:
            running_instances.extend(res.instances)

        # Enabled by default by AWS
        if source_dest_check is False:
            for inst in res.instances:
                inst.modify_attribute('sourceDestCheck', False)

        # Disabled by default by AWS
        if termination_protection is True:
            for inst in res.instances:
                inst.modify_attribute('disableApiTermination', True)

        # Leave this as late as possible to try and avoid InvalidInstanceID.NotFound
        if instance_tags and instids:
            try:
                ec2.create_tags(instids, instance_tags)
            except boto.exception.EC2ResponseError as e:
                module.fail_json(msg="Instance tagging failed => %s: %s" % (e.error_code, e.error_message))

    instance_dict_array = []
    created_instance_ids = []
    for inst in running_instances:
        inst.update()
        d = get_instance_info(inst)
        created_instance_ids.append(inst.id)
        instance_dict_array.append(d)

    return (instance_dict_array, created_instance_ids, changed)


def terminate_instances(module, ec2, instance_ids):
    """
    Terminates a list of instances

    module: Ansible module object
    ec2: authenticated ec2 connection object
    termination_list: a list of instances to terminate in the form of
      [ {id: <inst-id>}, ..]

    Returns a dictionary of instance information
    about the instances terminated.

    If the instance to be terminated is running
    "changed" will be set to False.

    """

    # Whether to wait for termination to complete before returning
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    changed = False
    instance_dict_array = []

    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        module.fail_json(msg='instance_ids should be a list of instances, aborting')

    terminated_instance_ids = []
    for res in ec2.get_all_instances(instance_ids):
        for inst in res.instances:
            if inst.state == 'running' or inst.state == 'stopped':
                terminated_instance_ids.append(inst.id)
                instance_dict_array.append(get_instance_info(inst))
                try:
                    ec2.terminate_instances([inst.id])
                except EC2ResponseError as e:
                    module.fail_json(msg='Unable to terminate instance {0}, error: {1}'.format(inst.id, e))
                changed = True

    # wait here until the instances are 'terminated'
    if wait:
        num_terminated = 0
        wait_timeout = time.time() + wait_timeout
        while wait_timeout > time.time() and num_terminated < len(terminated_instance_ids):
            response = ec2.get_all_instances(instance_ids=terminated_instance_ids,
                                             filters={'instance-state-name': 'terminated'})
            try:
                num_terminated = sum([len(res.instances) for res in response])
            except Exception as e:
                # got a bad response of some sort, possibly due to
                # stale/cached data. Wait a second and then try again
                time.sleep(1)
                continue

            if num_terminated < len(terminated_instance_ids):
                time.sleep(5)

        # waiting took too long
        if wait_timeout < time.time() and num_terminated < len(terminated_instance_ids):
            module.fail_json(msg="wait for instance termination timeout on %s" % time.asctime())
        # Lets get the current state of the instances after terminating - issue600
        instance_dict_array = []
        for res in ec2.get_all_instances(instance_ids=terminated_instance_ids, filters={'instance-state-name': 'terminated'}):
            for inst in res.instances:
                instance_dict_array.append(get_instance_info(inst))

    return (changed, instance_dict_array, terminated_instance_ids)


def startstop_instances(module, ec2, instance_ids, state, instance_tags):
    """
    Starts or stops a list of existing instances

    module: Ansible module object
    ec2: authenticated ec2 connection object
    instance_ids: The list of instances to start in the form of
      [ {id: <inst-id>}, ..]
    instance_tags: A dict of tag keys and values in the form of
      {key: value, ... }
    state: Intended state ("running" or "stopped")

    Returns a dictionary of instance information
    about the instances started/stopped.

    If the instance was not able to change state,
    "changed" will be set to False.

    Note that if instance_ids and instance_tags are both non-empty,
    this method will process the intersection of the two
    """

    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    source_dest_check = module.params.get('source_dest_check')
    termination_protection = module.params.get('termination_protection')
    group_id = module.params.get('group_id')
    group_name = module.params.get('group')
    changed = False
    instance_dict_array = []

    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        # Fail unless the user defined instance tags
        if not instance_tags:
            module.fail_json(msg='instance_ids should be a list of instances, aborting')

    # To make an EC2 tag filter, we need to prepend 'tag:' to each key.
    # An empty filter does no filtering, so it's safe to pass it to the
    # get_all_instances method even if the user did not specify instance_tags
    filters = {}
    if instance_tags:
        for key, value in instance_tags.items():
            filters["tag:" + key] = value

    if module.params.get('id'):
        filters['client-token'] = module.params['id']
    # Check that our instances are not in the state we want to take

    # Check (and eventually change) instances attributes and instances state
    existing_instances_array = []
    for res in ec2.get_all_instances(instance_ids, filters=filters):
        for inst in res.instances:

            warn_if_public_ip_assignment_changed(module, inst)

            # Check "source_dest_check" attribute
            try:
                if inst.vpc_id is not None and inst.get_attribute('sourceDestCheck')['sourceDestCheck'] != source_dest_check:
                    inst.modify_attribute('sourceDestCheck', source_dest_check)
                    changed = True
            except boto.exception.EC2ResponseError as exc:
                # instances with more than one Elastic Network Interface will
                # fail, because they have the sourceDestCheck attribute defined
                # per-interface
                if exc.code == 'InvalidInstanceID':
                    for interface in inst.interfaces:
                        if interface.source_dest_check != source_dest_check:
                            ec2.modify_network_interface_attribute(interface.id, "sourceDestCheck", source_dest_check)
                            changed = True
                else:
                    module.fail_json(msg='Failed to handle source_dest_check state for instance {0}, error: {1}'.format(inst.id, exc),
                                     exception=traceback.format_exc())

            # Check "termination_protection" attribute
            if (inst.get_attribute('disableApiTermination')['disableApiTermination'] != termination_protection and termination_protection is not None):
                inst.modify_attribute('disableApiTermination', termination_protection)
                changed = True

            # Check security groups and if we're using ec2-vpc; ec2-classic security groups may not be modified
            if inst.vpc_id and group_name:
                grp_details = ec2.get_all_security_groups(filters={'vpc_id': inst.vpc_id})
                if isinstance(group_name, string_types):
                    group_name = [group_name]
                unmatched = set(group_name) - set(to_text(grp.name) for grp in grp_details)
                if unmatched:
                    module.fail_json(msg="The following group names are not valid: %s" % ', '.join(unmatched))
                group_ids = [to_text(grp.id) for grp in grp_details if to_text(grp.name) in group_name]
            elif inst.vpc_id and group_id:
                if isinstance(group_id, string_types):
                    group_id = [group_id]
                grp_details = ec2.get_all_security_groups(group_ids=group_id)
                group_ids = [grp_item.id for grp_item in grp_details]
            if inst.vpc_id and (group_name or group_id):
                if set(sg.id for sg in inst.groups) != set(group_ids):
                    changed = inst.modify_attribute('groupSet', group_ids)

            # Check instance state
            if inst.state != state:
                instance_dict_array.append(get_instance_info(inst))
                try:
                    if state == 'running':
                        inst.start()
                    else:
                        inst.stop()
                except EC2ResponseError as e:
                    module.fail_json(msg='Unable to change state for instance {0}, error: {1}'.format(inst.id, e))
                changed = True
            existing_instances_array.append(inst.id)

    instance_ids = list(set(existing_instances_array + (instance_ids or [])))
    # Wait for all the instances to finish starting or stopping
    wait_timeout = time.time() + wait_timeout
    while wait and wait_timeout > time.time():
        instance_dict_array = []
        matched_instances = []
        for res in ec2.get_all_instances(instance_ids):
            for i in res.instances:
                if i.state == state:
                    instance_dict_array.append(get_instance_info(i))
                    matched_instances.append(i)
        if len(matched_instances) < len(instance_ids):
            time.sleep(5)
        else:
            break

    if wait and wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg="wait for instances running timeout on %s" % time.asctime())

    return (changed, instance_dict_array, instance_ids)


def restart_instances(module, ec2, instance_ids, state, instance_tags):
    """
    Restarts a list of existing instances

    module: Ansible module object
    ec2: authenticated ec2 connection object
    instance_ids: The list of instances to start in the form of
      [ {id: <inst-id>}, ..]
    instance_tags: A dict of tag keys and values in the form of
      {key: value, ... }
    state: Intended state ("restarted")

    Returns a dictionary of instance information
    about the instances.

    If the instance was not able to change state,
    "changed" will be set to False.

    Wait will not apply here as this is a OS level operation.

    Note that if instance_ids and instance_tags are both non-empty,
    this method will process the intersection of the two.
    """

    source_dest_check = module.params.get('source_dest_check')
    termination_protection = module.params.get('termination_protection')
    changed = False
    instance_dict_array = []

    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        # Fail unless the user defined instance tags
        if not instance_tags:
            module.fail_json(msg='instance_ids should be a list of instances, aborting')

    # To make an EC2 tag filter, we need to prepend 'tag:' to each key.
    # An empty filter does no filtering, so it's safe to pass it to the
    # get_all_instances method even if the user did not specify instance_tags
    filters = {}
    if instance_tags:
        for key, value in instance_tags.items():
            filters["tag:" + key] = value
    if module.params.get('id'):
        filters['client-token'] = module.params['id']

    # Check that our instances are not in the state we want to take

    # Check (and eventually change) instances attributes and instances state
    for res in ec2.get_all_instances(instance_ids, filters=filters):
        for inst in res.instances:

            warn_if_public_ip_assignment_changed(module, inst)

            # Check "source_dest_check" attribute
            try:
                if inst.vpc_id is not None and inst.get_attribute('sourceDestCheck')['sourceDestCheck'] != source_dest_check:
                    inst.modify_attribute('sourceDestCheck', source_dest_check)
                    changed = True
            except boto.exception.EC2ResponseError as exc:
                # instances with more than one Elastic Network Interface will
                # fail, because they have the sourceDestCheck attribute defined
                # per-interface
                if exc.code == 'InvalidInstanceID':
                    for interface in inst.interfaces:
                        if interface.source_dest_check != source_dest_check:
                            ec2.modify_network_interface_attribute(interface.id, "sourceDestCheck", source_dest_check)
                            changed = True
                else:
                    module.fail_json(msg='Failed to handle source_dest_check state for instance {0}, error: {1}'.format(inst.id, exc),
                                     exception=traceback.format_exc())

            # Check "termination_protection" attribute
            if (inst.get_attribute('disableApiTermination')['disableApiTermination'] != termination_protection and termination_protection is not None):
                inst.modify_attribute('disableApiTermination', termination_protection)
                changed = True

            # Check instance state
            if inst.state != state:
                instance_dict_array.append(get_instance_info(inst))
                try:
                    inst.reboot()
                except EC2ResponseError as e:
                    module.fail_json(msg='Unable to change state for instance {0}, error: {1}'.format(inst.id, e))
                changed = True

    return (changed, instance_dict_array, instance_ids)


def warn_if_public_ip_assignment_changed(module, instance):
    # This is a non-modifiable attribute.
    assign_public_ip = module.params.get('assign_public_ip')

    # Check that public ip assignment is the same and warn if not
    public_dns_name = getattr(instance, 'public_dns_name', None)
    if (assign_public_ip or public_dns_name) and (not public_dns_name or assign_public_ip is False):
        module.warn("Unable to modify public ip assignment to {0} for instance {1}. "
                    "Whether or not to assign a public IP is determined during instance creation.".format(assign_public_ip, instance.id))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            key_name=dict(aliases=['keypair']),
            id=dict(),
            group=dict(type='list', aliases=['groups']),
            group_id=dict(type='list'),
            zone=dict(aliases=['aws_zone', 'ec2_zone']),
            instance_type=dict(aliases=['type']),
            spot_price=dict(),
            spot_type=dict(default='one-time', choices=["one-time", "persistent"]),
            spot_launch_group=dict(),
            image=dict(),
            kernel=dict(),
            count=dict(type='int', default='1'),
            monitoring=dict(type='bool', default=False),
            ramdisk=dict(),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(default=300),
            spot_wait_timeout=dict(default=600),
            placement_group=dict(),
            user_data=dict(),
            instance_tags=dict(type='dict'),
            vpc_subnet_id=dict(),
            assign_public_ip=dict(type='bool'),
            private_ip=dict(),
            instance_profile_name=dict(),
            instance_ids=dict(type='list', aliases=['instance_id']),
            source_dest_check=dict(type='bool', default=True),
            termination_protection=dict(type='bool', default=None),
            state=dict(default='present', choices=['present', 'absent', 'running', 'restarted', 'stopped']),
            instance_initiated_shutdown_behavior=dict(default=None, choices=['stop', 'terminate']),
            exact_count=dict(type='int', default=None),
            count_tag=dict(),
            volumes=dict(type='list'),
            ebs_optimized=dict(type='bool', default=False),
            tenancy=dict(default='default'),
            network_interfaces=dict(type='list', aliases=['network_interface'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['group_name', 'group_id'],
            ['exact_count', 'count'],
            ['exact_count', 'state'],
            ['exact_count', 'instance_ids'],
            ['network_interfaces', 'assign_public_ip'],
            ['network_interfaces', 'group'],
            ['network_interfaces', 'group_id'],
            ['network_interfaces', 'private_ip'],
            ['network_interfaces', 'vpc_subnet_id'],
        ],
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)
        if module.params.get('region') or not module.params.get('ec2_url'):
            ec2 = ec2_connect(module)
        elif module.params.get('ec2_url'):
            ec2 = connect_ec2_endpoint(ec2_url, **aws_connect_kwargs)

        if 'region' not in aws_connect_kwargs:
            aws_connect_kwargs['region'] = ec2.region

        vpc = connect_vpc(**aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg="Failed to get connection: %s" % e.message, exception=traceback.format_exc())

    tagged_instances = []

    state = module.params['state']

    if state == 'absent':
        instance_ids = module.params['instance_ids']
        if not instance_ids:
            module.fail_json(msg='instance_ids list is required for absent state')

        (changed, instance_dict_array, new_instance_ids) = terminate_instances(module, ec2, instance_ids)

    elif state in ('running', 'stopped'):
        instance_ids = module.params.get('instance_ids')
        instance_tags = module.params.get('instance_tags')
        if not (isinstance(instance_ids, list) or isinstance(instance_tags, dict)):
            module.fail_json(msg='running list needs to be a list of instances or set of tags to run: %s' % instance_ids)

        (changed, instance_dict_array, new_instance_ids) = startstop_instances(module, ec2, instance_ids, state, instance_tags)

    elif state in ('restarted'):
        instance_ids = module.params.get('instance_ids')
        instance_tags = module.params.get('instance_tags')
        if not (isinstance(instance_ids, list) or isinstance(instance_tags, dict)):
            module.fail_json(msg='running list needs to be a list of instances or set of tags to run: %s' % instance_ids)

        (changed, instance_dict_array, new_instance_ids) = restart_instances(module, ec2, instance_ids, state, instance_tags)

    elif state == 'present':
        # Changed is always set to true when provisioning new instances
        if not module.params.get('image'):
            module.fail_json(msg='image parameter is required for new instance')

        if module.params.get('exact_count') is None:
            (instance_dict_array, new_instance_ids, changed) = create_instances(module, ec2, vpc)
        else:
            (tagged_instances, instance_dict_array, new_instance_ids, changed) = enforce_count(module, ec2, vpc)

    # Always return instances in the same order
    if new_instance_ids:
        new_instance_ids.sort()
    if instance_dict_array:
        instance_dict_array.sort(key=lambda x: x['id'])
    if tagged_instances:
        tagged_instances.sort(key=lambda x: x['id'])

    module.exit_json(changed=changed, instance_ids=new_instance_ids, instances=instance_dict_array, tagged_instances=tagged_instances)


if __name__ == '__main__':
    main()
