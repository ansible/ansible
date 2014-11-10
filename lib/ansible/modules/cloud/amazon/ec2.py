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

DOCUMENTATION = '''
---
module: ec2
short_description: create, terminate, start or stop an instance in ec2, return instanceid
description:
    - Creates or terminates ec2 instances. When created optionally waits for it to be 'running'. This module has a dependency on python-boto >= 2.5
version_added: "0.9"
options:
  key_name:
    description:
      - key pair to use on the instance
    required: false
    default: null
    aliases: ['keypair']
  id:
    description:
      - identifier for this instance or set of instances, so that the module will be idempotent with respect to EC2 instances. This identifier is valid for at least 24 hours after the termination of the instance, and should not be reused for another call later on. For details, see the description of client token at U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Run_Instance_Idempotency.html).
    required: false
    default: null
    aliases: []
  group:
    description:
      - security group (or list of groups) to use with the instance
    required: false
    default: null
    aliases: [ 'groups' ]
  group_id:
    version_added: "1.1"
    description:
      - security group id (or list of ids) to use with the instance
    required: false
    default: null
    aliases: []
  region:
    version_added: "1.2"
    description:
      - The AWS region to use.  Must be specified if ec2_url is not used. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    default: null
    aliases: [ 'aws_region', 'ec2_region' ]
  zone:
    version_added: "1.2"
    description:
      - AWS availability zone in which to launch the instance
    required: false
    default: null
    aliases: [ 'aws_zone', 'ec2_zone' ]
  instance_type:
    description:
      - instance type to use for the instance
    required: true
    default: null
    aliases: []
  spot_price:
    version_added: "1.5"
    description:
      - Maximum spot price to bid, If not set a regular on-demand instance is requested. A spot request is made with this maximum bid. When it is filled, the instance is started.
    required: false
    default: null
    aliases: []
  image:
    description:
       - I(emi) (or I(ami)) to use for the instance
    required: true
    default: null
    aliases: []
  kernel:
    description:
      - kernel I(eki) to use for the instance
    required: false
    default: null
    aliases: []
  ramdisk:
    description:
      - ramdisk I(eri) to use for the instance
    required: false
    default: null
    aliases: []
  wait:
    description:
      - wait for the instance to be in state 'running' before returning
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    aliases: []
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
    aliases: []
  spot_wait_timeout:
    version_added: "1.5"
    description:
      - how long to wait for the spot instance request to be fulfilled
    default: 600
    aliases: []
  count:
    description:
      - number of instances to launch
    required: False
    default: 1
    aliases: []
  monitoring:
    version_added: "1.1"
    description:
      - enable detailed monitoring (CloudWatch) for instance
    required: false
    default: null
    aliases: []
  user_data:
    version_added: "0.9"
    description:
      - opaque blob of data which is made available to the ec2 instance
    required: false
    default: null
    aliases: []
  instance_tags:
    version_added: "1.0"
    description:
      - a hash/dictionary of tags to add to the new instance; '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: false
    default: null
    aliases: []
  placement_group:
    version_added: "1.3"
    description:
      - placement group for the instance when using EC2 Clustered Compute
    required: false
    default: null
    aliases: []
  vpc_subnet_id:
    version_added: "1.1"
    description:
      - the subnet ID in which to launch the instance (VPC)
    required: false
    default: null
    aliases: []
  assign_public_ip:
    version_added: "1.5"
    description:
      - when provisioning within vpc, assign a public IP address. Boto library must be 2.13.0+
    required: false
    default: null
    aliases: []
  private_ip:
    version_added: "1.2"
    description:
      - the private ip address to assign the instance (from the vpc subnet)
    required: false
    default: null
    aliases: []
  instance_profile_name:
    version_added: "1.3"
    description:
      - Name of the IAM instance profile to use. Boto library must be 2.5.0+
    required: false
    default: null
    aliases: []
  instance_ids:
    version_added: "1.3"
    description:
      - "list of instance ids, currently used for states: absent, running, stopped"
    required: false
    default: null
    aliases: []
  source_dest_check:
    version_added: "1.6"
    description:
      - Enable or Disable the Source/Destination checks (for NAT instances and Virtual Routers)
    required: false
    default: true
  state:
    version_added: "1.3"
    description:
      - create or terminate instances
    required: false
    default: 'present'
    aliases: []
    choices: ['present', 'absent', 'running', 'stopped']
  volumes:
    version_added: "1.5"
    description:
      - a list of volume dicts, each containing device name and optionally ephemeral id or snapshot id. Size and type (and number of iops for io device type) must be specified for a new volume or a root volume, and may be passed for a snapshot volume. For any volume, a volume size less than 1 will be interpreted as a request not to create the volume.
    required: false
    default: null
    aliases: []
  ebs_optimized:
    version_added: "1.6"
    description:
      - whether instance is using optimized EBS volumes, see U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSOptimized.html)
    required: false
    default: false
  exact_count:
    version_added: "1.5"
    description:
      - An integer value which indicates how many instances that match the 'count_tag' parameter should be running. Instances are either created or terminated based on this value. 
    required: false
    default: null
    aliases: []
  count_tag:
    version_added: "1.5"
    description:
      - Used with 'exact_count' to determine how many nodes based on a specific tag criteria should be running.  This can be expressed in multiple ways and is shown in the EXAMPLES section.  For instance, one can request 25 servers that are tagged with "class=webserver".  
    required: false
    default: null
    aliases: []

author: Seth Vidal, Tim Gerla, Lester Wade
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Basic provisioning example
- local_action:
    module: ec2
    key_name: mykey
    instance_type: c1.medium
    image: emi-40603AD1
    wait: yes
    group: webserver
    count: 3

# Advanced example with tagging and CloudWatch
- local_action:
    module: ec2
    key_name: mykey
    group: databases
    instance_type: m1.large
    image: ami-6e649707
    wait: yes
    wait_timeout: 500
    count: 5
    instance_tags: 
       db: postgres
    monitoring: yes

# Single instance with additional IOPS volume from snapshot and volume delete on termination
local_action:
    module: ec2
    key_name: mykey
    group: webserver
    instance_type: m1.large
    image: ami-6e649707
    wait: yes
    wait_timeout: 500
    volumes:
    - device_name: /dev/sdb
      snapshot: snap-abcdef12
      device_type: io1
      iops: 1000
      volume_size: 100
      delete_on_termination: true
    monitoring: yes

# Multiple groups example
local_action:
    module: ec2
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

# Multiple instances with additional volume from snapshot
local_action:
    module: ec2
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

# VPC example
- local_action:
    module: ec2
    key_name: mykey
    group_id: sg-1dc53f72
    instance_type: m1.small
    image: ami-6e649707
    wait: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Spot instance example
- local_action:
    module: ec2
    spot_price: 0.24
    spot_wait_timeout: 600
    keypair: mykey
    group_id: sg-1dc53f72
    instance_type: m1.small
    image: ami-6e649707
    wait: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

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
      local_action: ec2 key_name={{ keypair }} group={{ security_group }} instance_type={{ instance_type }} image={{ image }} wait=true region={{ region }}
      register: ec2
    - name: Add new instance to host group
      local_action: add_host hostname={{ item.public_ip }} groupname=launched
      with_items: ec2.instances
    - name: Wait for SSH to come up
      local_action: wait_for host={{ item.public_dns_name }} port=22 delay=60 timeout=320 state=started
      with_items: ec2.instances

- name: Configure instance(s)
  hosts: launched
  sudo: True
  gather_facts: True
  roles:
    - my_awesome_role
    - my_awesome_test

- name: Terminate instances
  hosts: localhost
  connection: local
  tasks:
    - name: Terminate instances that were previously launched
      local_action:
        module: ec2
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
      local_action:
        module: ec2
        instance_ids: '{{ instance_ids }}'
        region: '{{ region }}'
        state: running
        wait: True
  role:
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
      local_action:
      module: ec2
      instance_ids: '{{ instance_ids }}'
      region: '{{ region }}'
      state: stopped
      wait: True

#
# Enforce that 5 instances with a tag "foo" are running
#

- local_action:
    module: ec2
    key_name: mykey
    instance_type: c1.medium
    image: emi-40603AD1
    wait: yes
    group: webserver
    instance_tags:
        foo: bar
    exact_count: 5
    count_tag: foo

#
# Enforce that 5 running instances named "database" with a "dbtype" of "postgres"
#

- local_action:
    module: ec2
    key_name: mykey
    instance_type: c1.medium
    image: emi-40603AD1
    wait: yes
    group: webserver
    instance_tags: 
        Name: database
        dbtype: postgres
    exact_count: 5
    count_tag: 
        Name: database
        dbtype: postgres

#
# count_tag complex argument examples
#

    # instances with tag foo
    count_tag:
        foo:

    # instances with tag foo=bar
    count_tag:
        foo: bar

    # instances with tags foo=bar & baz
    count_tag:
        foo: bar
        baz:

    # instances with tags foo & bar & baz=bang
    count_tag:
        - foo
        - bar
        - baz: bang

'''

