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
module: digital_ocean
short_description: Create/delete a droplet/SSH_key in DigitalOcean
description:
     - Create/delete a droplet in DigitalOcean and optionally wait for it to be 'running', or deploy an SSH key.
version_added: "1.3"
options:
  command:
    description:
     - Which target you want to operate on.
    default: droplet
    choices: ['droplet', 'ssh']
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'active', 'absent', 'deleted']
  client_id:
     description:
     - DigitalOcean manager id.
  api_key:
    description:
     - DigitalOcean api key.
  id:
    description:
     - Numeric, the droplet id you want to operate on.
  name:
    description:
     - String, this is the name of the droplet - must be formatted by hostname rules, or the name of a SSH key.
  unique_name:
    description:
     - Bool, require unique hostnames.  By default, DigitalOcean allows multiple hosts with the same name.  Setting this to "yes" allows only one host per name.  Useful for idempotence.
    version_added: "1.4"
    default: "no"
    choices: [ "yes", "no" ]
  size_id:
    description:
     - Numeric, this is the id of the size you would like the droplet created with.
  image_id:
    description:
     - Numeric, this is the id of the image you would like the droplet created with.
  region_id:
    description:
     - "Numeric, this is the id of the region you would like your server to be created in."
  ssh_key_ids:
    description:
     - Optional, comma separated list of ssh_key_ids that you would like to be added to the server.
  virtio:
    description:
     - "Bool, turn on virtio driver in droplet for improved network and storage I/O."
    version_added: "1.4"
    default: "yes"
    choices: [ "yes", "no" ]
  private_networking:
    description:
     - "Bool, add an additional, private network interface to droplet for inter-droplet communication."
    version_added: "1.4"
    default: "no"
    choices: [ "yes", "no" ]
  backups_enabled:
    description:
     - Optional, Boolean, enables backups for your droplet.
    version_added: "1.6"
    default: "no"
    choices: [ "yes", "no" ]
  wait:
    description:
     - Wait for the droplet to be in state 'running' before returning.  If wait is "no" an ip_address may not be returned.
    default: "yes"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
     - How long before wait gives up, in seconds.
    default: 300
  ssh_pub_key:
    description:
     - The public SSH key you want to add to your account.

notes:
  - Two environment variables can be used, DO_CLIENT_ID and DO_API_KEY.
requirements: [ dopy ]
'''


EXAMPLES = '''
# Ensure a SSH key is present
# If a key matches this name, will return the ssh key id and changed = False
# If no existing key matches this name, a new key is created, the ssh key id is returned and changed = False

- digital_ocean: >
      state=present
      command=ssh
      name=my_ssh_key
      ssh_pub_key='ssh-rsa AAAA...'
      client_id=XXX
      api_key=XXX

# Create a new Droplet
# Will return the droplet details including the droplet id (used for idempotence)

- digital_ocean: >
      state=present
      command=droplet
      name=mydroplet
      client_id=XXX
      api_key=XXX
      size_id=1
      region_id=2
      image_id=3
      wait_timeout=500
  register: my_droplet
- debug: msg="ID is {{ my_droplet.droplet.id }}"
- debug: msg="IP is {{ my_droplet.droplet.ip_address }}"

# Ensure a droplet is present
# If droplet id already exist, will return the droplet details and changed = False
# If no droplet matches the id, a new droplet will be created and the droplet details (including the new id) are returned, changed = True.

- digital_ocean: >
      state=present
      command=droplet
      id=123
      name=mydroplet
      client_id=XXX
      api_key=XXX
      size_id=1
      region_id=2
      image_id=3
      wait_timeout=500

# Create a droplet with ssh key
# The ssh key id can be passed as argument at the creation of a droplet (see ssh_key_ids).
# Several keys can be added to ssh_key_ids as id1,id2,id3
# The keys are used to connect as root to the droplet.

- digital_ocean: >
      state=present
      ssh_key_ids=id1,id2
      name=mydroplet
      client_id=XXX
      api_key=XXX
      size_id=1
      region_id=2
      image_id=3
