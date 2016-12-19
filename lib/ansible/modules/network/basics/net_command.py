#!/usr/bin/python
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
#

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'core',
    'version': '1.0'
}

DOCUMENTATION = """
---
module: net_command
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Executes a common on a remote network device
description:
  - This module will take the command and execute it on the remote
    device in a CLI shell.  The command will outout will be returned
    via the stdout return key.  If an error is detected, the command
    will return the error via the stderr key.
options:
  free_form:
    description:
      - A free form command to run on the remote host.  There is no
        parameter actually named 'free_form'.  See the examples .
    required: true
notes:
  - This module requires setting the Ansible connection type to network_cli
  - This module will always set the changed return key to C(True)
"""

EXAMPLES = """
- name: execute show version
  net_command: show version

- name: run a series of commmands
  net_command: "{{ item }}"
  with_items:
    - show interfaces
    - show ip route
    - show version
"""

RETURN = """
rc:
  description: The command return code (0 means success)
  returned: always
  type: int
  sample: 0
stdout:
  description: The command standard output
  returned: always
  type: string
  sample: "Hostname: ios01\nFQDN:     ios01.example.net"
stderr:
  description: The command standard error
  returned: always
  type: string
  sample: "shw hostname\r\n% Invalid input\r\nios01>"
stdout_lines:
  description: The command standard output split in lines
  returned: always
  type: list
  sample: ["Hostname: ios01", "FQDN:     ios01.example.net"]
start:
  description: The time the job started
  returned: always
  type: str
  sample: "2016-11-16 10:38:15.126146"
end:
  description: The time the job ended
  returned: always
  type: str
  sample: "2016-11-16 10:38:25.595612"
delta:
  description: The time elapsed to perform all operations
  returned: always
  type: str
  sample: "0:00:10.469466"
"""
from ansible.module_utils.local import LocalAnsibleModule

def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        _raw_params=dict()
    )

    module = LocalAnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=False)

    if str(module.params['_raw_params']).strip() == '':
        module.fail_json(rc=256, msg='no command given')

    result = {'changed': True}

    rc, out, err = module.exec_command(module.params['_raw_params'])

    try:
        out = module.from_json(out)
    except ValueError:
        if out:
            out = str(out).strip()
            result['stdout_lines'] = out.split('\n')

    result.update({
        'rc': rc,
        'stdout': out,
        'stderr': str(err).strip()
    })

    module.exit_json(**result)

if __name__ == '__main__':
    main()