import sys
import time
from ast import literal_eval

try:
    import boto.ec2
    from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping
    from boto.exception import EC2ResponseError
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def find_running_instances_by_count_tag(module, ec2, count_tag, zone=None):

    # get reservations for instances that match tag(s) and are running
    reservations = get_reservations(module, ec2, tags=count_tag, state="running", zone=zone)

    instances = []
    for res in reservations:
        if hasattr(res, 'instances'):
            for inst in res.instances:
                instances.append(inst) 
                
    return reservations, instances


def _set_none_to_blank(dictionary):
    result = dictionary
    for k in result.iterkeys():
        if type(result[k]) == dict:
            result[k] = _set_none_to_blank(result[k])
        elif not result[k]:
            result[k] = ""
    return result                        


def get_reservations(module, ec2, tags=None, state=None, zone=None):

    # TODO: filters do not work with tags that have underscores
    filters = dict()

    if tags is not None:

        if type(tags) is str:
            try:
                tags = literal_eval(tags)
            except:
                pass

        # if string, we only care that a tag of that name exists
        if type(tags) is str:
            filters.update({"tag-key": tags})

        # if list, append each item to filters
        if type(tags) is list:
            for x in tags:
                if type(x) is dict:
                    x = _set_none_to_blank(x)
                    filters.update(dict(("tag:"+tn, tv) for (tn,tv) in x.iteritems()))
                else:
                    filters.update({"tag-key": x})

        # if dict, add the key and value to the filter
        if type(tags) is dict:
            tags = _set_none_to_blank(tags)
            filters.update(dict(("tag:"+tn, tv) for (tn,tv) in tags.iteritems()))

    if state:
        # http://stackoverflow.com/questions/437511/what-are-the-valid-instancestates-for-the-amazon-ec2-api
        filters.update({'instance-state-name': state})

    if zone:
        filters.update({'availability-zone': zone})

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
                     'hypervisor': inst.hypervisor}
    try:
        instance_info['virtualization_type'] = getattr(inst,'virtualization_type')
    except AttributeError:
        instance_info['virtualization_type'] = None

    try:
        instance_info['ebs_optimized'] = getattr(inst, 'ebs_optimized')
    except AttributeError:
        instance_info['ebs_optimized'] = False

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
    return 'instance_profile_name' in run_instances_method.func_code.co_varnames

