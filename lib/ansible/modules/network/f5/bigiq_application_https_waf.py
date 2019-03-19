#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigiq_application_https_waf
short_description: Manages BIG-IQ HTTPS WAF applications
description:
  - Manages BIG-IQ applications used for load balancing an HTTPS application on port 443
    with a Web Application Firewall (WAF) using an ASM Rapid Deployment policy.
version_added: 2.6
options:
  name:
    description:
      - Name of the new application.
    type: str
    required: True
  description:
    description:
      - Description of the application.
    type: str
  servers:
    description:
      - A list of servers that the application is hosted on.
      - If you are familiar with other BIG-IP setting, you might also refer to this
        list as the list of pool members.
      - When creating a new application, at least one server is required.
    suboptions:
      address:
        description:
          - The IP address of the server.
        type: str
      port:
        description:
          - The port of the server.
        type: str
        default: 80
    type: list
  inbound_virtual:
    description:
      - Settings to configure the virtual which will receive the inbound connection.
      - This virtual will be used to host the HTTPS endpoint of the application.
      - Traffic destined to the C(redirect_virtual) will be offloaded to this
        parameter to ensure that proper redirection from insecure, to secure, occurs.
    suboptions:
      address:
        description:
          - Specifies destination IP address information to which the virtual server
            sends traffic.
          - This parameter is required when creating a new application.
        type: str
      netmask:
        description:
          - Specifies the netmask to associate with the given C(destination).
          - This parameter is required when creating a new application.
        type: str
      port:
        description:
          - The port that the virtual listens for connections on.
          - When creating a new application, if this parameter is not specified, the
            default value of C(443) will be used.
        type: str
        default: 443
    type: dict
  redirect_virtual:
    description:
      - Settings to configure the virtual which will receive the connection to be
        redirected.
      - This virtual will be used to host the HTTP endpoint of the application.
      - Traffic destined to this parameter will be offloaded to the
        C(inbound_virtual) parameter to ensure that proper redirection from insecure,
        to secure, occurs.
    suboptions:
      address:
        description:
          - Specifies destination IP address information to which the virtual server
            sends traffic.
          - This parameter is required when creating a new application.
        type: str
      netmask:
        description:
          - Specifies the netmask to associate with the given C(destination).
          - This parameter is required when creating a new application.
        type: str
      port:
        description:
          - The port that the virtual listens for connections on.
          - When creating a new application, if this parameter is not specified, the
            default value of C(80) will be used.
        type: str
        default: 80
    type: dict
  client_ssl_profile:
    description:
      - Specifies the SSL profile for managing client-side SSL traffic.
    suboptions:
      name:
        description:
          - The name of the client SSL profile to created and used.
          - When creating a new application, if this value is not specified, the
            default value of C(clientssl) will be used.
        type: str
      cert_key_chain:
        description:
          - One or more certificates and keys to associate with the SSL profile.
          - This option is always a list. The keys in the list dictate the details
            of the client/key/chain/passphrase combination.
          - Note that BIG-IPs can only have one of each type of each certificate/key
            type. This means that you can only have one RSA, one DSA, and one ECDSA
            per profile.
          - If you attempt to assign two RSA, DSA, or ECDSA certificate/key combo,
            the device will reject this.
          - This list is a complex list that specifies a number of keys.
          - When creating a new profile, if this parameter is not specified, the
            default value of C(inherit) will be used.
        suboptions:
          cert:
            description:
              - Specifies a cert name for use.
            type: str
            required: True
          key:
            description:
              - Specifies a key name.
            type: str
            required: True
          chain:
            description:
              - Specifies a certificate chain that is relevant to the certificate and
                key mentioned earlier.
              - This key is optional.
            type: str
          passphrase:
            description:
              - Contains the passphrase of the key file, should it require one.
              - Passphrases are encrypted on the remote BIG-IP device.
            type: str
        type: raw
    type: dict
  service_environment:
    description:
      - Specifies the name of service environment that the application will be
        deployed to.
      - When creating a new application, this parameter is required.
    type: str
  add_analytics:
    description:
      - Collects statistics of the BIG-IP that the application is deployed to.
      - This parameter is only relevant when specifying a C(service_environment) which
        is a BIG-IP; not an SSG.
    type: bool
    default: no
  domain_names:
    description:
      - Specifies host names that are used to access the web application that this
        security policy protects.
      - When creating a new application, this parameter is required.
    type: list
  state:
    description:
      - The state of the resource on the system.
      - When C(present), guarantees that the resource exists with the provided attributes.
      - When C(absent), removes the resource from the system.
    type: str
    choices:
      - absent
      - present
    default: present
  wait:
    description:
      - If the module should wait for the application to be created, deleted or updated.
    type: bool
    default: yes
