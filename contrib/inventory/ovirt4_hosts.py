#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Red Hat, Inc.
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
oVirt dynamic inventory script for hosts
=================================

Generates dynamic inventory hosts file for oVirt.

Script will return following attributes for each host:
 - id
 - name
 - address
 - cluster
 - status
 - description
 - os_type
 - tags
 - statistics
 - devices

When run in --list mode, hosts are grouped by the following categories:
 - cluster
 - tag
 - status

 Note: If there is some hosts which has has more tags it will be in both tag
       records.

Examples:
  # Execute update of system on hostX host:

    $ ansible -i contrib/inventory/ovirt4_hosts.py hostX -m yum -a "name=* state=latest"

  # Get hostX host information:

    $ contrib/inventory/ovirt4_hosts.py --host hostX

Author: Ondra Machacek (@machacekondra)
"""

import argparse
import os
import sys

from collections import defaultdict

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    import json
except ImportError:
    import simplejson as json

try:
    import ovirtsdk4 as sdk
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
        help='Get data of all hosts (default: True).',
    )
    parser.add_argument(
        '--host',
        help='Get data of specific host.',
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
            'ovirt_url': None,
            'ovirt_username': None,
            'ovirt_password': None,
            'ovirt_ca_file': None,
        }
    )
    if not config.has_section('ovirt'):
        config.add_section('ovirt')
    config.read(config_path)

    # Create a connection with options defined in ini file:
    return sdk.Connection(
        url=config.get('ovirt', 'ovirt_url'),
        username=config.get('ovirt', 'ovirt_username'),
        password=config.get('ovirt', 'ovirt_password'),
        ca_file=config.get('ovirt', 'ovirt_ca_file'),
        insecure=config.get('ovirt', 'ovirt_ca_file') is None,
    )


def get_dict_of_struct(connection, host):
    """
    Transform SDK Host Struct type to Python dictionary.
    """
    if host is None:
        return dict()

    hosts_service = connection.system_service().hosts_service()
    host_service = hosts_service.host_service(host.id)
    clusters_service = connection.system_service().clusters_service()
    devices = host_service.devices_service().list()
    tags = host_service.tags_service().list()
    stats = host_service.statistics_service().list()
    labels = host_service.affinity_labels_service().list()
    groups = clusters_service.cluster_service(
        host.cluster.id
    ).affinity_groups_service().list()

    return {
        'id': host.id,
        'name': host.name,
        'address': host.address,
        'cluster': connection.follow_link(host.cluster).name,
        'status': str(host.status),
        'description': host.description,
        'os_type': host.os.type,
        'os_version': host.os.version.full_version,
        'libvirt_version': host.libvirt_version.full_version,
        'vdsm_version': host.version.full_version,
        'tags': [tag.name for tag in tags],
        'affinity_labels': [label.name for label in labels],
        'affinity_groups': [
            group.name for group in groups
            if (
                connection.is_link(group.hosts)
                and host.name in [
                    h.name for h in connection.follow_link(group.hosts)
                ]
            )
        ],
        'statistics': dict(
            (stat.name, stat.values[0].datum) for stat in stats
        ),
        'devices': [device.name for device in devices],
        'ansible_host': host.address,
    }


def get_data(connection, host_name=None):
    """
    Obtain data of `host_name` if specified, otherwise obtain data of all hosts.
    """
    hosts_service = connection.system_service().hosts_service()
    clusters_service = connection.system_service().clusters_service()

    if host_name:
        host = hosts_service.list(search='name=%s' % host_name) or [None]
        data = get_dict_of_struct(
            connection=connection,
            host=host[0],
        )
    else:
        hosts = dict()
        data = defaultdict(list)
        for host in hosts_service.list():
            name = host.name
            host_service = hosts_service.host_service(host.id)
            cluster_service = clusters_service.cluster_service(host.cluster.id)

            # Add host to hosts dict:
            hosts[name] = get_dict_of_struct(connection, host)

            # Add host to cluster group:
            cluster_name = connection.follow_link(host.cluster).name
            data['cluster_%s' % cluster_name].append(name)

            # Add host to tag group:
            tags_service = host_service.tags_service()
            for tag in tags_service.list():
                data['tag_%s' % tag.name].append(name)

            # Add host to status group:
            data['status_%s' % host.status].append(name)

            # Add host to affinity group:
            for group in cluster_service.affinity_groups_service().list():
                if (
                    connection.is_link(group.hosts)
                    and host.name in [
                        h.name for h in connection.follow_link(group.hosts)
                    ]
                ):
                    data['affinity_group_%s' % group.name].append(host.name)

            # Add host to affinity label group:
            affinity_labels_service = host_service.affinity_labels_service()
            for label in affinity_labels_service.list():
                data['affinity_label_%s' % label.name].append(name)

        data["_meta"] = {
            'hostvars': hosts,
        }

    return data


def main():
    args = parse_args()
    connection = create_connection()

    print(
        json.dumps(
            obj=get_data(
                connection=connection,
                host_name=args.host,
            ),
            sort_keys=args.pretty,
            indent=args.pretty * 2,
        )
    )

if __name__ == '__main__':
    main()