def create_block_device(module, ec2, volume):
    # Not aware of a way to determine this programatically
    # http://aws.amazon.com/about-aws/whats-new/2013/10/09/ebs-provisioned-iops-maximum-iops-gb-ratio-increased-to-30-1/
    MAX_IOPS_TO_SIZE_RATIO = 30
    if 'snapshot' not in volume and 'ephemeral' not in volume:
        if 'volume_size' not in volume: 
            module.fail_json(msg = 'Size must be specified when creating a new volume or modifying the root volume')
    if 'snapshot' in volume:
        if 'device_type' in volume and volume.get('device_type') == 'io1' and 'iops' not in volume:
            module.fail_json(msg = 'io1 volumes must have an iops value set')
        if 'iops' in volume:
            snapshot = ec2.get_all_snapshots(snapshot_ids=[volume['snapshot']])[0]
            size = volume.get('volume_size', snapshot.volume_size)
            if int(volume['iops']) > MAX_IOPS_TO_SIZE_RATIO * size:
                module.fail_json(msg = 'IOPS must be at most %d times greater than size' % MAX_IOPS_TO_SIZE_RATIO)
    if 'ephemeral' in volume:
        if 'snapshot' in volume: 
            module.fail_json(msg = 'Cannot set both ephemeral and snapshot')
    return BlockDeviceType(snapshot_id=volume.get('snapshot'),
                           ephemeral_name=volume.get('ephemeral'),
                           size=volume.get('volume_size'),
                           volume_type=volume.get('device_type'),
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
    return param in method.func_code.co_varnames

def enforce_count(module, ec2):

    exact_count = module.params.get('exact_count')
    count_tag = module.params.get('count_tag')
    zone = module.params.get('zone')

    # fail here if the exact count was specified without filtering
    # on a tag, as this may lead to a undesired removal of instances
    if exact_count and count_tag is None:
        module.fail_json(msg="you must use the 'count_tag' option with exact_count")

    reservations, instances = find_running_instances_by_count_tag(module, ec2, count_tag, zone)

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
                = create_instances(module, ec2, override_count=to_create)

            for inst in instance_dict_array:
                instances.append(inst)
    elif len(instances) > exact_count:
        changed = True
        to_remove = len(instances) - exact_count
        if not checkmode:
            all_instance_ids = sorted([ x.id for x in instances ])
            remove_ids = all_instance_ids[0:to_remove]

            instances = [ x for x in instances if x.id not in remove_ids]

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
        if type(inst) is not dict:
            inst = get_instance_info(inst)
        all_instances.append(inst)            

    return (all_instances, instance_dict_array, changed_instance_ids, changed)
    
        
def create_instances(module, ec2, override_count=None):
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
    spot_price = module.params.get('spot_price')
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

    # group_id and group_name are exclusive of each other
    if group_id and group_name:
        module.fail_json(msg = str("Use only one type of parameter (group_name) or (group_id)"))
        sys.exit(1)

    try:
        # Here we try to lookup the group id from the security group name - if group is set.
        if group_name:
            grp_details = ec2.get_all_security_groups()
            if type(group_name) == list:
                group_id = [ str(grp.id) for grp in grp_details if str(grp.name) in group_name ]
            elif type(group_name) == str:
                for grp in grp_details:
                    if str(group_name) in str(grp):
                        group_id = [str(grp.id)]
                group_name = [group_name]
        # Now we try to lookup the group id testing if group exists.
        elif group_id:
            #wrap the group_id in a list if it's not one already
            if type(group_id) == str:
                group_id = [group_id]
            grp_details = ec2.get_all_security_groups(group_ids=group_id)
            grp_item = grp_details[0]
            group_name = [grp_item.name]
    except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))

    # Lookup any instances that much our run id.

    running_instances = []
    count_remaining = int(count)

    if id != None:
        filter_dict = {'client-token':id, 'instance-state-name' : 'running'}
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
                      'user_data': user_data}

            if ebs_optimized:
              params['ebs_optimized'] = ebs_optimized

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
                params['subnet_id'] = vpc_subnet_id
                if vpc_subnet_id:
                    params['security_group_ids'] = group_id
                else:
                    params['security_groups'] = group_name

            if volumes:
                bdm = BlockDeviceMapping()
                for volume in volumes: 
                    if 'device_name' not in volume:
                        module.fail_json(msg = 'Device name must be set for volume')
                    # Minimum volume size is 1GB. We'll use volume size explicitly set to 0
                    # to be a signal not to create this volume 
                    if 'volume_size' not in volume or int(volume['volume_size']) > 0:
                        bdm[volume['device_name']] = create_block_device(module, ec2, volume)

                params['block_device_map'] = bdm

            # check to see if we're using spot pricing first before starting instances
            if not spot_price:
                if assign_public_ip and private_ip:
                    params.update(dict(
                      min_count          = count_remaining,
                      max_count          = count_remaining,
                      client_token       = id,
                      placement_group    = placement_group,
                    ))
                else:
                    params.update(dict(
                      min_count          = count_remaining,
                      max_count          = count_remaining,
                      client_token       = id,
                      placement_group    = placement_group,
                      private_ip_address = private_ip,
                    ))

                res = ec2.run_instances(**params)
                instids = [ i.id for i in res.instances ]
                while True:
                    try:
                        ec2.get_all_instances(instids)
                        break
                    except boto.exception.EC2ResponseError as e:
                        if "<Code>InvalidInstanceID.NotFound</Code>" in str(e):
                            # there's a race between start and get an instance
                            continue
                        else:
                            module.fail_json(msg = str(e))
            else:
                if private_ip:
                    module.fail_json(
                        msg='private_ip only available with on-demand (non-spot) instances')
                if boto_supports_param_in_spot_request(ec2, placement_group):
                    params['placement_group'] = placement_group
                elif placement_group :
                        module.fail_json(
                            msg="placement_group parameter requires Boto version 2.3.0 or higher.")

                params.update(dict(
                    count = count_remaining,
                ))
                res = ec2.request_spot_instances(spot_price, **params)

                # Now we have to do the intermediate waiting
                if wait:
                    spot_req_inst_ids = dict()
                    spot_wait_timeout = time.time() + spot_wait_timeout
                    while spot_wait_timeout > time.time():
                        reqs = ec2.get_all_spot_instance_requests()
                        for sirb in res:
                            if sirb.id in spot_req_inst_ids:
                                continue
                            for sir in reqs:
                                if sir.id == sirb.id and sir.instance_id is not None:
                                    spot_req_inst_ids[sirb.id] = sir.instance_id
                        if len(spot_req_inst_ids) < count:
                            time.sleep(5)
                        else:
                            break
                    if spot_wait_timeout <= time.time():
                        module.fail_json(msg = "wait for spot requests timeout on %s" % time.asctime())
                    instids = spot_req_inst_ids.values()
        except boto.exception.BotoServerError, e:
            module.fail_json(msg = "Instance creation failed => %s: %s" % (e.error_code, e.error_message))

        # The instances returned through run_instances can be in
        # terminated state due to idempotency.
        terminated_instances = [ str(instance.id) for instance in res.instances
                                 if instance.state == 'terminated' ]
        if terminated_instances:
            module.fail_json(msg = "Instances with id(s) %s " % terminated_instances +
                                   "were created previously but have since been terminated - " +
                                   "use a (possibly different) 'instanceid' parameter")

        # wait here until the instances are up
        num_running = 0
        wait_timeout = time.time() + wait_timeout
        while wait_timeout > time.time() and num_running < len(instids):
            try: 
                res_list = ec2.get_all_instances(instids)
            except boto.exception.BotoServerError, e:
                if e.error_code == 'InvalidInstanceID.NotFound':
                    time.sleep(1)
                    continue
                else:
                    raise

            num_running = 0
            for res in res_list:
                num_running += len([ i for i in res.instances if i.state=='running' ])
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
            module.fail_json(msg = "wait for instances running timeout on %s" % time.asctime())

        #We do this after the loop ends so that we end up with one list
        for res in res_list:
            running_instances.extend(res.instances)

        # Enabled by default by Amazon
        if not source_dest_check:
            for inst in res.instances:
                inst.modify_attribute('sourceDestCheck', False)

        # Leave this as late as possible to try and avoid InvalidInstanceID.NotFound
        if instance_tags:
            try:
                ec2.create_tags(instids, instance_tags)
            except boto.exception.EC2ResponseError, e:
                module.fail_json(msg = "Instance tagging failed => %s: %s" % (e.error_code, e.error_message))

    instance_dict_array = []
    created_instance_ids = []
    for inst in running_instances:
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
                except EC2ResponseError, e:
                    module.fail_json(msg='Unable to terminate instance {0}, error: {1}'.format(inst.id, e))
                changed = True

    # wait here until the instances are 'terminated'
    if wait:
        num_terminated = 0
        wait_timeout = time.time() + wait_timeout
        while wait_timeout > time.time() and num_terminated < len(terminated_instance_ids):
            response = ec2.get_all_instances( \
                instance_ids=terminated_instance_ids, \
                filters={'instance-state-name':'terminated'})
            try:
                num_terminated = len(response.pop().instances)
            except Exception, e:
                # got a bad response of some sort, possibly due to
                # stale/cached data. Wait a second and then try again
                time.sleep(1)
                continue

            if num_terminated < len(terminated_instance_ids):
                time.sleep(5)

        # waiting took too long
        if wait_timeout < time.time() and num_terminated < len(terminated_instance_ids):
            module.fail_json(msg = "wait for instance termination timeout on %s" % time.asctime())

    return (changed, instance_dict_array, terminated_instance_ids)


