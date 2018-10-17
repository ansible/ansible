#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_win_password
short_description: gets the default administrator password for ec2 windows instances
description:
    - Gets the default administrator password from any EC2 Windows instance. The instance is referenced by its id (e.g. C(i-XXXXXXX)). This module
      has a dependency on python-boto.
version_added: "2.0"
author: "Rick Mendes (@rickmendes)"
options:
  instance_id:
    description:
      - The instance id to get the password data from.
    required: true
  key_file:
    description:
      - Path to the file containing the key pair used on the instance, conflicts with key_data.
    required: false
  key_data:
    version_added: "2.8"
    description:
      - Variable that references the private key (usually stored in vault), conflicts with key_file.
    required: false
  key_passphrase:
    version_added: "2.0"
    description:
      - The passphrase for the instance key pair. The key must use DES or 3DES encryption for this module to decrypt it. You can use openssl to
        convert your password protected keys if they do not use DES or 3DES. ex) C(openssl rsa -in current_key -out new_key -des3).
  wait:
    version_added: "2.0"
    description:
      - Whether or not to wait for the password to be available before returning.
    type: bool
    default: 'no'
  wait_timeout:
    version_added: "2.0"
    description:
      - Number of seconds to wait before giving up.
    default: 120

extends_documentation_fragment:
    - aws
    - ec2

requirements:
    - cryptography

notes:
    - As of Ansible 2.4, this module requires the python cryptography module rather than the
      older pycrypto module.
'''

EXAMPLES = '''
# Example of getting a password
- name: get the Administrator password
  ec2_win_password:
    profile: my-boto-profile
    instance_id: i-XXXXXX
    region: us-east-1
    key_file: "~/aws-creds/my_test_key.pem"

# Example of getting a password using a variable
- name: get the Administrator password
  ec2_win_password:
    profile: my-boto-profile
    instance_id: i-XXXXXX
    region: us-east-1
    key_data: "{{ ec2_private_key }}"

# Example of getting a password with a password protected key
- name: get the Administrator password
  ec2_win_password:
    profile: my-boto-profile
    instance_id: i-XXXXXX
    region: us-east-1
    key_file: "~/aws-creds/my_protected_test_key.pem"
    key_passphrase: "secret"

# Example of waiting for a password
- name: get the Administrator password
  ec2_win_password:
    profile: my-boto-profile
    instance_id: i-XXXXXX
    region: us-east-1
    key_file: "~/aws-creds/my_test_key.pem"
    wait: yes
    wait_timeout: 45
'''

import datetime
import time
from base64 import b64decode

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, ec2_argument_spec, ec2_connect
from ansible.module_utils._text import to_bytes


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        instance_id=dict(required=True),
        key_file=dict(required=False, default=None, type='path'),
        key_passphrase=dict(no_log=True, default=None, required=False),
        key_data=dict(no_log=True, default=None, required=False),
        wait=dict(type='bool', default=False, required=False),
        wait_timeout=dict(default=120, required=False, type='int'),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='Boto required for this module.')

    if not HAS_CRYPTOGRAPHY:
        module.fail_json(msg='cryptography package required for this module.')

    instance_id = module.params.get('instance_id')
    key_file = module.params.get('key_file')
    key_data = module.params.get('key_data')
    if module.params.get('key_passphrase') is None:
        b_key_passphrase = None
    else:
        b_key_passphrase = to_bytes(module.params.get('key_passphrase'), errors='surrogate_or_strict')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    ec2 = ec2_connect(module)

    if wait:
        start = datetime.datetime.now()
        end = start + datetime.timedelta(seconds=wait_timeout)

        while datetime.datetime.now() < end:
            data = ec2.get_password_data(instance_id)
            decoded = b64decode(data)
            if not decoded:
                time.sleep(5)
            else:
                break
    else:
        data = ec2.get_password_data(instance_id)
        decoded = b64decode(data)

    if wait and datetime.datetime.now() >= end:
        module.fail_json(msg="wait for password timeout after %d seconds" % wait_timeout)

    if key_file is not None and key_data is None:
        try:
            with open(key_file, 'rb') as f:
                key = load_pem_private_key(f.read(), b_key_passphrase, default_backend())
        except IOError as e:
            # Handle bad files
            module.fail_json(msg="I/O error (%d) opening key file: %s" % (e.errno, e.strerror))
        except (ValueError, TypeError) as e:
            # Handle issues loading key
            module.fail_json(msg="unable to parse key file")
    elif key_data is not None and key_file is None:
        try:
            key = load_pem_private_key(key_data, b_key_passphrase, default_backend())
        except (ValueError, TypeError) as e:
            module.fail_json(msg="unable to parse key data")

    try:
        decrypted = key.decrypt(decoded, PKCS1v15())
    except ValueError as e:
        decrypted = None

    if decrypted is None:
        module.exit_json(win_password='', changed=False)
    else:
        if wait:
            elapsed = datetime.datetime.now() - start
            module.exit_json(win_password=decrypted, changed=True, elapsed=elapsed.seconds)
        else:
            module.exit_json(win_password=decrypted, changed=True)


if __name__ == '__main__':
    main()
