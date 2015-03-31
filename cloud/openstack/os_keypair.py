#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
# Copyright (c) 2013, John Dewey <john@dewey.ws>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


DOCUMENTATION = '''
---
module: os_keypair
short_description: Add/Delete a keypair from OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
description:
   - Add or Remove key pair from OpenStack
options:
   name:
     description:
        - Name that has to be given to the key pair
     required: true
     default: None
   public_key:
     description:
        - The public key that would be uploaded to nova and injected to vm's upon creation
     required: false
     default: None
   public_key_file:
     description:
        - Path to local file containing ssh public key.  Mutually exclusive with public_key
    required: false
    default: None
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements: ["shade"]
'''

EXAMPLES = '''
# Creates a key pair with the running users public key
- os_keypair:
      cloud: mordred
      state: present
      name: ansible_key
      public_key: "{{ lookup('file','~/.ssh/id_rsa.pub') }}"

# Creates a new key pair and the private key returned after the run.
- os_keypair:
      cloud: rax-dfw
      state: present
      name: ansible_key
'''


def main():
    argument_spec = openstack_full_argument_spec(
        name            = dict(required=True),
        public_key      = dict(default=None),
        public_key_file = dict(default=None),
        state           = dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[['public_key', 'public_key_file']])
    module = AnsibleModule(argument_spec, **module_kwargs)

    if module.params['public_key_file']:
        public_key = open(module.params['public_key_file']).read()
    else:
        public_key = module.params['public_key']

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    name = module.params['name']
    public_key = module.params['public_key']

    try:
        cloud = shade.openstack_cloud(**module.params)

        if state == 'present':
            for key in cloud.list_keypairs():
                if key.name == name:
                    if public_key and (public_key != key.public_key):
                        module.fail_json(
                            msg="Key name %s present but key hash not the same"
                                " as offered. Delete key first." % key.name
                        )
                    else:
                        module.exit_json(changed=False, result="Key present")
            try:
                key = cloud.create_keypair(name, public_key)
            except Exception, e:
                module.exit_json(
                    msg="Error in creating the keypair: %s" % e.message
                )
            if not public_key:
                module.exit_json(changed=True, key=key.private_key)
            module.exit_json(changed=True, key=None)

        elif state == 'absent':
            for key in cloud.list_keypairs():
                if key.name == name:
                    try:
                        cloud.delete_keypair(name)
                    except Exception, e:
                        module.fail_json(
                            msg="Keypair deletion has failed: %s" % e.message
                        )
                    module.exit_json(changed=True, result="deleted")
            module.exit_json(changed=False, result="not present")

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