def startstop_instances(module, ec2, instance_ids, state):
    """
    Starts or stops a list of existing instances

    module: Ansible module object
    ec2: authenticated ec2 connection object
    instance_ids: The list of instances to start in the form of
      [ {id: <inst-id>}, ..]
    state: Intended state ("running" or "stopped")

    Returns a dictionary of instance information
    about the instances started/stopped.

    If the instance was not able to change state,
    "changed" will be set to False.

    """
    
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    changed = False
    instance_dict_array = []
    
    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        module.fail_json(msg='instance_ids should be a list of instances, aborting')

    # Check that our instances are not in the state we want to take them to
    # and change them to our desired state
    running_instances_array = []
    for res in ec2.get_all_instances(instance_ids):
        for inst in res.instances:
           if inst.state != state:
               instance_dict_array.append(get_instance_info(inst))
               try:
                   if state == 'running':
                       inst.start()
                   else:
                       inst.stop()
               except EC2ResponseError, e:
                   module.fail_json(msg='Unable to change state for instance {0}, error: {1}'.format(inst.id, e))
               changed = True

    ## Wait for all the instances to finish starting or stopping
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
        module.fail_json(msg = "wait for instances running timeout on %s" % time.asctime())

    return (changed, instance_dict_array, instance_ids)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            key_name = dict(aliases = ['keypair']),
            id = dict(),
            group = dict(type='list'),
            group_id = dict(type='list'),
            zone = dict(aliases=['aws_zone', 'ec2_zone']),
            instance_type = dict(aliases=['type']),
            spot_price = dict(),
            image = dict(),
            kernel = dict(),
            count = dict(type='int', default='1'),
            monitoring = dict(type='bool', default=False),
            ramdisk = dict(),
            wait = dict(type='bool', default=False),
            wait_timeout = dict(default=300),
            spot_wait_timeout = dict(default=600),
            placement_group = dict(),
            user_data = dict(),
            instance_tags = dict(type='dict'),
            vpc_subnet_id = dict(),
            assign_public_ip = dict(type='bool', default=False),
            private_ip = dict(),
            instance_profile_name = dict(),
            instance_ids = dict(type='list'),
            source_dest_check = dict(type='bool', default=True),
            state = dict(default='present'),
            exact_count = dict(type='int', default=None),
            count_tag = dict(),
            volumes = dict(type='list'),
            ebs_optimized = dict(type='bool', default=False),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive = [
                                ['exact_count', 'count'],
                                ['exact_count', 'state'],
                                ['exact_count', 'instance_ids']
                             ],
    )

    ec2 = ec2_connect(module)

    tagged_instances = [] 

    state = module.params.get('state')

    if state == 'absent':
        instance_ids = module.params.get('instance_ids')
        if not isinstance(instance_ids, list):
            module.fail_json(msg='termination_list needs to be a list of instances to terminate')

        (changed, instance_dict_array, new_instance_ids) = terminate_instances(module, ec2, instance_ids)

    elif state in ('running', 'stopped'):
        instance_ids = module.params.get('instance_ids')
        if not isinstance(instance_ids, list):
            module.fail_json(msg='running list needs to be a list of instances to run: %s' % instance_ids)

        (changed, instance_dict_array, new_instance_ids) = startstop_instances(module, ec2, instance_ids, state)

    elif state == 'present':
        # Changed is always set to true when provisioning new instances
        if not module.params.get('image'):
            module.fail_json(msg='image parameter is required for new instance')

        if module.params.get('exact_count') is None:
            (instance_dict_array, new_instance_ids, changed) = create_instances(module, ec2)
        else:
            (tagged_instances, instance_dict_array, new_instance_ids, changed) = enforce_count(module, ec2)

    module.exit_json(changed=changed, instance_ids=new_instance_ids, instances=instance_dict_array, tagged_instances=tagged_instances)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
