#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_appgateway
version_added: "2.7"
short_description: Manage Application Gateway instance
description:
    - Create, update and delete instance of Application Gateway.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    name:
        description:
            - The name of the application gateway.
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    sku:
        description:
            - SKU of the application gateway resource.
        suboptions:
            name:
                description:
                    - Name of an application gateway SKU.
                choices:
                    - 'standard_small'
                    - 'standard_medium'
                    - 'standard_large'
                    - 'waf_medium'
                    - 'waf_large'
            tier:
                description:
                    - Tier of an application gateway.
                choices:
                    - 'standard'
                    - 'waf'
            capacity:
                description:
                    - Capacity (instance count) of an application gateway.
    ssl_policy:
        description:
            - SSL policy of the application gateway resource.
        suboptions:
            disabled_ssl_protocols:
                description:
                    - List of SSL protocols to be disabled on application gateway.
                choices:
                    - 'tls_v1_0'
                    - 'tls_v1_1'
                    - 'tls_v1_2'
            policy_type:
                description:
                    - Type of SSL Policy.
                choices:
                    - 'predefined'
                    - 'custom'
            policy_name:
                description:
                    - Name of Ssl C(predefined) policy.
                choices:
                    - 'ssl_policy20150501'
                    - 'ssl_policy20170401'
                    - 'ssl_policy20170401_s'
            cipher_suites:
                description:
                    - List of SSL cipher suites to be enabled in the specified order to application gateway.
                choices:
                    - tls_ecdhe_rsa_with_aes_256_gcm_sha384
                    - tls_ecdhe_rsa_with_aes_128_gcm_sha256
                    - tls_ecdhe_rsa_with_aes_256_cbc_sha384
                    - tls_ecdhe_rsa_with_aes_128_cbc_sha256
                    - tls_ecdhe_rsa_with_aes_256_cbc_sha
                    - tls_ecdhe_rsa_with_aes_128_cbc_sha
                    - tls_dhe_rsa_with_aes_256_gcm_sha384
                    - tls_dhe_rsa_with_aes_128_gcm_sha256
                    - tls_dhe_rsa_with_aes_256_cbc_sha
                    - tls_dhe_rsa_with_aes_128_cbc_sha
                    - tls_rsa_with_aes_256_gcm_sha384
                    - tls_rsa_with_aes_128_gcm_sha256
                    - tls_rsa_with_aes_256_cbc_sha256
                    - tls_rsa_with_aes_128_cbc_sha256
                    - tls_rsa_with_aes_256_cbc_sha
                    - tls_rsa_with_aes_128_cbc_sha
                    - tls_ecdhe_ecdsa_with_aes_256_gcm_sha384
                    - tls_ecdhe_ecdsa_with_aes_128_gcm_sha256
                    - tls_ecdhe_ecdsa_with_aes_256_cbc_sha384
                    - tls_ecdhe_ecdsa_with_aes_128_cbc_sha256
                    - tls_ecdhe_ecdsa_with_aes_256_cbc_sha
                    - tls_ecdhe_ecdsa_with_aes_128_cbc_sha
                    - tls_dhe_dss_with_aes_256_cbc_sha256
                    - tls_dhe_dss_with_aes_128_cbc_sha256
                    - tls_dhe_dss_with_aes_256_cbc_sha
                    - tls_dhe_dss_with_aes_128_cbc_sha
                    - tls_rsa_with_3des_ede_cbc_sha
                    - tls_dhe_dss_with_3des_ede_cbc_sha
            min_protocol_version:
                description:
                    - Minimum version of Ssl protocol to be supported on application gateway.
                choices:
                    - 'tls_v1_0'
                    - 'tls_v1_1'
                    - 'tls_v1_2'
    gateway_ip_configurations:
        description:
            - List of subnets used by the application gateway.
        suboptions:
            subnet:
                description:
                    - Reference of the subnet resource. A subnet from where application gateway gets its private address.
            name:
                description:
                    - Name of the resource that is unique within a resource group. This name can be used to access the resource.
    authentication_certificates:
        description:
            - Authentication certificates of the application gateway resource.
        suboptions:
            data:
                description:
                    - Certificate public data - base64 encoded pfx.
            name:
                description:
                    - Name of the resource that is unique within a resource group. This name can be used to access the resource.
    redirect_configurations:
        version_added: "2.8"
        description:
            - Redirect configurations of the application gateway resource.
        suboptions:
            redirect_type:
                description:
                    - Redirection type.
                choices:
                    - 'permanent'
                    - 'found'
                    - 'see_other'
                    - 'temporary'
            target_listener:
                description:
                    - Reference to a listener to redirect the request to.
            include_path:
                description:
                    - Include path in the redirected url.
            include_query_string:
                description:
                    - Include query string in the redirected url.
            name:
                description:
                    - Name of the resource that is unique within a resource group.
    ssl_certificates:
        description:
            - SSL certificates of the application gateway resource.
        suboptions:
            data:
                description:
                    - Base-64 encoded pfx certificate.
                    - Only applicable in PUT Request.
            password:
                description:
                    - Password for the pfx file specified in I(data).
                    - Only applicable in PUT request.
            name:
                description:
                    - Name of the resource that is unique within a resource group. This name can be used to access the resource.
    frontend_ip_configurations:
        description:
            - Frontend IP addresses of the application gateway resource.
        suboptions:
            private_ip_address:
                description:
                    - PrivateIPAddress of the network interface IP Configuration.
            private_ip_allocation_method:
                description:
                    - PrivateIP allocation method.
                choices:
                    - 'static'
                    - 'dynamic'
            subnet:
                description:
                    - Reference of the subnet resource.
            public_ip_address:
                description:
                    - Reference of the PublicIP resource.
            name:
                description:
                    - Name of the resource that is unique within a resource group. This name can be used to access the resource.
    frontend_ports:
        description:
            - List of frontend ports of the application gateway resource.
        suboptions:
            port:
                description:
                    - Frontend port.
            name:
                description:
                    - Name of the resource that is unique within a resource group. This name can be used to access the resource.
    backend_address_pools:
        description:
            - List of backend address pool of the application gateway resource.
        suboptions:
            backend_addresses:
                description:
                    - List of backend addresses.
                suboptions:
                    fqdn:
                        description:
                            - Fully qualified domain name (FQDN).
                    ip_address:
                        description:
                            - IP address.
            name:
                description:
                    - Resource that is unique within a resource group. This name can be used to access the resource.
    probes:
        version_added: "2.8"
        description:
            - Probes available to the application gateway resource.
        suboptions:
            name:
                description:
                    - Name of the I(probe) that is unique within an Application Gateway.
            protocol:
                description:
                    - The protocol used for the I(probe).
                choices:
                    - 'http'
                    - 'https'
            host:
                description:
                    - Host name to send the I(probe) to.
            path:
                description:
                    - Relative path of I(probe).
                    - Valid path starts from '/'.
                    - Probe is sent to <Protocol>://<host>:<port><path>.
            timeout:
                description:
                    - The probe timeout in seconds.
                    - Probe marked as failed if valid response is not received with this timeout period.
                    - Acceptable values are from 1 second to 86400 seconds.
            interval:
                description:
                    - The probing interval in seconds.
                    - This is the time interval between two consecutive probes.
                    - Acceptable values are from 1 second to 86400 seconds.
            unhealthy_threshold:
                description:
                    - The I(probe) retry count.
                    - Backend server is marked down after consecutive probe failure count reaches UnhealthyThreshold.
                    - Acceptable values are from 1 second to 20.
    backend_http_settings_collection:
        description:
            - Backend http settings of the application gateway resource.
        suboptions:
            probe:
                description:
                    - Probe resource of an application gateway.
            port:
                description:
                    - The destination port on the backend.
            protocol:
                description:
                    - The protocol used to communicate with the backend.
                choices:
                    - 'http'
                    - 'https'
            cookie_based_affinity:
                description:
                    - Cookie based affinity.
                choices:
                    - 'enabled'
                    - 'disabled'
            request_timeout:
                description:
                    - Request timeout in seconds.
                    - Application Gateway will fail the request if response is not received within RequestTimeout.
                    - Acceptable values are from 1 second to 86400 seconds.
            authentication_certificates:
                description:
                    - List of references to application gateway authentication certificates.
                suboptions:
                    id:
                        description:
                            - Resource ID.
            host_name:
                description:
                    - Host header to be sent to the backend servers.
            pick_host_name_from_backend_address:
                description:
                    - Whether to pick host header should be picked from the host name of the backend server. Default value is false.
            affinity_cookie_name:
                description:
                    - Cookie name to use for the affinity cookie.
            path:
                description:
                    - Path which should be used as a prefix for all C(http) requests.
                    - Null means no path will be prefixed. Default value is null.
            name:
                description:
                    - Name of the resource that is unique within a resource group. This name can be used to access the resource.
    http_listeners:
        description:
            - List of HTTP listeners of the application gateway resource.
        suboptions:
            frontend_ip_configuration:
                description:
                    - Frontend IP configuration resource of an application gateway.
            frontend_port:
                description:
                    - Frontend port resource of an application gateway.
            protocol:
                description:
                    - Protocol of the c(http) listener.
                choices:
                    - 'http'
                    - 'https'
            host_name:
                description:
                    - Host name of C(http) listener.
            ssl_certificate:
                description:
                    - SSL certificate resource of an application gateway.
            require_server_name_indication:
                description:
                    - Applicable only if I(protocol) is C(https). Enables SNI for multi-hosting.
            name:
                description:
                    - Name of the resource that is unique within a resource group. This name can be used to access the resource.
    request_routing_rules:
        description:
            - List of request routing rules of the application gateway resource.
        suboptions:
            rule_type:
                description:
                    - Rule type.
                choices:
                    - 'basic'
                    - 'path_based_routing'
            backend_address_pool:
                description:
                    - Backend address pool resource of the application gateway.
            backend_http_settings:
                description:
                    - Backend C(http) settings resource of the application gateway.
            http_listener:
                description:
                    - Http listener resource of the application gateway.
            name:
                description:
                    - Name of the resource that is unique within a resource group. This name can be used to access the resource.
            redirect_configuration:
                description:
                    - Redirect configuration resource of the application gateway.
    state:
        description:
            - Assert the state of the Public IP. Use C(present) to create or update a and
              C(absent) to delete.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
