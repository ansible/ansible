#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
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

DOCUMENTATION = '''
---
module: panos_cert_gen_ssh
short_description: generates a self-signed certificate using SSH protocol with SSH key
description:
    - This module generates a self-signed certificate that can be used by GlobalProtect client, SSL connector, or
    - otherwise. Root certificate must be preset on the system first. This module depends on paramiko for ssh.
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - paramiko
notes:
    - Checkmode is not supported.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device being configured.
        required: true
    key_filename:
        description:
            - Location of the filename that is used for the auth. Either I(key_filename) or I(password) is required.
        required: true
    password:
        description:
            - Password credentials to use for auth. Either I(key_filename) or I(password) is required.
        required: true
    cert_friendly_name:
        description:
            - Human friendly certificate name (not CN but just a friendly name).
        required: true
    cert_cn:
        description:
            - Certificate CN (common name) embedded in the certificate signature.
        required: true
    signed_by:
        description:
            - Undersigning authority (CA) that MUST already be presents on the device.
        required: true
    rsa_nbits:
        description:
            - Number of bits used by the RSA algorithm for the certificate generation.
        default: "2048"
'''

EXAMPLES = '''
# Generates a new self-signed certificate using ssh
- name: generate self signed certificate
  panos_cert_gen_ssh:
    ip_address: "192.168.1.1"
    password: "paloalto"
    cert_cn: "1.1.1.1"
    cert_friendly_name: "test123"
    signed_by: "root-ca"
'''

RETURN = '''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import time

try:
    import paramiko
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_PROMPTBUFF = 4096


def wait_with_timeout(module, shell, prompt, timeout=60):
    now = time.time()
    result = ""
    while True:
        if shell.recv_ready():
            result += shell.recv(_PROMPTBUFF)
            endresult = result.strip()
            if len(endresult) != 0 and endresult[-1] == prompt:
                break

        if time.time() - now > timeout:
            module.fail_json(msg="Timeout waiting for prompt")

    return result


def generate_cert(module, ip_address, key_filename, password,
                  cert_cn, cert_friendly_name, signed_by, rsa_nbits):
    stdout = ""

    client = paramiko.SSHClient()

    # add policy to accept all host keys, I haven't found
    # a way to retrieve the instance SSH key fingerprint from AWS
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if not key_filename:
        client.connect(ip_address, username="admin", password=password)
    else:
        client.connect(ip_address, username="admin", key_filename=key_filename)

    shell = client.invoke_shell()
    # wait for the shell to start
    buff = wait_with_timeout(module, shell, ">")
    stdout += buff

    # generate self-signed certificate
    if isinstance(cert_cn, list):
        cert_cn = cert_cn[0]
    cmd = 'request certificate generate signed-by {0} certificate-name {1} name {2} algorithm RSA rsa-nbits {3}\n'.format(
        signed_by, cert_friendly_name, cert_cn, rsa_nbits)
    shell.send(cmd)

    # wait for the shell to complete
    buff = wait_with_timeout(module, shell, ">")
    stdout += buff

    # exit
    shell.send('exit\n')

    if 'Success' not in buff:
        module.fail_json(msg="Error generating self signed certificate: " + stdout)

    client.close()
    return stdout


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        key_filename=dict(),
        password=dict(no_log=True),
        cert_cn=dict(required=True),
        cert_friendly_name=dict(required=True),
        rsa_nbits=dict(default='2048'),
        signed_by=dict(required=True)

    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['key_filename', 'password']])
    if not HAS_LIB:
        module.fail_json(msg='paramiko is required for this module')

    ip_address = module.params["ip_address"]
    key_filename = module.params["key_filename"]
    password = module.params["password"]
    cert_cn = module.params["cert_cn"]
    cert_friendly_name = module.params["cert_friendly_name"]
    signed_by = module.params["signed_by"]
    rsa_nbits = module.params["rsa_nbits"]

    try:
        stdout = generate_cert(module,
                               ip_address,
                               key_filename,
                               password,
                               cert_cn,
                               cert_friendly_name,
                               signed_by,
                               rsa_nbits)
    except Exception as exc:
        module.fail_json(msg=to_native(exc))

    module.exit_json(changed=True, msg="okey dokey")


if __name__ == '__main__':
    main()
