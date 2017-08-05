#!/usr/bin/python
#
# (c) 2013, RSD Services S.A
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: java_cert
version_added: '2.3'
short_description: Uses keytool to import/remove key from java keystore(cacerts)
description:
  - This is a wrapper module around keytool. Which can be used to import/remove
    certificates from a given java keystore.
options:
  cert_url:
    description:
      - Basic URL to fetch SSL certificate from. One of cert_url or cert_path is required to load certificate.
  cert_port:
    description:
      - Port to connect to URL. This will be used to create server URL:PORT
    default: 443
  cert_path:
    description:
      - Local path to load certificate from. One of cert_url or cert_path is required to load certificate.
  cert_alias:
    description:
      - Imported certificate alias.
  keystore_path:
    description:
      - Path to keystore.
  keystore_pass:
    description:
      - Keystore password.
    required: true
  keystore_create:
    description:
      - Create keystore if it doesn't exist
  executable:
    description:
      - Path to keytool binary if not used we search in PATH for it.
    default: keytool
  state:
    description:
      - Defines action which can be either certificate import or removal.
    choices: [ 'present', 'absent' ]
    default: present

author: Adam Hamsik @haad
'''

EXAMPLES = '''
# Import SSL certificate from google.com to a given cacerts keystore
java_cert:
  cert_url: google.com
  cert_port: 443
  keystore_path: /usr/lib/jvm/jre7/lib/security/cacerts
  keystore_pass: changeit
  state: present

# Remove certificate with given alias from a keystore
java_cert:
  cert_url: google.com
  keystore_path: /usr/lib/jvm/jre7/lib/security/cacerts
  keystore_pass: changeit
  executable: /usr/lib/jvm/jre7/bin/keytool
  state: absent

# Import SSL certificate from google.com to a keystore,
# create it if it doesn't exist
java_cert:
  cert_url: google.com
  keystore_path: /tmp/cacerts
  keystore_pass: changeit
  keystore_create: yes
  state: present
'''

RETURN = '''
msg:
  description: Output from stdout of keytool command after execution of given command.
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

# import module snippets
from ansible.module_utils.basic import AnsibleModule

def check_cert_present(module, executable, keystore_path, keystore_pass, alias):
    ''' Check if certificate with alias is present in keystore
        located at keystore_path '''
    test_cmd = ("%s -noprompt -list -keystore '%s' -storepass '%s' "
                "-alias '%s'")%(executable, keystore_path, keystore_pass, alias)

    (check_rc, _, _) = module.run_command(test_cmd)
    if check_rc == 0:
        return True
    return False

def import_cert_url(module, executable, url, port, keystore_path, keystore_pass, alias):
    ''' Import certificate from URL into keystore located at keystore_path '''
    fetch_cmd = ("%s -printcert -rfc -sslserver %s:%d")%(executable, url, port)
    import_cmd = ("%s -importcert -noprompt -keystore '%s' "
                  "-storepass '%s' -alias '%s'")%(executable, keystore_path,
                                                  keystore_pass, alias)

    if module.check_mode:
        module.exit_json(changed=True)

    # Fetch SSL certificate from remote host.
    (_, fetch_out, _) = module.run_command(fetch_cmd, check_rc=True)

    # Use remote certificate from remote host and import it to a java keystore
    (import_rc, import_out, import_err) = module.run_command(import_cmd,
                                                             data=fetch_out,
                                                             check_rc=False)
    diff = {'before': '\n', 'after': '%s\n'%alias}
    if import_rc == 0:
        return module.exit_json(changed=True, msg=import_out,
                                rc=import_rc, cmd=import_cmd, stdout=import_out,
                                diff=diff)
    else:
        return module.fail_json(msg=import_out, rc=import_rc, cmd=import_cmd,
                                error=import_err)

