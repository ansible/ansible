#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_elb_facts
short_description: Gather facts about EC2 Elastic Load Balancers in AWS
description:
    - Gather facts about EC2 Elastic Load Balancers in AWS
version_added: "2.0"
author: "Michael Schultz (github.com/mjschultz)"
options:
  names:
    description:
      - List of ELB names to gather facts about. Pass this option to gather facts about a set of ELBs, otherwise, all ELBs are returned.
    required: false
    default: null
    aliases: ['elb_ids', 'ec2_elbs']
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Output format tries to match ec2_elb_lb module input parameters

# Gather facts about all ELBs
- action:
    module: ec2_elb_facts
  register: elb_facts

- action:
    module: debug
    msg: "{{ item.dns_name }}"
  with_items: elb_facts.elbs

# Gather facts about a particular ELB
- action:
    module: ec2_elb_facts
    names: frontend-prod-elb
  register: elb_facts

- action:
    module: debug
    msg: "{{ elb_facts.elbs.0.dns_name }}"

# Gather facts about a set of ELBs
- action:
    module: ec2_elb_facts
    names:
    - frontend-prod-elb
    - backend-prod-elb
  register: elb_facts

- action:
    module: debug
    msg: "{{ item.dns_name }}"
  with_items: elb_facts.elbs

'''

import xml.etree.ElementTree as ET

try:
    import boto.ec2.elb
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def get_error_message(xml_string):

    root = ET.fromstring(xml_string)
    for message in root.findall('.//Message'):
        return message.text


def get_elb_listeners(listeners):
    listener_list = []
    for listener in listeners:
        listener_dict = {
            'load_balancer_port': listener[0],
            'instance_port': listener[1],
            'protocol': listener[2],
        }
        try:
            ssl_certificate_id = listener[4]
        except IndexError:
            pass
        else:
            if ssl_certificate_id:
                listener_dict['ssl_certificate_id'] = ssl_certificate_id
        listener_list.append(listener_dict)

    return listener_list


def get_health_check(health_check):
    protocol, port_path = health_check.target.split(':')
    try:
        port, path = port_path.split('/')
        path = '/{}'.format(path)
    except ValueError:
        port = port_path
        path = None

    health_check_dict = {
        'ping_protocol': protocol.lower(),
        'ping_port': int(port),
        'response_timeout': health_check.timeout,
        'interval': health_check.interval,
        'unhealthy_threshold': health_check.unhealthy_threshold,
        'healthy_threshold': health_check.healthy_threshold,
    }
    if path:
        health_check_dict['ping_path'] = path
    return health_check_dict


def get_elb_info(elb):
    elb_info = {
        'name': elb.name,
        'zones': elb.availability_zones,
        'dns_name': elb.dns_name,
        'instances': [instance.id for instance in elb.instances],
        'listeners': get_elb_listeners(elb.listeners),
        'scheme': elb.scheme,
        'security_groups': elb.security_groups,
        'health_check': get_health_check(elb.health_check),
        'subnets': elb.subnets,
    }
    if elb.vpc_id:
        elb_info['vpc_id'] = elb.vpc_id

    return elb_info


def list_elb(connection, module):
    elb_names = module.params.get("names")
    if not elb_names:
        elb_names = None

    try:
        all_elbs = connection.get_all_load_balancers(elb_names)
    except BotoServerError as e:
        module.fail_json(msg=get_error_message(e.args[2]))

    elb_array = []
    for elb in all_elbs:
        elb_array.append(get_elb_info(elb))

    module.exit_json(elbs=elb_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            names={'default': None, 'type': 'list'}
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.ec2.elb, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, StandardError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    list_elb(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
