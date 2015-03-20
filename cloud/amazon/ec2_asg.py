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
DOCUMENTATION = """
---
module: ec2_asg
short_description: Create or delete AWS Autoscaling Groups
description:
  - Can create or delete AWS Autoscaling Groups
  - Works with the ec2_lc module to manage Launch Configurations
version_added: "1.6"
author: Gareth Rushgrove
options:
  state:
    description:
      - register or deregister the instance
    required: true
    choices: ['present', 'absent']
  name:
    description:
      - Unique name for group to be created or deleted
    required: true
  load_balancers:
    description:
      - List of ELB names to use for the group
    required: false
  availability_zones:
    description:
      - List of availability zone names in which to create the group.  Defaults to all the availability zones in the region if vpc_zone_identifier is not set.
    required: false
  launch_config_name:
    description:
      - Name of the Launch configuration to use for the group. See the ec2_lc module for managing these.
    required: false
  min_size:
    description:
      - Minimum number of instances in group
    required: false
  max_size:
    description:
      - Maximum number of instances in group
    required: false
  desired_capacity:
    description:
      - Desired number of instances in group
    required: false
  replace_all_instances:
    description:
      - In a rolling fashion, replace all instances with an old launch configuration with one from the current launch configuraiton.
    required: false
    version_added: "1.8"
    default: False
  replace_batch_size:
    description:
      - Number of instances you'd like to replace at a time.  Used with replace_all_instances.
    required: false
    version_added: "1.8"
    default: 1  
  replace_instances:
    description:
      - List of instance_ids belonging to the named ASG that you would like to terminate and be replaced with instances matching the current launch configuration.
    required: false
    version_added: "1.8"
    default: None
  lc_check:
    description:
      - Check to make sure instances that are being replaced with replace_instances do not aready have the current launch_config.
    required: false
    version_added: "1.8"
    default: True
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    aliases: ['aws_region', 'ec2_region']
  vpc_zone_identifier:
    description:
      - List of VPC subnets to use
    required: false
    default: None
  tags:
    description:
      - A list of tags to add to the Auto Scale Group. Optional key is 'propagate_at_launch', which defaults to true.
    required: false
    default: None
    version_added: "1.7"
  health_check_period:
    description:
      - Length of time in seconds after a new EC2 instance comes into service that Auto Scaling starts checking its health.
    required: false
    default: 500 seconds
    version_added: "1.7"
  health_check_type:
    description:
      - The service you want the health status from, Amazon EC2 or Elastic Load Balancer.
    required: false
    default: EC2
    version_added: "1.7"
    choices: ['EC2', 'ELB']
  wait_timeout:
    description:
      - how long before wait instances to become viable when replaced.  Used in concjunction with instance_ids option.
    default: 300
    version_added: "1.8"
  wait_for_instances:
    description:
      - Wait for the ASG instances to be in a ready state before exiting.  If instances are behind an ELB, it will wait until the instances are considered by the ELB.
    version_added: "1.9"
    default: yes
    required: False
extends_documentation_fragment: aws
"""

EXAMPLES = '''
# Basic configuration

- ec2_asg:
    name: special
    load_balancers: [ 'lb1', 'lb2' ]
    availability_zones: [ 'eu-west-1a', 'eu-west-1b' ]
    launch_config_name: 'lc-1'
    min_size: 1
    max_size: 10
    desired_capacity: 5
    vpc_zone_identifier: [ 'subnet-abcd1234', 'subnet-1a2b3c4d' ]
    tags:
      - environment: production
        propagate_at_launch: no

# Rolling ASG Updates

Below is an example of how to assign a new launch config to an ASG and terminate old instances.  

All instances in "myasg" that do not have the launch configuration named "my_new_lc" will be terminated in 
a rolling fashion with instances using the current launch configuration, "my_new_lc".

This could also be considered a rolling deploy of a pre-baked AMI.

If this is a newly created group, the instances will not be replaced since all instances
will have the current launch configuration.

- name: create launch config
  ec2_lc:
    name: my_new_lc
    image_id: ami-lkajsf
    key_name: mykey
    region: us-east-1
    security_groups: sg-23423
    instance_type: m1.small
    assign_public_ip: yes

- ec2_asg:
    name: myasg
    launch_config_name: my_new_lc
    health_check_period: 60
    health_check_type: ELB
    replace_all_instances: yes
    min_size: 5
    max_size: 5
    desired_capacity: 5
    region: us-east-1

To only replace a couple of instances instead of all of them, supply a list
to "replace_instances":

- ec2_asg:
    name: myasg
    launch_config_name: my_new_lc
    health_check_period: 60
    health_check_type: ELB
    replace_instances:
    - i-b345231
    - i-24c2931
    min_size: 5
    max_size: 5
    desired_capacity: 5
    region: us-east-1
'''

