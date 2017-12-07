#!/usr/bin/python
""" PN CLI cluster-create/cluster-delete """

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
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_cluster
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: CLI command to create/delete a cluster.
description:
  - Execute cluster-create or cluster-delete command.
  - A cluster allows two switches to cooperate in high-availability (HA)
    deployments. The nodes that form the cluster must be members of the same
    fabric. Clusters are typically used in conjunction with a virtual link
    aggregation group (VLAG) that allows links physically connected to two
    separate switches appear as a single trunk to a third device. The third
    device can be a switch,server, or any Ethernet device.
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
      - Target switch to run the cli on.
    required: False
  state:
    description:
      - Specify action to perform. Use 'present' to create cluster and 'absent'
        to delete cluster.
    required: true
    choices: ['present', 'absent']
  pn_name:
    description:
      - Specify the name of the cluster.
    required: true
  pn_cluster_node1:
    description:
      - Specify the name of the first switch in the cluster.
      - Required for 'cluster-create'.
  pn_cluster_node2:
    description:
      - Specify the name of the second switch in the cluster.
      - Required for 'cluster-create'.
  pn_validate:
    description:
      - Validate the inter-switch links and state of switches in the cluster.
    choices: ['validate', 'no-validate']
"""

EXAMPLES = """
- name: create spine cluster
  pn_cluster:
    state: 'present'
    pn_name: 'spine-cluster'
    pn_cluster_node1: 'spine01'
    pn_cluster_node2: 'spine02'
    pn_validate: validate
    pn_quiet: True

- name: delete spine cluster
  pn_cluster:
    state: 'absent'
    pn_name: 'spine-cluster'
    pn_quiet: True
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the cluster command.
  returned: always
  type: list
stderr:
  description: The set of error responses from the cluster command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex

NAME_EXISTS = None
NODE1_EXISTS = None
NODE2_EXISTS = None


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

    if cliswitch == 'local':
        cli += ' switch-local '
    else:
        cli += ' switch ' + cliswitch
    return cli


def check_cli(module, cli):
    """
    This method checks for idempotency using the cluster-show command.
    If a cluster with given name exists, return NAME_EXISTS as True else False.
    If the given cluster-node-1 is already a part of another cluster, return
    NODE1_EXISTS as True else False.
    If the given cluster-node-2 is already a part of another cluster, return
    NODE2_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: NAME_EXISTS, NODE1_EXISTS, NODE2_EXISTS
    """
    name = module.params['pn_name']
    node1 = module.params['pn_cluster_node1']
    node2 = module.params['pn_cluster_node2']

    show = cli + ' cluster-show  format name,cluster-node-1,cluster-node-2 '
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()
    # Global flags
    global NAME_EXISTS, NODE1_EXISTS, NODE2_EXISTS

    if name in out:
        NAME_EXISTS = True
    else:
        NAME_EXISTS = False
    if node1 in out:
        NODE1_EXISTS = True
    else:
        NODE2_EXISTS = False
    if node2 in out:
        NODE2_EXISTS = True
    else:
        NODE2_EXISTS = False


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    command = get_command_from_state(state)

    cmd = shlex.split(cli)

    # 'out' contains the output
    # 'err' contains the error messages
    result, out, err = module.run_command(cmd)

    print_cli = cli.split(cliswitch)[1]

    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=print_cli,
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=print_cli,
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=print_cli,
            msg="%s operation completed" % command,
            changed=True
        )


def get_command_from_state(state):
    """
    This method gets appropriate command name for the state specified. It
    returns the command name for the specified state.
    :param state: The state for which the respective command name is required.
    """
    command = None
    if state == 'present':
        command = 'cluster-create'
    if state == 'absent':
        command = 'cluster-delete'
    return command


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            pn_name=dict(required=True, type='str'),
            pn_cluster_node1=dict(type='str'),
            pn_cluster_node2=dict(type='str'),
            pn_validate=dict(type='bool')
        ),
        required_if=(
            ["state", "present",
             ["pn_name", "pn_cluster_node1", "pn_cluster_node2"]],
            ["state", "absent", ["pn_name"]]
        )
    )

    # Accessing the parameters
    state = module.params['state']
    name = module.params['pn_name']
    cluster_node1 = module.params['pn_cluster_node1']
    cluster_node2 = module.params['pn_cluster_node2']
    validate = module.params['pn_validate']

    command = get_command_from_state(state)

    # Building the CLI command string
    cli = pn_cli(module)

    if command == 'cluster-create':

        check_cli(module, cli)

        if NAME_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Cluster with name %s already exists' % name
            )
        if NODE1_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Node %s already part of a cluster' % cluster_node1
            )
        if NODE2_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Node %s already part of a cluster' % cluster_node2
            )

        cli += ' %s name %s ' % (command, name)
        cli += 'cluster-node-1 %s cluster-node-2 %s ' % (cluster_node1,
                                                         cluster_node2)
        if validate is True:
            cli += ' validate '
        if validate is False:
            cli += ' no-validate '

    if command == 'cluster-delete':

        check_cli(module, cli)

        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='Cluster with name %s does not exist' % name
            )
        cli += ' %s name %s ' % (command, name)

    run_cli(module, cli)

# AnsibleModule boilerplate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
