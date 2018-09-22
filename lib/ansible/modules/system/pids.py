#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: pids
version_added: 2.8
description: "Retrieves a list of process IDs (PIDs) of all processes of the given name. Returns an empty list if no process of the given name exists."
short_description: "Retrieves process IDs list if the process is running otherwise return empty list"
author:
  - Saranya Sridharan (@saranyasridharan)
requirements:
  - Needs 'pidof' to be installed in the system
options:
  name:
    description: the name of the process you want to get PID for
    required: true
'''
EXAMPLES = '''
# Pass the process name
- name: Getting process IDs of the process
  pids:
      name: python
  register: pids_of_python

- name: Printing the process IDs obtained
  debug:
    msg: "PIDS of python:{{pids_of_python.pids|join(',')}}"
'''

RETURN = '''
pids:
  description: Process IDs of the given process
  returned: list of none, one, or more process IDs
  type: list
'''

from ansible.module_utils.basic import AnsibleModule


def get_pid(name, module):
    command = module.get_bin_path('pidof', True)
    rc, processid, stderr = module.run_command([command, name])
    return [int(pid) for pid in processid.split() if processid]


def main():
    module = AnsibleModule(
        argument_spec={
            "name": {"required": True, "type": "str"}
        }
    )
    name = module.params["name"]
    response = dict(pids=get_pid(name, module))
    module.exit_json(**response)


if __name__ == '__main__':
    main()