import sys
import time

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

try:
    import boto.ec2.autoscale
    from boto.ec2.autoscale import AutoScaleConnection, AutoScalingGroup, Tag
    from boto.exception import BotoServerError
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

ASG_ATTRIBUTES = ('availability_zones', 'default_cooldown', 'desired_capacity',
    'health_check_period', 'health_check_type', 'launch_config_name',
    'load_balancers', 'max_size', 'min_size', 'name', 'placement_group',
    'termination_policies', 'vpc_zone_identifier')

INSTANCE_ATTRIBUTES = ('instance_id', 'health_status', 'lifecycle_state', 'launch_config_name')

def enforce_required_arguments(module):
    ''' As many arguments are not required for autoscale group deletion
        they cannot be mandatory arguments for the module, so we enforce
        them here '''
    missing_args = []
    for arg in ('min_size', 'max_size', 'launch_config_name'):
        if module.params[arg] is None:
            missing_args.append(arg)
    if missing_args:
        module.fail_json(msg="Missing required arguments for autoscaling group create/update: %s" % ",".join(missing_args))


def get_properties(autoscaling_group):
    properties = dict((attr, getattr(autoscaling_group, attr)) for attr in ASG_ATTRIBUTES)

    # Ugly hack to make this JSON-serializable.  We take a list of boto Tag
    # objects and replace them with a dict-representation.  Needed because the
    # tags are included in ansible's return value (which is jsonified)
    if 'tags' in properties and isinstance(properties['tags'], list):
        serializable_tags = {}
        for tag in properties['tags']:
            serializable_tags[tag.key] = [tag.value, tag.propagate_at_launch]
        properties['tags'] = serializable_tags

    properties['healthy_instances'] = 0
    properties['in_service_instances'] = 0
    properties['unhealthy_instances'] = 0
    properties['pending_instances'] = 0
    properties['viable_instances'] = 0
    properties['terminating_instances'] = 0

    if autoscaling_group.instances:
        properties['instances'] = [i.instance_id for i in autoscaling_group.instances]
        instance_facts = {}
        for i in autoscaling_group.instances:
            instance_facts[i.instance_id] = {'health_status': i.health_status,
                                            'lifecycle_state': i.lifecycle_state,
                                            'launch_config_name': i.launch_config_name }
            if i.health_status == 'Healthy' and i.lifecycle_state == 'InService':
                properties['viable_instances'] += 1
            if i.health_status == 'Healthy':
                properties['healthy_instances'] += 1
            else:
                properties['unhealthy_instances'] += 1
            if i.lifecycle_state == 'InService':
                properties['in_service_instances'] += 1
            if i.lifecycle_state == 'Terminating':
                properties['terminating_instances'] += 1
            if i.lifecycle_state == 'Pending':
                properties['pending_instances'] += 1
        properties['instance_facts'] = instance_facts
    properties['load_balancers'] = autoscaling_group.load_balancers

    if getattr(autoscaling_group, "tags", None):
        properties['tags'] = dict((t.key, t.value) for t in autoscaling_group.tags)

    return properties


