#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
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
#

"""
oVirt dynamic inventory script
=================================

Generates dynamic inventory file for oVirt.

Script will return following attributes for each virtual machine:
 - id
 - name
 - host
 - cluster
 - status
 - description
 - fqdn
 - os_type
 - template
 - tags
 - statistics
 - devices

When run in --list mode, virtual machines are grouped by the following categories:
 - cluster
 - tag
 - status

 Note: If there is some virtual machine which has has more tags it will be in both tag
       records.

Examples:
  # Execute update of system on webserver virtual machine:

    $ ansible -i contrib/inventory/ovirt4.py webserver -m yum -a "name=* state=latest"

  # Get webserver virtual machine information:

    $ contrib/inventory/ovirt4.py --host webserver

Author: Ondra Machacek (@machacekondra)
"""

import argparse
import os
import sys

from collections import defaultdict

from ansible.module_utils.six.moves import configparser

import json

try:
    import ovirtsdk4 as sdk
    import ovirtsdk4.types as otypes
except ImportError:
    print('oVirt inventory script requires ovirt-engine-sdk-python >= 4.0.0')
    sys.exit(1)


def parse_args():
    """
    Create command line parser for oVirt dynamic inventory script.
    """
    parser = argparse.ArgumentParser(
        description='Ansible dynamic inventory script for oVirt.',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        default=True,
        help='Get data of all virtual machines (default: True).',
    )
    parser.add_argument(
        '--host',
        help='Get data of virtual machines running on specified host.',
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        default=False,
        help='Pretty format (default: False).',
    )
    return parser.parse_args()


def create_connection():
    """
    Create a connection to oVirt engine API.
    """
    # Get the path of the configuration file, by default use
    # 'ovirt.ini' file in script directory:
    default_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'ovirt.ini',
    )
    config_path = os.environ.get('OVIRT_INI_PATH', default_path)

    # Create parser and add ovirt section if it doesn't exist:
    config = configparser.SafeConfigParser(
        defaults={
            'ovirt_url': os.environ.get('OVIRT_URL'),
            'ovirt_username': os.environ.get('OVIRT_USERNAME'),
            'ovirt_password': os.environ.get('OVIRT_PASSWORD'),
            'ovirt_ca_file': os.environ.get('OVIRT_CAFILE'),
        }
    )
    if not config.has_section('ovirt'):
        config.add_section('ovirt')
    config.read(config_path)

    # Create a connection with options defined in ini file:
    return sdk.Connection(
        url=config.get('ovirt', 'ovirt_url'),
        username=config.get('ovirt', 'ovirt_username'),
        password=config.get('ovirt', 'ovirt_password', raw=True),
        ca_file=config.get('ovirt', 'ovirt_ca_file'),
        insecure=config.get('ovirt', 'ovirt_ca_file') is None,
    )


def get_dict_of_struct(connection, vm):
    """
    Transform SDK Vm Struct type to Python dictionary.
    """
    if vm is None:
        return dict()

    vms_service = connection.system_service().vms_service()
    clusters_service = connection.system_service().clusters_service()
    vm_service = vms_service.vm_service(vm.id)
    devices = vm_service.reported_devices_service().list()
    tags = vm_service.tags_service().list()
    stats = vm_service.statistics_service().list()
    labels = vm_service.affinity_labels_service().list()
    groups = clusters_service.cluster_service(
        vm.cluster.id
    ).affinity_groups_service().list()

    return {
        'id': vm.id,
        'name': vm.name,
        'host': connection.follow_link(vm.host).name if vm.host else None,
        'cluster': connection.follow_link(vm.cluster).name,
        'status': str(vm.status),
        'description': vm.description,
        'fqdn': vm.fqdn,
        'os_type': vm.os.type,
        'template': connection.follow_link(vm.template).name,
        'tags': [tag.name for tag in tags],
        'affinity_labels': [label.name for label in labels],
        'affinity_groups': [
            group.name for group in groups
            if vm.name in [vm.name for vm in connection.follow_link(group.vms)]
        ],
        'statistics': dict(
            (stat.name, stat.values[0].datum) for stat in stats if stat.values
        ),
        'devices': dict(
            (device.name, [ip.address for ip in device.ips]) for device in devices if device.ips
        ),
        'ansible_host': next((device.ips[0].address for device in devices if device.ips), None)
    }


def get_data(connection, vm_name=None):
    """
    Obtain data of `vm_name` if specified, otherwise obtain data of all vms.
    """
    vms_service = connection.system_service().vms_service()
    clusters_service = connection.system_service().clusters_service()

    if vm_name:
        vm = vms_service.list(search='name=%s' % vm_name) or [None]
        data = get_dict_of_struct(
            connection=connection,
            vm=vm[0],
        )
    else:
        vms = dict()
        data = defaultdict(list)
        for vm in vms_service.list():
            name = vm.name
            vm_service = vms_service.vm_service(vm.id)
            cluster_service = clusters_service.cluster_service(vm.cluster.id)

            # Add vm to vms dict:
            vms[name] = get_dict_of_struct(connection, vm)

            # Add vm to cluster group:
            cluster_name = connection.follow_link(vm.cluster).name
            data['cluster_%s' % cluster_name].append(name)

            # Add vm to tag group:
            tags_service = vm_service.tags_service()
            for tag in tags_service.list():
                data['tag_%s' % tag.name].append(name)

            # Add vm to status group:
            data['status_%s' % vm.status].append(name)

            # Add vm to affinity group:
            for group in cluster_service.affinity_groups_service().list():
                if vm.name in [
                    v.name for v in connection.follow_link(group.vms)
                ]:
                    data['affinity_group_%s' % group.name].append(vm.name)

            # Add vm to affinity label group:
            affinity_labels_service = vm_service.affinity_labels_service()
            for label in affinity_labels_service.list():
                data['affinity_label_%s' % label.name].append(name)

        data["_meta"] = {
            'hostvars': vms,
        }

    return data


def main():
    args = parse_args()
    connection = create_connection()

    print(
        json.dumps(
            obj=get_data(
                connection=connection,
                vm_name=args.host,
            ),
            sort_keys=args.pretty,
            indent=args.pretty * 2,
        )
    )


if __name__ == '__main__':
    main()
