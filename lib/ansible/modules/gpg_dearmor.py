#!/usr/bin/env python3
# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
from tarfile import GNUTYPE_LONGNAME
__metaclass__ = type
import os
from os.path import exists
import urllib.request
import gnupg

DOCUMENTATION = r'''
---
module: gpg_dearmor

short_description: Download ASCII armored GPG data and write to disk without armor

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This module is intended to complement the existing apt_key module and fill the gaps for distrbutions like Ubuntu Jammy

options:
    dir_path:
        description: Directory path to write the file to. Defaults to /usr/share/keyrings
        required: false
        type: str
    filename:
        description: The name of the file. This will be suffixed with -archive-keyring.gpg. e.g. "foo" becomes "foo-archive-keyring.gpg"
        required: true
        type: str
    state:
        description: If present the key is installed, if absent the file is removed. Defaults to present
        required: false
        type: str
    url:
        description:
        required: true
        type: str
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - ansible.builtin.gpg_dearmor

author:
    - Your Name (@yourGitHubHandle)

requires:
    - python3-gnupg
'''

EXAMPLES = r'''
# Install vscode key
- name: Test with a message
  ansible.builtin.gpg_dearmor:
    file_name: vscode
    url: https://packages.microsoft.com/keys/microsoft.asc

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    file_exists: Whether or not the specified key file already exists on the system
    type: bool
    returned: always
    sample: 'True'
message:
    description: A friendly message
    type: str
    returned: always
    sample: 'Added new keys'
key_path:
    description: The full file location where the keys were written
    type: str
    returned: always
    sample: '/usr/share/keyrings/foo-archive-keyring.gpg'
current_keys:
    description: Currently installed key fingerprints present in the specified file
    type: list
    returned: always
    sample: []
new_keys:
    description: Key fingerprints present at the specified URL
    type: list
    returned: always
    sample: []
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        dir_path=dict(type='str', default="/usr/share/keyrings"),
        file_name=dict(type='str', required=True),
        state=dict(type='str', default="present"),
        url=dict(type=str, required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    key_path = module.params['dir_path'] + '/' + module.params['file_name'] + "-archive-keyring.gpg"
    required_state = "present"
    if module.params['state'] == 'absent':
        required_state = "absent"
    elif module.params['state'] == 'present':
        pass
    else:
        module.fail_json(msg="Unrecognised state: " + module.params['state'], **result)
    gpg = gnupg.GPG()
    if exists(key_path):
        result['file_exists'] = True
        with open(key_path, "rb") as current_keyfile:
            current_key_result = gpg.import_keys(current_keyfile.read())
            result['current_keys'] = current_key_result.fingerprints
        if required_state == 'absent':
            os.remove(key_path)
            result['changed'] = True
    else:
        result['current_keys'] = []
    with urllib.request.urlopen(module.params['url']) as f:
        html = f.read().decode('utf-8')
        import_result = gpg.import_keys(html)
        result['new_keys'] = import_result.fingerprints
        key_data = gpg.export_keys(import_result.fingerprints[0], armor=False)
        if result['new_keys'] != result['current_keys'] and required_state == 'present':
            with open(key_path, "wb") as binary_keyfile:
                binary_keyfile.write(key_data)
            result['message'] = 'Added new keys'
            result['changed'] = True
        else:
            result['message'] = 'No keys added'
            result['changed'] = False
    result['key_path'] = key_path


    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