def wait_for_elb(asg_connection, module, group_name):
    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    wait_timeout = module.params.get('wait_timeout')

    # if the health_check_type is ELB, we want to query the ELBs directly for instance
    # status as to avoid health_check_grace period that is awarded to ASG instances
    as_group = asg_connection.get_all_groups(names=[group_name])[0]

    if as_group.load_balancers and as_group.health_check_type == 'ELB':
        try:
            elb_connection = connect_to_aws(boto.ec2.elb, region, **aws_connect_params)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg=str(e))

        wait_timeout = time.time() + wait_timeout
        healthy_instances = {}

        while len(healthy_instances.keys()) < as_group.min_size and wait_timeout > time.time():
            as_group = asg_connection.get_all_groups(names=[group_name])[0]
            props = get_properties(as_group)
            # get healthy, inservice instances from ASG
            instances = []
            for instance, settings in props['instance_facts'].items():
                if settings['lifecycle_state'] == 'InService' and settings['health_status'] == 'Healthy':
                    instances.append(instance)
            for lb in as_group.load_balancers:
                # we catch a race condition that sometimes happens if the instance exists in the ASG
                # but has not yet show up in the ELB
                try:
                    lb_instances = elb_connection.describe_instance_health(lb, instances=instances)
                except boto.exception.InvalidInstance, e:
                    pass
                for i in lb_instances:
                    if i.state == "InService":
                        healthy_instances[i.instance_id] = i.state
            time.sleep(10)
        if wait_timeout <= time.time():
        # waiting took too long
            module.fail_json(msg = "Waited too long for ELB instances to be healthy. %s" % time.asctime())

def create_autoscaling_group(connection, module):
    group_name = module.params.get('name')
    load_balancers = module.params['load_balancers']
    availability_zones = module.params['availability_zones']
    launch_config_name = module.params.get('launch_config_name')
    min_size = module.params['min_size']
    max_size = module.params['max_size']
    desired_capacity = module.params.get('desired_capacity')
    vpc_zone_identifier = module.params.get('vpc_zone_identifier')
    set_tags = module.params.get('tags')
    health_check_period = module.params.get('health_check_period')
    health_check_type = module.params.get('health_check_type')
    wait_for_instances = module.params.get('wait_for_instances')
    as_groups = connection.get_all_groups(names=[group_name])
    wait_timeout = module.params.get('wait_timeout')

    if not vpc_zone_identifier and not availability_zones:
        region, ec2_url, aws_connect_params = get_aws_connection_info(module)
        try:
            ec2_connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    elif vpc_zone_identifier:
        vpc_zone_identifier = ','.join(vpc_zone_identifier)

    asg_tags = []
    for tag in set_tags:
        for k,v in tag.iteritems():
            if k !='propagate_at_launch':
                asg_tags.append(Tag(key=k,
                     value=v,
                     propagate_at_launch=bool(tag.get('propagate_at_launch', True)),
                     resource_id=group_name))

    if not as_groups:
        if not vpc_zone_identifier and not availability_zones:
            availability_zones = module.params['availability_zones'] = [zone.name for zone in ec2_connection.get_all_zones()]
        enforce_required_arguments(module)
        launch_configs = connection.get_all_launch_configurations(names=[launch_config_name])
        ag = AutoScalingGroup(
                 group_name=group_name,
                 load_balancers=load_balancers,
                 availability_zones=availability_zones,
                 launch_config=launch_configs[0],
                 min_size=min_size,
                 max_size=max_size,
                 desired_capacity=desired_capacity,
                 vpc_zone_identifier=vpc_zone_identifier,
                 connection=connection,
                 tags=asg_tags,
                 health_check_period=health_check_period,
                 health_check_type=health_check_type)

        try:
            connection.create_auto_scaling_group(ag)
            if wait_for_instances == True:
                wait_for_new_instances(module, connection, group_name, wait_timeout, desired_capacity, 'viable_instances')
                wait_for_elb(connection, module, group_name)
            as_group = connection.get_all_groups(names=[group_name])[0]
            asg_properties = get_properties(as_group)
            changed = True
            return(changed, asg_properties)
        except BotoServerError, e:
            module.fail_json(msg=str(e))
    else:
        as_group = as_groups[0]
        changed = False
        for attr in ASG_ATTRIBUTES:
            if module.params.get(attr, None) is not None:
                module_attr = module.params.get(attr)
                if attr == 'vpc_zone_identifier':
                    module_attr = ','.join(module_attr)
                group_attr = getattr(as_group, attr)
                # we do this because AWS and the module may return the same list
                # sorted differently
                try:
                    module_attr.sort()
                except:
                    pass
                try:
                    group_attr.sort()
                except:
                    pass
                if group_attr != module_attr:
                    changed = True
                    setattr(as_group, attr, module_attr)

        if len(set_tags) > 0:
            have_tags = {}
            want_tags = {}

            for tag in asg_tags:
                want_tags[tag.key] = [tag.value, tag.propagate_at_launch]

            dead_tags = []
            for tag in as_group.tags:
                have_tags[tag.key] = [tag.value, tag.propagate_at_launch]
                if not tag.key in want_tags:
                    changed = True
                    dead_tags.append(tag)

            if dead_tags != []:
                connection.delete_tags(dead_tags)

            if have_tags != want_tags:
                changed = True
                connection.create_or_update_tags(asg_tags)

        # handle loadbalancers separately because None != []
        load_balancers = module.params.get('load_balancers') or []
        if load_balancers and as_group.load_balancers != load_balancers:
            changed = True
            as_group.load_balancers = module.params.get('load_balancers')


        if changed:
            try:
                as_group.update()
            except BotoServerError, e:
                module.fail_json(msg=str(e))

        if wait_for_instances == True:
            wait_for_new_instances(module, connection, group_name, wait_timeout, desired_capacity, 'viable_instances')
            wait_for_elb(connection, module, group_name)
        try:
            as_group = connection.get_all_groups(names=[group_name])[0]
            asg_properties = get_properties(as_group)
        except BotoServerError, e:
            module.fail_json(msg=str(e))
        return(changed, asg_properties)


