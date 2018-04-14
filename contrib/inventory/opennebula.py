#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""
OpenNebula dynamic inventory script
===================================

Generates dynamic inventory for OpenNebula.

Note: the script uses the IPv4 address of the first NIC as ansible_host.

Connection configuration is read by default from opennebula.ini, or PYONE_CONFIG_PATH if specified.
PYONE_ENDPOINT and PYONE_SESSION environment variables overwrite settings read from file.

When run for a specific host using the --host option, this script returns the following structure:

{
  "DEPLOY_ID": "one-2",
  "DISK_CLUSTER_ID": [
    "0",
    "0"
  ],
  "DISK_DISK_ID": [
    "0",
    "0"
  ],
  "DISK_IMAGE": [
    "testvm",
    null
  ],
  "DISK_IMAGE_ID": [
    "0",
    null
  ],
  "HOSTNAME": "node1",
  "ID": "2",
  "LABELS": "mylabel1,label1/mylabel3/mylabel4",
  "LCM_STATE": "3",
  "NAME": "testvm-2",
  "NIC_CLUSTER_ID": [
    "0",
    "0"
  ],
  "NIC_IP": [
    "AAA.AAA.AAA.AAA",
    "BBB.BBB.BBB.BBB"
  ],
  "NIC_NETWORK": [
    "private",
    "private"
  ],
  "NIC_NETWORK_ID": [
    "0",
    "0"
  ],
  "PREV_LCM_STATE": "3",
  "PREV_STATE": "3",
  "RESCHED": "0",
  "STATE": "3",
  "TEMPLATE_ID": "0",
  "ansible_host": "AAA.AAA.AAA.AAA",
}

When run in --list mode, virtual machines are grouped by the following categories:
 - DISK CLUSTER_ID
 - NIC CLUSTER_ID
 - HOSTNAME
 - LABELS

{
  "DISK_CLUSTER_ID_0": {
    "hosts": [
      "testvm-0",
      "testvm-2"
    ]
  },
  "HOSTNAME_node1": {
    "hosts": [
      "testvm-0"
    ]
  },
  "HOSTNAME_node2": {
    "hosts": [
      "testvm-2"
    ]
  },
  "LABELS_label1/mylabel3/mylabel4": {
    "hosts": [
      "testvm-0",
      "testvm-2"
    ]
  },
  "LABELS_mylabel1": {
    "hosts": [
      "testvm-2"
    ]
  },
  ...,
  "NIC_CLUSTER_ID_0": {
    "hosts": [
      "testvm-2"
    ]
  },
  "_meta": {
    "hostvars": {
      "testvm-0": {
        ...,
        "ansible_host": null
      },
      ...,
      "testvm-2": {
        ...,
        "ansible_host": "AAA.AAA.AAA.AAA"
      }
    }
  },
  "ansible_host": {
    "hosts": [
      "testvm-2"
    ]
  }
}

Examples:

  # Provide credentials:

    $ PYONE_CONFIG_PATH=config.ini python opennebula.py --list --pretty
    $ PYONE_SESSION=oneadmin:password python opennebula.py --list --pretty

  # Select Ansible network and nic

    $ python opennebula.py --ansible-network-id 1 --ansible-nic-index 2 --list --pretty  # third nic on network id 1

  # List hosts:

    $ python opennebula.py --list --pretty
    $ ansible -i opennebula.py --list-hosts all

  # List hosts which have ansible_host IP defined, where LABELS is not `test`:

    $ ansible -i opennebula.py --list-hosts 'ansible_host:!LABELS_test'

  # Use a wrapper script if you need to pass arguments to opennebula.py (see https://github.com/ansible/ansible/issues/20432):

    $ cat <<EOF > opennebula.sh
    #!/bin/bash
    python opennebula.py --ansible-network-id 1 --ansible-nic-index 2 $@
    EOF
    $ chmod u+x opennebula.sh
    $ ansible -i opennebula.sh --list-hosts all

  # List groups:

    $ ansible localhost -i opennebula.py -m debug -a 'var=groups'

  # Get the n-th (zero-based indexing) host in DISK_CLUSTER_ID_0 information (note that the order in all group is non-deterministic):

    $ n=2
    $ host=`ansible -o -i opennebula.py --list-hosts DISK_CLUSTER_ID_0 --limit DISK_CLUSTER_ID_0[$n] | grep -v -E '\(|\)'`
    $ python opennebula.py --pretty --host $host

  # Ping the host when ssh key-based authentication is not configured, using root/password credentials:

    $ ANSIBLE_HOST_KEY_CHECKING=false sshpass -p 'password' ansible -i opennebula.py --user root --ask-pass -m ping $host

