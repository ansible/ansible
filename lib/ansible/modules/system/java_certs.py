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

# keytool -printcert -rfc -sslserver ppid.rsd-cloud.com:443 | keytool -importcert -keystore /usr/lib/jvm/java-7-oracle-amd64/jre/lib/security/cacerts -storepass changeit -alias ppid.rsd-cloud.com

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
    default: 'present'
    required: false

author: Adam Hamsik
'''

EXAMPLES = '''
# Import SSL certificate from google.com to a given cacerts keystore
java_certs: cert_url=google.com cert_port=443 keystore_path=/usr/lib/jvm/jre7/lib/security/cacerts keystore_pass=changeit state=present

# Remove certificate with given alias from a keystore
java_certs: cert_url=google.com keystore_path=/usr/lib/jvm/jre7/lib/security/cacerts keystore_pass=changeit state=absent

# Import SSL certificate from google.com to a keystore, create it if it doesn't exist
java_certs: cert_url=google.com keystore_path=/tmp/cacerts keystore_pass=changeit keystore_create=yes state=present
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

try:
    import json
except ImportError:
    import simplejson as json

import os
import subprocess
import sys
import datetime
import syslog

def check_cert_present(module, keystore_path, keystore_pass, alias):
    test_cmd = "keytool -noprompt -list -keystore '%s' -storepass '%s' -alias '%s'" % (keystore_path, keystore_pass, alias)

    (rc, out, err) = module.run_command(test_cmd)
    if rc == 0:
        return True
    return False

def import_cert_url(module, url, port, keystore_path, keystore_pass, alias):
    fetch_cmd = "keytool -printcert -rfc -sslserver %s:%s" % (url, port)
    import_cmd = "keytool -importcert -noprompt -keystore '%s' -storepass '%s' -alias '%s'" % (keystore_path, keystore_pass, alias)

    # Fetch SSL certificate from remote host.
    (rc, fetch_out, fetch_err) = module.run_command(fetch_cmd, check_rc=True)

    # Use remote certificate from remote host and import it to a java keystore
    (rc, import_out, import_err) = module.run_command(import_cmd, data=fetch_out, check_rc=False)
    if rc == 0:
        return module.exit_json(changed=True, msg=import_out,
            rc=rc, cmd=import_cmd, stdout_lines=import_out)
    else:
        return module.fail_json(msg=import_out, rc=rc, cmd=import_cmd)


def import_cert_path(module, path, keystore_path, keystore_pass):
    import_cmd = "keytool -importcert -noprompt -keystore '%s' -storepass '%s' -file '%s'" % (keystore_path, keystore_pass, path)

    # Use local certificate from local path and import it to a java keystore
    (rc, import_out, import_err) = module.run_command(import_cmd, check_rc=False)
    if rc == 0:
        return module.exit_json(changed=True, msg=import_out,
            rc=rc, cmd=import_cmd, stdout_lines=import_out)
    else:
        return module.fail_json(msg=import_out, rc=rc, cmd=import_cmd)


def delete_cert(module, keystore_path, keystore_pass, alias):
    del_cmd = "keytool -delete -keystore '%s' -storepass '%s' -alias '%s'" % (keystore_path, keystore_pass, alias)

    # Delete SSL certificate from keystore
    (rc, del_out, del_err) = module.run_command(del_cmd, check_rc=True)

    return module.exit_json(changed=True, msg=del_out,
        rc=rc, cmd=del_cmd, stdout_lines=del_out)

def test_keytool(module):
    ''' Test if keytool is actuall executable or not '''
    test_cmd = "keytool"

    (rc, del_out, del_err) = module.run_command(test_cmd, check_rc=True)

def test_keystore(module, keystore_path):
    ''' Check if we can access keystore as file or not '''
    if keystore_path is None:
        keystore_path=''

    if not os.path.exists(keystore_path) and not os.path.isfile(keystore_path):
        ## Keystore doesn't exist we want to create it
        return module.fail_json(changed=False, msg="Module require existing keystore at keystore_path '%s'" % keystore_path)

def main():
    argument_spec = dict(
            cert_url = dict(required=False),
            cert_path = dict(required=False),
            cert_alias = dict(required=False),
            cert_port = dict(required=False, default='443'),
            keystore_path = dict(required=False),
            keystore_pass = dict(required=False, default='changeit'),
            keystore_create = dict(required=False, default=False, type='bool'),
            state = dict(required=False, default='present', choices=['present', 'absent'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive = [
                                ['cert_url', 'cert_path']
                             ],
    )

    filter = {}
    url = module.params.get('cert_url')
    path = module.params.get('cert_path')
    port = module.params.get('cert_port')
    cert_alias = module.params.get('cert_alias') or url

    keystore_path = module.params.get('keystore_path')
    keystore_pass = module.params.get('keystore_pass')
    keystore_create = module.params.get('keystore_create')
    state = module.params.get('state')

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
            import_cert_path(module, path, keystore_path, keystore_pass)

        if url:
            import_cert_url(module, url, port, keystore_path, keystore_pass, cert_alias)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == "__main__":
    main()
