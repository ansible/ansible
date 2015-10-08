#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_win_password
short_description: gets the default administrator password for ec2 windows instances
description:
    - Gets the default administrator password from any EC2 Windows instance.  The instance is referenced by its id (e.g. i-XXXXXXX). This module has a dependency on python-boto.
version_added: "2.0"
author: "Rick Mendes (@rickmendes)"
options:
  instance_id:
    description:
      - The instance id to get the password data from. 
    required: true
  key_file:
    description:
      - Path to the file containing the key pair used on the instance.
    required: true
  key_passphrase:
    version_added: "2.0"
    description:
      - The passphrase for the instance key pair. The key must use DES or 3DES encryption for this module to decrypt it. You can use openssl to convert your password protected keys if they do not use DES or 3DES. ex) openssl rsa -in current_key -out new_key -des3. 
    required: false
    default: null
  wait:
    version_added: "2.0"
    description:
      - Whether or not to wait for the password to be available before returning.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    version_added: "2.0"
    description:
      - Number of seconds to wait before giving up.
    required: false
    default: 120

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Example of getting a password
tasks:
- name: get the Administrator password
  ec2_win_password:
    profile: my-boto-profile
    instance_id: i-XXXXXX
    region: us-east-1
    key_file: "~/aws-creds/my_test_key.pem"

# Example of getting a password with a password protected key
tasks:
- name: get the Administrator password
  ec2_win_password:
    profile: my-boto-profile
    instance_id: i-XXXXXX
    region: us-east-1
    key_file: "~/aws-creds/my_protected_test_key.pem"
    key_passphrase: "secret"

# Example of waiting for a password
tasks:
- name: get the Administrator password
  ec2_win_password:
    profile: my-boto-profile
    instance_id: i-XXXXXX
    region: us-east-1
    key_file: "~/aws-creds/my_test_key.pem"
    wait: yes
    wait_timeout: 45
'''

from base64 import b64decode
from os.path import expanduser
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import datetime

try:
    import boto.ec2
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            instance_id = dict(required=True),
            key_file = dict(required=True),
            key_passphrase = dict(no_log=True, default=None, required=False),
            wait = dict(type='bool', default=False, required=False),
            wait_timeout = dict(default=120, required=False),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='Boto required for this module.')

    instance_id = module.params.get('instance_id')
    key_file = expanduser(module.params.get('key_file'))
    key_passphrase = module.params.get('key_passphrase')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    ec2 = ec2_connect(module)

    if wait:
        start = datetime.datetime.now()
        end = start + datetime.timedelta(seconds=wait_timeout)

        while datetime.datetime.now() < end:
            data = ec2.get_password_data(instance_id)
            decoded = b64decode(data)
            if wait and not decoded:
                time.sleep(5)
            else:
                break
    else:
        data = ec2.get_password_data(instance_id)
        decoded = b64decode(data)

    if wait and datetime.datetime.now() >= end:
        module.fail_json(msg = "wait for password timeout after %d seconds" % wait_timeout)

    f = open(key_file, 'r')
    key = RSA.importKey(f.read(), key_passphrase)
    cipher = PKCS1_v1_5.new(key)
    sentinel = 'password decryption failed!!!'

    try:
        decrypted = cipher.decrypt(decoded, sentinel)
    except ValueError as e:
        decrypted = None

    if decrypted == None:
        module.exit_json(win_password='', changed=False)
    else:
        if wait:
            elapsed = datetime.datetime.now() - start
            module.exit_json(win_password=decrypted, changed=True, elapsed=elapsed.seconds)
        else:
            module.exit_json(win_password=decrypted, changed=True)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
