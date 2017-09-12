#!/usr/bin/env python
# Copyright 2015 IIX Inc.
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

"""
ovirt external inventory script
=================================

Generates inventory that Ansible can understand by making API requests to
oVirt via the ovirt-engine-sdk-python library.

When run against a specific host, this script returns the following variables
based on the data obtained from the ovirt_sdk Node object:
 - ovirt_uuid
 - ovirt_id
 - ovirt_image
 - ovirt_machine_type
 - ovirt_ips
 - ovirt_name
 - ovirt_description
 - ovirt_status
 - ovirt_zone
 - ovirt_tags
 - ovirt_stats

When run in --list mode, instances are grouped by the following categories:

 - zone:
   zone group name.
 - instance tags:
   An entry is created for each tag.  For example, if you have two instances
   with a common tag called 'foo', they will both be grouped together under
   the 'tag_foo' name.
 - network name:
   the name of the network is appended to 'network_' (e.g. the 'default'
   network will result in a group named 'network_default')
 - running status:
   group name prefixed with 'status_' (e.g. status_up, status_down,..)

Examples:
  Execute uname on all instances in the us-central1-a zone
  $ ansible -i ovirt.py us-central1-a -m shell -a "/bin/uname -a"

  Use the ovirt inventory script to print out instance specific information
  $ contrib/inventory/ovirt.py --host my_instance

Author: Josha Inglis <jinglis@iix.net> based on the gce.py by Eric Johnson <erjohnso@google.com>
Version: 0.0.1
"""

USER_AGENT_PRODUCT = "Ansible-ovirt_inventory_plugin"
USER_AGENT_VERSION = "v1"

import sys
import os
import argparse
import ConfigParser
from collections import defaultdict

try:
    import json
except ImportError:
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    import simplejson as json

try:
    # noinspection PyUnresolvedReferences
    from ovirtsdk.api import API
    # noinspection PyUnresolvedReferences
    from ovirtsdk.xml import params
except ImportError:
    print("ovirt inventory script requires ovirt-engine-sdk-python")
    sys.exit(1)


