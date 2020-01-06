#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Guardicore Assets (c) 2019
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: guardicore_asset
short_description: Manages Assets in Guardicore Centra.
description:
  - Configure Assets in Guardicore Centra.
  - This module gather Linux machines information and configure them as 'Assets' in Guardicore Centra.
  - This module also can be used only to dump the 'Asset' configuration to a file.
  - Please check the Guardicore Centra Admin Guide for the Inventory API Configuration Instructions.
version_added: "2.10"
author: "Lior Bar-Oz (@liorBaroz)"
options:
  inventory_api_username:
    description:
      - the username for the inventory api configuration. required with C(inventory_api_password).
      - not mandatory if C(inventory_api_token) is given, depends on Guardicore Centra Configuration.
    required: False
    type: str
  inventory_api_password:
    description:
      - the password for the inventory api configuration. required with C(inventory_api_username).
      - not mandatory if C(inventory_api_token) is given, depends on Guardicore Centra Configuration.
    required: False
    type: str
  inventory_api_token:
    description:
      - the token for the inventory api configuration.
      - not mandatory if both C(inventory_api_password) and C(inventory_api_username) are given, depends on Guardicore Centra Configuration.
    required: False
    type: str
  ssl_address:
    description:
      - the ssl address to configure the asset in front of.
    required: False
    type: str
  ssl_port:
    description:
      - the ssl port to configure the asset in front of. default is C(443).
    required: False
    type: str
    default: 443
  state:
    description:
      - present or absent. Defaults to present.
      - C('present') will configure the asset in Guardicore Centra, while C('absent') will skip the configuration.
    type: str
    default: present
  labels:
    description:
      - Set a list of labels in the form of C('key1:value1,key2:value2') for labeling the Assets.
      - See examples below.
    type: str
    required: False
  asset_name:
    description:
      - The name of the asset.
    required: True
    type: str
  bios_uuid:
    description:
      - The bios uuid of the asset.
      - If not set, the bios uuid from the machine will be retrieve automatically.
      - For Linux, use this file content C('/sys/class/dmi/id/product_uuid').
      - Please refer to Guardicore Admin Guides for more information.
    required: False
    type: str
  asset_id:
    description:
      - A unique ID of the asset. for example C('422F81AE-781B-4823-F1FD-7E51093BF316').
      - If not set, the bios uuid will be configured as the asset id.
      - Note, This unique ID must be created by the customer automation, and must be reused when reporting the same asset on subsequent calls.
    required: False
    type: str
  aws_instance:
    description:
      - Set as C('True') in case of AWS instances to gather more data.
    required: False
    type: bool
    default: False
  asset_metadata:
    description:
      - Set a list of metadata in the form of C('key1:value1,key2:value2') to add metadata to the asset.
      - Optional parameters which will be attached to the asset and reported to the management console.
    required: False
    type: str
  inventory_api_version:
    description:
      - the version of the Guardicore Centra inventory API for ex, v2.0.
    required: False
    type: str
    default: v2.0
  load_assets_requests:
    description:
      - Whether to load existing assets data. If C('True'), C('assets_request_data_path') must be provide.
    required: False
    type: bool
    default: False
  dump_assets_requests:
    description:
      - Whether to load existing assets data. If C('True'), C('assets_request_data_path') must be provide.
    required: False
    type: bool
    default: False
  asset_request_data_file_path:
    description:
      - The local path for the assets requests data file.
    required: False
    type: path
'''

EXAMPLES = r'''
- name: Configure Asset in Guardicore Centra using username and password
  guardicore_asset:
    inventory_api_username: "InventoryApiUsername"
    inventory_api_password: "InventoryApiPassword"
    asset_name: "prod-web-machine-a"
    state: present
    ssl_address: 192.168.1.100
    labels: "environment:production,app:web"

- name: Configure Asset in Guardicore Centra using a token
  guardicore_asset:
    inventory_api_token: "TokenString"
    state: present
    ssl_address: 192.168.1.100
    ssl_port: 1443
    asset_metadata: "language:en_US.UTF-8,kernel-version:9.9,distro:testing,version:9.9"
    load_assets_requests: True
    asset_request_data_file_path: "/tmp/asset_dump"

- name: Dump Asset configuration to a local file
  guardicore_asset:
    inventory_api_username: "InventoryApiUsername"
    inventory_api_password: "InventoryApiPassword"
    asset_name: "prod-aws-machine-a"
    state: absent
    load_assets_requests: False
    dump_assets_requests: True
    aws_instance: True
    asset_request_data_file_path: "/tmp/asset_dump"