extends_documentation_fragment: f5
notes:
  - This module will not work on BIGIQ version 6.1.x or greater.
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Load balance an HTTPS application on port 443 with a WAF using ASM
  bigiq_application_https_waf:
    name: my-app
    description: Redirect HTTP to HTTPS via WAF
    service_environment: my-ssg
    servers:
      - address: 1.2.3.4
        port: 8080
      - address: 5.6.7.8
        port: 8080
    inbound_virtual:
      address: 2.2.2.2
      netmask: 255.255.255.255
      port: 443
    redirect_virtual:
      address: 2.2.2.2
      netmask: 255.255.255.255
      port: 80
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
    state: present
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The new description of the application of the resource.
  returned: changed
  type: str
  sample: My application
service_environment:
  description: The environment which the service was deployed to.
  returned: changed
  type: str
  sample: my-ssg1
inbound_virtual_destination:
  description: The destination of the virtual that was created.
  returned: changed
  type: str
  sample: 6.7.8.9
inbound_virtual_netmask:
  description: The network mask of the provided inbound destination.
  returned: changed
  type: str
  sample: 255.255.255.0
inbound_virtual_port:
  description: The port the inbound virtual address listens on.
  returned: changed
  type: int
  sample: 80
servers:
  description: List of servers, and their ports, that make up the application.
  type: complex
  returned: changed
  contains:
    address:
      description: The IP address of the server.
      returned: changed
      type: str
      sample: 2.3.4.5
    port:
      description: The port that the server listens on.
      returned: changed
      type: int
      sample: 8080
  sample: hash/dictionary of values