def delete_autoscaling_group(connection, module):
    group_name = module.params.get('name')
    groups = connection.get_all_groups(names=[group_name])
    if groups:
        group = groups[0]
        group.max_size = 0
        group.min_size = 0
        group.desired_capacity = 0
        group.update()
        instances = True
        while instances:
            tmp_groups = connection.get_all_groups(names=[group_name])
            if tmp_groups:
                tmp_group = tmp_groups[0]
                if not tmp_group.instances:
                   instances = False
            time.sleep(10)

        group.delete()
        while len(connection.get_all_groups(names=[group_name])):
            time.sleep(5)
        changed=True
        return changed
    else:
        changed=False
        return changed

def get_chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def replace(connection, module):
    batch_size = module.params.get('replace_batch_size')
    wait_timeout = module.params.get('wait_timeout')
    group_name = module.params.get('name')
    max_size =  module.params.get('max_size')
    min_size =  module.params.get('min_size')
    desired_capacity =  module.params.get('desired_capacity')

    # FIXME: we need some more docs about this feature
    replace_instances = module.params.get('replace_instances')

    as_group = connection.get_all_groups(names=[group_name])[0]
    wait_for_new_instances(module, connection, group_name, wait_timeout, as_group.min_size, 'viable_instances')
    props = get_properties(as_group)
    instances = props['instances']
    replaceable = 0
    if replace_instances:
        instances = replace_instances
    for k in props['instance_facts'].keys():
        if k in instances:
          if  props['instance_facts'][k]['launch_config_name'] != props['launch_config_name']:
              replaceable += 1
    if replaceable == 0:
        changed = False
        return(changed, props)
        
    # set temporary settings and wait for them to be reached
    as_group = connection.get_all_groups(names=[group_name])[0]
    as_group.max_size = max_size + batch_size
    as_group.min_size = min_size + batch_size
    as_group.desired_capacity = desired_capacity + batch_size
    as_group.update()
    wait_for_new_instances(module, connection, group_name, wait_timeout, as_group.min_size, 'viable_instances')
    wait_for_elb(connection, module, group_name)
    as_group = connection.get_all_groups(names=[group_name])[0]
    props = get_properties(as_group)
    instances = props['instances']
    if replace_instances:
        instances = replace_instances
    for i in get_chunks(instances, batch_size):
        terminate_batch(connection, module, i)
        wait_for_new_instances(module, connection, group_name, wait_timeout, as_group.min_size, 'viable_instances')
        wait_for_elb(connection, module, group_name)
        as_group = connection.get_all_groups(names=[group_name])[0]
    # return settings to normal
    as_group.max_size = max_size 
    as_group.min_size = min_size 
    as_group.desired_capacity = desired_capacity
    as_group.update()
    as_group = connection.get_all_groups(names=[group_name])[0]
    asg_properties = get_properties(as_group)
    changed=True
    return(changed, asg_properties)

