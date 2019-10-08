#!/usr/bin/python

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Marco Chiappero - <marco.chiappero@intel.com>
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
module: rsd_compose

short_description: Manages the life cycle of Rack Scale Design composed
                   resources

description:
    - Allocate/Assemble/Destroy Rack Scale Design Composed Nodes.
    - Non-absent nodes may be called "composed" within this source file, i.e.,
      nodes that are either allocated or assembled but the distinction
      wouldn't matter under the context.

version_added: "2.10"

author:
    - Marco Chiappero (@intmc)

options:
    id:
      description:
          - Specify the node to act on by specifying 'type' for type of
            identification key and 'value' for its value.
      required: false
      suboptions:
          type:
              type: str
              description:
                  - Specify type of identification. For best performance
                    it is suggested to use identity as type.
              required: false
              default: identity
              choices: [identity, uuid, name]
          value:
              type: str
              description:
                  - Identification signature.
              required: true
    spec:
        description:
            - Enumerate the desired resources for allocating or assembling a
              node. It's incompatible with I(id) and I(specfile). Each
              sub-option can express PODM API compliant specifications in
              either JSON or YAML format. Refer to the PODM API specification
              for a complete list of available options.
        required: false
        type: dict
        suboptions:
            name:
                type: str
                description:
                    - Name for the composed node
            description:
                type: str
                description:
                    - Description of the composed node
            processors:
                type: json
                description:
                    - List of processors and related requirements
            memory:
                type: json
                description:
                    - List of memory modules and related requirements
            local_drives:
                type: json
                description:
                    - A list of local drives and related requirements
            remote_drives:
                type: json
                description:
                    - A list of remote drives and related requirements
            eth_ifaces:
                type: json
                description:
                    - A list of ethernet interfaces and related requirements
            security:
                type: dict
                description:
                    - Security specifications
            total_cores:
                type: int
                description:
                    - Total core count for the whole composed node
            total_mem:
                type: int
                description:
                    - Total memory amount for the whole composed node

    specfile:
        description:
            - Execute this task even if it requires deleting a Composed Node
            - This option is mutually exclusive with I(spec) and I(id)
        type: path
        aliases:
        - 'file'

    state:
        description:
            - Assert the desired state for the composed node, whether such node
              is described by I(spec), I(specfile) or I(id). I(state=allocated)
              will try to allocate a node as described in I(spec) or
              I(specfile). I(state=assembled) will try to first allocate and
              then assemble a node as described in I(spec) or I(specfile), or
              assemble a pre-allocated node referenced by I(id). An existing
              allocated or assembled node specified by I(id) can be decomposed
              and its resources released by requesting I(state=absent).
        choices: [allocated, assembled, absent]
        default: assembled
        required: false
        type: str

extends_documentation_fragment:
    - rsd

requirements:
    - enum34 or Python >= 3.4

notes:
    - Due to the nature of the PODM API, check mode cannot be supported
    - For the same reason the module is not idempotent at the moment, since any
      result depends on decisions actually made by PODM
    - While modules should not require that a user know all the underlying
      options of an API/tool to be used, PODM API contains multiple nested
      levels that would be difficult to capture anyway. Moreover the API is
      still under heavy development and the use of a 'catch-all' spec/specfile
      option, promotes forward compatibility while delegating up-to-date value
      checking to rsd-lib.
'''

EXAMPLES = '''
---
- name: Allocate a node with the provided specs
  rsd_compose:
    spec:
      processors:
      - ProcessorType: CPU
        AchievableSpeedMHz: 3000
      - ProcessorType: FPGA
        Connectivity: RemotePCIe
      local_drives:
      - Type: SSD
      remote_drives:
      - CapacityGiB: 60
        Protocol: iSCSI
      - CapacityGiB: 80
        Protcol: NVMeOverFabrics
    state: allocated
  register: result

- name: Assemble the allocated node
  rsd_compose:
    id:
      value: result.node.Id
    state: assembled

- name: Delete the previously assembled
  rsd_compose:
    id:
      value: result.node.Id
    state: absent

- name: Assemble a node from spec file
  rsd_compose:
    specfile: /path/to/my_node_spec.json
    podm:
        host: 192.168.0.1
        port: 12345