"""

from __future__ import print_function

import argparse
import os
import ssl
import sys

from collections import OrderedDict, defaultdict

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    import json
except ImportError:
    import simplejson as json

try:
    import pyone
except ImportError:
    print('OpenNebula dynamic inventory script requires https://github.com/OpenNebula/addon-pyone', file=sys.stderr)
    sys.exit(1)


def parse_args():
    """
    Create command line parser for OpenNebula dynamic inventory script.
    """
    parser = argparse.ArgumentParser(
        description='Ansible dynamic inventory script for OpenNebula.',
    )
    parser.add_argument(
        '--ansible-nic-index',
        default=0,
        type=int,
        help='The index of the nic on ansible-network-id used by Ansible (default: 0).',
    )
    parser.add_argument(
        '--ansible-network-id',
        default=0,
        type=int,
        help='The OpenNebula network id used by Ansible (default: 0).',
    )
    parser.add_argument(
        '--host',
        help='Get data for specific virtual machine.',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        default=True,
        help='Get data of all virtual machines (default: True).',
    )
    parser.add_argument(
        '--no-check-certificate',
        action='store_true',
        default=False,
        help='Disable certificate verification (default: False).',
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        default=False,
        help='Pretty format (default: False).',
    )
    parser.add_argument(
        '--vmpool-info',
        default='-2,-1,-1,-1',
        help='Limit the scope of the one.vmpool.info API call (default: -2,-1,-1,-1).',
    )
    return parser.parse_args()


def create_connection(no_check_certificate=False):
    """
    Create a connection to OpenNebula OneServer.
    """
    default_config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'opennebula.ini',
    )
    config_path = os.environ.get('PYONE_CONFIG_PATH', default_config_path)
    if not os.path.exists(config_path):
        config_path = None

    config = configparser.SafeConfigParser()
    if config_path is not None:
        config.read(config_path)

    if not config.has_section('one'):
        config.add_section('one')

    if os.environ.get('PYONE_ENDPOINT'):
        config.set('one', 'pyone_endpoint', os.environ.get('PYONE_ENDPOINT'))
    if os.environ.get('PYONE_SESSION'):
        config.set('one', 'pyone_session', os.environ.get('PYONE_SESSION'))

    try:
        if no_check_certificate:
            return pyone.OneServer(
                uri=config.get('one', 'pyone_endpoint'),
                session=config.get('one', 'pyone_session'),
                context=ssl._create_unverified_context(),
            )
        else:
            return pyone.OneServer(
                uri=config.get('one', 'pyone_endpoint'),
                session=config.get('one', 'pyone_session'),
            )
    except configparser.NoOptionError:
        print('Connection configuration incomplete', file=sys.stderr)
        sys.exit(1)


def get_host_dict(vm_data):
    """
    Return Python dictionary containing the selected information from vm_data.
    """
    if vm_data is None:
        return dict()

    # handle multiple DISK/NIC
    groups = {'DISK': {}, 'NIC': {}}
    for group in sorted(groups.keys()):
        if group not in vm_data.TEMPLATE:
            print('%s information missing for VM ID %s' % (group, vm_data.ID), file=sys.stderr)
            groups[group]['CLUSTER_ID'] = []
            if group == 'DISK':
                groups[group]['DISK_ID'] = []
                groups[group]['IMAGE'] = []
                groups[group]['IMAGE_ID'] = []
            if group == 'NIC':
                groups[group]['IP'] = []
                groups[group]['NETWORK'] = []
                groups[group]['NETWORK_ID'] = []
        else:
            template_data = vm_data.TEMPLATE[group]
            if isinstance(template_data, list):
                # each DISK/NIC can be in a different CLUSTER
                groups[group]['CLUSTER_ID'] = [entry['CLUSTER_ID'] for entry in template_data]
                if group == 'DISK':
                    groups[group]['DISK_ID'] = [entry['DISK_ID'] for entry in template_data]
                    groups[group]['IMAGE'] = [entry['IMAGE'] if 'IMAGE' in entry else None for entry in template_data]
                    groups[group]['IMAGE_ID'] = [entry['IMAGE_ID'] if 'IMAGE_ID' in entry else None for entry in template_data]
                if group == 'NIC':
                    groups[group]['IP'] = [entry['IP'] if 'IP' in entry else None for entry in template_data]
                    groups[group]['NETWORK'] = [entry['NETWORK'] for entry in template_data]
                    groups[group]['NETWORK_ID'] = [entry['NETWORK_ID'] for entry in template_data]
            else:
                groups[group]['CLUSTER_ID'] = [template_data['CLUSTER_ID']]
                if group == 'DISK':
                    groups[group]['DISK_ID'] = [template_data['DISK_ID']]
                    groups[group]['IMAGE'] = [template_data['IMAGE']]
                    groups[group]['IMAGE_ID'] = [template_data['IMAGE_ID']]
                if group == 'NIC':
                    groups[group]['IP'] = [template_data['IP'] if 'IP' in template_data else None]
                    groups[group]['NETWORK'] = [template_data['NETWORK']]
                    groups[group]['NETWORK_ID'] = [template_data['NETWORK_ID']]

    return OrderedDict({
        'ID': vm_data.ID,
        'NAME': vm_data.NAME,
        'STATE': vm_data.STATE,
        'LCM_STATE': vm_data.LCM_STATE,
        'PREV_STATE': vm_data.PREV_STATE,
        'PREV_LCM_STATE': vm_data.PREV_LCM_STATE,
        'RESCHED': vm_data.RESCHED,
        'HOSTNAME': vm_data.HISTORY_RECORDS.HISTORY[0].HOSTNAME,
        'DEPLOY_ID': vm_data.DEPLOY_ID,
        'TEMPLATE_ID': vm_data.TEMPLATE['TEMPLATE_ID'],
        'LABELS': vm_data.USER_TEMPLATE['LABELS'] if (vm_data.USER_TEMPLATE and 'LABELS' in vm_data.USER_TEMPLATE) else None,
        'DISK_CLUSTER_ID': groups['DISK']['CLUSTER_ID'],
        'DISK_DISK_ID': groups['DISK']['DISK_ID'],
        'DISK_IMAGE': groups['DISK']['IMAGE'],
        'DISK_IMAGE_ID': groups['DISK']['IMAGE_ID'],
        'NIC_CLUSTER_ID': groups['NIC']['CLUSTER_ID'],
        'NIC_IP': groups['NIC']['IP'],
        'NIC_NETWORK': groups['NIC']['NETWORK'],
        'NIC_NETWORK_ID': groups['NIC']['NETWORK_ID'],
    })


def get_inventory(connection, vm_name=None, vmpool_info=(-2, -1, -1, -1), ansible_nic_index=0, ansible_network_id=0):
    """
    Obtain data of `vm_name` if specified, otherwise obtain data of all vms.
    """
    vmpool = connection.vmpool.info(*vmpool_info)

    def append_inventory_group(group, name, data):
        """
        Append the VM name to the inventory group.
        """
        if group not in data:
            data.update({group: {'hosts': []}})
        if name not in data[group]['hosts']:
            data[group]['hosts'].append(name)

    if vm_name:
        data = get_host_dict(
            next((vm for vm in vmpool.VM if vm.NAME == vm_name), None),
        )
    else:
        vms = dict()
        data = defaultdict(list)
        vmpool_data = vmpool.VM
        if 'DEPLOY_ID' in vmpool_data:
            vmpool_data = [vmpool_data]  # a single, lonely VM
        for vm_data in vmpool_data:
            name = vm_data.NAME
            # Add vm information to vms dict
            vms[name] = get_host_dict(vm_data)

            # Populate DISK_CLUSTER_ID groups
            for cluster_id in vms[name]['DISK_CLUSTER_ID']:
                append_inventory_group('DISK_CLUSTER_ID_%s' % cluster_id, name, data)

            # Populate NIC_CLUSTER_ID groups
            for cluster_id in vms[name]['NIC_CLUSTER_ID']:
                append_inventory_group('NIC_CLUSTER_ID_%s' % cluster_id, name, data)

            # Populate HOSTNAME groups
            append_inventory_group('HOSTNAME_%s' % vms[name]['HOSTNAME'], name, data)

            # Populate LABELS groups
            labels = vms[name]['LABELS'].split(',') if vms[name]['LABELS'] else []
            for label in labels:
                append_inventory_group('LABELS_%s' % label, name, data)

            # Set ansible_host
            ips = [ip for network, ip in zip(vms[name]['NIC_NETWORK_ID'], vms[name]['NIC_IP']) if int(network) == ansible_network_id]
            try:
                vms[name].update({'ansible_host': ips[ansible_nic_index]})
                if vms[name]['ansible_host'] is not None:
                    append_inventory_group('ansible_host', name, data)
            except IndexError:
                print('Incorrect ansible-nic-index %s for ansible-network-id %s for VM ID %s' % (ansible_nic_index, ansible_network_id, vms[name]['ID']), file=sys.stderr)

        data["_meta"] = {
            'hostvars': vms,
        }

    return data


def main():
    """
    Return dynamic inventory json string for OpenNebula.
    """
    args = parse_args()
    connection = create_connection(args.no_check_certificate)

    print(
        json.dumps(
            obj=get_inventory(
                connection=connection,
                vm_name=args.host,
                vmpool_info=tuple([int(item) for item in args.vmpool_info.split(',')]),
                ansible_nic_index=args.ansible_nic_index,
                ansible_network_id=args.ansible_network_id,
            ),
            sort_keys=args.pretty,
            indent=args.pretty * 2,
        )
    )

if __name__ == '__main__':
    main()
