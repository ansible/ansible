#!/usr/bin/python
""" PN CLI show commands """

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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_show
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: Run show commands on nvOS device.
deprecated:
  removed_in: '2.12'
  why: Doesn't support latest Pluribus Networks netvisor
  alternative: Latest modules will be pushed in Ansible future versions.
description:
  - Execute show command in the nodes and returns the results
    read from the device.
options:
  pn_cliusername:
    description:
      - Provide login username if user is not root.
    required: False
  pn_clipassword:
    description:
      - Provide login password if user is not root.
    required: False
  pn_cliswitch:
    description:
      - Target switch(es) to run the cli on.
    required: False
  pn_command:
    description:
      - The C(pn_command) takes a CLI show command as value.
    required: true
  pn_parameters:
    description:
      - Display output using a specific parameter. Use 'all' to display
        possible output. List of comma separated parameters.
    default: 'all'
  pn_options:
    description:
      - Specify formatting options.
"""

EXAMPLES = """
- name: run the vlan-show command
  pn_show:
    pn_command: 'vlan-show'
    pn_parameters: id,scope,ports
    pn_options: 'layout vertical'

- name: run the vlag-show command
  pn_show:
    pn_command: 'vlag-show'
    pn_parameters: 'id,name,cluster,mode'
    pn_options: 'no-show-headers'

- name: run the cluster-show command
  pn_show:
    pn_command: 'cluster-show'
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the show command.
  returned: always
  type: list
stderr:
  description: The set of error responses from the show command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused any change on the target.
  returned: always(False)
  type: bool
"""

import shlex

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch
    :return: returns the cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    if cliswitch:
        if cliswitch == 'local':
            cli += ' switch-local '
        else:
            cli += ' switch ' + cliswitch
    return cli


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    cmd = shlex.split(cli)

    # 'out' contains the output
    # 'err' contains the error messages
    result, out, err = module.run_command(cmd)

    print_cli = cli.split(cliswitch)[1]

    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=print_cli,
            msg='%s: ' % command,
            stderr=err.strip(),
            changed=False
        )

    if out:
        module.exit_json(
            command=print_cli,
            msg='%s: ' % command,
            stdout=out.strip(),
            changed=False
        )

    else:
        module.exit_json(
            command=cli,
            msg='%s: Nothing to display!!!' % command,
            changed=False
        )


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str'),
            pn_command=dict(required=True, type='str'),
            pn_parameters=dict(default='all', type='str'),
            pn_options=dict(type='str')
        )
    )

    # Accessing the arguments
    command = module.params['pn_command']
    parameters = module.params['pn_parameters']
    options = module.params['pn_options']

    # Building the CLI command string
    cli = pn_cli(module)

    cli += ' %s format %s ' % (command, parameters)

    if options:
        cli += options

    run_cli(module, cli)


if __name__ == '__main__':
    main()
