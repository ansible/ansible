#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_sshkey
short_description: Create/delete an SSH key in DigitalOcean
description:
     - Create/delete an SSH key.
version_added: "1.6"
author: "Michael Gregson (@mgregson)"
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
  - Version 1 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
  - dopy
'''


EXAMPLES = '''
# Ensure a SSH key is present
# If a key matches this name, will return the ssh key id and changed = False
# If no existing key matches this name, a new key is created, the ssh key id is returned and changed = False

- digital_ocean_sshkey:
    state: present
    name: my_ssh_key
    ssh_pub_key: 'ssh-rsa AAAA...'
    client_id: XXX
    api_key: XXX

'''

import os
import traceback

try:
    from dopy.manager import DoError, DoManager
    HAS_DOPY = True
except ImportError:
    HAS_DOPY = False

from ansible.module_utils.basic import AnsibleModule


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
    except KeyError as e:
        module.fail_json(msg='Unable to load %s' % e.message)

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
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            client_id=dict(aliases=['CLIENT_ID'], no_log=True),
            api_key=dict(aliases=['API_KEY'], no_log=True),
            name=dict(type='str'),
            id=dict(aliases=['droplet_id'], type='int'),
            ssh_pub_key=dict(type='str'),
        ),
        required_one_of=(
            ['id', 'name'],
        ),
    )
    if not HAS_DOPY:
        module.fail_json(msg='dopy required for this module')

    try:
        core(module)
    except (DoError, Exception) as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