- name: Allocate a node using JSON formatted specs
  rsd_compose:
    spec:
      processors: [{ ProcessorType: CPU, AchievableSpeedMHz: 3000 }]
      remote_drives: [{ CapacityGiB: 60, Protocol: iSCSI }]
    state: allocated
'''

RETURN = '''
---
node:
    description: Complete description of the node
    returned: On success
    type: complex
    contains:
        Id:
            description: Composed node ID
        Name:
            description: Composed node name
        Description:
            description: Description associated with the node
        UUID:
            description: The resource UUID assigned by PODM
        PowerState:
            description: Current power state
        ComposedNodeState:
            description: State of the composed node

    sample:
        "Id": "Node1"
        "Name": "Composed Node"
        "Description": "Node #1"
        "UUID": "00000000-0000-0000-0000-000000000000"
        "PowerState": "On"
        "ComposedNodeState": "Allocated"
'''

from time import sleep
import os.path
import json
from enum import Enum, unique

from ansible.module_utils.remote_management.rsd.rsd_common import RSD

try:
    import sushy
    import jsonschema
except ImportError:
    pass


class RsdNodeCompose(RSD):

    @unique
    class STATE(Enum):
        ABSENT = 'absent'
        ALLOCATING = 'allocating'
        ALLOCATED = 'allocated'
        ASSEMBLING = 'assembling'
        ASSEMBLED = 'assembled'
        FAILED = 'failed'

        @classmethod
        def allowed_module_args(cls):
            return (
                cls.ABSENT.value,
                cls.ALLOCATED.value,
                cls.ASSEMBLED.value
            )

        @classmethod
        def allowed_for_deletion(cls):
            return (
                cls.ALLOCATED,
                cls.ASSEMBLED,
                cls.FAILED
            )

        @classmethod
        def transition_states(cls):
            return (
                cls.ALLOCATING,
                cls.ASSEMBLING
            )

        @staticmethod
        def of(node):
            return RsdNodeCompose.STATE(node.composed_node_state.lower())

    def __init__(self):

        required_if = [
            ['state', 'absent', ['id']],
            ['state', 'allocated', ['spec', 'specfile'], True],
            ['state', 'assembled', ['spec', 'specfile', 'id'], True],
        ]

        mutually_exclusive = [
            ['id', 'spec', 'specfile']
        ]

        required_one_of = [
            ['id', 'spec', 'specfile']
        ]

        argument_spec = dict(
            id=dict(
                type='dict',
                required=False,
                options=dict(
                    type=dict(
                        type='str',
                        required=False,
                        choices=['name', 'identity', 'uuid'],
                        default='identity'
                    ),
                    value=dict(
                        type='str',
                        required=True
                    )
                )
            ),
            spec=dict(
                type='dict',
                required=False,
                options=dict(
                    name=dict(type='str', required=False),
                    description=dict(type='str', required=False),
                    processors=dict(type='json', required=False),
                    memory=dict(type='json', required=False),
                    local_drives=dict(type='json', required=False),
                    remote_drives=dict(type='json', required=False),
                    eth_ifaces=dict(type='json', required=False),
                    security=dict(type='dict', required=False),
                    total_cores=dict(type='int', required=False),
                    total_mem=dict(type='int', required=False),
                ),
            ),
            specfile=dict(
                type='path',
                aliases=['file'],
                required=False
            ),
            state=dict(
                default=self.STATE.ASSEMBLED.value,
                choices=self.STATE.allowed_module_args(),
                required=False,
                type='str',
            ),
        )

        super(RsdNodeCompose, self).__init__(
            argument_spec,
            required_one_of=required_one_of,
            required_if=required_if,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=False)

    def _wait_for_state_transition(self, node, wait_time=0.5, retries=60):
        if not node:
            raise ValueError("Cannot wait on node transition without a node")

        while retries > 0:
            sleep(wait_time)

            node.refresh()
            state = self.STATE.of(node)

            if state in self.STATE.transition_states():
                retries -= 1
            else:
                break

        return state

    def _delete_node(self, node):
        if not node:
            # Nothing to delete, no changes
            self.module.exit_json(changed=False, msg="Node already absent")

        state = self.STATE.of(node)

        self.module.debug(
            "Trying to delete node '{0}' from state '{1}'".format(
                node.identity, state.value))

        if state in self.STATE.transition_states():
            state = self._wait_for_state_transition(node)

        if state in self.STATE.allowed_for_deletion():
            node.delete_node()
            self.module.exit_json(changed=True, msg="Node deleted")
        else:
            self.module.fail_json(
                msg="Cannot delete node in '{0}' state".format(state.value))

    def _parse_node_specfile(self):
        podm_file_mappings = [
            ('Name', 'name', False),
            ('Description', 'description', False),
            ('Processors', 'processor_req', False),
            ('Memory', 'memory_req', False),
            ('RemoteDrives', 'remote_drive_req', False),
            ('LocalDrives', 'local_drive_req', False),
            ('EthernetInterfaces', 'ethernet_interface_req', False),
            ('Security', 'security_req', False),
            ('TotalSystemCoreCount', 'total_system_core_req', False),
            ('TotalSystemMemoryMiB', 'total_system_memory_req', False),
        ]

        filename = self.module.params.get('specfile', None)
        if not filename:
            return

        if not filename.endswith(".json"):
            raise ValueError("File must end with .json extension")

        with open(filename, 'r') as f:
            spec = json.load(f)

        return self._translate_request(spec, podm_file_mappings)

    def _parse_node_spec(self):
        module_arg_mappings = [
            ('name', 'name', False),
            ('description', 'description', False),
            ('processors', 'processor_req', True),
            ('memory', 'memory_req', True),
            ('remote_drives', 'remote_drive_req', True),
            ('local_drives', 'local_drive_req', True),
            ('eth_ifaces', 'ethernet_interface_req', True),
            ('security', 'security_req', False),
            ('total_cores', 'total_system_core_req', False),
            ('total_mem', 'total_system_memory_req', False),
        ]

        spec = self.module.params.get('spec', None)
        return self._translate_request(spec, module_arg_mappings)

    def _translate_request(self, spec, mappings):
        if not spec:
            raise ValueError("Missing node spec to perform transtation")

        if not isinstance(spec, dict):
            raise TypeError("Node specifications must be a dictionary")

        if not mappings:
            raise ValueError("Missing node mappings to perform translation")

        to_translate = spec.copy()   # no need for a deep copy
        translated = dict()
        for (podm_opt, lib_opt, decode) in mappings:
            value = to_translate.pop(podm_opt, None)
            if value:
                if decode:
                    translated[lib_opt] = json.loads(value)
                else:
                    translated[lib_opt] = value

        if to_translate:
            self.module.fail_json(msg="Invalid, unsupported or duplicated "
                                  "values in spec: {0}".format(to_translate))

        self.module.debug("rsd-lib node spec {0}".format(translated))

        return translated

    def _allocate_node(self):
        spec = self._parse_node_specfile()
        if not spec:
            spec = self._parse_node_spec()
        if not spec:
            self.module.fail_json(msg="Unable to parse node specs")

        return self._do_allocate_node(spec)

    def _do_allocate_node(self, spec):
        nodes = self.rsd.get_node_collection()
        try:
            node_uri = nodes.compose_node(**spec)
        except sushy.exceptions.HTTPError as e:
            self.module.fail_json(
                msg="Failed to allocate node: {0}".format(str(e)))
        except jsonschema.exceptions.ValidationError as e:
            self.module.fail_json(
                msg="Invalid spec formatting or value: {0}".format(str(e)))

        node_id = os.path.split(node_uri)[-1]
        node = self.rsd.get_node(node_uri)

        state = self._wait_for_state_transition(node)
        if state is not self.STATE.ALLOCATED:
            self.module.fail_json(
                msg="Failed to allocate node '{0}'".format(node_id))

        self.module.debug("Allocated new node with id '{0}'".format(node_id))

        return node

    def _assemble_node(self, node):
        if not node:
            raise ValueError("No node provided to assemble")

        state = self.STATE.of(node)
        self.module.debug(
            "Trying to assemble node '{0}' from state {1}".format(
                node.identity, state.value))

        if state in self.STATE.transition_states():
            state = self._wait_for_state_transition(node)

        if state is self.STATE.ALLOCATED:
            self._do_assemble_node(node)
            self._return_ok_node_response(node, True)

        elif state is self.STATE.ASSEMBLED:
            # Already in the desired state, nothing to do
            self._return_ok_node_response(node, False)

        elif state is self.STATE.FAILED:
            self.module.fail_json(
                msg="Cannot assemble node in 'Failed' state")

        else:
            self.module.fail_json(
                msg="Cannot assemble node '{0}' from state '{1}'".format(
                    node.identity, state.value))

    def _do_assemble_node(self, node):
        node.assemble_node()
        state = self._wait_for_state_transition(node)

        if state is self.STATE.ASSEMBLED:
            self.module.debug(
                "Node '{0}' now in Assembled state".format(node.identity))

        elif state is self.STATE.FAILED:
            self.module.fail_json(
                msg="Failed to assemble node '{0}'".format(node.identity))

        else:
            self.module.fail_json(
                msg="Node '{0}' is in state '{1}', cannot assemble".format(
                    node.identity, state))

    def _get_node_links_info(self, node):
        info = dict()
        system = self._get_system(node.links.computer_system)

        info["System"] = {
            "Name": system.name,
            "Description": system.description,
            "Id": system.identity,
            "ProcessorSummary": {
                "Count": system.processor_summary.count,
                "Model": system.processor_summary.model},
            "TotalSystemMemoryGiB": system.memory_summary.total_system_memory_gib}
        # TODO: Currently, retrieving interfaces information fails due to an
        # issue in rsd-lib. Once the bug is resolved, a patch will be applied
        # to enable this functionality.
        # ifaces = []
        # info["Interfaces"] = ifaces
        # iface_ids = node.links.ethernet_interfaces  # (tuple of URIs/IDs)
        # for iface_id in iface_ids:
        #     iface = system.ethernet_interfaces.get_member(iface_id)
        #     ifaces.append({
        #         "Name": iface.name,
        #         "Description": iface.description,
        #         "Id": iface.identity,
        #         "MACAddress": iface.mac_address,
        #         "IPv4Addresses": [a.address for a in iface.ipv4_addresses],
        #         "IPv6Addresses": [a.address for a in iface.ipv6_addresses],
        #     })
        return info

    def _return_ok_node_response(self, node, changed):
        if not node:
            raise ValueError("No node provided to return")

        if not node.uuid:
            self.module.fail_json(msg="There is no UUID. Failure.")

        node_desc = dict()
        node_desc["Id"] = node.identity
        node_desc["Name"] = node.name
        node_desc["Description"] = node.description
        node_desc["UUID"] = node.uuid
        node_desc["ComposedNodeState"] = node.composed_node_state
        node_desc["PowerState"] = node.power_state
        node_desc["Status"] = {
            'State': node.status.state,
            'Health': node.status.health,
        }
        node_desc['Details'] = self._get_node_links_info(node)

        self.module.exit_json(changed=changed, node=node_desc)

    def _delete_existing_node(self):
        self.module.debug("Request to delete an existing node")

        node = self._get_node()
        self._delete_node(node)

    def _assemble_allocated_node(self):
        self.module.debug("Request to assemble an existing node")

        node = self._get_node()
        self._assemble_node(node)

    def _allocate_new_node(self):
        self.module.debug("Request to allocate a new node")

        node = self._allocate_node()
        self._return_ok_node_response(node, True)

    def _allocate_and_assemble_new_node(self):
        self.module.debug("Request to assemble a new node")

        node = self._allocate_node()
        self._assemble_node(node)

    def run(self):
        id = self.module.params.get('id', None)
        requested_state = self.STATE(self.module.params['state'])

        if id and requested_state is self.STATE.ABSENT:
            self._delete_existing_node()

        elif id and requested_state is self.STATE.ASSEMBLED:
            self._assemble_allocated_node()

        elif requested_state is self.STATE.ALLOCATED:
            self._allocate_new_node()

        elif requested_state is self.STATE.ASSEMBLED:
            self._allocate_and_assemble_new_node()

        else:
            self.module.fail_json(msg="Invalid options for the module")


def main():
    compose = RsdNodeCompose()
    compose.run()


if __name__ == '__main__':
    main()
