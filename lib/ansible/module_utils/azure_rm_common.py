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

import json
import os
import re
import sys
import copy
import importlib
import inspect

from packaging.version import Version
from os.path import expanduser

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import configparser

AZURE_COMMON_ARGS = dict(
    profile=dict(type='str'),
    subscription_id=dict(type='str', no_log=True),
    client_id=dict(type='str', no_log=True),
    secret=dict(type='str', no_log=True),
    tenant=dict(type='str', no_log=True),
    ad_user=dict(type='str', no_log=True),
    password=dict(type='str', no_log=True),
    # debug=dict(type='bool', default=False),
)

AZURE_CREDENTIAL_ENV_MAPPING = dict(
    profile='AZURE_PROFILE',
    subscription_id='AZURE_SUBSCRIPTION_ID',
    client_id='AZURE_CLIENT_ID',
    secret='AZURE_SECRET',
    tenant='AZURE_TENANT',
    ad_user='AZURE_AD_USER',
    password='AZURE_PASSWORD'
)

AZURE_TAG_ARGS = dict(
    tags=dict(type='dict'),
    append_tags=dict(type='bool', default=True),
)

AZURE_COMMON_REQUIRED_IF = [
    ('log_mode', 'file', ['log_path'])
]

ANSIBLE_USER_AGENT = 'Ansible-Deploy'

CIDR_PATTERN = re.compile("(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1"
                          "[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))")

AZURE_SUCCESS_STATE = "Succeeded"
AZURE_FAILED_STATE = "Failed"

HAS_AZURE = True
HAS_AZURE_EXC = None

HAS_MSRESTAZURE = True
HAS_MSRESTAZURE_EXC = None

# NB: packaging issue sometimes cause msrestazure not to be installed, check it separately
try:
    from msrest.serialization import Serializer
except ImportError as exc:
    HAS_MSRESTAZURE_EXC = exc
    HAS_MSRESTAZURE = False

try:
    from enum import Enum
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network.models import PublicIPAddress, NetworkSecurityGroup, SecurityRule, NetworkInterface, \
        NetworkInterfaceIPConfiguration, Subnet
    from azure.common.credentials import ServicePrincipalCredentials, UserPassCredentials
    from azure.mgmt.network.version import VERSION as network_client_version
    from azure.mgmt.storage.version import VERSION as storage_client_version
    from azure.mgmt.compute.version import VERSION as compute_client_version
    from azure.mgmt.resource.version import VERSION as resource_client_version
    from azure.mgmt.network.network_management_client import NetworkManagementClient
    from azure.mgmt.resource.resources.resource_management_client import ResourceManagementClient
    from azure.mgmt.storage.storage_management_client import StorageManagementClient
    from azure.mgmt.compute.compute_management_client import ComputeManagementClient
    from azure.storage.cloudstorageaccount import CloudStorageAccount
except ImportError as exc:
    HAS_AZURE_EXC = exc
    HAS_AZURE = False


def azure_id_to_dict(id):
    pieces = re.sub(r'^\/', '', id).split('/')
    result = {}
    index = 0
    while index < len(pieces) - 1:
        result[pieces[index]] = pieces[index + 1]
        index += 1
    return result


AZURE_EXPECTED_VERSIONS = dict(
    storage_client_version="0.30.0rc5",
    compute_client_version="0.30.0rc5",
    network_client_version="0.30.0rc5",
    resource_client_version="0.30.0rc5"
)

AZURE_MIN_RELEASE = '2.0.0rc5'