'''

RETURN = r'''
installation_result:
    description: the Asset configuraiton in Guardicore Centra result
    returned: always
    type: dict
    sample: None
'''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts import ansible_collector
from ansible.module_utils.facts.namespace import PrefixFactNamespace
from ansible.module_utils.facts import default_collectors
from ansible.module_utils.urls import open_url


def verify_params(params):
    """ verifying params before triggering the Gaurdicore Asset configuration """
    boolean_flag_params = ['dump_assets_requests', 'load_assets_requests', 'aws_instance']
    allowed_inventory_api_version = ['v1.0', 'v2.0']
    wrong_params = []

    # for flag_param in boolean_flag_params:
    #     if flag_param in params:
    for flag_param in (set(boolean_flag_params) & set(params)):
        if not isinstance(params[flag_param], bool):
            wrong_params.append(flag_param)

    if params['inventory_api_version'] not in allowed_inventory_api_version:
        wrong_params.append('inventory_api_version')

    return wrong_params


def load_request_data(module, params):
    """ :return the request from the existing dump file if exist. """

    if params['asset_request_data_file_path']:
        with open(params['asset_request_data_file_path'], 'r') as f:
            return module.from_json(data=f.read())

    return None


def dump_request_data(module, params, request_data=None):
    """ dump the request data locally """

    if not request_data:
        request_data = _get_request_body(module=module, params=params)

    with open(params['asset_request_data_file_path'], 'w') as f:
        json.dump(request_data, f, indent=4)

    return "File dump successfully to {asset_request_data_file_path}".format(
        asset_request_data_file_path=params['asset_request_data_file_path'])


def _get_request_body(module, params):
    """ :return the arranged request body by the given params"""
    params['ansible_facts'] = _get_ansible_facts(module=module)
    params['bios_uuid'] = _get_bios_uuid(module=module)
    request_data = {}

    if params['asset_id']:
        request_data['id'] = params['asset_id']
    else:
        request_data['id'] = params['bios_uuid']

    request_data['bios-uuid'] = params['bios_uuid']
    request_data['name'] = params['asset_name']

    if params['labels']:
        request_data['labels'] = _get_asset_labels(params=params)

    if params['asset_metadata']:
        request_data['metadata'] = _get_asset_metadata(params)

    if params['aws_instance']:
        aws_instance_id = _get_aws_instance_id()
        if aws_instance_id:
            request_data['instance-id'] = aws_instance_id
            request_data['metadata']['aws instance id'] = aws_instance_id

    if params['inventory_api_version'] == 'v1.0':
        request_data['addresses'] = params['ansible_facts']['ansible_all_ipv4_addresses']
        if params['ansible_facts']['ansible_all_ipv6_addresses']:
            request_data['addresses'] += params['ansible_facts']['ansible_all_ipv6_addresses']

    elif params['inventory_api_version'] == 'v2.0':
        request_data['nics'] = _get_asset_interfaces_list(params=params)

    return request_data


def _get_ansible_facts(module):
    """ :return the required ansible facts """
    gather_subset = ["all"]
    gather_timeout = 10
    filter = "*"

    namespace = PrefixFactNamespace(namespace_name='ansible', prefix='ansible_')
    minimal_gather_subset = frozenset(['apparmor', 'caps', 'cmdline', 'date_time',
                                       'distribution', 'dns', 'env', 'fips', 'local',
                                       'lsb', 'pkg_mgr', 'platform', 'python', 'selinux',
                                       'service_mgr', 'ssh_pub_keys', 'user'])
    all_collector_classes = default_collectors.collectors
    fact_collector = ansible_collector.get_ansible_collector(all_collector_classes=all_collector_classes,
                                                             namespace=namespace,
                                                             filter_spec=filter,
                                                             gather_subset=gather_subset,
                                                             gather_timeout=gather_timeout,
                                                             minimal_gather_subset=minimal_gather_subset)

    all_facts_dict = fact_collector.collect(module=module)

    desired_facts = ["ansible_all_ipv4_addresses", "ansible_default_ipv4", "ansible_distribution_major_version",
                     "ansible_lsb", "ansible_machine", "ansible_os_family", "ansible_distribution_release",
                     "ansible_distribution", "ansible_bios_version", "ansible_system",
                     "ansible_virtualization_type", "ansible_distribution_file_path", "ansible_kernel_version",
                     "ansible_nodename", "ansible_kernel", "ansible_all_ipv6_addresses", "ansible_hostname",
                     "ansible_interfaces"]

    for interface_name in all_facts_dict["ansible_interfaces"]:
        desired_facts.append("ansible_%s" % interface_name)

    required_facts_dict = {}
    for fact in desired_facts:
        required_facts_dict[fact] = all_facts_dict[fact]

    return required_facts_dict


def _get_bios_uuid(module):
    """ :return the bios uuid"""
    output = ""
    rc, stdout, stderr = module.run_command("cat /sys/class/dmi/id/product_uuid")

    if rc == 0:
        output = stdout
    else:
        output += stderr

    if not output:
        module.fail_json(msg="Failed to get bios uuid from remote machine")

    return output.rstrip()


def _get_aws_instance_id():
    """ :return True if remote machine is aws instance """
    url = 'http://169.254.169.254/latest/meta-data/instance-id'
    try:
        response = open_url(url=url, method="GET", validate_certs=False)
        response_content = response.read().decode('utf-8')
        if response_content:
            if response_content.startswith('i-'):
                return response_content
    except Exception:
        return None


def _get_asset_labels(params):
    """ :return arranged form of the labels of the asset """
    labels = []

    for label in params['labels'].split(','):
        labels.append({
            'key': label.split(':')[0],
            'value': label.split(':')[1]
        })

    return labels


def _get_asset_metadata(params):
    """ :return arranged form of the asset metadata of the asset """
    asset_metadata = {}
    for metadata in params['asset_metadata'].split(','):
        asset_metadata[metadata.split(':')[0]] = metadata.split(':')[1]

    return asset_metadata


def _get_asset_interfaces_list(params):
    """ :return the arraged form of the asset interfaces"""
    interfaces = []

    interfaces_dict = _get_asset_interfaces_dict(params=params)

    for interface_name in interfaces_dict:
        interfaces.append({'mac_address': interfaces_dict[interface_name]['mac_address'],
                           'addresses': interfaces_dict[interface_name]['addresses']})

    return interfaces


def _get_asset_interfaces_dict(params):
    """:return the interfaces dict base on the ansible params"""
    interfaces_dict = {}

    for interface_name in params['ansible_facts']["ansible_interfaces"]:

        if interface_name == 'lo':
            continue

        ansible_facts_interface_name = 'ansible_{interface_name}'.format(interface_name=interface_name)
        if ansible_facts_interface_name in params['ansible_facts']:
            if 'macaddress' in params['ansible_facts'][ansible_facts_interface_name]:
                interfaces_dict = _get_asset_mac_addresses(interfaces_dict=interfaces_dict,
                                                           interface_name=interface_name,
                                                           params=params,
                                                           ansible_facts_interface_name=ansible_facts_interface_name)

            interfaces_dict = _get_asset_ip_addresses(interfaces_dict=interfaces_dict,
                                                      interface_name=interface_name,
                                                      params=params,
                                                      ansible_facts_interface_name=ansible_facts_interface_name)

    return interfaces_dict


def _get_asset_mac_addresses(interfaces_dict, interface_name, params, ansible_facts_interface_name):
    """ :return interfaces_dict with the mac address """
    if interface_name not in interfaces_dict:
        interfaces_dict[interface_name] = {}
    if 'mac_address' not in interfaces_dict[interface_name]:
        interfaces_dict[interface_name]['mac_address'] = params['ansible_facts'][ansible_facts_interface_name][
            'macaddress']

    return interfaces_dict


def _get_asset_ip_addresses(interfaces_dict, interface_name, params, ansible_facts_interface_name):
    """ :return interfaces_dict with the ip addresses """
    if 'macaddress' in params['ansible_facts'][ansible_facts_interface_name]:
        if interface_name not in interfaces_dict:
            interfaces_dict[interface_name] = {}
        if 'addresses' not in interfaces_dict[interface_name]:
            interfaces_dict[interface_name]['addresses'] = []
        interfaces_dict[interface_name]['addresses'] += _get_ansible_interface_ip_address(
            interface_dict=params['ansible_facts'][ansible_facts_interface_name])
    else:
        for main_interface_name in params['ansible_facts']["ansible_interfaces"]:
            if (main_interface_name in interface_name) and (len(main_interface_name) < len(interface_name)):
                if main_interface_name not in interfaces_dict:
                    interfaces_dict[main_interface_name] = {}
                if 'addresses' not in interfaces_dict[main_interface_name]:
                    interfaces_dict[main_interface_name]['addresses'] = []
                interfaces_dict[main_interface_name]['addresses'] += _get_ansible_interface_ip_address(
                    interface_dict=params['ansible_facts'][ansible_facts_interface_name])

    return interfaces_dict


def _get_ansible_interface_ip_address(interface_dict):
    """ :return as list of all the ipv4 and ipv6 of interface by the ansible facts """
    interface_ip_addresses = []

    if 'ipv4' in interface_dict:
        interface_ip_addresses.append(interface_dict['ipv4']['address'])
    if 'ipv6' in interface_dict:
        for ipv6_list in interface_dict['ipv6']:
            interface_ip_addresses.append(ipv6_list['address'])

    return interface_ip_addresses


def post_request(request_data, params):
    """ send request for asset configuration to the ssl address"""
    force_basic_auth = False
    url_username = None
    url_password = None
    ssl_address = _get_ssl_address(params)

    if ssl_address:
        url = 'https://{ssl_address}/api/{api_version}/assets'.format(ssl_address=ssl_address,
                                                                      api_version=params['inventory_api_version'])
        if params['inventory_api_username'] and params['inventory_api_password']:
            force_basic_auth = True
            url_username = params['inventory_api_username']
            url_password = params['inventory_api_password']

        if params['inventory_api_token']:
            url += "?token={inventory_api_token}".format(inventory_api_token=params['inventory_api_token'])

    request_headers = {'Content-Type': 'application/json'}

    response = open_url(url=url, headers=request_headers, method="POST", data=json.dumps({'assets': [request_data]}),
                        validate_certs=False, force_basic_auth=force_basic_auth,
                        url_username=url_username, url_password=url_password)

    return response.read()


def _get_ssl_address(params):
    """ :return the ssl address based on the parameters """
    if params['ssl_port'] == '443':
        return params['ssl_address']

    return "{ssl_address}:{ssl_port}".format(ssl_address=params['ssl_address'], ssl_port=params['ssl_port'])


def main():

    argument_spec = dict(
        inventory_api_username=dict(type='str', required=False),
        inventory_api_password=dict(type='str', required=False),
        inventory_api_token=dict(type='str', required=False),
        ssl_address=dict(type='str', required=False),
        ssl_port=dict(type='str', required=False, default='443'),
        labels=dict(type='str', required=False),
        state=dict(type='str', default='present'),
        asset_name=dict(type='str', required=True),
        bios_uuid=dict(type='str', required=False),
        asset_id=dict(type='str', required=False),
        aws_instance=dict(type='bool', required=False, default=False),
        asset_metadata=dict(type='str', required=False),
        inventory_api_version=dict(type='str', required=False, default='v2.0'),
        load_assets_requests=dict(type='bool', required=False, default=False),
        dump_assets_requests=dict(type='bool', required=False, default=False),
        asset_request_data_file_path=dict(type='path', required=False)
    )

    required_if = [('state', 'present', ['ssl_address', 'asset_name'])]
    module = AnsibleModule(argument_spec=argument_spec, required_if=required_if)
    params = module.params

    result = {}

    try:
        unverified_params = verify_params(params)
        if not unverified_params:

            if params['load_assets_requests']:
                request_data = load_request_data(module=module, params=params)

                if not request_data:
                    request_data = _get_request_body(module=module, params=params)

                    if params['dump_assets_requests']:
                        result['dump_result'] = dump_request_data(module=module, params=params, request_data=request_data)
                else:
                    if params['state'] == 'present':
                        result['configure_asset_result'] = post_request(request_data=request_data, params=params)

            else:
                request_data = _get_request_body(module=module, params=params)

                if params['dump_assets_requests']:
                    result['dump_result'] = dump_request_data(module=module, params=params, request_data=request_data)

                if params['state'] == 'present':
                    result['configure_asset_result'] = post_request(request_data=request_data, params=params)

            module.exit_json(changed=True, msg="Done with: {result}".format(result=result))
        else:
            module.fail_json(msg="Some parameters value are not valid: {unverified_params}\n{params}".format(
                unverified_params=unverified_params, params=params))
    except Exception as e:
        module.fail_json(msg="Something fatal happened: {exception}".format(exception=e))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
