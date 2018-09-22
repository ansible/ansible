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
description: "Gives either one or more pids/process ids  of the given process name or simply empty list if the process does not exist"
short_description: "Gives either one or more pids/process ids  of the given process name or simply empty list if the process does not exist"
author:
  - Saranya Sridharan
requirements:
  - Needs 'pidof' to be installed in the system
options:
  name:
    description: the name of the process you want to get pid for
    required: true
'''
EXAMPLES = '''
# Pass the process name
- name: Getting pids/process ids of the process
  pids:
      name: python
      register: pids_of_python
  
- name: Getting the pids/process ids obtained
- debug: msg = "PIDS of python: {{ ','.join(pids_of_python.pid) }}"
'''

RETURN = '''
pids:
  description: It return process ids/pids of the given process
  returned: list of process ids/pids
  type: list
'''

import subprocess
from ansible.module_utils.basic import AnsibleModule


def get_pid(name):
    processid = subprocess.check_output(["pidof", name])
    processid = processid.strip("\n")
    return map(int, processid.split(" "))


def main():
    module = AnsibleModule(argument_spec={"name": {"required": True, "type": "str"}})
    name = module.params["name"]
    response = dict(pid=get_pid(name))
    module.exit_json(**response)


if __name__ == '__main__':
    main()
