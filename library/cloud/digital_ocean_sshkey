#!/usr/bin/python
# -*- coding: utf-8 -*-

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
DOCUMENTATION = '''
---
module: digital_ocean_sshkey
short_description: Create/delete an SSH key in DigitalOcean
description:
     - Create/delete an SSH key.
version_added: "1.6"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  client_id:
     description:
     - DigitalOcean manager id.
  api_key:
    description:
     - DigitalOcean api key.
  id:
    description:
     - Numeric, the SSH key id you want to operate on.
  name:
    description:
     - String, this is the name of an SSH key to create or destroy.
  ssh_pub_key:
    description:
     - The public SSH key you want to add to your account.

notes:
  - Two environment variables can be used, DO_CLIENT_ID and DO_API_KEY.
'''


EXAMPLES = '''
# Ensure a SSH key is present
# If a key matches this name, will return the ssh key id and changed = False
# If no existing key matches this name, a new key is created, the ssh key id is returned and changed = False

- digital_ocean_sshkey: >
      state=present
      name=my_ssh_key
      ssh_pub_key='ssh-rsa AAAA...'
      client_id=XXX
      api_key=XXX

'''

import sys
import os
import time

try:
    from dopy.manager import DoError, DoManager
except ImportError as e:
    print "failed=True msg='dopy required for this module'"
    sys.exit(1)

class TimeoutError(DoError):
    def __init__(self, msg, id):
        super(TimeoutError, self).__init__(msg)
        self.id = id

class JsonfyMixIn(object):
    def to_json(self):
        return self.__dict__

class SSH(JsonfyMixIn):
    manager = None

    def __init__(self, ssh_key_json):
        self.__dict__.update(ssh_key_json)
    update_attr = __init__

    def destroy(self):
        self.manager.destroy_ssh_key(self.id)
        return True

    @classmethod
    def setup(cls, client_id, api_key):
        cls.manager = DoManager(client_id, api_key)

    @classmethod
    def find(cls, name):
        if not name:
            return False
        keys = cls.list_all()
        for key in keys:
            if key.name == name:
                return key
        return False

    @classmethod
    def list_all(cls):
        json = cls.manager.all_ssh_keys()
        return map(cls, json)

    @classmethod
    def add(cls, name, key_pub):
        json = cls.manager.new_ssh_key(name, key_pub)
        return cls(json)

def core(module):
    def getkeyordie(k):
        v = module.params[k]
        if v is None:
            module.fail_json(msg='Unable to load %s' % k)
        return v

    try:
        # params['client_id'] will be None even if client_id is not passed in
        client_id = module.params['client_id'] or os.environ['DO_CLIENT_ID']
        api_key = module.params['api_key'] or os.environ['DO_API_KEY']
    except KeyError, e:
        module.fail_json(msg='Unable to load %s' % e.message)

    changed = True
    state = module.params['state']

    SSH.setup(client_id, api_key)
    name = getkeyordie('name')
    if state in ('present'):
        key = SSH.find(name)
        if key:
            module.exit_json(changed=False, ssh_key=key.to_json())
        key = SSH.add(name, getkeyordie('ssh_pub_key'))
        module.exit_json(changed=True, ssh_key=key.to_json())

    elif state in ('absent'):
        key = SSH.find(name)
        if not key:
            module.exit_json(changed=False, msg='SSH key with the name of %s is not found.' % name)
        key.destroy()
        module.exit_json(changed=True)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(choices=['present', 'absent'], default='present'),
            client_id = dict(aliases=['CLIENT_ID'], no_log=True),
            api_key = dict(aliases=['API_KEY'], no_log=True),
            name = dict(type='str'),
            id = dict(aliases=['droplet_id'], type='int'),
            ssh_pub_key = dict(type='str'),
        ),
        required_one_of = (
            ['id', 'name'],
        ),
    )

    try:
        core(module)
    except TimeoutError as e:
        module.fail_json(msg=str(e), id=e.id)
    except (DoError, Exception) as e:
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *

main()
