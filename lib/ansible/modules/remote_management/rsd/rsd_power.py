#!/usr/bin/python

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Radoslaw Kuschel - <radoslaw.kuschel@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: rsd_power

short_description: Change power state of RSD Composed Nodes

version_added: "2.10"

description:
    - Change the power state of composed node.
    - The module supports the 'on', 'off' and 'restarted' power states, which
      are equivalent to 'on', 'graceful shutdown', 'graceful restart'.
    - The module also support force flag which is equivalent to
      'force on', 'force off', 'force restart'.
    - "The node on which power action will be performed can by identified by
      one of the following: uuid, identity, or name."

options:
    state:
        description:
            - Desired power action to be performed on the node.
        required: true
        type: str
        choices: ['on', 'off', 'restarted']
    force:
        description:
            - Force power action on the node
        required: false
        type: bool
        default: false

extends_documentation_fragment:
    - rsd

author:
    - Radoslaw Kuschel (@radoslawKuschel)
'''
EXAMPLES = '''
---
- name: Restart Node by specifying node id.
  rsd_power:
    id:
      value: 1
    state: restarted

- name: Shutdown node by specifying node uuid.
  rsd_power:
    id:
      value: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
      type: uuid
    state: off

- name: Force shutdown of Node by specifying node name.
  rsd_power:
    id:
      value: test_node
      type: name
    state: off
    force: true

'''

RETURN = '''
node:
    description: Information regarding the node
    returned: On success
    type: complex
    contains:
        id:
            description: Node ID.
        name:
            description: Node name.
        uuid:
            description: Node uuid.
        requested_power_action:
            description: Power action specified by user.
        previous_power_state:
            description: Previous power state of the node.
        supported_power_action:
            description: Supported power actions of the node.

    sample:
        "id": "1"
        "name": "node_test"
        "previous_power_state": "on"
        "requested_power_action": "force restart"
        "supported_power_action": [
            "graceful restart",
            "on",
            "force off",
            "graceful shutdown",
            "force restart"
        ]
        "uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
'''

from ansible.module_utils.remote_management.rsd.rsd_common import RSD
try:
    import sushy
except ImportError:
    pass


class RsdNodePower(RSD):

    def __init__(self):
        argument_spec = dict(
            state=dict(
                type='str',
                required=True,
                choices=['on', 'off', 'restarted']
            ),
            force=dict(
                type='bool',
                required=False,
                default=False
            )
        )

        super(RsdNodePower, self).__init__(argument_spec, False)

    def _convert_power_param(self):
        params = self.module.params
        mappings = {
            'on': ('On', 'ForceOn'),
            'off': ('GracefulShutdown', 'ForceOff'),
            'restarted': ('GracefulRestart', 'ForceRestart')
        }

        if params['force']:
            power_state = mappings[params['state']][1]
        else:
            power_state = mappings[params['state']][0]

        return power_state

    def _check_state_is_allowed(self, node, requested_state):
        compute_reset_values = node.get_allowed_reset_node_values()

        if requested_state not in compute_reset_values:
            self.module.fail_json(
                msg="This node does not support such power action: "
                    "'{0}'. The node supports following power actions: "
                    "{1}".format(requested_state, compute_reset_values))

    def _reset_node(self, node, power_state):
        try:
            node.reset_node(power_state)
            return self._return_power_result(node, True, power_state)
        except sushy.exceptions.ServerSideError:
            same_as = {
                'On': ('On', 'ForceOn'),
                'Off': ('GracefulShutdown', 'ForceOff')
            }

            node.refresh()
            current_state = node.power_state

            if power_state in same_as[current_state]:
                return self._return_power_result(node, False, power_state)
            else:
                self.module.fail_json(msg="Reset action failed. The required "
                                      "transition might not be supported")

    def _return_power_result(self, node, changed, requested_state):
        result = dict()
        result["id"] = node.identity
        result["name"] = node.name
        result["uuid"] = node.uuid
        result["requested_power_action"] = requested_state
        result["previous_power_state"] = node.power_state
        result["supported_power_action"] = node.get_allowed_reset_node_values()
        self.module.exit_json(changed=changed, node=result)

    def run(self):
        node = self._get_node()
        requested_state = self._convert_power_param()
        self._check_state_is_allowed(node, requested_state)
        self._reset_node(node, requested_state)


def main():
    power = RsdNodePower()
    power.run()


if __name__ == '__main__':
    main()