'''

import sys
import os
import time

try:
    import dopy
    from dopy.manager import DoError, DoManager
except ImportError, e:
    print "failed=True msg='dopy >= 0.2.3 required for this module'"
    sys.exit(1)

if dopy.__version__ < '0.2.3':
    print "failed=True msg='dopy >= 0.2.3 required for this module'"
    sys.exit(1)

class TimeoutError(DoError):
    def __init__(self, msg, id):
        super(TimeoutError, self).__init__(msg)
        self.id = id

class JsonfyMixIn(object):
    def to_json(self):
        return self.__dict__

class Droplet(JsonfyMixIn):
    manager = None

    def __init__(self, droplet_json):
        self.status = 'new'
        self.__dict__.update(droplet_json)

    def is_powered_on(self):
        return self.status == 'active'

    def update_attr(self, attrs=None):
        if attrs:
            for k, v in attrs.iteritems():
                setattr(self, k, v)
        else:
            json = self.manager.show_droplet(self.id)
            if json['ip_address']:
                self.update_attr(json)

    def power_on(self):
        assert self.status == 'off', 'Can only power on a closed one.'
        json = self.manager.power_on_droplet(self.id)
        self.update_attr(json)

    def ensure_powered_on(self, wait=True, wait_timeout=300):
        if self.is_powered_on():
            return
        if self.status == 'off':  # powered off
            self.power_on()

        if wait:
            end_time = time.time() + wait_timeout
            while time.time() < end_time:
                time.sleep(min(20, end_time - time.time()))
                self.update_attr()
                if self.is_powered_on():
                    if not self.ip_address:
                        raise TimeoutError('No ip is found.', self.id)
                    return
            raise TimeoutError('Wait for droplet running timeout', self.id)

    def destroy(self):
        return self.manager.destroy_droplet(self.id, scrub_data=True)

    @classmethod
    def setup(cls, client_id, api_key):
        cls.manager = DoManager(client_id, api_key)

    @classmethod
    def add(cls, name, size_id, image_id, region_id, ssh_key_ids=None, virtio=True, private_networking=False, backups_enabled=False):
        private_networking_lower = str(private_networking).lower()
        backups_enabled_lower = str(backups_enabled).lower()
        json = cls.manager.new_droplet(name, size_id, image_id, region_id, ssh_key_ids, virtio, private_networking_lower, backups_enabled_lower)
        droplet = cls(json)
        return droplet

    @classmethod
    def find(cls, id=None, name=None):
        if not id and not name:
            return False

        droplets = cls.list_all()

        # Check first by id.  digital ocean requires that it be unique
        for droplet in droplets:
            if droplet.id == id:
                return droplet

        # Failing that, check by hostname.
        for droplet in droplets:
            if droplet.name == name:
                return droplet

        return False

    @classmethod
    def list_all(cls):
        json = cls.manager.all_active_droplets()
        return map(cls, json)

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
    command = module.params['command']
    state = module.params['state']

    if command == 'droplet':
        Droplet.setup(client_id, api_key)
        if state in ('active', 'present'):

            # First, try to find a droplet by id.
            droplet = Droplet.find(id=module.params['id'])

            # If we couldn't find the droplet and the user is allowing unique
            # hostnames, then check to see if a droplet with the specified
            # hostname already exists.
            if not droplet and module.params['unique_name']:
                droplet = Droplet.find(name=getkeyordie('name'))

            # If both of those attempts failed, then create a new droplet.
            if not droplet:
                droplet = Droplet.add(
                    name=getkeyordie('name'),
                    size_id=getkeyordie('size_id'),
                    image_id=getkeyordie('image_id'),
                    region_id=getkeyordie('region_id'),
                    ssh_key_ids=module.params['ssh_key_ids'],
                    virtio=module.params['virtio'],
                    private_networking=module.params['private_networking'],
                    backups_enabled=module.params['backups_enabled'],
                )

            if droplet.is_powered_on():
                changed = False

            droplet.ensure_powered_on(
                wait=getkeyordie('wait'),
                wait_timeout=getkeyordie('wait_timeout')
            )

            module.exit_json(changed=changed, droplet=droplet.to_json())

        elif state in ('absent', 'deleted'):
            # First, try to find a droplet by id.
            droplet = Droplet.find(module.params['id'])

            # If we couldn't find the droplet and the user is allowing unique
            # hostnames, then check to see if a droplet with the specified
            # hostname already exists.
            if not droplet and module.params['unique_name']:
                droplet = Droplet.find(name=getkeyordie('name'))

            if not droplet:
                module.exit_json(changed=False, msg='The droplet is not found.')

            event_json = droplet.destroy()
            module.exit_json(changed=True, event_id=event_json['event_id'])

    elif command == 'ssh':
        SSH.setup(client_id, api_key)
        name = getkeyordie('name')
        if state in ('active', 'present'):
            key = SSH.find(name)
            if key:
                module.exit_json(changed=False, ssh_key=key.to_json())
            key = SSH.add(name, getkeyordie('ssh_pub_key'))
            module.exit_json(changed=True, ssh_key=key.to_json())

        elif state in ('absent', 'deleted'):
            key = SSH.find(name)
            if not key:
                module.exit_json(changed=False, msg='SSH key with the name of %s is not found.' % name)
            key.destroy()
            module.exit_json(changed=True)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            command = dict(choices=['droplet', 'ssh'], default='droplet'),
            state = dict(choices=['active', 'present', 'absent', 'deleted'], default='present'),
            client_id = dict(aliases=['CLIENT_ID'], no_log=True),
            api_key = dict(aliases=['API_KEY'], no_log=True),
            name = dict(type='str'),
            size_id = dict(type='int'),
            image_id = dict(type='int'),
            region_id = dict(type='int'),
            ssh_key_ids = dict(default=''),
            virtio = dict(type='bool', default='yes'),
            private_networking = dict(type='bool', default='no'),
            backups_enabled = dict(type='bool', default='no'),
            id = dict(aliases=['droplet_id'], type='int'),
            unique_name = dict(type='bool', default='no'),
            wait = dict(type='bool', default=True),
            wait_timeout = dict(default=300, type='int'),
            ssh_pub_key = dict(type='str'),
        ),
        required_together = (
            ['size_id', 'image_id', 'region_id'],
        ),
        mutually_exclusive = (
            ['size_id', 'ssh_pub_key'],
            ['image_id', 'ssh_pub_key'],
            ['region_id', 'ssh_pub_key'],
        ),
        required_one_of = (
            ['id', 'name'],
        ),
    )

    try:
        core(module)
    except TimeoutError, e:
        module.fail_json(msg=str(e), id=e.id)
    except (DoError, Exception), e:
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *

main()
