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
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aos_blueprint_virtnet
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage AOS blueprint parameter values
deprecated:
    removed_in: "2.9"
    why: This module does not support AOS 2.1 or later
    alternative: See new modules at U(https://www.ansible.com/ansible-apstra).
description:
 - Apstra AOS Blueprint Virtual Network module let you manage your Virtual Network easily.
   You can create access, define and delete Virtual Network by name or by using a JSON / Yaml file.
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
      - Name of Virtual Network as part of the Blueprint.
  content:
    description:
      - Datastructure of the Virtual Network to manage. The data can be in YAML / JSON or
        directly a variable. It's the same datastructure that is returned on success in I(value).
  state:
    description:
      - Indicate what is the expected state of the Virtual Network (present or not).
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''

- name: "Access Existing Virtual Network"
  aos_blueprint_virtnet:
    session: "{{ aos_session }}"
    blueprint: "my-blueprint-l2"
    name: "my-virtual-network"
    state: present

- name: "Delete Virtual Network with JSON File"
  aos_blueprint_virtnet:
    session: "{{ aos_session }}"
    blueprint: "my-blueprint-l2"
    content: "{{ lookup('file', 'resources/virtual-network-02.json') }}"
    state: absent

- name: "Create Virtual Network"
  aos_blueprint_virtnet:
    session: "{{ aos_session }}"
    blueprint: "my-blueprint-l2"
    content: "{{ lookup('file', 'resources/virtual-network-02.json') }}"
    state: present
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.network.aos.aos import get_aos_session, find_collection_item, do_load_resource, check_aos_version, content_to_dict


def ensure_present(module, aos, blueprint, virtnet):

    # if exist already return tru
    if virtnet.exists:
        module.exit_json(changed=False,
                         blueprint=blueprint.name,
                         name=virtnet.name,
                         id=virtnet.id,
                         value=virtnet.value)

    else:
        if not module.check_mode:
            try:
                virtnet.create(module.params['content'])
            except Exception as e:
                module.fail_json(msg="unable to create virtual-network : %s" % to_native(e))

        module.exit_json(changed=True,
                         blueprint=blueprint.name,
                         name=virtnet.name,
                         id=virtnet.id,
                         value=virtnet.value)


def ensure_absent(module, aos, blueprint, virtnet):

    if virtnet.exists:
        if not module.check_mode:
            try:
                virtnet.delete()
            except Exception as e:
                module.fail_json(msg="unable to delete virtual-network %s : %s" % (virtnet.name, to_native(e)))

        module.exit_json(changed=True,
                         blueprint=blueprint.name)

    else:
        module.exit_json(changed=False,
                         blueprint=blueprint.name)


def blueprint_virtnet(module):

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
    # Convert "content" to dict and extract name
    # --------------------------------------------------------------------
    if margs['content'] is not None:

        content = content_to_dict(module, margs['content'])

        if 'display_name' in content.keys():
            item_name = content['display_name']
        else:
            module.fail_json(msg="Unable to extract 'display_name' from 'content'")

    elif margs['name'] is not None:
        item_name = margs['name']

    # --------------------------------------------------------------------
    # Try to find VirtualNetwork object
    # --------------------------------------------------------------------
    try:
        virtnet = blueprint.VirtualNetworks[item_name]
    except:
        module.fail_json(msg="Something went wrong while trying to find Virtual Network %s in blueprint %s"
                         % (item_name, blueprint.name))

    # --------------------------------------------------------------------
    # Proceed based on State value
    # --------------------------------------------------------------------
    if margs['state'] == 'absent':

        ensure_absent(module, aos, blueprint, virtnet)

    elif margs['state'] == 'present':

        ensure_present(module, aos, blueprint, virtnet)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            blueprint=dict(required=True),
            name=dict(required=False),
            content=dict(required=False, type="json"),
            state=dict(choices=['present', 'absent'], default='present')
        ),
        mutually_exclusive=[('name', 'content')],
        required_one_of=[('name', 'content')],
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    blueprint_virtnet(module)


if __name__ == '__main__':
    main()