class AzureRMModuleBase(object):

    def __init__(self, derived_arg_spec, bypass_checks=False, no_log=False,
                 check_invalid_arguments=True, mutually_exclusive=None, required_together=None,
                 required_one_of=None, add_file_common_args=False, supports_check_mode=False,
                 required_if=None, supports_tags=True, facts_module=False):

        merged_arg_spec = dict()
        merged_arg_spec.update(AZURE_COMMON_ARGS)
        if supports_tags:
            merged_arg_spec.update(AZURE_TAG_ARGS)

        if derived_arg_spec:
            merged_arg_spec.update(derived_arg_spec)

        merged_required_if = list(AZURE_COMMON_REQUIRED_IF)
        if required_if:
            merged_required_if += required_if

        self.module = AnsibleModule(argument_spec=merged_arg_spec,
                                    bypass_checks=bypass_checks,
                                    no_log=no_log,
                                    check_invalid_arguments=check_invalid_arguments,
                                    mutually_exclusive=mutually_exclusive,
                                    required_together=required_together,
                                    required_one_of=required_one_of,
                                    add_file_common_args=add_file_common_args,
                                    supports_check_mode=supports_check_mode,
                                    required_if=merged_required_if)

        if not HAS_MSRESTAZURE:
            self.fail("Do you have msrestazure installed? Try `pip install msrestazure`"
                      "- {0}".format(HAS_MSRESTAZURE_EXC))

        if not HAS_AZURE:
            self.fail("Do you have azure>={1} installed? Try `pip install 'azure>={1}' --upgrade`"
                      "- {0}".format(HAS_AZURE_EXC, AZURE_MIN_RELEASE))

        self._network_client = None
        self._storage_client = None
        self._resource_client = None
        self._compute_client = None
        self.check_mode = self.module.check_mode
        self.facts_module = facts_module
        # self.debug = self.module.params.get('debug')

        # authenticate
        self.credentials = self._get_credentials(self.module.params)
        if not self.credentials:
            self.fail("Failed to get credentials. Either pass as parameters, set environment variables, "
                      "or define a profile in ~/.azure/credentials.")

        if self.credentials.get('subscription_id', None) is None:
            self.fail("Credentials did not include a subscription_id value.")
        self.log("setting subscription_id")
        self.subscription_id = self.credentials['subscription_id']

        if self.credentials.get('client_id') is not None and \
           self.credentials.get('secret') is not None and \
           self.credentials.get('tenant') is not None:
            self.azure_credentials = ServicePrincipalCredentials(client_id=self.credentials['client_id'],
                                                                 secret=self.credentials['secret'],
                                                                 tenant=self.credentials['tenant'])
        elif self.credentials.get('ad_user') is not None and self.credentials.get('password') is not None:
            tenant = self.credentials.get('tenant')
            if tenant is not None:
                self.azure_credentials = UserPassCredentials(self.credentials['ad_user'], self.credentials['password'], tenant=tenant)
            else:
                self.azure_credentials = UserPassCredentials(self.credentials['ad_user'], self.credentials['password'])
        else:
            self.fail("Failed to authenticate with provided credentials. Some attributes were missing. "
                      "Credentials must include client_id, secret and tenant or ad_user and password.")

        # common parameter validation
        if self.module.params.get('tags'):
            self.validate_tags(self.module.params['tags'])

        res = self.exec_module(**self.module.params)
        self.module.exit_json(**res)

    def check_client_version(self, client_name, client_version, expected_version):
        # Ensure Azure modules are at least 2.0.0rc5.
        if Version(client_version) < Version(expected_version):
            self.fail("Installed {0} client version is {1}. The supported version is {2}. Try "
                      "`pip install azure>={3} --upgrade`".format(client_name, client_version, expected_version,
                                                                  AZURE_MIN_RELEASE))

    def exec_module(self, **kwargs):
        self.fail("Error: {0} failed to implement exec_module method.".format(self.__class__.__name__))

    def fail(self, msg, **kwargs):
        '''
        Shortcut for calling module.fail()

        :param msg: Error message text.
        :param kwargs: Any key=value pairs
        :return: None
        '''
        self.module.fail_json(msg=msg, **kwargs)

    def log(self, msg, pretty_print=False):
        pass
        # Use only during module development
        # if self.debug:
        #     log_file = open('azure_rm.log', 'a')
        #     if pretty_print:
        #         log_file.write(json.dumps(msg, indent=4, sort_keys=True))
        #     else:
        #         log_file.write(msg + u'\n')

    def validate_tags(self, tags):
        '''
        Check if tags dictionary contains string:string pairs.

        :param tags: dictionary of string:string pairs
        :return: None
        '''
        if not self.facts_module:
            if not isinstance(tags, dict):
                self.fail("Tags must be a dictionary of string:string values.")
            for key, value in tags.items():
                if not isinstance(value, str):
                    self.fail("Tags values must be strings. Found {0}:{1}".format(str(key), str(value)))

    def update_tags(self, tags):
        '''
        Call from the module to update metadata tags. Returns tuple
        with bool indicating if there was a change and dict of new
        tags to assign to the object.

        :param tags: metadata tags from the object
        :return: bool, dict
        '''
        new_tags = copy.copy(tags) if isinstance(tags, dict) else dict()
        changed = False
        if isinstance(self.module.params.get('tags'), dict):
            for key, value in self.module.params['tags'].items():
                if not new_tags.get(key) or new_tags[key] != value:
                    changed = True
                    new_tags[key] = value
            if isinstance(tags, dict):
                for key, value in tags.items():
                    if not self.module.params['tags'].get(key):
                        new_tags.pop(key)
                        changed = True
        return changed, new_tags

    def has_tags(self, obj_tags, tag_list):
        '''
        Used in fact modules to compare object tags to list of parameter tags. Return true if list of parameter tags
        exists in object tags.

        :param obj_tags: dictionary of tags from an Azure object.
        :param tag_list: list of tag keys or tag key:value pairs
        :return: bool
        '''

        if not obj_tags and tag_list:
            return False

        if not tag_list:
            return True

        matches = 0
        result = False
        for tag in tag_list:
            tag_key = tag
            tag_value = None
            if ':' in tag:
                tag_key, tag_value = tag.split(':')
            if tag_value and obj_tags.get(tag_key) == tag_value:
                matches += 1
            elif not tag_value and obj_tags.get(tag_key):
                matches += 1
        if matches == len(tag_list):
            result = True
        return result

    def get_resource_group(self, resource_group):
        '''
        Fetch a resource group.

        :param resource_group: name of a resource group
        :return: resource group object
        '''
        try:
            return self.rm_client.resource_groups.get(resource_group)
        except CloudError:
            self.fail("Parameter error: resource group {0} not found".format(resource_group))
        except Exception as exc:
            self.fail("Error retrieving resource group {0} - {1}".format(resource_group, str(exc)))

    def _get_profile(self, profile="default"):
        path = expanduser("~/.azure/credentials")
        try:
            config = configparser.ConfigParser()
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

        if credentials.get('subscription_id'):
            return credentials

        return None

    def _get_env_credentials(self):
        env_credentials = dict()
        for attribute, env_variable in AZURE_CREDENTIAL_ENV_MAPPING.items():
            env_credentials[attribute] = os.environ.get(env_variable, None)

        if env_credentials['profile']:
            credentials = self._get_profile(env_credentials['profile'])
            return credentials

        if env_credentials.get('subscription_id') is not None:
            return env_credentials

        return None

    def _get_credentials(self, params):
        # Get authentication credentials.
        # Precedence: module parameters-> environment variables-> default profile in ~/.azure/credentials.

        self.log('Getting credentials')

        arg_credentials = dict()
        for attribute, env_variable in AZURE_CREDENTIAL_ENV_MAPPING.items():
            arg_credentials[attribute] = params.get(attribute, None)

        # try module params
        if arg_credentials['profile'] is not None:
            self.log('Retrieving credentials with profile parameter.')
            credentials = self._get_profile(arg_credentials['profile'])
            return credentials

        if arg_credentials['subscription_id']:
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

    def serialize_obj(self, obj, class_name, enum_modules=[]):
        '''
        Return a JSON representation of an Azure object.

        :param obj: Azure object
        :param class_name: Name of the object's class
        :param enum_modules: List of module names to build enum dependencies from.
        :return: serialized result
        '''
        dependencies = dict()
        if enum_modules:
            for module_name in enum_modules:
                mod = importlib.import_module(module_name)
                for mod_class_name, mod_class_obj in inspect.getmembers(mod, predicate=inspect.isclass):
                    dependencies[mod_class_name] = mod_class_obj
            self.log("dependencies: ")
            self.log(str(dependencies))
        serializer = Serializer(classes=dependencies)
        return serializer.body(obj, class_name)

    def get_poller_result(self, poller, wait=5):
        '''
        Consistent method of waiting on and retrieving results from Azure's long poller

        :param poller Azure poller object
        :return object resulting from the original request
        '''
        try:
            delay = wait
            while not poller.done():
                self.log("Waiting for {0} sec".format(delay))
                poller.wait(timeout=delay)
            return poller.result()
        except Exception as exc:
            self.log(str(exc))
            raise

    def check_provisioning_state(self, azure_object, requested_state='present'):
        '''
        Check an Azure object's provisioning state. If something did not complete the provisioning
        process, then we cannot operate on it.

        :param azure_object An object such as a subnet, storageaccount, etc. Must have provisioning_state
                            and name attributes.
        :return None
        '''

        if hasattr(azure_object, 'properties') and hasattr(azure_object.properties, 'provisioning_state') and \
           hasattr(azure_object, 'name'):
            # resource group object fits this model
            if isinstance(azure_object.properties.provisioning_state, Enum):
                if azure_object.properties.provisioning_state.value != AZURE_SUCCESS_STATE and \
                   requested_state != 'absent':
                    self.fail("Error {0} has a provisioning state of {1}. Expecting state to be {2}.".format(
                              azure_object.name, azure_object.properties.provisioning_state, AZURE_SUCCESS_STATE))
                return
            if azure_object.properties.provisioning_state != AZURE_SUCCESS_STATE and \
               requested_state != 'absent':
                self.fail("Error {0} has a provisioning state of {1}. Expecting state to be {2}.".format(
                    azure_object.name, azure_object.properties.provisioning_state, AZURE_SUCCESS_STATE))
            return

        if hasattr(azure_object, 'provisioning_state') or not hasattr(azure_object, 'name'):
            if isinstance(azure_object.provisioning_state, Enum):
                if azure_object.provisioning_state.value != AZURE_SUCCESS_STATE and requested_state != 'absent':
                    self.fail("Error {0} has a provisioning state of {1}. Expecting state to be {2}.".format(
                        azure_object.name, azure_object.provisioning_state, AZURE_SUCCESS_STATE))
                return
            if azure_object.provisioning_state != AZURE_SUCCESS_STATE and requested_state != 'absent':
                self.fail("Error {0} has a provisioning state of {1}. Expecting state to be {2}.".format(
                    azure_object.name, azure_object.provisioning_state, AZURE_SUCCESS_STATE))

    def get_blob_client(self, resource_group_name, storage_account_name):
        keys = dict()
        try:
            # Get keys from the storage account
            self.log('Getting keys')
            account_keys = self.storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
        except Exception as exc:
            self.fail("Error getting keys for account {0} - {1}".format(storage_account_name, str(exc)))

        try:
            self.log('Create blob service')
            return CloudStorageAccount(storage_account_name, account_keys.keys[0].value).create_block_blob_service()
        except Exception as exc:
            self.fail("Error creating blob service client for storage account {0} - {1}".format(storage_account_name,
                                                                                                str(exc)))

    def create_default_pip(self, resource_group, location, name, allocation_method='Dynamic'):
        '''
        Create a default public IP address <name>01 to associate with a network interface.
        If a PIP address matching <vm name>01 exists, return it. Otherwise, create one.

        :param resource_group: name of an existing resource group
        :param location: a valid azure location
        :param name: base name to assign the public IP address
        :param allocation_method: one of 'Static' or 'Dynamic'
        :return: PIP object
        '''
        public_ip_name = name + '01'
        pip = None

        self.log("Starting create_default_pip {0}".format(public_ip_name))
        self.log("Check to see if public IP {0} exists".format(public_ip_name))
        try:
            pip = self.network_client.public_ip_addresses.get(resource_group, public_ip_name)
        except CloudError:
            pass

        if pip:
            self.log("Public ip {0} found.".format(public_ip_name))
            self.check_provisioning_state(pip)
            return pip

        params = PublicIPAddress(
            location=location,
            public_ip_allocation_method=allocation_method,
        )
        self.log('Creating default public IP {0}'.format(public_ip_name))
        try:
            poller = self.network_client.public_ip_addresses.create_or_update(resource_group, public_ip_name, params)
        except Exception as exc:
            self.fail("Error creating {0} - {1}".format(public_ip_name, str(exc)))

        return self.get_poller_result(poller)

    def create_default_securitygroup(self, resource_group, location, name, os_type, open_ports):
        '''
        Create a default security group <name>01 to associate with a network interface. If a security group matching
        <name>01 exists, return it. Otherwise, create one.

        :param resource_group: Resource group name
        :param location: azure location name
        :param name: base name to use for the security group
        :param os_type: one of 'Windows' or 'Linux'. Determins any default rules added to the security group.
        :param ssh_port: for os_type 'Linux' port used in rule allowing SSH access.
        :param rdp_port: for os_type 'Windows' port used in rule allowing RDP access.
        :return: security_group object
        '''
        security_group_name = name + '01'
        group = None

        self.log("Create security group {0}".format(security_group_name))
        self.log("Check to see if security group {0} exists".format(security_group_name))
        try:
            group = self.network_client.network_security_groups.get(resource_group, security_group_name)
        except CloudError:
            pass

        if group:
            self.log("Security group {0} found.".format(security_group_name))
            self.check_provisioning_state(group)
            return group

        parameters = NetworkSecurityGroup()
        parameters.location = location

        if not open_ports:
            # Open default ports based on OS type
            if os_type == 'Linux':
                # add an inbound SSH rule
                parameters.security_rules = [
                    SecurityRule('Tcp', '*', '*', 'Allow', 'Inbound', description='Allow SSH Access',
                                 source_port_range='*', destination_port_range='22', priority=100, name='SSH')
                ]
                parameters.location = location
            else:
                # for windows add inbound RDP and WinRM rules
                parameters.security_rules = [
                    SecurityRule('Tcp', '*', '*', 'Allow', 'Inbound', description='Allow RDP port 3389',
                                 source_port_range='*', destination_port_range='3389', priority=100, name='RDP01'),
                    SecurityRule('Tcp', '*', '*', 'Allow', 'Inbound', description='Allow WinRM HTTPS port 5986',
                                 source_port_range='*', destination_port_range='5986', priority=101, name='WinRM01'),
                ]
        else:
            # Open custom ports
            parameters.security_rules = []
            priority = 100
            for port in open_ports:
                priority += 1
                rule_name = "Rule_{0}".format(priority)
                parameters.security_rules.append(
                    SecurityRule('Tcp', '*', '*', 'Allow', 'Inbound', source_port_range='*',
                                 destination_port_range=str(port), priority=priority, name=rule_name)
                )

        self.log('Creating default security group {0}'.format(security_group_name))
        try:
            poller = self.network_client.network_security_groups.create_or_update(resource_group,
                                                                                  security_group_name,
                                                                                  parameters)
        except Exception as exc:
            self.fail("Error creating default security rule {0} - {1}".format(security_group_name, str(exc)))

        return self.get_poller_result(poller)

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
    def storage_client(self):
        self.log('Getting storage client...')
        if not self._storage_client:
            self.check_client_version('storage', storage_client_version, AZURE_EXPECTED_VERSIONS['storage_client_version'])
            self._storage_client = StorageManagementClient(self.azure_credentials, self.subscription_id)
            self._register('Microsoft.Storage')
        return self._storage_client

    @property
    def network_client(self):
        self.log('Getting network client')
        if not self._network_client:
            self.check_client_version('network', network_client_version, AZURE_EXPECTED_VERSIONS['network_client_version'])
            self._network_client = NetworkManagementClient(self.azure_credentials, self.subscription_id)
            self._register('Microsoft.Network')
        return self._network_client

    @property
    def rm_client(self):
        self.log('Getting resource manager client')
        if not self._resource_client:
            self.check_client_version('resource', resource_client_version, AZURE_EXPECTED_VERSIONS['resource_client_version'])
            self._resource_client = ResourceManagementClient(self.azure_credentials, self.subscription_id)
        return self._resource_client

    @property
    def compute_client(self):
        self.log('Getting compute client')
        if not self._compute_client:
            self.check_client_version('compute', compute_client_version, AZURE_EXPECTED_VERSIONS['compute_client_version'])
            self._compute_client = ComputeManagementClient(self.azure_credentials, self.subscription_id)
            self._register('Microsoft.Compute')
        return self._compute_client
