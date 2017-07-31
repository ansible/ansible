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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: ec2_key
version_added: "1.5"
short_description: maintain an ec2 key pair.
description:
    - maintains ec2 key pairs. This module has a dependency on python-boto >= 2.5
options:
  name:
    description:
      - Name of the key pair.
    required: true
  key_material:
    description:
      - Public key material.
    required: false
  force:
    description:
      - Force overwrite of already existing key pair if key has changed.
    required: false
    default: true
    version_added: "2.3"
  state:
    description:
      - create or delete keypair
    required: false
    default: 'present'
    aliases: []
  wait:
    description:
      - Wait for the specified action to complete before returning.
    required: false
    default: false
    aliases: []
    version_added: "1.6"
  wait_timeout:
    description:
      - How long before wait gives up, in seconds
    required: false
    default: 300
    aliases: []
    version_added: "1.6"

extends_documentation_fragment:
 - aws
 - ec2
author: "Vincent Viallet (@zbal)"
'''

EXAMPLES = '''
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Creates a new ec2 key pair named `example` if not present, returns generated
# private key
- name: example ec2 key
  ec2_key:
    name: example

# Creates a new ec2 key pair named `example` if not present using provided key
# material.  This could use the 'file' lookup plugin to pull this off disk.
- name: example2 ec2 key
  ec2_key:
    name: example2
    key_material: 'ssh-rsa AAAAxyz...== me@example.com'
    state: present

# Given example2 is already existing, the key will not be replaced because the
# force flag was set to `false`
- name: example2 ec2 key
  ec2_key:
    name: example2
    key_material: 'ssh-rsa AAAAxyz...== me@example.com'
    force: false
    state: present

# Creates a new ec2 key pair named `example` if not present using provided key
# material
- name: example3 ec2 key
  ec2_key:
    name: example3
    key_material: "{{ item }}"
  with_file: /path/to/public_key.id_rsa.pub

# Removes ec2 key pair by name
- name: remove example key
  ec2_key:
    name: example
    state: absent
'''

try:
    import boto.ec2
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils._text import to_bytes
import random
import string


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        key_material=dict(required=False),
        force = dict(required=False, type='bool', default=True),
        state = dict(default='present', choices=['present', 'absent']),
        wait = dict(type='bool', default=False),
        wait_timeout = dict(default=300),
    )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    name = module.params['name']
    state = module.params.get('state')
    key_material = module.params.get('key_material')
    force = module.params.get('force')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    changed = False

    ec2 = ec2_connect(module)

    # find the key if present
    key = ec2.get_key_pair(name)

    # Ensure requested key is absent
    if state == 'absent':
        if key:
            '''found a match, delete it'''
            if not module.check_mode:
                try:
                    key.delete()
                    if wait:
                        start = time.time()
                        action_complete = False
                        while (time.time() - start) < wait_timeout:
                            if not ec2.get_key_pair(name):
                                action_complete = True
                                break
                            time.sleep(1)
                        if not action_complete:
                            module.fail_json(msg="timed out while waiting for the key to be removed")
                except Exception as e:
                    module.fail_json(msg="Unable to delete key pair '%s' - %s" % (key, e))
            key = None
            changed = True

    # Ensure requested key is present
    elif state == 'present':
        if key:
            # existing key found
            if key_material and force:
                # EC2's fingerprints are non-trivial to generate, so push this key
                # to a temporary name and make ec2 calculate the fingerprint for us.
                #
                # http://blog.jbrowne.com/?p=23
                # https://forums.aws.amazon.com/thread.jspa?messageID=352828

                # find an unused name
                test = 'empty'
                while test:
                    randomchars = [random.choice(string.ascii_letters + string.digits) for x in range(0,10)]
                    tmpkeyname = "ansible-" + ''.join(randomchars)
                    test = ec2.get_key_pair(tmpkeyname)

                # create tmp key
                tmpkey = ec2.import_key_pair(tmpkeyname, to_bytes(key_material))
                # get tmp key fingerprint
                tmpfingerprint = tmpkey.fingerprint
                # delete tmp key
                tmpkey.delete()

                if key.fingerprint != tmpfingerprint:
                    if not module.check_mode:
                        key.delete()
                        key = ec2.import_key_pair(name, to_bytes(key_material))

                        if wait:
                            start = time.time()
                            action_complete = False
                            while (time.time() - start) < wait_timeout:
                                if ec2.get_key_pair(name):
                                    action_complete = True
                                    break
                                time.sleep(1)
                            if not action_complete:
                                module.fail_json(msg="timed out while waiting for the key to be re-created")

                    changed = True
            pass

        # if the key doesn't exist, create it now
        else:
            '''no match found, create it'''
            if not module.check_mode:
                if key_material:
                    '''We are providing the key, need to import'''
                    key = ec2.import_key_pair(name, to_bytes(key_material))
                else:
                    '''
                    No material provided, let AWS handle the key creation and
                    retrieve the private key
                    '''
                    key = ec2.create_key_pair(name)

                if wait:
                    start = time.time()
                    action_complete = False
                    while (time.time() - start) < wait_timeout:
                        if ec2.get_key_pair(name):
                            action_complete = True
                            break
                        time.sleep(1)
                    if not action_complete:
                        module.fail_json(msg="timed out while waiting for the key to be created")

            changed = True

    if key:
        data = {
            'name': key.name,
            'fingerprint': key.fingerprint
        }
        if key.material:
            data.update({'private_key': key.material})

        module.exit_json(changed=changed, key=data)
    else:
        module.exit_json(changed=changed, key=None)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