class OVirtInventory(object):
    def __init__(self):
        # Read settings and parse CLI arguments
        self.args = self.parse_cli_args()
        self.driver = self.get_ovirt_driver()

        # Just display data for specific host
        if self.args.host:
            print(self.json_format_dict(
                self.node_to_dict(self.get_instance(self.args.host)),
                pretty=self.args.pretty
            ))
            sys.exit(0)

        # Otherwise, assume user wants all instances grouped
        print(
            self.json_format_dict(
                data=self.group_instances(),
                pretty=self.args.pretty
            )
        )
        sys.exit(0)

    @staticmethod
    def get_ovirt_driver():
        """
        Determine the ovirt authorization settings and return a ovirt_sdk driver.

        :rtype : ovirtsdk.api.API
        """
        kwargs = {}

        ovirt_ini_default_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "ovirt.ini")
        ovirt_ini_path = os.environ.get('OVIRT_INI_PATH', ovirt_ini_default_path)

        # Create a ConfigParser.
        # This provides empty defaults to each key, so that environment
        # variable configuration (as opposed to INI configuration) is able
        # to work.
        config = ConfigParser.SafeConfigParser(defaults={
            'ovirt_url': '',
            'ovirt_username': '',
            'ovirt_password': '',
            'ovirt_api_secrets': '',
        })
        if 'ovirt' not in config.sections():
            config.add_section('ovirt')
        config.read(ovirt_ini_path)

        # Attempt to get ovirt params from a configuration file, if one
        # exists.
        secrets_path = config.get('ovirt', 'ovirt_api_secrets')
        secrets_found = False
        try:
            # noinspection PyUnresolvedReferences,PyPackageRequirements
            import secrets

            kwargs = getattr(secrets, 'OVIRT_KEYWORD_PARAMS', {})
            secrets_found = True
        except ImportError:
            pass

        if not secrets_found and secrets_path:
            if not secrets_path.endswith('secrets.py'):
                err = "Must specify ovirt_sdk secrets file as /absolute/path/to/secrets.py"
                print(err)
                sys.exit(1)
            sys.path.append(os.path.dirname(secrets_path))
            try:
                # noinspection PyUnresolvedReferences,PyPackageRequirements
                import secrets

                kwargs = getattr(secrets, 'OVIRT_KEYWORD_PARAMS', {})
            except ImportError:
                pass
        if not secrets_found:
            kwargs = {
                'url': config.get('ovirt', 'ovirt_url'),
                'username': config.get('ovirt', 'ovirt_username'),
                'password': config.get('ovirt', 'ovirt_password'),
            }

        # If the appropriate environment variables are set, they override
        # other configuration; process those into our args and kwargs.
        kwargs['url'] = os.environ.get('OVIRT_URL', kwargs['url'])
        kwargs['username'] = next(val for val in [os.environ.get('OVIRT_EMAIL'), os.environ.get('OVIRT_USERNAME'), kwargs['username']] if val is not None)
        kwargs['password'] = next(val for val in [os.environ.get('OVIRT_PASS'), os.environ.get('OVIRT_PASSWORD'), kwargs['password']] if val is not None)

        # Retrieve and return the ovirt driver.
        return API(insecure=True, **kwargs)

    @staticmethod
    def parse_cli_args():
        """
        Command line argument processing

        :rtype : argparse.Namespace
        """

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on ovirt')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all information about an instance')
        parser.add_argument('--pretty', action='store_true', default=False, help='Pretty format (default: False)')
        return parser.parse_args()

    def node_to_dict(self, inst):
        """
        :type inst: params.VM
        """
        if inst is None:
            return {}

        inst.get_custom_properties()
        ips = [ip.get_address() for ip in inst.get_guest_info().get_ips().get_ip()] \
            if inst.get_guest_info() is not None else []
        stats = {}
        for stat in inst.get_statistics().list():
            stats[stat.get_name()] = stat.get_values().get_value()[0].get_datum()

        return {
            'ovirt_uuid': inst.get_id(),
            'ovirt_id': inst.get_id(),
            'ovirt_image': inst.get_os().get_type(),
            'ovirt_machine_type': self.get_machine_type(inst),
            'ovirt_ips': ips,
            'ovirt_name': inst.get_name(),
            'ovirt_description': inst.get_description(),
            'ovirt_status': inst.get_status().get_state(),
            'ovirt_zone': inst.get_cluster().get_id(),
            'ovirt_tags': self.get_tags(inst),
            'ovirt_stats': stats,
            # Hosts don't have a public name, so we add an IP
            'ansible_ssh_host': ips[0] if len(ips) > 0 else None
        }

    @staticmethod
    def get_tags(inst):
        """
        :type inst: params.VM
        """
        return [x.get_name() for x in inst.get_tags().list()]

    def get_machine_type(self, inst):
        inst_type = inst.get_instance_type()
        if inst_type:
            return self.driver.instancetypes.get(id=inst_type.id).name

    # noinspection PyBroadException,PyUnusedLocal
    def get_instance(self, instance_name):
        """Gets details about a specific instance """
        try:
            return self.driver.vms.get(name=instance_name)
        except Exception as e:
            return None

    def group_instances(self):
        """Group all instances"""
        groups = defaultdict(list)
        meta = {"hostvars": {}}

        for node in self.driver.vms.list():
            assert isinstance(node, params.VM)
            name = node.get_name()

            meta["hostvars"][name] = self.node_to_dict(node)

            zone = node.get_cluster().get_name()
            groups[zone].append(name)

            tags = self.get_tags(node)
            for t in tags:
                tag = 'tag_%s' % t
                groups[tag].append(name)

            nets = [x.get_name() for x in node.get_nics().list()]
            for net in nets:
                net = 'network_%s' % net
                groups[net].append(name)

            status = node.get_status().get_state()
            stat = 'status_%s' % status.lower()
            if stat in groups:
                groups[stat].append(name)
            else:
                groups[stat] = [name]

        groups["_meta"] = meta

        return groups

    @staticmethod
    def json_format_dict(data, pretty=False):
        """ Converts a dict to a JSON object and dumps it as a formatted
        string """

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

# Run the script
OVirtInventory()
