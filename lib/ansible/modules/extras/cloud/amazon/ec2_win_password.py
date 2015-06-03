#!/usr/bin/python

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
      - path to the file containing the key pair used on the instance
    required: true
  key_passphrase:
    version_added: "2.0"
    description:
      - The passphrase for the instance key pair. The key must use DES or 3DES encryption for this module to decrypt it. You can use openssl to convert your password protected keys if they do not use DES or 3DES. ex) openssl rsa -in current_key -out new_key -des3. 
    required: false
  region:
    description:
      - The AWS region to use.  Must be specified if ec2_url is not used. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    default: null
    aliases: [ 'aws_region', 'ec2_region' ]

extends_documentation_fragment: aws
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
'''

from base64 import b64decode
from os.path import expanduser
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

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
            key_passphrase = dict(default=None),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='Boto required for this module.')

    instance_id = module.params.get('instance_id')
    key_file = expanduser(module.params.get('key_file'))
    key_passphrase = module.params.get('key_passphrase')

    ec2 = ec2_connect(module)

    data = ec2.get_password_data(instance_id)
    decoded = b64decode(data)

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
        module.exit_json(win_password=decrypted, changed=True)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
