#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013, Benno Joy <benno@ansible.com>
# (c) 2013, John Dewey <john@dewey.ws>
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
    from novaclient.v1_1 import client as nova_client
    from novaclient import exceptions as exc
    import time
except ImportError:
    print("failed=True msg='novaclient is required for this module to work'")

DOCUMENTATION = '''
---
module: nova_keypair
version_added: "1.2"
short_description: Add/Delete key pair from nova
description:
   - Add or Remove key pair from nova .
options:
   login_username:
     description:
        - login username to authenticate to keystone
     required: true
     default: admin
   login_password:
     description:
        - Password of login user
     required: true
     default: 'yes'
   login_tenant_name:
     description:
        - The tenant name of the login user
     required: true
     default: 'yes'
   auth_url:
     description:
        - The keystone url for authentication
     required: false
     default: 'http://127.0.0.1:35357/v2.0/'
   region_name:
     description:
        - Name of the region
     required: false
     default: None
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
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

requirements: ["novaclient"]
'''
EXAMPLES = '''
# Creates a key pair with the running users public key
- nova_keypair: state=present login_username=admin
                login_password=admin login_tenant_name=admin name=ansible_key
                public_key={{ lookup('file','~/.ssh/id_rsa.pub') }}

# Creates a new key pair and the private key returned after the run.
- nova_keypair: state=present login_username=admin login_password=admin
                login_tenant_name=admin name=ansible_key
'''

def main():
    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
        name                            = dict(required=True),
        public_key                      = dict(default=None),
        state                           = dict(default='present', choices=['absent', 'present'])
    ))
    module = AnsibleModule(argument_spec=argument_spec)

    nova = nova_client.Client(module.params['login_username'],
                              module.params['login_password'],
                              module.params['login_tenant_name'],
                              module.params['auth_url'],
                              region_name=module.params['region_name'],
                              service_type='compute')
    try:
        nova.authenticate()
    except exc.Unauthorized, e:
        module.fail_json(msg = "Invalid OpenStack Nova credentials.: %s" % e.message)
    except exc.AuthorizationFailure, e:
        module.fail_json(msg = "Unable to authorize user: %s" % e.message)

    if module.params['state'] == 'present':
        for key in nova.keypairs.list():
            if key.name == module.params['name']:
                if module.params['public_key'] and (module.params['public_key'] != key.public_key ):
                    module.fail_json(msg = "name {} present but key hash not the same as offered.  Delete key first.".format(key['name']))
                else:
                    module.exit_json(changed = False, result = "Key present")            
        try:
            key = nova.keypairs.create(module.params['name'], module.params['public_key'])
        except Exception, e:
            module.exit_json(msg = "Error in creating the keypair: %s" % e.message)
        if not module.params['public_key']:
            module.exit_json(changed = True, key = key.private_key)
        module.exit_json(changed = True, key = None)
    if module.params['state'] == 'absent':
        for key in nova.keypairs.list():
            if key.name == module.params['name']:
                try:
                    nova.keypairs.delete(module.params['name'])
                except Exception, e:
                    module.fail_json(msg = "The keypair deletion has failed: %s" % e.message)
                module.exit_json( changed = True, result = "deleted")
        module.exit_json(changed = False, result = "not present")

# this is magic, see lib/ansible/module.params['common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()

