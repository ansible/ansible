#!/usr/bin/env python

DOCUMENTATION = '''
---
inventory: consul_inventory
short_description: Consul external inventory script
description:
  - Generates inventory that Ansible can understand by making API request to Consul API
  - Additionally will gather data from ec2, using pieces of the EC2 external inventory.
  - |
    When run against a specific host, this script returns the following variables:
        Node:
            - Address
            - Node
        Services:
            - Name:
                - ID
                - Port
                - Service
                - Tags
        cluster
        consul_ui
        ec2__in_monitoring_element
        ec2_ami_launch_index
        ec2_architecture
        ec2_client_token"
        ec2_dns_name
        ec2_ebs_optimized
        ec2_eventsSet
        ec2_group_name
        ec2_hypervisor
        ec2_id
        ec2_image_id
        ec2_instance_profile
        ec2_instance_type
        ec2_ip_address
        ec2_item
        ec2_kernel
        ec2_key_name
        ec2_launch_time
        ec2_monitored
        ec2_monitoring
        ec2_monitoring_state
        ec2_persistent
        ec2_placement
        ec2_platform
        ec2_previous_state
        ec2_previous_state_code
        ec2_private_dns_name
        ec2_private_ip_address
        ec2_public_dns_name
        ec2_ramdisk
        ec2_reason
        ec2_region
        ec2_requester_id
        ec2_root_device_name
        ec2_root_device_type
        ec2_security_group_ids
        ec2_security_group_names
        ec2_sourceDestCheck
        ec2_spot_instance_request_id
        ec2_state
        ec2_state_code
        ec2_state_reason
        ec2_subnet_id
        ec2_tag_Name
        ec2_tag_cluster
        ec2_tag_consul
        ec2_virtualization_type
        ec2_vpc_id

    where some item can have nested structure.
version_added: None
authors:
  - Matthew Finlayson <matthew.finlayson@jivesoftware.com>
notes:
requirements: [ "consulate", "boto" ]
examples:
    - description: List server instances
      code: consul_inventory_bad.py --list
    - description: Get server details for server named "server.example.com"
      code: consul_inventory_bad.py --host server.example.com
'''

import sys
import re
import os

import argparse
import collections

try:
    import json
except ImportError:
    import simplejson as json

try:
    import consulate
except ImportError:
    print('consulate required for this module')
    sys.exit(1)

try:
    import boto.ec2
except ImportError:
    print('boto required for this module')
    sys.exit(1)

class Node(object):
    def __init__(self, ec2, services):
        self.ec2 = ec2
        self.services = services

def get_connection():
    return boto.ec2.connect_to_region(os.environ['AWS_REGION'], aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])


def get_host_info_from_ip(ip):
    conn = get_connection()
    instance = conn.get_only_instances(filters={'ip-address': ip})[0]

    instance_vars = {}
    for key in vars(instance):
        value = getattr(instance, key)
        key = to_safe('ec2_' + key)

        # Handle complex types
        # state/previous_state changed to properties in boto in https://github.com/boto/boto/commit/a23c379837f698212252720d2af8dec0325c9518
        if key == 'ec2__state':
            instance_vars['ec2_state'] = instance.state or ''
            instance_vars['ec2_state_code'] = instance.state_code
        elif key == 'ec2__previous_state':
            instance_vars['ec2_previous_state'] = instance.previous_state or ''
            instance_vars['ec2_previous_state_code'] = instance.previous_state_code
        elif type(value) in [int, bool]:
            instance_vars[key] = value
        elif type(value) in [str, unicode]:
            instance_vars[key] = value.strip()
        elif type(value) == type(None):
            instance_vars[key] = ''
        elif key == 'ec2_region':
            instance_vars[key] = value.name
        elif key == 'ec2__placement':
            instance_vars['ec2_placement'] = value.zone
        elif key == 'ec2_tags':
            for k, v in value.iteritems():
                key = to_safe('ec2_tag_' + k)
                instance_vars[key] = v
        elif key == 'ec2_groups':
            group_ids = []
            group_names = []
            for group in value:
                group_ids.append(group.id)
                group_names.append(group.name)
            instance_vars["ec2_security_group_ids"] = ','.join(group_ids)
            instance_vars["ec2_security_group_names"] = ','.join(group_names)
        else:
            pass

    return instance_vars


