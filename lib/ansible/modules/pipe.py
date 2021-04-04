#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, LoveIsGrief
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: pipe
version_added: devel
short_description: Pipe local command to a remote command
description:
    - The C(pipe) action executes a command locally and pipes the output thereof to a remote host.
options:
  local:
    description:
    - The command to execute on the local machine
    type: str
    required: yes
  remote:
    description:
    - The command to execute on the remote machine. 
    - Its input will be the stdoutput of the local command 
    type: str
    required: yes
extends_documentation_fragment:
- command
- execute
- local
notes:
- Your remote connection should probably support pipelining
seealso:
- ansible.modules.command
- ansible.modules.script
author:
- LoveIsGrief
'''

EXAMPLES = r'''
- name: Copy file with owner and permissions
  ansible.builtin.pipe:
    src: docker save {{ image }} 
    dest: docker load
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule

# The AnsibleModule object
module = None


def main():
    global module

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            src=dict(type='str', required=True),
            dest=dict(type='str', required=True),
        ),
        supports_check_mode=False,
    )
    module.fail_json(
        msg='Cannot be executed directly. All work is done in the pipe action',
    )


if __name__ == '__main__':
    main()
