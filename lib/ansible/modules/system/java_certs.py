#!/usr/bin/python
#
# (c) 2013, RSD Services S.A
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
module: java_cert
version_added: "2.2"
short_description: Uses keytool to import/remove key from java keystore(cacerts)
description:
  - This is a wrapper module around keytool. Which can be used to import/remove certificates from a given java keystore.
options:
  cert_url:
    description:
      - Basic URL to fetch SSL certificate from
    required: true
  cert_port:
    description:
      - Port to connect to URL. This will be used to create server URL:PORT
    required: false
    default: 443
  cert_path:
    description:
      - Local path to load certificate from
    required: false
    default: null
  cert_alias:
    description:
      - Imported certificate alias
    required: false
    default: null
  keystore_path:
    description:
      - Path to keystore.
    required: false
    default: null
  keystore_pass:
    description:
      - Keystore password
    required: false
    default: null
  keystore_create:
    description:
      - Create keystore if it doesn't exist
    required: false
    default: null
  state:
    description:
      - Defines action which can be either certificate import or removal.
    choices: [ 'present', 'absent' ]
    default: present
    required: false

author: Adam Hamsik @haad
'''

EXAMPLES = '''
# Import SSL certificate from google.com to a given cacerts keystore
java_certs:
  cert_url: google.com
  cert_port: 443
  keystore_path: /usr/lib/jvm/jre7/lib/security/cacerts
  keystore_pass: changeit
  state: present

# Remove certificate with given alias from a keystore
java_certs:
  cert_url: google.com
  keystore_path: /usr/lib/jvm/jre7/lib/security/cacerts
  keystore_pass: changeit
  state: absent

# Import SSL certificate from google.com to a keystore, create it if it doesn't exist
java_certs:
  cert_url: google.com
  keystore_path: /tmp/cacerts
  keystore_pass: changeit
  keystore_create: yes
  state: present
'''

RETURN = '''
msg:
  description: Output from stdou of keytool command after execution of given command.
  returned: success
  type: string
  sample: "Module require existing keystore at keystore_path '/tmp/test/cacerts'"

rc:
  description: Keytool command execution return value
  returned: success
  type: int
  sample: "0"

cmd:
  description: Executed command to get action done
  returned: success
  type: string
  sample: "keytool -importcert -noprompt -keystore"
'''

import os

def check_cert_present(module, keystore_path, keystore_pass, alias):
    ''' Check if certificate with alias is present in keystore located at keystore_path '''
    test_cmd = ("keytool -noprompt -list -keystore '{}' -storepass '{}' "
                "-alias '{}'").format(keystore_path, keystore_pass, alias)

    (check_rc, _, _) = module.run_command(test_cmd)
    if check_rc == 0:
        return True
    return False

def import_cert_url(module, url, port, keystore_path, keystore_pass, alias):
    ''' Import certificate from URL into keystore located at keystore_path '''
    fetch_cmd = ("keytool -printcert -rfc -sslserver {}:{}").format(url, port)
    import_cmd = ("keytool -importcert -noprompt -keystore '{}' -storepass '{}' "
                  "-alias '{}'").format(keystore_path, keystore_pass, alias)

    # Fetch SSL certificate from remote host.
    (_, fetch_out, _) = module.run_command(fetch_cmd, check_rc=True)

    # Use remote certificate from remote host and import it to a java keystore
    (import_rc, import_out, import_err) = module.run_command(import_cmd, data=fetch_out,
                                                             check_rc=False)
    if import_rc == 0:
        return module.exit_json(changed=True, msg=import_out,
                                rc=import_rc, cmd=import_cmd, stdout_lines=import_out)
    else:
        return module.fail_json(msg=import_out, rc=import_rc, cmd=import_cmd, error=import_err)

def import_cert_path(module, path, keystore_path, keystore_pass, alias):
    ''' Import certificate from path into keystore located on keystore_path as alias '''
    import_cmd = ("keytool -importcert -noprompt -keystore '{}' -storepass '{}' "
                  "-file '{}' -alias '{}'").format(keystore_path, keystore_pass, path, alias)

    # Use local certificate from local path and import it to a java keystore
    (import_rc, import_out, import_err) = module.run_command(import_cmd, check_rc=False)
    if import_rc == 0:
        return module.exit_json(changed=True, msg=import_out,
                                rc=import_rc, cmd=import_cmd, stdout_lines=import_out,
                                error=import_err)
    else:
        return module.fail_json(msg=import_out, rc=import_rc, cmd=import_cmd)

def delete_cert(module, keystore_path, keystore_pass, alias):
    ''' Delete cerificate identified with alias from keystore on keystore_path '''
    del_cmd = ("keytool -delete -keystore '{}' -storepass '{}' "
               "-alias '{}'").format(keystore_path, keystore_pass, alias)

    # Delete SSL certificate from keystore
    (del_rc, del_out, del_err) = module.run_command(del_cmd, check_rc=True)

    return module.exit_json(changed=True, msg=del_out,
                            rc=del_rc, cmd=del_cmd, stdout_lines=del_out,
                            error=del_err)

def test_keytool(module):
    ''' Test if keytool is actuall executable or not '''
    test_cmd = "keytool"

    module.run_command(test_cmd, check_rc=True)

def test_keystore(module, keystore_path):
    ''' Check if we can access keystore as file or not '''
    if keystore_path is None:
        keystore_path = ''

    if not os.path.exists(keystore_path) and not os.path.isfile(keystore_path):
        ## Keystore doesn't exist we want to create it
        return module.fail_json(changed=False,
                                msg="Module require existing keystore at keystore_path '{}'"
                                .format(keystore_path))

def main():
    argument_spec = dict(
        cert_url=dict(required=False, type='str'),
        cert_path=dict(required=False, type='str'),
        cert_alias=dict(required=False, type='str'),
        cert_port=dict(required=False, default='443'),
        keystore_path=dict(required=False, type='str'),
        keystore_pass=dict(required=False, default='changeit', type='str'),
        keystore_create=dict(required=False, default=False, type='bool'),
        state=dict(required=False, default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['cert_path', 'cert_url']],
        required_together=[['keystore_path', 'keystore_pass']],
        mutually_exclusive=[
            ['cert_url', 'cert_path']
        ],
    )

    url = module.params.get('cert_url')
    path = module.params.get('cert_path')
    port = module.params.get('cert_port')
    cert_alias = module.params.get('cert_alias') or url

    keystore_path = module.params.get('keystore_path')
    keystore_pass = module.params.get('keystore_pass')
    keystore_create = module.params.get('keystore_create')
    state = module.params.get('state')

    if path and not cert_alias:
        module.fail_json(changed=False,
                         msg="Using local path import from {} requires alias argument."
                         .format(keystore_path))

    test_keytool(module)

    if not keystore_create:
        test_keystore(module, keystore_path)

    if state == 'absent':
        if check_cert_present(module, keystore_path, keystore_pass, cert_alias):
            delete_cert(module, keystore_path, keystore_pass, cert_alias)
        else:
            module.exit_json(changed=False)

    if check_cert_present(module, keystore_path, keystore_pass, cert_alias):
        module.exit_json(changed=False)
    else:
        if path:
            import_cert_path(module, path, keystore_path, keystore_pass, cert_alias)

        if url:
            import_cert_url(module, url, port, keystore_path, keystore_pass, cert_alias)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == "__main__":
    main()