def to_safe(word):
    ''' Converts 'bad' characters in a string to underscores so they can be
    used as Ansible groups '''

    return re.sub("[^A-Za-z0-9\-]", "_", word)

def host(instance, session, cluster):
    hostvars = {}

    hostvars.update(get_host_info_from_ip(instance.ip_address))
    hostvars.update(session.catalog.node(instance.ip_address))
    hostvars['cluster'] = cluster
    hostvars['consul_ui'] = session._host
    print(json.dumps(hostvars, sort_keys=True, indent=4))


def _list(sessions):
    hostvars = collections.defaultdict(dict)

    groups = {
        'consul_servers': [],
        'consul_ui': [],
        'healthy': [],
        'unhealthy': [],
        'zookeeper': [],
        'kafka': [],
        'miru': [],
        'sensei': [],
        'fe': [],
        'dp': []
    }

    for session in sessions:
        for node in session.catalog.nodes():
            detail = session.catalog.node(node['Node'])
            ip_address = detail['Node']['Node']

            host_detail = get_host_info_from_ip(ip_address)
            host_detail.update(detail['Services'])

            hostvars[ip_address] = host_detail

            if host_detail['ec2_tag_consul'] == 'ui':
                groups['consul_ui'].append(ip_address)
            elif host_detail['ec2_tag_consul'] == 'server':
                groups['consul_servers'].append(ip_address)
            elif host_detail['ec2_tag_consul'] == 'agent':
                groups['consul_agents'].append(ip_address)

    if hostvars:
        groups['_meta'] = {'hostvars': hostvars}
    print(json.dumps(groups, sort_keys=True, indent=4))


def parse_args():
    parser = argparse.ArgumentParser(description='Ansible Consul inventory module')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--list', action='store_true', help='List active servers', default=True)
    group.add_argument('--host', help='List details about the specific host')
    return parser.parse_args()


def setup_list():
    conn = get_connection()
    sessions = []
    for instance in conn.get_only_instances(filters={'instance-state-name': 'running', 'tag:consul': 'ui'}):
        try:
            sessions.append(consulate.Consulate(host=instance.ip_address))
        except Exception, e:
            sys.stderr.write("%s: %s\n" % (e, e.message))
            print(json.dumps({}, sort_keys=True, indent=4))
            sys.exit(1)
    return sessions


def setup_host(host_input):
    conn = get_connection()

    if re.match("(^[2][0-5][0-5]|^[1]{0,1}[0-9]{1,2})\.([0-2][0-5][0-5]|[1]{0,1}[0-9]{1,2})\.([0-2][0-5][0-5]|[1]{0,1}[0-9]{1,2})\.([0-2][0-5][0-5]|[1]{0,1}[0-9]{1,2})$", host_input) is not None:
        instances = conn.get_only_instances(filters={'instance-state-name': 'running', 'ip-address': host_input})
    else:
        instances = conn.get_only_instances(filters={'instance-state-name': 'running', 'dns-name': host_input})

    if len(instances) != 1:
        print(json.dumps({}, sort_keys=True, indent=4))
        sys.exit(1)
    else:
        instance = instances[0]

    if 'cluster' in instance.tags:
        cluster = instance.tags['cluster']

    sessions = []
    for consul in conn.get_only_instances(filters={'instance-state-name': 'running', 'tag:consul': 'ui', 'tag:cluster': cluster}):
        try:
            sessions.append(consulate.Consulate(host=consul.ip_address))
        except Exception, e:
            sys.stderr.write("%s: %s\n" % (e, e.message))
            print(json.dumps({}, sort_keys=True, indent=4))
            sys.exit(1)

    if len(sessions) != 1:
        print(json.dumps({}, sort_keys=True, indent=4))
        sys.exit(1)
    else:
        session = sessions[0]

    return instance, session, cluster



def main():
    args = parse_args()
    if args.list:
        sessions = setup_list()
        session = sessions[0]
        output = {}
        for k, v in session.kv.items().iteritems():
            print k, v
            if not v is None and type(v) is str and v.startswith("[") and v.endswith("]"):
                output[k] = v.replace('[', '').replace(']', '').split(', ')
            else:
                output[k] = v
        _list(sessions)
    elif args.host:
        instance, session, cluster = setup_host(args.host)
        host(instance, session, cluster)
    sys.exit(0)

if __name__ == '__main__':
    main()