def import_cert_path(module, executable, path, keystore_path, keystore_pass, alias):
    ''' Import certificate from path into keystore located on
        keystore_path as alias '''
    import_cmd = ("%s -importcert -noprompt -keystore '%s' "
                  "-storepass '%s' -file '%s' -alias '%s'")%(executable,
                                                             keystore_path,
                                                             keystore_pass,
                                                             path, alias)

    if module.check_mode:
        module.exit_json(changed=True)

    # Use local certificate from local path and import it to a java keystore
    (import_rc, import_out, import_err) = module.run_command(import_cmd,
                                                             check_rc=False)

    diff = {'before': '\n', 'after': '%s\n'%alias}
    if import_rc == 0:
        return module.exit_json(changed=True, msg=import_out,
                                rc=import_rc, cmd=import_cmd, stdout=import_out,
                                error=import_err, diff=diff)
    else:
        return module.fail_json(msg=import_out, rc=import_rc, cmd=import_cmd)

def delete_cert(module, executable, keystore_path, keystore_pass, alias):
    ''' Delete certificate identified with alias from keystore on keystore_path '''
    del_cmd = ("%s -delete -keystore '%s' -storepass '%s' "
               "-alias '%s'")%(executable, keystore_path, keystore_pass, alias)

    if module.check_mode:
        module.exit_json(changed=True)

    # Delete SSL certificate from keystore
    (del_rc, del_out, del_err) = module.run_command(del_cmd, check_rc=True)

    diff = {'before': '%s\n'%alias, 'after': None}

    return module.exit_json(changed=True, msg=del_out,
                            rc=del_rc, cmd=del_cmd, stdout=del_out,
                            error=del_err, diff=diff)

def test_keytool(module, executable):
    ''' Test if keytool is actuall executable or not '''
    test_cmd = "%s"%(executable)

    module.run_command(test_cmd, check_rc=True)

def test_keystore(module, keystore_path):
    ''' Check if we can access keystore as file or not '''
    if keystore_path is None:
        keystore_path = ''

    if not os.path.exists(keystore_path) and not os.path.isfile(keystore_path):
        ## Keystore doesn't exist we want to create it
        return module.fail_json(changed=False,
                                msg="Module require existing keystore at keystore_path '%s'"
                                %(keystore_path))

def main():
    argument_spec = dict(
        cert_url=dict(type='str'),
        cert_path=dict(type='str'),
        cert_alias=dict(type='str'),
        cert_port=dict(default='443', type='int'),
        keystore_path=dict(type='str'),
        keystore_pass=dict(required=True, type='str', no_log=True),
        keystore_create=dict(default=False, type='bool'),
        executable=dict(default='keytool', type='str'),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['cert_path', 'cert_url']],
        required_together=[['keystore_path', 'keystore_pass']],
        mutually_exclusive=[
            ['cert_url', 'cert_path']
        ],
        supports_check_mode=True,
    )

    url = module.params.get('cert_url')
    path = module.params.get('cert_path')
    port = module.params.get('cert_port')
    cert_alias = module.params.get('cert_alias') or url

    keystore_path = module.params.get('keystore_path')
    keystore_pass = module.params.get('keystore_pass')
    keystore_create = module.params.get('keystore_create')
    executable = module.params.get('executable')
    state = module.params.get('state')

    if path and not cert_alias:
        module.fail_json(changed=False,
                         msg="Using local path import from %s requires alias argument."
                         %(keystore_path))

    test_keytool(module, executable)

    if not keystore_create:
        test_keystore(module, keystore_path)

    cert_present = check_cert_present(module, executable, keystore_path,
                                      keystore_pass, cert_alias)

    if state == 'absent':
        if cert_present:
            delete_cert(module, executable, keystore_path, keystore_pass, cert_alias)

    elif state == 'present':
        if not cert_present:
            if path:
                import_cert_path(module, executable, path, keystore_path,
                                 keystore_pass, cert_alias)

            if url:
                import_cert_url(module, executable, url, port, keystore_path,
                                keystore_pass, cert_alias)

    module.exit_json(changed=False)

if __name__ == "__main__":
    main()
