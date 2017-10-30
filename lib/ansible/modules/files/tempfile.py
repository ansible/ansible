#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Krzysztof Magosa <krzysztof@magosa.pl>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tempfile
version_added: "2.3"
author:
  - Krzysztof Magosa
short_description: Creates temporary files and directories.
description:
  - The C(tempfile) module creates temporary files and directories. C(mktemp) command takes different parameters on various systems, this module helps
    to avoid troubles related to that. Files/directories created by module are accessible only by creator. In case you need to make them world-accessible
    you need to use M(file) module.
  - For Windows targets, use the M(win_tempfile) module instead.
options:
  state:
    description:
      - Whether to create file or directory.
    choices: [ directory, file ]
    default: file
  path:
    description:
      - Location where temporary file or directory should be created. If path is not specified default system temporary directory will be used.
  prefix:
    description:
      - Prefix of file/directory name created by module.
    default: ansible.
  suffix:
    description:
      - Suffix of file/directory name created by module.
    default: ""
notes:
  - For Windows targets, use the M(win_tempfile) module instead.
'''

EXAMPLES = """
- name: create temporary build directory
  tempfile:
    state: directory
    suffix: build

- name: create temporary file
  tempfile:
    state: file
    suffix: temp
"""

RETURN = '''
path:
  description: Path to created file or directory
  returned: success
  type: string
  sample: "/tmp/ansible.bMlvdk"
'''

from os import close
from tempfile import mkstemp, mkdtemp
from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='file', choices=['file', 'directory']),
            path=dict(type='path'),
            prefix=dict(type='str', default='ansible.'),
            suffix=dict(type='str', default=''),
        ),
    )

    try:
        if module.params['state'] == 'file':
            handle, path = mkstemp(
                prefix=module.params['prefix'],
                suffix=module.params['suffix'],
                dir=module.params['path'],
            )
            close(handle)
        elif module.params['state'] == 'directory':
            path = mkdtemp(
                prefix=module.params['prefix'],
                suffix=module.params['suffix'],
                dir=module.params['path'],
            )

        module.exit_json(changed=True, path=path)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