- name: Create instance of Application Gateway
  azure_rm_appgateway:
    resource_group: myResourceGroup
    name: myappgateway
    sku:
      name: standard_small
      tier: standard
      capacity: 2
    gateway_ip_configurations:
      - subnet:
          id: "{{ subnet_id }}"
        name: app_gateway_ip_config
    frontend_ip_configurations:
      - subnet:
          id: "{{ subnet_id }}"
        name: sample_gateway_frontend_ip_config
    frontend_ports:
      - port: 90
        name: ag_frontend_port
    backend_address_pools:
      - backend_addresses:
          - ip_address: 10.0.0.4
        name: test_backend_address_pool
    backend_http_settings_collection:
      - port: 80
        protocol: http
        cookie_based_affinity: enabled
        name: sample_appgateway_http_settings
    http_listeners:
      - frontend_ip_configuration: sample_gateway_frontend_ip_config
        frontend_port: ag_frontend_port
        name: sample_http_listener
    request_routing_rules:
      - rule_type: Basic
        backend_address_pool: test_backend_address_pool
        backend_http_settings: sample_appgateway_http_settings
        http_listener: sample_http_listener
        name: rule1
'''

RETURN = '''
id:
    description:
        - Resource ID.
    returned: always
    type: str
    sample: id
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from copy import deepcopy
from ansible.module_utils.network.common.utils import dict_merge
from ansible.module_utils.common.dict_transformations import (
    camel_dict_to_snake_dict, snake_dict_to_camel_dict,
    _camel_to_snake, _snake_to_camel,
)

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from azure.mgmt.network import NetworkManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


