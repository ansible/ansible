#!/usr/bin/env python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
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

'''
Azure External Inventory Script
===============================
Generates dynamic inventory by making API requests to the Azure Resource
Manager using the Azure Python SDK. For instruction on installing the
Azure Python SDK see http://azure-sdk-for-python.readthedocs.org/

Authentication
--------------
The order of precedence is command line arguments, environment variables,
and finally the [default] profile found in ~/.azure/credentials.

If using a credentials file, it should be an ini formatted file with one or
more sections, which we refer to as profiles. The script looks for a
[default] section, if a profile is not specified either on the command line
or with an environment variable. The keys in a profile will match the
list of command line arguments below.

For command line arguments and environment variables specify a profile found
in your ~/.azure/credentials file, or a service principal or Active Directory
user.

Command line arguments:
 - profile
 - client_id
 - secret
 - subscription_id
 - tenant
 - ad_user
 - password
 - cloud_environment

Environment variables:
 - AZURE_PROFILE
 - AZURE_CLIENT_ID
 - AZURE_SECRET
 - AZURE_SUBSCRIPTION_ID
 - AZURE_TENANT
 - AZURE_AD_USER
 - AZURE_PASSWORD
 - AZURE_CLOUD_ENVIRONMENT

Run for Specific Host
-----------------------
When run for a specific host using the --host option, a resource group is
required. For a specific host, this script returns the following variables:

{
  "ansible_host": "XXX.XXX.XXX.XXX",
  "computer_name": "computer_name2",
  "fqdn": null,
  "id": "/subscriptions/subscription-id/resourceGroups/galaxy-production/providers/Microsoft.Compute/virtualMachines/object-name",
  "image": {
    "offer": "CentOS",
    "publisher": "OpenLogic",
    "sku": "7.1",
    "version": "latest"
  },
  "location": "westus",
  "mac_address": "00-00-5E-00-53-FE",
  "name": "object-name",
  "network_interface": "interface-name",
  "network_interface_id": "/subscriptions/subscription-id/resourceGroups/galaxy-production/providers/Microsoft.Network/networkInterfaces/object-name1",
  "network_security_group": null,
  "network_security_group_id": null,
  "os_disk": {
    "name": "object-name",
    "operating_system_type": "Linux"
  },
  "plan": null,
  "powerstate": "running",
  "private_ip": "172.26.3.6",
  "private_ip_alloc_method": "Static",
  "provisioning_state": "Succeeded",
  "public_ip": "XXX.XXX.XXX.XXX",
  "public_ip_alloc_method": "Static",
  "public_ip_id": "/subscriptions/subscription-id/resourceGroups/galaxy-production/providers/Microsoft.Network/publicIPAddresses/object-name",
  "public_ip_name": "object-name",
  "resource_group": "galaxy-production",
  "security_group": "object-name",
  "security_group_id": "/subscriptions/subscription-id/resourceGroups/galaxy-production/providers/Microsoft.Network/networkSecurityGroups/object-name",
  "tags": {
      "db": "database"
  },
  "type": "Microsoft.Compute/virtualMachines",
  "virtual_machine_size": "Standard_DS4"
}

Groups
------
When run in --list mode, instances are grouped by the following categories:
 - azure
 - location
 - resource_group
 - security_group
 - tag key
 - tag key_value

Control groups using azure_rm.ini or set environment variables:

AZURE_GROUP_BY_RESOURCE_GROUP=yes
AZURE_GROUP_BY_LOCATION=yes
AZURE_GROUP_BY_SECURITY_GROUP=yes
AZURE_GROUP_BY_TAG=yes

Select hosts within specific resource groups by assigning a comma separated list to:

AZURE_RESOURCE_GROUPS=resource_group_a,resource_group_b

Select hosts for specific tag key by assigning a comma separated list of tag keys to:

AZURE_TAGS=key1,key2,key3

Select hosts for specific locations:

AZURE_LOCATIONS=eastus,westus,eastus2

Or, select hosts for specific tag key:value pairs by assigning a comma separated list key:value pairs to:

AZURE_TAGS=key1:value1,key2:value2

If you don't need the powerstate, you can improve performance by turning off powerstate fetching:
AZURE_INCLUDE_POWERSTATE=no

azure_rm.ini
------------
As mentioned above, you can control execution using environment variables or a .ini file. A sample
azure_rm.ini is included. The name of the .ini file is the basename of the inventory script (in this case
'azure_rm') with a .ini extension. It also assumes the .ini file is alongside the script. To specify
a different path for the .ini file, define the AZURE_INI_PATH environment variable:

  export AZURE_INI_PATH=/path/to/custom.ini

Powerstate:
-----------
The powerstate attribute indicates whether or not a host is running. If the value is 'running', the machine is
up. If the value is anything other than 'running', the machine is down, and will be unreachable.

Examples:
---------
  Execute /bin/uname on all instances in the galaxy-qa resource group
  $ ansible -i azure_rm.py galaxy-qa -m shell -a "/bin/uname -a"

  Use the inventory script to print instance specific information
  $ contrib/inventory/azure_rm.py --host my_instance_host_name --pretty

  Use with a playbook
  $ ansible-playbook -i contrib/inventory/azure_rm.py my_playbook.yml --limit galaxy-qa


Insecure Platform Warning
-------------------------
If you receive InsecurePlatformWarning from urllib3, install the
requests security packages:

    pip install requests[security]


author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)

Company: Ansible by Red Hat

Version: 1.0.0
'''

