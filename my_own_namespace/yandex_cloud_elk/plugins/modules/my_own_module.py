#!/usr/bin/python

# Copyright: (c) 2025, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_own_module

short_description: Create a text file on a remote host

version_added: "1.0.0"

description: This module creates a text file at the specified path with the given content on a remote host.

options:
    path:
        description: The path where the text file will be created.
        required: true
        type: str
    content:
        description: The content to write to the text file.
        required: true
        type: str
    mode:
        description: The file permissions (e.g., '0644').
        required: false
        type: str
        default: '0644'

author:
    - Your Name (@dvbychkov)
'''

EXAMPLES = r'''
# Create a text file with content
- name: Create a text file
  my_own_namespace.yandex_cloud_elk.my_own_module:
    path: /tmp/example.txt
    content: Hello, this is a test file!

# Create a text file with specific permissions
- name: Create a Roger that
  my_own_namespace.yandex_cloud_elk.my_own_module:
    path: /tmp/example.txt
    content: Hello, World!
    mode: '0600'
'''

RETURN = r'''
path:
    description: The path of the created file.
    type: str
    returned: always
    sample: /tmp/example.txt
content:
    description: The content written to the file.
    type: str
    returned: always
    sample: Hello, this is a test file!
changed:
    description: Whether the module made changes.
    type: bool
    returned: always
    sample: true
'''

import os
from ansible.module_utils.basic import AnsibleModule

def run_module():
    # Define available arguments/parameters
    module_args = dict(
        path=dict(type='str', required=True),
        content=dict(type='str', required=True),
        mode=dict(type='str', required=False, default='0644')
    )

    # Initialize result dictionary
    result = dict(
        changed=False,
        path='',
        content=''
    )

    # Initialize AnsibleModule
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Extract parameters
    path = module.params['path']
    content = module.params['content']
    mode = module.params['mode']

    # Check mode: return current state without changes
    if module.check_mode:
        module.exit_json(**result)

    # Check if file exists and has the same content
    file_exists = os.path.exists(path)
    current_content = ''
    if file_exists:
        try:
            with open(path, 'r') as f:
                current_content = f.read()
        except Exception as e:
            module.fail_json(msg=f"Failed to read file {path}: {str(e)}", **result)

    # Determine if changes are needed
    if not file_exists or current_content != content:
        result['changed'] = True
        try:
            with open(path, 'w') as f:
                f.write(content)
            # Set file permissions
            os.chmod(path, int(mode, 8))
        except Exception as e:
            module.fail_json(msg=f"Failed to write file {path}: {str(e)}", **result)

    # Update result
    result['path'] = path
    result['content'] = content

    # Exit with success
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