ssl_policy_spec = dict(
    disabled_ssl_protocols=dict(type='list'),
    policy_type=dict(type='str', choices=['predefined', 'custom']),
    policy_name=dict(type='str', choices=['ssl_policy20150501', 'ssl_policy20170401', 'ssl_policy20170401_s']),
    cipher_suites=dict(type='list'),
    min_protocol_version=dict(type='str', choices=['tls_v1_0', 'tls_v1_1', 'tls_v1_2'])
)


probe_spec = dict(
    host=dict(type='str'),
    interval=dict(type='int'),
    name=dict(type='str'),
    path=dict(type='str'),
    protocol=dict(type='str', choices=['http', 'https']),
    timeout=dict(type='int'),
    unhealthy_threshold=dict(type='int')
)


redirect_configuration_spec = dict(
    include_path=dict(type='bool'),
    include_query_string=dict(type='bool'),
    name=dict(type='str'),
    redirect_type=dict(type='str', choices=['permanent', 'found', 'see_other', 'temporary']),
    target_listener=dict(type='str')
)


class AzureRMApplicationGateways(AzureRMModuleBase):
    """Configuration class for an Azure RM Application Gateway resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            location=dict(
                type='str'
            ),
            sku=dict(
                type='dict'
            ),
            ssl_policy=dict(
                type='dict',
                options=ssl_policy_spec
            ),
            gateway_ip_configurations=dict(
                type='list'
            ),
            authentication_certificates=dict(
                type='list'
            ),
            ssl_certificates=dict(
                type='list'
            ),
            redirect_configurations=dict(
                type='list',
                elements='dict',
                options=redirect_configuration_spec
            ),
            frontend_ip_configurations=dict(
                type='list'
            ),
            frontend_ports=dict(
                type='list'
            ),
            backend_address_pools=dict(
                type='list'
            ),
            backend_http_settings_collection=dict(
                type='list'
            ),
            probes=dict(
                type='list',
                elements='dict',
                options=probe_spec
            ),
            http_listeners=dict(
                type='list'
            ),
            request_routing_rules=dict(
                type='list'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.parameters = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMApplicationGateways, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                         supports_check_mode=True,
                                                         supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "id":
                    self.parameters["id"] = kwargs[key]
                elif key == "location":
                    self.parameters["location"] = kwargs[key]
                elif key == "sku":
                    ev = kwargs[key]
                    if 'name' in ev:
                        if ev['name'] == 'standard_small':
                            ev['name'] = 'Standard_Small'
                        elif ev['name'] == 'standard_medium':
                            ev['name'] = 'Standard_Medium'
                        elif ev['name'] == 'standard_large':
                            ev['name'] = 'Standard_Large'
                        elif ev['name'] == 'waf_medium':
                            ev['name'] = 'WAF_Medium'
                        elif ev['name'] == 'waf_large':
                            ev['name'] = 'WAF_Large'
                    if 'tier' in ev:
                        if ev['tier'] == 'standard':
                            ev['tier'] = 'Standard'
                        elif ev['tier'] == 'waf':
                            ev['tier'] = 'WAF'
                    self.parameters["sku"] = ev
                elif key == "ssl_policy":
                    ev = kwargs[key]
                    if 'policy_type' in ev:
                        ev['policy_type'] = _snake_to_camel(ev['policy_type'], True)
                    if 'policy_name' in ev:
                        if ev['policy_name'] == 'ssl_policy20150501':
                            ev['policy_name'] = 'AppGwSslPolicy20150501'
                        elif ev['policy_name'] == 'ssl_policy20170401':
                            ev['policy_name'] = 'AppGwSslPolicy20170401'
                        elif ev['policy_name'] == 'ssl_policy20170401_s':
                            ev['policy_name'] = 'AppGwSslPolicy20170401S'
                    if 'min_protocol_version' in ev:
                        if ev['min_protocol_version'] == 'tls_v1_0':
                            ev['min_protocol_version'] = 'TLSv1_0'
                        elif ev['min_protocol_version'] == 'tls_v1_1':
                            ev['min_protocol_version'] = 'TLSv1_1'
                        elif ev['min_protocol_version'] == 'tls_v1_2':
                            ev['min_protocol_version'] = 'TLSv1_2'
                    if 'disabled_ssl_protocols' in ev:
                        protocols = ev['disabled_ssl_protocols']
                        if protocols is not None:
                            for i in range(len(protocols)):
                                if protocols[i] == 'tls_v1_0':
                                    protocols[i] = 'TLSv1_0'
                                elif protocols[i] == 'tls_v1_1':
                                    protocols[i] = 'TLSv1_1'
                                elif protocols[i] == 'tls_v1_2':
                                    protocols[i] = 'TLSv1_2'
                    if 'cipher_suites' in ev:
                        suites = ev['cipher_suites']
                        if suites is not None:
                            for i in range(len(suites)):
                                suites[i] = suites[i].upper()
                elif key == "gateway_ip_configurations":
                    self.parameters["gateway_ip_configurations"] = kwargs[key]
                elif key == "authentication_certificates":
                    self.parameters["authentication_certificates"] = kwargs[key]
                elif key == "ssl_certificates":
                    self.parameters["ssl_certificates"] = kwargs[key]
                elif key == "redirect_configurations":
                    ev = kwargs[key]
                    for i in range(len(ev)):
                        item = ev[i]
                        if 'redirect_type' in item:
                            item['redirect_type'] = _snake_to_camel(item['redirect_type'], True)
                        if 'target_listener' in item:
                            id = http_listener_id(self.subscription_id,
                                                  kwargs['resource_group'],
                                                  kwargs['name'],
                                                  item['target_listener'])
                            item['target_listener'] = {'id': id}
                    self.parameters["redirect_configurations"] = ev
                elif key == "frontend_ip_configurations":
                    ev = kwargs[key]
                    for i in range(len(ev)):
                        item = ev[i]
                        if 'private_ip_allocation_method' in item:
                            item['private_ip_allocation_method'] = _snake_to_camel(item['private_ip_allocation_method'], True)
                        if 'public_ip_address' in item:
                            id = public_ip_id(self.subscription_id,
                                              kwargs['resource_group'],
                                              item['public_ip_address'])
                            item['public_ip_address'] = {'id': id}
                    self.parameters["frontend_ip_configurations"] = ev
                elif key == "frontend_ports":
                    self.parameters["frontend_ports"] = kwargs[key]
                elif key == "backend_address_pools":
                    self.parameters["backend_address_pools"] = kwargs[key]
                elif key == "probes":
                    ev = kwargs[key]
                    for i in range(len(ev)):
                        item = ev[i]
                        if 'protocol' in item:
                            item['protocol'] = _snake_to_camel(item['protocol'], True)
                    self.parameters["probes"] = ev
                elif key == "backend_http_settings_collection":
                    ev = kwargs[key]
                    for i in range(len(ev)):
                        item = ev[i]
                        if 'protocol' in item:
                            item['protocol'] = _snake_to_camel(item['protocol'], True)
                        if 'cookie_based_affinity' in item:
                            item['cookie_based_affinity'] = _snake_to_camel(item['cookie_based_affinity'], True)
                        if 'probe' in item:
                            id = probe_id(self.subscription_id,
                                          kwargs['resource_group'],
                                          kwargs['name'],
                                          item['probe'])
                            item['probe'] = {'id': id}
                    self.parameters["backend_http_settings_collection"] = ev
                elif key == "http_listeners":
                    ev = kwargs[key]
                    for i in range(len(ev)):
                        item = ev[i]
                        if 'frontend_ip_configuration' in item:
                            id = frontend_ip_configuration_id(self.subscription_id,
                                                              kwargs['resource_group'],
                                                              kwargs['name'],
                                                              item['frontend_ip_configuration'])
                            item['frontend_ip_configuration'] = {'id': id}

                        if 'frontend_port' in item:
                            id = frontend_port_id(self.subscription_id,
                                                  kwargs['resource_group'],
                                                  kwargs['name'],
                                                  item['frontend_port'])
                            item['frontend_port'] = {'id': id}
                        if 'ssl_certificate' in item:
                            id = ssl_certificate_id(self.subscription_id,
                                                    kwargs['resource_group'],
                                                    kwargs['name'],
                                                    item['ssl_certificate'])
                            item['ssl_certificate'] = {'id': id}
                        if 'protocol' in item:
                            item['protocol'] = _snake_to_camel(item['protocol'], True)
                        ev[i] = item
                    self.parameters["http_listeners"] = ev
                elif key == "request_routing_rules":
                    ev = kwargs[key]
                    for i in range(len(ev)):
                        item = ev[i]
                        if 'backend_address_pool' in item:
                            id = backend_address_pool_id(self.subscription_id,
                                                         kwargs['resource_group'],
                                                         kwargs['name'],
                                                         item['backend_address_pool'])
                            item['backend_address_pool'] = {'id': id}
                        if 'backend_http_settings' in item:
                            id = backend_http_settings_id(self.subscription_id,
                                                          kwargs['resource_group'],
                                                          kwargs['name'],
                                                          item['backend_http_settings'])
                            item['backend_http_settings'] = {'id': id}
                        if 'http_listener' in item:
                            id = http_listener_id(self.subscription_id,
                                                  kwargs['resource_group'],
                                                  kwargs['name'],
                                                  item['http_listener'])
                            item['http_listener'] = {'id': id}
                        if 'protocol' in item:
                            item['protocol'] = _snake_to_camel(item['protocol'], True)
                        if 'rule_type' in ev:
                            item['rule_type'] = _snake_to_camel(item['rule_type'], True)
                        if 'redirect_configuration' in item:
                            id = redirect_configuration_id(self.subscription_id,
                                                           kwargs['resource_group'],
                                                           kwargs['name'],
                                                           item['redirect_configuration'])
                            item['redirect_configuration'] = {'id': id}
                        ev[i] = item
                    self.parameters["request_routing_rules"] = ev
                elif key == "etag":
                    self.parameters["etag"] = kwargs[key]

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(NetworkManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_applicationgateway()

        if not old_response:
            self.log("Application Gateway instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Application Gateway instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if Application Gateway instance has to be deleted or may be updated")
                self.to_do = Actions.Update

        if (self.to_do == Actions.Update):
            if (self.parameters['location'] != old_response['location'] or
                    self.parameters['sku']['name'] != old_response['sku']['name'] or
                    self.parameters['sku']['tier'] != old_response['sku']['tier'] or
                    self.parameters['sku']['capacity'] != old_response['sku']['capacity'] or
                    not compare_arrays(old_response, self.parameters, 'authentication_certificates') or
                    not compare_arrays(old_response, self.parameters, 'gateway_ip_configurations') or
                    not compare_arrays(old_response, self.parameters, 'redirect_configurations') or
                    not compare_arrays(old_response, self.parameters, 'frontend_ip_configurations') or
                    not compare_arrays(old_response, self.parameters, 'frontend_ports') or
                    not compare_arrays(old_response, self.parameters, 'backend_address_pools') or
                    not compare_arrays(old_response, self.parameters, 'probes') or
                    not compare_arrays(old_response, self.parameters, 'backend_http_settings_collection') or
                    not compare_arrays(old_response, self.parameters, 'request_routing_rules') or
                    not compare_arrays(old_response, self.parameters, 'http_listeners')):

                self.to_do = Actions.Update
            else:
                self.to_do = Actions.NoAction

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Application Gateway instance")

            if self.check_mode:
                self.results['changed'] = True
                self.results["parameters"] = self.parameters
                return self.results

            response = self.create_update_applicationgateway()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Application Gateway instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_applicationgateway()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_applicationgateway():
                time.sleep(20)
        else:
            self.log("Application Gateway instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

        return self.results

    def create_update_applicationgateway(self):
        '''
        Creates or updates Application Gateway with the specified configuration.

        :return: deserialized Application Gateway instance state dictionary
        '''
        self.log("Creating / Updating the Application Gateway instance {0}".format(self.name))

        try:
            response = self.mgmt_client.application_gateways.create_or_update(resource_group_name=self.resource_group,
                                                                              application_gateway_name=self.name,
                                                                              parameters=self.parameters)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Application Gateway instance.')
            self.fail("Error creating the Application Gateway instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_applicationgateway(self):
        '''
        Deletes specified Application Gateway instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Application Gateway instance {0}".format(self.name))
        try:
            response = self.mgmt_client.application_gateways.delete(resource_group_name=self.resource_group,
                                                                    application_gateway_name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Application Gateway instance.')
            self.fail("Error deleting the Application Gateway instance: {0}".format(str(e)))

        return True

    def get_applicationgateway(self):
        '''
        Gets the properties of the specified Application Gateway.

        :return: deserialized Application Gateway instance state dictionary
        '''
        self.log("Checking if the Application Gateway instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.application_gateways.get(resource_group_name=self.resource_group,
                                                                 application_gateway_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Application Gateway instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Application Gateway instance.')
        if found is True:
            return response.as_dict()

        return False


def public_ip_id(subscription_id, resource_group_name, name):
    """Generate the id for a frontend ip configuration"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/publicIPAddresses/{2}'.format(
        subscription_id,
        resource_group_name,
        name
    )


