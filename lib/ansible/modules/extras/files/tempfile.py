#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2016 Krzysztof Magosa <krzysztof@magosa.pl>
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
module: tempfile
version_added: "2.3"
author:
  - Krzysztof Magosa
short_description: Creates temporary files and directories.
description:
  - The M(tempfile) module creates temporary files and directories. C(mktemp) command takes different parameters on various systems, this module helps to avoid troubles related to that. Files/directories created by module are accessible only by creator. In case you need to make them world-accessible you need to use M(file) module.
options:
  state:
    description:
      - Whether to create file or directory.
    required: false
    choices: [ "file", "directory" ]
    default: file
  path:
    description:
      - Location where temporary file or directory should be created. If path is not specified default system temporary directory will be used.
    required: false
    default: null
  prefix:
    description:
      - Prefix of file/directory name created by module.
    required: false
    default: ansible.
  suffix:
    description:
      - Suffix of file/directory name created by module.
    required: false
    default: ""
'''

EXAMPLES = """
  - name: create temporary build directory
    tempfile: state=directory suffix=build

  - name: create temporary file
    tempfile: state=file suffix=temp
"""

RETURN = '''
path:
  description: Path to created file or directory
  returned: success
  type: string
  sample: "/tmp/ansible.bMlvdk"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from tempfile import mkstemp, mkdtemp
from os import close

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='file', choices=['file', 'directory']),
            path      = dict(default=None),
            prefix    = dict(default='ansible.'),
            suffix    = dict(default='')
        )
    )

    try:
        if module.params['state'] == 'file':
            handle, path = mkstemp(
                prefix=module.params['prefix'],
                suffix=module.params['suffix'],
                dir=module.params['path']
            )
            close(handle)
        elif module.params['state'] == 'directory':
            path = mkdtemp(
                prefix=module.params['prefix'],
                suffix=module.params['suffix'],
                dir=module.params['path']
            )

        module.exit_json(changed=True, path=path)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
