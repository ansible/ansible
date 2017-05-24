#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c)Matthias Dellweg & Bernhard Hopfenmüller 2017
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: foreman_global_parameter
short_description: Manage Foreman Global Parameters
description:
    - "Manage Foreman Global Parameter Entities"
    - "Uses https://github.com/SatelliteQE/nailgun"
version_added: "2.4"
author:
- "Bernhard Hopfenmueller(@Fobhep)"
- "Matthias Dellweg (@mdellweg)"
requirements:
    - nailgun >= 0.29.0
options:
    server_url:
        description:
        - URL of Foreman server
        required: true
    username:
        description:
        - Username on Foreman server
        required: true
        default: true
    password:
        description:
        - Password for user accessing Foreman server
        required: true
    verify_ssl:
        description:
        - Verify SSL of the Foreman server
        required: false
    name:
        description:
        - Name of the Global Parameter
        required: true
    value:
        description:
        - Value of the Global Parameter
        required: false
    state:
        description:
        - State of the Global Parameter
        required: false
        choices:
        - present
        - absent
'''

EXAMPLES = '''
- name: "Create a Global Parameter"
  local_action:
      module: foreman_global_parameter
      username: "admin"
      password: "admin"
      server_url: "https://fakeserver.com"
      name: "TheAnswer"
      value: "42"
      state: present

- name: "Delete a Global Parameter"
  local_action:
      module: foreman_global_parameter
      username: "admin"
      password: "admin"
      server_url: "https://fakeserver.com"
      name: "TheAnswer"
      state: absent
'''

RETURN = ''' # '''

try:
    from nailgun.config import ServerConfig
    import nailgun.entity_mixins
    import nailgun.entities
    HAS_NAILGUN_PACKAGE = True
except:
    HAS_NAILGUN_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule

'''CommonParameter needs to inherit functionalities
   for searching, updating and deleting'''


class CommonParameter(
    nailgun.entities.CommonParameter,
    nailgun.entity_mixins.Entity,
    nailgun.entity_mixins.EntityCreateMixin,
    nailgun.entity_mixins.EntityDeleteMixin,
    nailgun.entity_mixins.EntityReadMixin,
    nailgun.entity_mixins.EntitySearchMixin,
    nailgun.entity_mixins.EntityUpdateMixin
):

    pass


def createCommonParameter(name, value):
    CommonParameter(name=name, value=value).create()


def updateCommonParameter(name, value):
    CommonParameter(name=name, value=value).update()


def createServer(server_url, auth, verify_ssl):
    ServerConfig(
        url=server_url,
        auth=auth,
        verify=verify_ssl,
    ).save()


def findEntity(entity, **kwargs):
    instance = entity(**kwargs)
    return instance.search(
        set(),
        dict(('search', '{0}="{1}"'.format(key, kwargs[key])) for key in kwargs)
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            verify_ssl=dict(required=False, type='bool', default=True),
            name=dict(required=True),
            value=dict(required=False),
            state=dict(required=True, choices=['present', 'absent']),
        ),
        required_if=(['state', 'present', ['value']],),
        supports_check_mode=True
    )
    if not HAS_NAILGUN_PACKAGE:
        module.fail_json(
            msg="""Missing required nailgun module (check docs or install)
            with: pip install nailgun"""
        )

    server_url = module.params['server_url']
    username = module.params['username']
    password = module.params['password']
    verify_ssl = module.params['verify_ssl']
    name = module.params['name']
    value = module.params['value']
    state = module.params['state']
    auth = (username, password)
    changed = False
    try:
        createServer(server_url, auth, verify_ssl)
        param = findEntity(CommonParameter, name=name)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Foreman server: %s " % e)
    try:
        if state == 'present':
            if len(param) == 1:
                if param[0].value != value:
                    param[0].value = value
                    param[0].update()
                    changed = True
            else:
                createCommonParameter(name, value)
                changed = True
        elif state == 'absent':
            if len(param) == 1:
                param[0].delete()
                changed = True
    except Exception as e:
        module.fail_json(msg=e)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