import argparse
import json
import os
import re
import sys
import inspect

try:
    # python2
    import ConfigParser as cp
except ImportError:
    # python3
    import configparser as cp

from packaging.version import Version

from os.path import expanduser
import ansible.module_utils.six.moves.urllib.parse as urlparse

HAS_AZURE = True
HAS_AZURE_EXC = None

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure import azure_cloud
    from azure.mgmt.compute import __version__ as azure_compute_version
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
    from azure.common.credentials import ServicePrincipalCredentials, UserPassCredentials
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.mgmt.compute import ComputeManagementClient
except ImportError as exc:
    HAS_AZURE_EXC = exc
    HAS_AZURE = False


AZURE_CREDENTIAL_ENV_MAPPING = dict(
    profile='AZURE_PROFILE',
    subscription_id='AZURE_SUBSCRIPTION_ID',
    client_id='AZURE_CLIENT_ID',
    secret='AZURE_SECRET',
    tenant='AZURE_TENANT',
    ad_user='AZURE_AD_USER',
    password='AZURE_PASSWORD',
    cloud_environment='AZURE_CLOUD_ENVIRONMENT',
)

AZURE_CONFIG_SETTINGS = dict(
    resource_groups='AZURE_RESOURCE_GROUPS',
    tags='AZURE_TAGS',
    locations='AZURE_LOCATIONS',
    include_powerstate='AZURE_INCLUDE_POWERSTATE',
    group_by_resource_group='AZURE_GROUP_BY_RESOURCE_GROUP',
    group_by_location='AZURE_GROUP_BY_LOCATION',
    group_by_security_group='AZURE_GROUP_BY_SECURITY_GROUP',
    group_by_tag='AZURE_GROUP_BY_TAG'
)

AZURE_MIN_VERSION = "2.0.0"


def azure_id_to_dict(id):
    pieces = re.sub(r'^\/', '', id).split('/')
    result = {}
    index = 0
    while index < len(pieces) - 1:
        result[pieces[index]] = pieces[index + 1]
        index += 1
    return result