'''

import time

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types

try:
    from library.module_utils.network.f5.bigiq import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.icontrol import bigiq_version
except ImportError:
    from ansible.module_utils.network.f5.bigiq import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.icontrol import bigiq_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'templateReference': 'template_reference',
        'subPath': 'sub_path',
        'ssgReference': 'ssg_reference',
        'configSetName': 'config_set_name',
        'defaultDeviceReference': 'default_device_reference',
        'addAnalytics': 'add_analytics',
        'domains': 'domain_names'
    }

    api_attributes = [
        'resources', 'description', 'configSetName', 'subPath', 'templateReference',
        'ssgReference', 'defaultDeviceReference', 'addAnalytics', 'domains'
    ]

    returnables = [
        'resources', 'description', 'config_set_name', 'sub_path', 'template_reference',
        'ssg_reference', 'default_device_reference', 'servers', 'inbound_virtual',
        'redirect_virtual', 'client_ssl_profile', 'add_analytics', 'domain_names'
    ]

    updatables = [
        'resources', 'description', 'config_set_name', 'sub_path', 'template_reference',
        'ssg_reference', 'default_device_reference', 'servers', 'add_analytics', 'domain_names'
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def http_profile(self):
        return "profile_http"

    @property
    def config_set_name(self):
        return self.name

    @property
    def sub_path(self):
        return self.name

    @property
    def template_reference(self):
        filter = "name+eq+'Default-f5-HTTPS-WAF-lb-template'"
        uri = "https://{0}:{1}/mgmt/cm/global/templates/?$filter={2}&$top=1&$select=selfLink".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            filter
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if resp.status == 200 and response['totalItems'] == 0:
            raise F5ModuleError(
                "No default HTTP LB template was found."
            )
        elif 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)

        result = dict(
            link=response['items'][0]['selfLink']
        )
        return result

    @property
    def default_device_reference(self):
        if is_valid_ip(self.service_environment):
            # An IP address was specified
            filter = "address+eq+'{0}'".format(self.service_environment)
        else:
            # Assume a hostname was specified
            filter = "hostname+eq+'{0}'".format(self.service_environment)

        uri = "https://{0}:{1}/mgmt/shared/resolver/device-groups/cm-adccore-allbigipDevices/devices/?$filter={2}&$top=1&$select=selfLink".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            filter
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if resp.status == 200 and response['totalItems'] == 0:
            return None
        elif 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)
        result = dict(
            link=response['items'][0]['selfLink']
        )
        return result

    @property
    def ssg_reference(self):
        filter = "name+eq+'{0}'".format(self.service_environment)
        uri = "https://{0}:{1}/mgmt/cm/cloud/service-scaling-groups/?$filter={2}&$top=1&$select=selfLink".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            filter
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if resp.status == 200 and response['totalItems'] == 0:
            return None
        elif 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)
        result = dict(
            link=response['items'][0]['selfLink']
        )
        return result

    @property
    def domain_names(self):
        if self._values['domain_names'] is None:
            return None
        result = []
        for domain in self._values['domain_names']:
            result.append(
                dict(
                    domainName=domain
                )
            )
        return result


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def resources(self):
        result = dict()
        result.update(self.http_profile)
        result.update(self.http_monitor)
        result.update(self.inbound_virtual_server)
        result.update(self.redirect_virtual_server)
        result.update(self.pool)
        result.update(self.nodes)
        result.update(self.ssl_profile)
        return result

    @property
    def inbound_virtual_server(self):
        result = dict()
        result['ltm:virtual:90735960bf4b'] = [
            dict(
                parameters=dict(
                    name='default_vs',
                    destinationAddress=self.inbound_virtual['address'],
                    mask=self.inbound_virtual['netmask'],
                    destinationPort=self.inbound_virtual['port']
                ),
                subcollectionResources=self.inbound_profiles
            )
        ]
        return result

    @property
    def inbound_profiles(self):
        result = {
            'profiles:78b1bcfdafad': [
                dict(
                    parameters=dict()
                )
            ],
            'profiles:2f52acac9fde': [
                dict(
                    parameters=dict()
                )
            ],
            'profiles:9448fe71611e': [
                dict(
                    parameters=dict()
                )
            ]
        }
        return result

    @property
    def redirect_virtual_server(self):
        result = dict()
        result['ltm:virtual:3341f412b980'] = [
            dict(
                parameters=dict(
                    name='default_redirect_vs',
                    destinationAddress=self.redirect_virtual['address'],
                    mask=self.redirect_virtual['netmask'],
                    destinationPort=self.redirect_virtual['port']
                ),
                subcollectionResources=self.redirect_profiles
            )
        ]
        return result

    @property
    def redirect_profiles(self):
        result = {
            'profiles:2f52acac9fde': [
                dict(
                    parameters=dict()
                )
            ],
            'profiles:9448fe71611e': [
                dict(
                    parameters=dict()
                )
            ]
        }
        return result

    @property
    def pool(self):
        result = dict()
        result['ltm:pool:8bc5b256f9d1'] = [
            dict(
                parameters=dict(
                    name='pool_0'
                ),
                subcollectionResources=self.pool_members
            )
        ]
        return result

    @property
    def pool_members(self):
        result = dict()
        result['members:dec6d24dc625'] = []
        for x in self.servers:
            member = dict(
                parameters=dict(
                    port=x['port'],
                    nodeReference=dict(
                        link='#/resources/ltm:node:c072248f8e6a/{0}'.format(x['address']),
                        fullPath='# {0}'.format(x['address'])
                    )
                )
            )
            result['members:dec6d24dc625'].append(member)
        return result

    @property
    def http_profile(self):
        result = dict()
        result['ltm:profile:http:2f52acac9fde'] = [
            dict(
                parameters=dict(
                    name='profile_http'
                )
            )
        ]
        return result

    @property
    def http_monitor(self):
        result = dict()
        result['ltm:monitor:http:18765a198150'] = [
            dict(
                parameters=dict(
                    name='monitor-http'
                )
            )
        ]
        return result

    @property
    def nodes(self):
        result = dict()
        result['ltm:node:c072248f8e6a'] = []
        for x in self.servers:
            tmp = dict(
                parameters=dict(
                    name=x['address'],
                    address=x['address']
                )
            )
            result['ltm:node:c072248f8e6a'].append(tmp)
        return result

    @property
    def node_addresses(self):
        result = [x['address'] for x in self.servers]
        return result

    @property
    def ssl_profile(self):
        result = dict()
        result['ltm:profile:client-ssl:78b1bcfdafad'] = [
            dict(
                parameters=dict(
                    name='clientssl',
                    certKeyChain=self.cert_key_chains
                )
            )
        ]
        return result

    def _get_cert_references(self):
        result = dict()
        uri = "https://{0}:{1}/mgmt/cm/adc-core/working-config/sys/file/ssl-cert/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        for cert in response['items']:
            key = fq_name(cert['partition'], cert['name'])
            result[key] = cert['selfLink']
        return result

    def _get_key_references(self):
        result = dict()
        uri = "https://{0}:{1}/mgmt/cm/adc-core/working-config/sys/file/ssl-key/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        for cert in response['items']:
            key = fq_name(cert['partition'], cert['name'])
            result[key] = cert['selfLink']
        return result

    @property
    def cert_key_chains(self):
        result = []

        if self.client_ssl_profile is None:
            return None
        if 'cert_key_chain' not in self.client_ssl_profile:
            return None

        kc = self.client_ssl_profile['cert_key_chain']
        if isinstance(kc, string_types) and kc != 'inherit':
            raise F5ModuleError(
                "Only the 'inherit' setting is available when 'cert_key_chain' is a string."
            )

        if not isinstance(kc, list):
            raise F5ModuleError(
                "The value of 'cert_key_chain' is not one of the supported types."
            )

        cert_references = self._get_cert_references()
        key_references = self._get_key_references()

        for idx, x in enumerate(kc):
            tmp = dict(
                name='clientssl{0}'.format(idx)
            )
            if 'cert' not in x:
                raise F5ModuleError(
                    "A 'cert' option is required when specifying the 'cert_key_chain' parameter.."
                )
            elif x['cert'] not in cert_references:
                raise F5ModuleError(
                    "The specified 'cert' was not found. Did you specify its full path?"
                )
            else:
                key = x['cert']
                tmp['certReference'] = dict(
                    link=cert_references[key],
                    fullPath=key
                )

            if 'key' not in x:
                raise F5ModuleError(
                    "A 'key' option is required when specifying the 'cert_key_chain' parameter.."
                )
            elif x['key'] not in key_references:
                raise F5ModuleError(
                    "The specified 'key' was not found. Did you specify its full path?"
                )
            else:
                key = x['key']
                tmp['keyReference'] = dict(
                    link=key_references[key],
                    fullPath=key
                )

            if 'chain' in x and x['chain'] not in cert_references:
                raise F5ModuleError(
                    "The specified 'key' was not found. Did you specify its full path?"
                )
            else:
                key = x['chain']
                tmp['chainReference'] = dict(
                    link=cert_references[key],
                    fullPath=key
                )

            if 'passphrase' in x:
                tmp['passphrase'] = x['passphrase']
            result.append(tmp)
        return result


class ReportableChanges(Changes):
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.want.client = self.client
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)
            self.changes.client = self.client

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            self.changes.client = self.client
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def check_bigiq_version(self):
        version = bigiq_version(self.client)
        if LooseVersion(version) >= LooseVersion('6.1.0'):
            raise F5ModuleError(
                'Module supports only BIGIQ version 6.0.x or lower.'
            )

    def exec_module(self):
        self.check_bigiq_version()
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return False
        else:
            return self.create()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/ap/query/v1/tenants/default/reports/AllApplicationsList?$filter=name+eq+'{2}'".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if resp.status == 200 and 'result' in response and 'totalItems' in response['result'] and response['result']['totalItems'] == 0:
            return False
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self_link = self.remove_from_device()
        if self.want.wait:
            self.wait_for_apply_template_task(self_link)
            if self.exists():
                raise F5ModuleError("Failed to delete the resource.")
        return True

    def has_no_service_environment(self):
        if self.want.default_device_reference is None and self.want.ssg_reference is None:
            return True
        return False

    def create(self):
        if self.want.service_environment is None:
            raise F5ModuleError(
                "A 'service_environment' must be specified when creating a new application."
            )
        if self.want.servers is None:
            raise F5ModuleError(
                "At least one 'servers' item is needed when creating a new application."
            )
        if self.want.inbound_virtual is None:
            raise F5ModuleError(
                "An 'inbound_virtual' must be specified when creating a new application."
            )
        if self.want.domain_names is None:
            raise F5ModuleError(
                "You must provide at least one value in the 'domain_names' parameter."
            )
        self._set_changed_options()

        if self.has_no_service_environment():
            raise F5ModuleError(
                "The specified 'service_environment' ({0}) was not found.".format(self.want.service_environment)
            )

        if self.module.check_mode:
            return True
        self_link = self.create_on_device()
        if self.want.wait:
            self.wait_for_apply_template_task(self_link)
            if not self.exists():
                raise F5ModuleError(
                    "Failed to deploy application."
                )
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['mode'] = 'CREATE'

        uri = 'https://{0}:{1}/mgmt/cm/global/tasks/apply-template'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)
        return response['selfLink']

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        params = dict(
            configSetName=self.want.name,
            mode='DELETE'
        )
        uri = 'https://{0}:{1}/mgmt/cm/global/tasks/apply-template'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)
        return response['selfLink']

    def wait_for_apply_template_task(self, self_link):
        host = 'https://{0}:{1}'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        uri = self_link.replace('https://localhost', host)

        while True:
            resp = self.client.api.get(uri)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if response['status'] == 'FINISHED' and response.get('currentStep', None) == 'DONE':
                return True
            elif 'errorMessage' in response:
                raise F5ModuleError(response['errorMessage'])
            time.sleep(5)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            description=dict(),
            servers=dict(
                type='list',
                options=dict(
                    address=dict(required=True),
                    port=dict(default=80)
                )
            ),
            inbound_virtual=dict(
                type='dict',
                options=dict(
                    address=dict(required=True),
                    netmask=dict(required=True),
                    port=dict(default=443)
                )
            ),
            redirect_virtual=dict(
                type='dict',
                options=dict(
                    address=dict(required=True),
                    netmask=dict(required=True),
                    port=dict(default=80)
                )
            ),
            service_environment=dict(),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            client_ssl_profile=dict(
                type='dict',
                name=dict(default='clientssl'),
                cert_key_chain=dict(
                    type='raw',
                    options=dict(
                        cert=dict(),
                        key=dict(),
                        chain=dict(),
                        passphrase=dict()
                    )
                )
            ),
            add_analytics=dict(type='bool', default='no'),
            domain_names=dict(type='list'),
            wait=dict(type='bool', default='yes')
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['inherit_cert_key_chain', 'cert_key_chain']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
