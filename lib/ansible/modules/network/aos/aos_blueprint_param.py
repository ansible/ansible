#!/usr/bin/python
#
# (c) 2017 Apstra Inc, <community@apstra.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aos_blueprint_param
author: jeremy@apstra.com (@jeremyschulman)
version_added: "2.3"
short_description: Manage AOS blueprint parameter values
description:
 - Apstra AOS Blueprint Parameter module let you manage your Blueprint Parameter easily.
   You can create access, define and delete Blueprint Parameter. The list of
   Parameters supported is different per Blueprint. The option I(get_param_list)
   can help you to access the list of supported Parameters for your blueprint.
   This module is idempotent and support the I(check) mode. It's using the AOS REST API.
requirements:
  - "aos-pyez >= 0.6.0"
options:
  session:
    description:
      - An existing AOS session as obtained by M(aos_login) module.
    required: true
  blueprint:
    description:
      - Blueprint Name or Id as defined in AOS.
    required: True
  name:
    description:
      - Name of blueprint parameter, as defined by AOS design template. You can
        use the option I(get_param_list) to get the complete list of supported
        parameters for your blueprint.
  value:
    description:
      - Blueprint parameter value.  This value may be transformed by using the
        I(param_map) field; used when the blueprint parameter requires
        an AOS unique ID value.
  get_param_list:
    description:
      - Get the complete list of supported parameters for this blueprint and the
        description of those parameters.
  state:
    description:
      - Indicate what is the expected state of the Blueprint Parameter (present or not).
    default: present
    choices: ['present', 'absent']
  param_map:
    description:
      - Defines the aos-pyez collection that will is used to map the user-defined
        item name into the AOS unique ID value.  For example, if the caller
        provides an IP address pool I(param_value) called "Server-IpAddrs", then
        the aos-pyez collection is 'IpPools'. Some I(param_map) are already defined
        by default like I(logical_device_maps).
'''

EXAMPLES = '''

- name: Add Logical Device Maps information in a Blueprint
  aos_blueprint_param:
    session: "{{ aos_session }}"
    blueprint: "my-blueprint-l2"
    name: "logical_device_maps"
    value:
      spine_1: CumulusVX-Spine-Switch
      spine_2: CumulusVX-Spine-Switch
      leaf_1: CumulusVX-Leaf-Switch
      leaf_2: CumulusVX-Leaf-Switch
      leaf_3: CumulusVX-Leaf-Switch
    state: present

- name: Access Logical Device Maps information from a Blueprint
  aos_blueprint_param:
    session: "{{ aos_session }}"
    blueprint: "my-blueprint-l2"
    name: "logical_device_maps"
    state: present

- name: Reset Logical Device Maps information in a Blueprint
  aos_blueprint_param:
    session: "{{ aos_session }}"
    blueprint: "my-blueprint-l2"
    name: "logical_device_maps"
    state: absent

- name: Get list of all supported Params for a blueprint
  aos_blueprint_param:
    session: "{{ aos_session }}"
    blueprint: "my-blueprint-l2"
    get_param_list: yes
  register: params_list
- debug: var=params_list

- name: Add Resource Pools information in a Blueprint, by providing a param_map
  aos_blueprint_param:
    session: "{{ aos_session }}"
    blueprint: "my-blueprint-l2"
    name: "resource_pools"
    value:
        leaf_loopback_ips: ['Switches-IpAddrs']
        spine_loopback_ips: ['Switches-IpAddrs']
        spine_leaf_link_ips: ['Switches-IpAddrs']
        spine_asns: ['Private-ASN-pool']
        leaf_asns: ['Private-ASN-pool']
        virtual_network_svi_subnets: ['Servers-IpAddrs']
    param_map:
        leaf_loopback_ips: IpPools
        spine_loopback_ips: IpPools
        spine_leaf_link_ips: IpPools
        spine_asns: AsnPools
        leaf_asns: AsnPools
        virtual_network_svi_subnets: IpPools
    state: present
'''

RETURNS = '''
blueprint:
  description: Name of the Blueprint
  returned: always
  type: str
  sample: Server-IpAddrs

name:
  description: Name of the Blueprint Parameter
  returned: always
  type: str
  sample: fcc4ac1c-e249-4fe7-b458-2138bfb44c06

value:
  description: Value of the Blueprint Parameter as returned by the AOS Server
  returned: always
  type: dict
  sample: {'...'}

params_list:
  description: Value of the Blueprint Parameter as returned by the AOS Server
  returned: when I(get_param_list) is defined.
  type: dict
  sample: {'...'}
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aos.aos import get_aos_session, find_collection_item, check_aos_version
from ansible.module_utils.pycompat24 import get_exception

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from apstra.aosom.collection_mapper import CollectionMapper, MultiCollectionMapper
    HAS_AOS_PYEZ_MAPPER = True
except ImportError:
    HAS_AOS_PYEZ_MAPPER = False

param_map_list = dict(
    logical_device_maps='LogicalDeviceMaps',
    resource_pools=dict(
        spine_asns="AsnPools",
        leaf_asns="AsnPools",
        virtual_network_svi_subnets="IpPools",
        spine_loopback_ips="IpPools",
        leaf_loopback_ips="IpPools",
        spine_leaf_link_ips="IpPools"
    )
)