class AzureRM(object):

    def __init__(self, args):
        self._args = args
        self._cloud_environment = None
        self._compute_client = None
        self._resource_client = None
        self._network_client = None

        self.debug = False
        if args.debug:
            self.debug = True

        self.credentials = self._get_credentials(args)
        if not self.credentials:
            self.fail("Failed to get credentials. Either pass as parameters, set environment variables, "
                      "or define a profile in ~/.azure/credentials.")

        # if cloud_environment specified, look up/build Cloud object
        raw_cloud_env = self.credentials.get('cloud_environment')
        if not raw_cloud_env:
            self._cloud_environment = azure_cloud.AZURE_PUBLIC_CLOUD  # SDK default
        else:
            # try to look up "well-known" values via the name attribute on azure_cloud members
            all_clouds = [x[1] for x in inspect.getmembers(azure_cloud) if isinstance(x[1], azure_cloud.Cloud)]
            matched_clouds = [x for x in all_clouds if x.name == raw_cloud_env]
            if len(matched_clouds) == 1:
                self._cloud_environment = matched_clouds[0]
            elif len(matched_clouds) > 1:
                self.fail("Azure SDK failure: more than one cloud matched for cloud_environment name '{0}'".format(raw_cloud_env))
            else:
                if not urlparse.urlparse(raw_cloud_env).scheme:
                    self.fail("cloud_environment must be an endpoint discovery URL or one of {0}".format([x.name for x in all_clouds]))
                try:
                    self._cloud_environment = azure_cloud.get_cloud_from_metadata_endpoint(raw_cloud_env)
                except Exception as e:
                    self.fail("cloud_environment {0} could not be resolved: {1}".format(raw_cloud_env, e.message))

        if self.credentials.get('subscription_id', None) is None:
            self.fail("Credentials did not include a subscription_id value.")
        self.log("setting subscription_id")
        self.subscription_id = self.credentials['subscription_id']

        if self.credentials.get('client_id') is not None and \
           self.credentials.get('secret') is not None and \
           self.credentials.get('tenant') is not None:
            self.azure_credentials = ServicePrincipalCredentials(client_id=self.credentials['client_id'],
                                                                 secret=self.credentials['secret'],
                                                                 tenant=self.credentials['tenant'],
                                                                 cloud_environment=self._cloud_environment)
        elif self.credentials.get('ad_user') is not None and self.credentials.get('password') is not None:
            tenant = self.credentials.get('tenant')
            if not tenant:
                tenant = 'common'
            self.azure_credentials = UserPassCredentials(self.credentials['ad_user'],
                                                         self.credentials['password'],
                                                         tenant=tenant,
                                                         cloud_environment=self._cloud_environment)
        else:
            self.fail("Failed to authenticate with provided credentials. Some attributes were missing. "
                      "Credentials must include client_id, secret and tenant or ad_user and password.")

    def log(self, msg):
        if self.debug:
            print(msg + u'\n')

    def fail(self, msg):
        raise Exception(msg)

    def _get_profile(self, profile="default"):
        path = expanduser("~")
        path += "/.azure/credentials"
        try:
            config = cp.ConfigParser()
            config.read(path)
        except Exception as exc:
            self.fail("Failed to access {0}. Check that the file exists and you have read "
                      "access. {1}".format(path, str(exc)))
        credentials = dict()
        for key in AZURE_CREDENTIAL_ENV_MAPPING:
            try:
                credentials[key] = config.get(profile, key, raw=True)
            except:
                pass

        if credentials.get('client_id') is not None or credentials.get('ad_user') is not None:
            return credentials

        return None

    def _get_env_credentials(self):
        env_credentials = dict()
        for attribute, env_variable in AZURE_CREDENTIAL_ENV_MAPPING.items():
            env_credentials[attribute] = os.environ.get(env_variable, None)

        if env_credentials['profile'] is not None:
            credentials = self._get_profile(env_credentials['profile'])
            return credentials

        if env_credentials['client_id'] is not None or env_credentials['ad_user'] is not None:
            return env_credentials

        return None

    def _get_credentials(self, params):
        # Get authentication credentials.
        # Precedence: cmd line parameters-> environment variables-> default profile in ~/.azure/credentials.

        self.log('Getting credentials')

        arg_credentials = dict()
        for attribute, env_variable in AZURE_CREDENTIAL_ENV_MAPPING.items():
            arg_credentials[attribute] = getattr(params, attribute)

        # try module params
        if arg_credentials['profile'] is not None:
            self.log('Retrieving credentials with profile parameter.')
            credentials = self._get_profile(arg_credentials['profile'])
            return credentials

        if arg_credentials['client_id'] is not None:
            self.log('Received credentials from parameters.')
            return arg_credentials

        if arg_credentials['ad_user'] is not None:
            self.log('Received credentials from parameters.')
            return arg_credentials

        # try environment
        env_credentials = self._get_env_credentials()
        if env_credentials:
            self.log('Received credentials from env.')
            return env_credentials

        # try default profile from ~./azure/credentials
        default_credentials = self._get_profile()
        if default_credentials:
            self.log('Retrieved default profile credentials from ~/.azure/credentials.')
            return default_credentials

        return None

    def _register(self, key):
        try:
            # We have to perform the one-time registration here. Otherwise, we receive an error the first
            # time we attempt to use the requested client.
            resource_client = self.rm_client
            resource_client.providers.register(key)
        except Exception as exc:
            self.log("One-time registration of {0} failed - {1}".format(key, str(exc)))
            self.log("You might need to register {0} using an admin account".format(key))
            self.log(("To register a provider using the Python CLI: "
                      "https://docs.microsoft.com/azure/azure-resource-manager/"
                      "resource-manager-common-deployment-errors#noregisteredproviderfound"))

    @property
    def network_client(self):
        self.log('Getting network client')
        if not self._network_client:
            self._network_client = NetworkManagementClient(
                self.azure_credentials,
                self.subscription_id,
                base_url=self._cloud_environment.endpoints.resource_manager,
                api_version='2017-06-01'
            )
            self._register('Microsoft.Network')
        return self._network_client

    @property
    def rm_client(self):
        self.log('Getting resource manager client')
        if not self._resource_client:
            self._resource_client = ResourceManagementClient(
                self.azure_credentials,
                self.subscription_id,
                base_url=self._cloud_environment.endpoints.resource_manager,
                api_version='2017-05-10'
            )
        return self._resource_client

    @property
    def compute_client(self):
        self.log('Getting compute client')
        if not self._compute_client:
            self._compute_client = ComputeManagementClient(
                self.azure_credentials,
                self.subscription_id,
                base_url=self._cloud_environment.endpoints.resource_manager,
                api_version='2017-03-30'
            )
            self._register('Microsoft.Compute')
        return self._compute_client