def terminate_batch(connection, module, replace_instances):
    group_name = module.params.get('name')
    wait_timeout = int(module.params.get('wait_timeout'))
    lc_check = module.params.get('lc_check')

    as_group = connection.get_all_groups(names=[group_name])[0]
    props = get_properties(as_group)

    # check to make sure instances given are actually in the given ASG
    # and they have a non-current launch config
    old_instances = []
    instances = ( inst_id for inst_id in replace_instances if inst_id in props['instances'])

    if lc_check:
        for i in instances:
           if props['instance_facts'][i]['launch_config_name']  != props['launch_config_name']:
                old_instances.append(i)
    else:
        old_instances = instances

    # set all instances given to unhealthy
    for instance_id in old_instances:
        connection.set_instance_health(instance_id,'Unhealthy')
    
    # we wait to make sure the machines we marked as Unhealthy are
    # no longer in the list

    count = 1
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and count > 0:
        count = 0
        as_group = connection.get_all_groups(names=[group_name])[0]
        props = get_properties(as_group)
        instance_facts = props['instance_facts']
        instances = ( i for i in instance_facts if i in old_instances)
        for i in instances:
            if  ( instance_facts[i]['lifecycle_state'] == 'Terminating'
                 or instance_facts[i]['health_status'] == 'Unhealthy' ):
                count += 1
        time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "Waited too long for old instances to terminate. %s" % time.asctime())

def wait_for_new_instances(module, connection, group_name, wait_timeout, desired_size, prop):

    # make sure we have the latest stats after that last loop.
    as_group = connection.get_all_groups(names=[group_name])[0]
    props = get_properties(as_group)
    # now we make sure that we have enough instances in a viable state
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and desired_size > props[prop]:
        time.sleep(10)
        as_group = connection.get_all_groups(names=[group_name])[0]
        props = get_properties(as_group)
    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "Waited too long for new instances to become viable. %s" % time.asctime())

    return props

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            load_balancers=dict(type='list'),
            availability_zones=dict(type='list'),
            launch_config_name=dict(type='str'),
            min_size=dict(type='int'),
            max_size=dict(type='int'),
            desired_capacity=dict(type='int'),
            vpc_zone_identifier=dict(type='list'),
            replace_batch_size=dict(type='int', default=1),
            replace_all_instances=dict(type='bool', default=False),
            replace_instances=dict(type='list', default=[]),
            lc_check=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=300),
            state=dict(default='present', choices=['present', 'absent']),
            tags=dict(type='list', default=[]),
            health_check_period=dict(type='int', default=300),
            health_check_type=dict(default='EC2', choices=['EC2', 'ELB']),
            wait_for_instances=dict(type='bool', default=True)
        ),
    )
    
    module = AnsibleModule(
        argument_spec=argument_spec, 
        mutually_exclusive = [['replace_all_instances', 'replace_instances']]
    )
    state = module.params.get('state')
    replace_instances = module.params.get('replace_instances')
    replace_all_instances = module.params.get('replace_all_instances')
    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    try:
        connection = connect_to_aws(boto.ec2.autoscale, region, **aws_connect_params)
        if not connection:
            module.fail_json(msg="failed to connect to AWS for the given region: %s" % str(region))
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg=str(e))
    changed = create_changed = replace_changed = False

    if state == 'present':
        create_changed, asg_properties=create_autoscaling_group(connection, module)
    elif state == 'absent':
       changed = delete_autoscaling_group(connection, module)
       module.exit_json( changed = changed )
    if replace_all_instances or replace_instances:
        replace_changed, asg_properties=replace(connection, module)
    if create_changed or replace_changed:
        changed = True
    module.exit_json( changed = changed, **asg_properties )


main()