def get_collection_from_param_map(module, aos):

    param_map = None

    # Check if param_map is provided
    if module.params['param_map'] is not None:
        param_map_json = module.params['param_map']

        if not HAS_YAML:
            module.fail_json(msg="Python library Yaml is mandatory to use 'param_map'")

        try:
            param_map = yaml.safe_load(param_map_json)
        except:
            module.fail_json(msg="Unable to parse param_map information")

    else:
        # search in the param_map_list to find the right one
        for key, value in param_map_list.items():
            if module.params['name'] == key:
                param_map = value

    # If param_map is defined, search for a Collection that matches
    if param_map:
        if isinstance(param_map, dict):
            return MultiCollectionMapper(aos, param_map)
        else:
            return CollectionMapper(getattr(aos, param_map))

    return None


def blueprint_param_present(module, aos, blueprint, param, param_value):

    margs = module.params

    # If param_value is not defined, just return the object
    if not param_value:
        module.exit_json(changed=False,
                         blueprint=blueprint.name,
                         name=param.name,
                         value=param.value)

    # Check if current value is the same or not
    elif param.value != param_value:
        if not module.check_mode:
            try:
                param.value = param_value
            except:
                exc = get_exception()
                module.fail_json(msg='unable to write to param %s: %r' %
                                     (margs['name'], exc))

        module.exit_json(changed=True,
                         blueprint=blueprint.name,
                         name=param.name,
                         value=param.value)

    # If value are already the same, nothing needs to be changed
    else:
        module.exit_json(changed=False,
                         blueprint=blueprint.name,
                         name=param.name,
                         value=param.value)


def blueprint_param_absent(module, aos, blueprint, param, param_value):

    margs = module.params

    # Check if current value is the same or not
    if param.value != dict():
        if not module.check_mode:
            try:
                param.value = {}
            except:
                exc = get_exception()
                module.fail_json(msg='Unable to write to param %s: %r' % (margs['name'], exc))

        module.exit_json(changed=True,
                         blueprint=blueprint.name,
                         name=param.name,
                         value=param.value)

    else:
        module.exit_json(changed=False,
                         blueprint=blueprint.name,
                         name=param.name,
                         value=param.value)


def blueprint_param(module):

    margs = module.params

    # --------------------------------------------------------------------
    # Get AOS session object based on Session Info
    # --------------------------------------------------------------------
    try:
        aos = get_aos_session(module, margs['session'])
    except:
        module.fail_json(msg="Unable to login to the AOS server")

    # --------------------------------------------------------------------
    # Get the blueprint Object based on either name or ID
    # --------------------------------------------------------------------
    try:
        blueprint = find_collection_item(aos.Blueprints,
                                         item_name=margs['blueprint'],
                                         item_id=margs['blueprint'])
    except:
        module.fail_json(msg="Unable to find the Blueprint based on name or ID, something went wrong")

    if blueprint.exists is False:
        module.fail_json(msg='Blueprint %s does not exist.\n'
                             'known blueprints are [%s]' %
                             (margs['blueprint'], ','.join(aos.Blueprints.names)))

    # --------------------------------------------------------------------
    # If get_param_list is defined, build the list of supported parameters
    # and extract info for each
    # --------------------------------------------------------------------
    if margs['get_param_list']:

        params_list = {}
        for param in blueprint.params.names:
            params_list[param] = blueprint.params[param].info

        module.exit_json(changed=False,
                         blueprint=blueprint.name,
                         params_list=params_list)

    # --------------------------------------------------------------------
    # Check Param name, return an error if not supported by this blueprint
    # --------------------------------------------------------------------
    if margs['name'] in blueprint.params.names:
        param = blueprint.params[margs['name']]
    else:
        module.fail_json(msg='unable to access param %s' % margs['name'])

    # --------------------------------------------------------------------
    # Check if param_value needs to be converted to an object
    # based on param_map
    # --------------------------------------------------------------------
    param_value = margs['value']
    param_collection = get_collection_from_param_map(module, aos)

    # If a collection is find and param_value is defined,
    #   convert param_value into an object
    if param_collection and param_value:
        param_value = param_collection.from_label(param_value)

    # --------------------------------------------------------------------
    # Proceed based on State value
    # --------------------------------------------------------------------
    if margs['state'] == 'absent':

        blueprint_param_absent(module, aos, blueprint, param, param_value)

    elif margs['state'] == 'present':

        blueprint_param_present(module, aos, blueprint, param, param_value)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            blueprint=dict(required=True),
            get_param_list=dict(required=False, type="bool"),
            name=dict(required=False),
            value=dict(required=False, type="dict"),
            param_map=dict(required=False),
            state=dict(choices=['present', 'absent'], default='present')
        ),
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    # aos-pyez availability has been verify already by "check_aos_version"
    # but this module requires few more object
    if not HAS_AOS_PYEZ_MAPPER:
        module.fail_json(msg='unable to load the Mapper library from aos-pyez')

    blueprint_param(module)


if __name__ == '__main__':
    main()