class AzureInventory(object):

    def __init__(self):

        self._args = self._parse_cli_args()

        try:
            rm = AzureRM(self._args)
        except Exception as e:
            sys.exit("{0}".format(str(e)))

        self._compute_client = rm.compute_client
        self._network_client = rm.network_client
        self._resource_client = rm.rm_client
        self._security_groups = None

        self.resource_groups = []
        self.tags = None
        self.locations = None
        self.replace_dash_in_groups = False
        self.group_by_resource_group = True
        self.group_by_location = True
        self.group_by_security_group = True
        self.group_by_tag = True
        self.include_powerstate = True

        self._inventory = dict(
            _meta=dict(
                hostvars=dict()
            ),
            azure=[]
        )

        self._get_settings()

        if self._args.resource_groups:
            self.resource_groups = self._args.resource_groups.split(',')

        if self._args.tags:
            self.tags = self._args.tags.split(',')

        if self._args.locations:
            self.locations = self._args.locations.split(',')

        if self._args.no_powerstate:
            self.include_powerstate = False

        self.get_inventory()
        print(self._json_format_dict(pretty=self._args.pretty))
        sys.exit(0)

    def _parse_cli_args(self):
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description='Produce an Ansible Inventory file for an Azure subscription')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument('--debug', action='store_true', default=False,
                            help='Send debug messages to STDOUT')
        parser.add_argument('--host', action='store',
                            help='Get all information about an instance')
        parser.add_argument('--pretty', action='store_true', default=False,
                            help='Pretty print JSON output(default: False)')
        parser.add_argument('--profile', action='store',
                            help='Azure profile contained in ~/.azure/credentials')
        parser.add_argument('--subscription_id', action='store',
                            help='Azure Subscription Id')
        parser.add_argument('--client_id', action='store',
                            help='Azure Client Id ')
        parser.add_argument('--secret', action='store',
                            help='Azure Client Secret')
        parser.add_argument('--tenant', action='store',
                            help='Azure Tenant Id')
        parser.add_argument('--ad_user', action='store',
                            help='Active Directory User')
        parser.add_argument('--password', action='store',
                            help='password')
        parser.add_argument('--cloud_environment', action='store',
                            help='Azure Cloud Environment name or metadata discovery URL')
        parser.add_argument('--resource-groups', action='store',
                            help='Return inventory for comma separated list of resource group names')
        parser.add_argument('--tags', action='store',
                            help='Return inventory for comma separated list of tag key:value pairs')
        parser.add_argument('--locations', action='store',
                            help='Return inventory for comma separated list of locations')
        parser.add_argument('--no-powerstate', action='store_true', default=False,
                            help='Do not include the power state of each virtual host')
        return parser.parse_args()

    def get_inventory(self):
        if len(self.resource_groups) > 0:
            # get VMs for requested resource groups
            for resource_group in self.resource_groups:
                try:
                    virtual_machines = self._compute_client.virtual_machines.list(resource_group)
                except Exception as exc:
                    sys.exit("Error: fetching virtual machines for resource group {0} - {1}".format(resource_group, str(exc)))
                if self._args.host or self.tags:
                    selected_machines = self._selected_machines(virtual_machines)
                    self._load_machines(selected_machines)
                else:
                    self._load_machines(virtual_machines)
        else:
            # get all VMs within the subscription
            try:
                virtual_machines = self._compute_client.virtual_machines.list_all()
            except Exception as exc:
                sys.exit("Error: fetching virtual machines - {0}".format(str(exc)))

            if self._args.host or self.tags or self.locations:
                selected_machines = self._selected_machines(virtual_machines)
                self._load_machines(selected_machines)
            else:
                self._load_machines(virtual_machines)

    def _load_machines(self, machines):
        for machine in machines:
            id_dict = azure_id_to_dict(machine.id)

            # TODO - The API is returning an ID value containing resource group name in ALL CAPS. If/when it gets
            #       fixed, we should remove the .lower(). Opened Issue
            #       #574: https://github.com/Azure/azure-sdk-for-python/issues/574
            resource_group = id_dict['resourceGroups'].lower()

            if self.group_by_security_group:
                self._get_security_groups(resource_group)

            host_vars = dict(
                ansible_host=None,
                private_ip=None,
                private_ip_alloc_method=None,
                public_ip=None,
                public_ip_name=None,
                public_ip_id=None,
                public_ip_alloc_method=None,
                fqdn=None,
                location=machine.location,
                name=machine.name,
                type=machine.type,
                id=machine.id,
                tags=machine.tags,
                network_interface_id=None,
                network_interface=None,
                resource_group=resource_group,
                mac_address=None,
                plan=(machine.plan.name if machine.plan else None),
                virtual_machine_size=machine.hardware_profile.vm_size,
                computer_name=(machine.os_profile.computer_name if machine.os_profile else None),
                provisioning_state=machine.provisioning_state,
            )

            host_vars['os_disk'] = dict(
                name=machine.storage_profile.os_disk.name,
                operating_system_type=machine.storage_profile.os_disk.os_type.value
            )

            if self.include_powerstate:
                host_vars['powerstate'] = self._get_powerstate(resource_group, machine.name)

            if machine.storage_profile.image_reference:
                host_vars['image'] = dict(
                    offer=machine.storage_profile.image_reference.offer,
                    publisher=machine.storage_profile.image_reference.publisher,
                    sku=machine.storage_profile.image_reference.sku,
                    version=machine.storage_profile.image_reference.version
                )

            # Add windows details
            if machine.os_profile is not None and machine.os_profile.windows_configuration is not None:
                host_vars['ansible_connection'] = 'winrm'
                host_vars['windows_auto_updates_enabled'] = \
                    machine.os_profile.windows_configuration.enable_automatic_updates
                host_vars['windows_timezone'] = machine.os_profile.windows_configuration.time_zone
                host_vars['windows_rm'] = None
                if machine.os_profile.windows_configuration.win_rm is not None:
                    host_vars['windows_rm'] = dict(listeners=None)
                    if machine.os_profile.windows_configuration.win_rm.listeners is not None:
                        host_vars['windows_rm']['listeners'] = []
                        for listener in machine.os_profile.windows_configuration.win_rm.listeners:
                            host_vars['windows_rm']['listeners'].append(dict(protocol=listener.protocol,
                                                                             certificate_url=listener.certificate_url))

            for interface in machine.network_profile.network_interfaces:
                interface_reference = self._parse_ref_id(interface.id)
                network_interface = self._network_client.network_interfaces.get(
                    interface_reference['resourceGroups'],
                    interface_reference['networkInterfaces'])
                if network_interface.primary:
                    if self.group_by_security_group and \
                       self._security_groups[resource_group].get(network_interface.id, None):
                        host_vars['security_group'] = \
                            self._security_groups[resource_group][network_interface.id]['name']
                        host_vars['security_group_id'] = \
                            self._security_groups[resource_group][network_interface.id]['id']
                    host_vars['network_interface'] = network_interface.name
                    host_vars['network_interface_id'] = network_interface.id
                    host_vars['mac_address'] = network_interface.mac_address
                    for ip_config in network_interface.ip_configurations:
                        host_vars['private_ip'] = ip_config.private_ip_address
                        host_vars['private_ip_alloc_method'] = ip_config.private_ip_allocation_method
                        if ip_config.public_ip_address:
                            public_ip_reference = self._parse_ref_id(ip_config.public_ip_address.id)
                            public_ip_address = self._network_client.public_ip_addresses.get(
                                public_ip_reference['resourceGroups'],
                                public_ip_reference['publicIPAddresses'])
                            host_vars['ansible_host'] = public_ip_address.ip_address
                            host_vars['public_ip'] = public_ip_address.ip_address
                            host_vars['public_ip_name'] = public_ip_address.name
                            host_vars['public_ip_alloc_method'] = public_ip_address.public_ip_allocation_method
                            host_vars['public_ip_id'] = public_ip_address.id
                            if public_ip_address.dns_settings:
                                host_vars['fqdn'] = public_ip_address.dns_settings.fqdn

            self._add_host(host_vars)

    def _selected_machines(self, virtual_machines):
        selected_machines = []
        for machine in virtual_machines:
            if self._args.host and self._args.host == machine.name:
                selected_machines.append(machine)
            if self.tags and self._tags_match(machine.tags, self.tags):
                selected_machines.append(machine)
            if self.locations and machine.location in self.locations:
                selected_machines.append(machine)
        return selected_machines

    def _get_security_groups(self, resource_group):
        ''' For a given resource_group build a mapping of network_interface.id to security_group name '''
        if not self._security_groups:
            self._security_groups = dict()
        if not self._security_groups.get(resource_group):
            self._security_groups[resource_group] = dict()
            for group in self._network_client.network_security_groups.list(resource_group):
                if group.network_interfaces:
                    for interface in group.network_interfaces:
                        self._security_groups[resource_group][interface.id] = dict(
                            name=group.name,
                            id=group.id
                        )

    def _get_powerstate(self, resource_group, name):
        try:
            vm = self._compute_client.virtual_machines.get(resource_group,
                                                           name,
                                                           expand='instanceview')
        except Exception as exc:
            sys.exit("Error: fetching instanceview for host {0} - {1}".format(name, str(exc)))

        return next((s.code.replace('PowerState/', '')
                    for s in vm.instance_view.statuses if s.code.startswith('PowerState')), None)

    def _add_host(self, vars):

        host_name = self._to_safe(vars['name'])
        resource_group = self._to_safe(vars['resource_group'])
        security_group = None
        if vars.get('security_group'):
            security_group = self._to_safe(vars['security_group'])

        if self.group_by_resource_group:
            if not self._inventory.get(resource_group):
                self._inventory[resource_group] = []
            self._inventory[resource_group].append(host_name)

        if self.group_by_location:
            if not self._inventory.get(vars['location']):
                self._inventory[vars['location']] = []
            self._inventory[vars['location']].append(host_name)

        if self.group_by_security_group and security_group:
            if not self._inventory.get(security_group):
                self._inventory[security_group] = []
            self._inventory[security_group].append(host_name)

        self._inventory['_meta']['hostvars'][host_name] = vars
        self._inventory['azure'].append(host_name)

        if self.group_by_tag and vars.get('tags'):
            for key, value in vars['tags'].items():
                safe_key = self._to_safe(key)
                safe_value = safe_key + '_' + self._to_safe(value)
                if not self._inventory.get(safe_key):
                    self._inventory[safe_key] = []
                if not self._inventory.get(safe_value):
                    self._inventory[safe_value] = []
                self._inventory[safe_key].append(host_name)
                self._inventory[safe_value].append(host_name)

    def _json_format_dict(self, pretty=False):
        # convert inventory to json
        if pretty:
            return json.dumps(self._inventory, sort_keys=True, indent=2)
        else:
            return json.dumps(self._inventory)

    def _get_settings(self):
        # Load settings from the .ini, if it exists. Otherwise,
        # look for environment values.
        file_settings = self._load_settings()
        if file_settings:
            for key in AZURE_CONFIG_SETTINGS:
                if key in ('resource_groups', 'tags', 'locations') and file_settings.get(key):
                    values = file_settings.get(key).split(',')
                    if len(values) > 0:
                        setattr(self, key, values)
                elif file_settings.get(key):
                    val = self._to_boolean(file_settings[key])
                    setattr(self, key, val)
        else:
            env_settings = self._get_env_settings()
            for key in AZURE_CONFIG_SETTINGS:
                if key in('resource_groups', 'tags', 'locations') and env_settings.get(key):
                    values = env_settings.get(key).split(',')
                    if len(values) > 0:
                        setattr(self, key, values)
                elif env_settings.get(key, None) is not None:
                    val = self._to_boolean(env_settings[key])
                    setattr(self, key, val)

    def _parse_ref_id(self, reference):
        response = {}
        keys = reference.strip('/').split('/')
        for index in range(len(keys)):
            if index < len(keys) - 1 and index % 2 == 0:
                response[keys[index]] = keys[index + 1]
        return response

    def _to_boolean(self, value):
        if value in ['Yes', 'yes', 1, 'True', 'true', True]:
            result = True
        elif value in ['No', 'no', 0, 'False', 'false', False]:
            result = False
        else:
            result = True
        return result

    def _get_env_settings(self):
        env_settings = dict()
        for attribute, env_variable in AZURE_CONFIG_SETTINGS.items():
            env_settings[attribute] = os.environ.get(env_variable, None)
        return env_settings

    def _load_settings(self):
        basename = os.path.splitext(os.path.basename(__file__))[0]
        default_path = os.path.join(os.path.dirname(__file__), (basename + '.ini'))
        path = os.path.expanduser(os.path.expandvars(os.environ.get('AZURE_INI_PATH', default_path)))
        config = None
        settings = None
        try:
            config = cp.ConfigParser()
            config.read(path)
        except:
            pass

        if config is not None:
            settings = dict()
            for key in AZURE_CONFIG_SETTINGS:
                try:
                    settings[key] = config.get('azure', key, raw=True)
                except:
                    pass

        return settings

    def _tags_match(self, tag_obj, tag_args):
        '''
        Return True if the tags object from a VM contains the requested tag values.

        :param tag_obj:  Dictionary of string:string pairs
        :param tag_args: List of strings in the form key=value
        :return: boolean
        '''

        if not tag_obj:
            return False

        matches = 0
        for arg in tag_args:
            arg_key = arg
            arg_value = None
            if re.search(r':', arg):
                arg_key, arg_value = arg.split(':')
            if arg_value and tag_obj.get(arg_key, None) == arg_value:
                matches += 1
            elif not arg_value and tag_obj.get(arg_key, None) is not None:
                matches += 1
        if matches == len(tag_args):
            return True
        return False

    def _to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be used as Ansible groups '''
        regex = r"[^A-Za-z0-9\_"
        if not self.replace_dash_in_groups:
            regex += r"\-"
        return re.sub(regex + "]", "_", word)


def main():
    if not HAS_AZURE:
        sys.exit("The Azure python sdk is not installed (try `pip install 'azure>={0}' --upgrade`) - {1}".format(AZURE_MIN_VERSION, HAS_AZURE_EXC))

    AzureInventory()


if __name__ == '__main__':
    main()
