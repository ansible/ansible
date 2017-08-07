#!/usr/bin/python
# Copyright 2017 Tomas Karasek <tom.to.the.k@gmail.com>
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: packet_project
short_description: Create/delete a project in Packet host.
description:
     - Create/delete a project in Packet host.
     - API is documented at U(https://www.packet.net/developers/api/projects).
version_added: "2.4"
author: "Tomas Karasek <tom.to.the.k@gmail.com>"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  payment_method:
    description:
     - Payment method is name of one of the payment methods available to your user.
     - When blank, the API assumes the default payment method.
  auth_token:
    description:
     - Packet api token. You can also supply it in env var C(PACKET_API_TOKEN).
  name:
     description:
     - Name for/of the project.
  id:
    description:
     - UUID of the project which you want to remove.

requirements:
  - "python >= 2.6"
  - "packet-python >= 1.35"

'''

EXAMPLES = '''
# All the examples assume that you have your Packet API token in env var PACKET_API_TOKEN.
# You can also pass the api token in module param auth_token.

- name: create new project
  hosts: localhost
  tasks:
    packet_project:
      name: "new project"

- name: remove project by id
  hosts: localhost
  tasks:
    packet_project:
      state: absent
      id: eef49903-7a09-4ca1-af67-4087c29ab5b6

- name: create new project with nondefault billing method
  hosts: localhost
  tasks:
    packet_project:
      name: "newer project"
      payment_method: "the other visa"
'''

RETURN = '''
changed:
  description: True if a project was created or removed.
  type: bool
  sample: True
  returned: success
name:
  description: Name of addressed project.
  type: string
  returned: success
id:
  description: UUID of addressed project.
  type: string
  returned: success
'''  # NOQA

import os
import uuid

from ansible.module_utils.basic import AnsibleModule


HAS_PACKET_SDK = True


try:
    import packet
except ImportError:
    HAS_PACKET_SDK = False


PACKET_API_TOKEN_ENV_VAR = "PACKET_API_TOKEN"


def is_valid_uuid(myuuid):
    try:
        val = uuid.UUID(myuuid, version=4)
    except ValueError:
        return False
    return str(val) == myuuid


def act_on_project(target_state, module, packet_conn):
    result_dict = {'changed': False}
    given_id = module.params.get('id')
    given_name = module.params.get('name')
    matching_projects = []
    if given_id:
        if not is_valid_uuid(given_id):
            raise Exception("%s is not valid UUID" % given_id)
        matching_projects = [
            p for p in packet_conn.list_projects() if given_id == p.id]
    else:
        matching_projects = [
            p for p in packet_conn.list_projects() if given_name == p.name]

    if target_state == 'present':
        if len(matching_projects) == 0:
            payment_method = module.params.get('payment_method')
            params = {"name": given_name, "payment_method_id": payment_method}
            new_project_data = packet_conn.call_api("projects", "POST", params)
            new_project = packet.Project(new_project_data, packet_conn)
            result_dict['changed'] = True
            matching_projects.append(new_project)
        result_dict['name'] = matching_projects[0].name
        result_dict['id'] = matching_projects[0].id
    else:
        if len(matching_projects) > 1:
            _msg = ("More than projects matched for module call with state = absent:"
                    "%s" % matching_projects)
            raise Exception("More than projects matched for module call with")
        if len(matching_projects) == 1:
            p = matching_projects[0]
            result_dict['name'] = p.name
            result_dict['id'] = p.id
            result_dict['changed'] = True
            try:
                p.delete()
            except Exception as e:
                _msg = ("while trying to remove project %s, id %s, got error: %s" %
                        (p.name, p.id, e))
                raise Exception(_msg)
    return result_dict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            auth_token=dict(default=os.environ.get(PACKET_API_TOKEN_ENV_VAR),
                            no_log=True),
            name=dict(type='str'),
            payment_method=dict(type='str'),
            id=dict(type='str'),
        ),
        required_one_of=[("name", "id",)],
        mutually_exclusive=[
            ('name', 'id'),
            ('id', 'payment_method'),
        ]
    )

    if not HAS_PACKET_SDK:
        module.fail_json(msg='packet required for this module')

    if not module.params.get('auth_token'):
        _fail_msg = ("if Packet API token is not in environment variable %s, "
                     "the auth_token parameter is required" %
                     PACKET_API_TOKEN_ENV_VAR)
        module.fail_json(msg=_fail_msg)

    auth_token = module.params.get('auth_token')

    packet_conn = packet.Manager(auth_token=auth_token)

    state = module.params.get('state')

    if state in ['present', 'absent']:
        try:
            module.exit_json(**act_on_project(state, module, packet_conn))
        except Exception as e:
            module.fail_json(
                msg='failed to set project state %s: %s' %
                (state, e))
    else:
        module.fail_json(msg='%s is not a valid state for this module' % state)


if __name__ == '__main__':
    main()