def frontend_ip_configuration_id(subscription_id, resource_group_name, appgateway_name, name):
    """Generate the id for a frontend ip configuration"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationGateways/{2}/frontendIPConfigurations/{3}'.format(
        subscription_id,
        resource_group_name,
        appgateway_name,
        name
    )


def frontend_port_id(subscription_id, resource_group_name, appgateway_name, name):
    """Generate the id for a frontend port"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationGateways/{2}/frontendPorts/{3}'.format(
        subscription_id,
        resource_group_name,
        appgateway_name,
        name
    )


def redirect_configuration_id(subscription_id, resource_group_name, appgateway_name, name):
    """Generate the id for a redirect configuration"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationGateways/{2}/redirectConfigurations/{3}'.format(
        subscription_id,
        resource_group_name,
        appgateway_name,
        name
    )


def ssl_certificate_id(subscription_id, resource_group_name, ssl_certificate_name, name):
    """Generate the id for a frontend port"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationGateways/{2}/sslCertificates/{3}'.format(
        subscription_id,
        resource_group_name,
        ssl_certificate_name,
        name
    )


def backend_address_pool_id(subscription_id, resource_group_name, appgateway_name, name):
    """Generate the id for an address pool"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationGateways/{2}/backendAddressPools/{3}'.format(
        subscription_id,
        resource_group_name,
        appgateway_name,
        name
    )


def probe_id(subscription_id, resource_group_name, appgateway_name, name):
    """Generate the id for a probe"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationGateways/{2}/probes/{3}'.format(
        subscription_id,
        resource_group_name,
        appgateway_name,
        name
    )


def backend_http_settings_id(subscription_id, resource_group_name, appgateway_name, name):
    """Generate the id for a http settings"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationGateways/{2}/backendHttpSettingsCollection/{3}'.format(
        subscription_id,
        resource_group_name,
        appgateway_name,
        name
    )


def http_listener_id(subscription_id, resource_group_name, appgateway_name, name):
    """Generate the id for a http listener"""
    return '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/applicationGateways/{2}/httpListeners/{3}'.format(
        subscription_id,
        resource_group_name,
        appgateway_name,
        name
    )


def compare_arrays(old_params, new_params, param_name):
    old = old_params.get(param_name) or []
    new = new_params.get(param_name) or []

    oldd = {}
    for item in old:
        name = item['name']
        oldd[name] = item
    newd = {}
    for item in new:
        name = item['name']
        newd[name] = item

    newd = dict_merge(oldd, newd)
    return newd == oldd


def main():
    """Main execution"""
    AzureRMApplicationGateways()


if __name__ == '__main__':
    main()
