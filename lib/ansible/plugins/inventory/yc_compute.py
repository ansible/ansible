# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: yc_compute
    plugin_type: inventory
    short_description: Yandex.Cloud Compute inventory source
    requirements:
      - yandexcloud==0.10.1
    extends_documentation_fragment:
      - constructed
      - inventory_cache
    description:
      - Pull inventory from Yandex Cloud Compute.
      - Uses a YAML configuration file that ends with yc_compute.(yml|yaml) or yc.(yml|yaml).
    version_added: "2.10"
    options:
      auth_kind:
        description: The type of credential used.
        required: True
        choices: ['oauth', 'serviceaccountfile']
        env:
          - name: YC_ANSIBLE_AUTH_KIND
      oauth_token:
        description: OAUTH token string. See U(https://cloud.yandex.com/docs/iam/concepts/authorization/oauth-token).
        type: string
        env:
          - name: YC_ANSIBLE_OAUTH_TOKEN
      service_account_file:
        description:
          - The path of a Service Account JSON file. Must be set if auth_kind is "serviceaccountfile".
          - "Service Account JSON file can be created by C(yc) tool:"
          - C(yc iam key create --service-account-name my_service_account --output my_service_account.json)
        type: path
        env:
          - name: YC_ANSIBLE_SERVICE_ACCOUNT_FILE
      service_account_contents:
        description: Similar to service_account_file. Should contain raw contents of the Service Account JSON file.
        type: string
        env:
          - name: YC_ANSIBLE_SERVICE_ACCOUNT_CONTENTS
      hostnames:
        description:
          - The list of methods for determining the hostname.
          - Several methods can be tried one by one. Until successful hostname detection.
          - Currently supported methods are 'public_ip', 'private_ip' and 'fqdn'.
          - Any other value is parsed as a jinja2 expression.
        default: ['public_ip', 'private_ip', 'fqdn']
        type: list
      folders:
        description: List of Yandex.Cloud folder ID's to list instances from.
        type: list
        required: True
      remote_filter:
        description:
          - Sets C(filter) parameter for C(list) API call.
          - Currently you can use filtering only on the Instance.name field.
          - See U(https://cloud.yandex.com/docs/compute/api-ref/Instance/list).
          - Use C(filters) option for more flexible client-side filtering.
        type: string
      filters:
        description:
          - List of jinja2 expressions to perform client-side hosts filtering.
          - Possible fields are described here U(https://cloud.yandex.com/docs/compute/api-ref/Instance/list).
          - When overriding this option don't forget to explicitly include default value to your rules (if you need it).
        type: list
        default: status == 'RUNNING'
      api_retry_count:
        description: Retries count for API calls.
        type: int
        default: 5
'''

EXAMPLES = r'''
plugin: yc_compute
folders:  # List inventory hosts from these folders.
  - <your_folder_id>
filters:
  - status == 'RUNNING'
  - labels['role'] == 'db'
auth_kind: serviceaccountfile
service_account_file: /path/to/your/service/account/file.json
hostnames:
  - fqdn  # Use FQDN for inventory hostnames.
# You can also format hostnames with jinja2 expressions like this
# - "{{id}}_{{name}}"

compose:
  # Set ansible_host to the Public IP address to connect to the host.
  # For Private IP use "network_interfaces[0].primary_v4_address.address".
  ansible_host: network_interfaces[0].primary_v4_address.one_to_one_nat.address

keyed_groups:
  # Place hosts in groups named by folder_id.
  - key: folder_id
    prefix: ''
    separator: ''
  # Place hosts in groups named by value of labels['group'].
  - key: labels['group']

groups:
  # Place hosts in 'ssd' group if they have appropriate disk_type label.
  ssd: labels['disk_type'] == 'ssd'
'''

import json

import grpc
from yandex.cloud.compute.v1.instance_service_pb2 import ListInstancesRequest
from yandex.cloud.compute.v1.instance_service_pb2_grpc import InstanceServiceStub
import yandexcloud
import json
import grpc
import yandexcloud

from google.protobuf.json_format import MessageToDict
from yandex.cloud.compute.v1.instance_service_pb2 import ListInstancesRequest
from yandex.cloud.compute.v1.instance_service_pb2_grpc import InstanceServiceStub

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_native


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = 'yc_compute'

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.sdk = None
        self.service = None

    def verify_file(self, path):
        ''' return true/false if this is possibly a valid file for this plugin to consume '''
        return super(InventoryModule, self).verify_file(path) and path.endswith((
            'yc.yml', 'yc.yaml', 'yc_compute.yml', 'yc_compute.yaml'))

    def public_ip(self, instance):
        '''Returns Public IP of instance or None'''
        return (instance
                .get('network_interfaces', [{}])[0]
                .get('primary_v4_address', {})
                .get('one_to_one_nat', {})
                .get('address'))

    def private_ip(self, instance):
        '''Returns Private IP of instance or None'''
        return (instance
                .get('network_interfaces', [{}])[0]
                .get('primary_v4_address', {})
                .get('address'))

    def choose_hostname(self, instance):
        '''Choose hostname for given instance'''
        hostnames = self.get_option('hostnames')
        if not hostnames:
            raise AnsibleError('hostnames option should not be empty')
        for expr in hostnames:
            if expr == 'public_ip':
                name = self.public_ip(instance)
            elif expr == 'private_ip':
                name = self.private_ip(instance)
            elif expr == 'fqdn':
                name = instance['fqdn']
            else:
                self.templar.set_available_variables(instance)
                name = self.templar.template(expr)
            if name:
                return name
        raise AnsibleError("No valid name found for host")

    def filter_host(self, variables, strict=False):
        '''
        Apply client-side host filtering.
        :param variables: variables to run expression with.
        :param strict: should it raise exceptions on errors or not.
        :return: True if host pass filters and should be included in inventory.
        '''
        filters = self.get_option('filters')
        if not filters:
            return True

        self.templar.set_available_variables(variables)
        for rule in filters:
            conditional = '{{% if {0} %}} True {{% else %}} False {{% endif %}}'.format(rule)
            try:
                return boolean(self.templar.template(conditional))
            except Exception as e:
                if strict:
                    raise AnsibleParserError('Could not apply host filter "{0}": {1}'.format(rule, to_native(e)))
                continue

    def list_instances(self, folder_id, remote_filter):
        '''Make API calls to list folder with given ID. Wraps pagination loop. Returns generator.'''
        page_token = None
        while True:
            response = self.service.List(
                ListInstancesRequest(folder_id=folder_id, filter=remote_filter, page_token=page_token))
            for instance in response.instances:
                yield MessageToDict(instance, preserving_proto_field_name=True)
            page_token = response.next_page_token
            if not page_token:
                break

    def populate(self, instances):
        '''Populate inventory with given instances'''
        strict = self.get_option('strict')
        for instance in instances:
            hostname = self.choose_hostname(instance)
            if self.filter_host(variables=instance, strict=strict):
                self.inventory.add_host(host=hostname)
                self._set_composite_vars(
                    compose=self.get_option('compose'),
                    variables=instance,
                    host=hostname,
                    strict=strict)
                self._add_host_to_composed_groups(
                    groups=self.get_option('groups'),
                    variables=instance,
                    host=hostname,
                    strict=strict)
                self._add_host_to_keyed_groups(
                    keys=self.get_option('keyed_groups'),
                    variables=instance,
                    host=hostname,
                    strict=strict)

    def init_sdk(self):
        '''Init Yandex.Cloud SDK with provided auth method'''
        interceptor = yandexcloud.RetryInterceptor(
            max_retry_count=self.get_option('api_retry_count'),
            retriable_codes=[grpc.StatusCode.UNAVAILABLE])
        auth_kind = self.get_option('auth_kind')
        if auth_kind == 'serviceaccountfile':
            sa_file_path = self.get_option('service_account_file')
            sa_file_contents = self.get_option('service_account_contents')
            if bool(sa_file_path) == bool(sa_file_contents):
                raise AnsibleError('Either "service_account_file" or "service_account_contents" must be set '
                                   'when auth_kind is set to "serviceaccountfile"')
            if sa_file_path:
                try:
                    with open(sa_file_path, 'r') as f:
                        sa_file_contents = f.read()
                except Exception as e:
                    raise AnsibleError('Error reading Service Account data from file: "{0}": {1}'
                                       .format(sa_file_path, to_native(e)))
            try:
                sa = json.loads(sa_file_contents)
            except Exception as e:
                raise AnsibleError('Error reading Service Account data from JSON: {0}'.format(to_native(e)))
            self.sdk = yandexcloud.SDK(interceptor=interceptor, service_account_key=sa)

        elif auth_kind == 'oauth':
            oauth_token = self.get_option('oauth_token')
            if not oauth_token:
                raise AnsibleError('oauth_token should be set')
            self.sdk = yandexcloud.SDK(interceptor=interceptor, token=oauth_token)
        else:
            raise AnsibleError('Unknown value for auth_kind: {0}'.format(auth_kind))

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)
        self.init_sdk()
        self.service = self.sdk.client(InstanceServiceStub)

        cache_key = self.get_cache_key(path)
        # cache may be True or False at this point to indicate if the inventory is being refreshed
        # get the user's cache option too to see if we should save the cache if it is changing.
        user_cache_setting = self.get_option('cache')
        # read if the user has caching enabled and the cache isn't being refreshed.
        attempt_to_read_cache = user_cache_setting and cache
        # update if the user has caching enabled and the cache is being refreshed; update this value to True
        # if the cache has expired below.
        cache_needs_update = user_cache_setting and not cache
        instances = None
        # attempt to read the cache if inventory isn't being refreshed and the user has caching enabled.
        if attempt_to_read_cache:
            try:
                instances = self._cache[cache_key]
            except KeyError:
                # This occurs if the cache_key is not in the cache or if the cache_key expired,
                # so the cache needs to be updated.
                cache_needs_update = True

        if not instances:
            instances = []
            remote_filter = self.get_option('remote_filter')
            for folder_id in (self.get_option('folders') or []):
                instances.extend(self.list_instances(folder_id=folder_id, remote_filter=remote_filter))

        if cache_needs_update:
            self._cache[cache_key] = instances

        self.populate(instances)
