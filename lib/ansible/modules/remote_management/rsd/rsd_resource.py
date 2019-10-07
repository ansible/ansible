#!/usr/bin/python
# -*- coding: utf-8 -*-

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
module: rsd_resource

short_description: Manage node post composition resources
                   attachment/detachment.

version_added: "2.10"

description:
    - rsd_boot module attaches/detaches resources to pre-created node.
    - To attach resource to composed node it is necessary to provide URL
      endpoint to the resource.
    - 'The node on which attach/detach action will be performed can
      be identified by one of the following: uuid, identity, or name.'

options:
    resource:
        description:
            - URL endpoint of the resource which should be
              attached/detached.
        required: true
        type: str
    state:
        description:
            - choose state of the resource either to be attached or detached
              from the node.
        required: true
        type: str
        choices: ['attached', 'detached']

extends_documentation_fragment:
    - rsd

author:
    - Radoslaw Kuschel (@radoslawKuschel)
'''
EXAMPLES = '''
---
- name: Attach volume to Node with ID 1.
  rsd_resource:
    id:
      value: 1
    resource: "/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/4"
    state: attached

- name: Detach volume from Node with ID 1.
  rsd_resource:
    id:
      value: 1
    resource: "/redfish/v1/StorageServices/f9c7e17e-6682_1/Volumes/4"
    state: detached

'''

RETURN = '''
node:
    description: Information regarding the node.
    returned: On success
    type: complex
    contains:
        id:
            description: Node ID.
        name:
            description: Node name.
        uuid:
            description: Node uuid.
        endpoint_attached:
            description: If attached state was chosen. Show attached
                         resource URL
        endpoint_detached:
            description: If detached state was chosen. Show detached
                         resource URL.

    sample:
        "id": "1"
        "name": "node_01"
        "endpoint_attached": "/redfish/v1/StorageServices/f9c7e1_1/Volumes/4"
        "uuid": "254bbb38-b98c-46a0-af5f-bef452854061"
'''

from ansible.module_utils.remote_management.rsd.rsd_common import RSD
try:
    import sushy
except ImportError:
    pass


class RsdNodeResource(RSD):

    def __init__(self):
        argument_spec = dict(
            resource=dict(
                type='str',
                required=True
            ),
            state=dict(
                type='str',
                required=True,
                choices=['attached', 'detached']
            )
        )

        super(RsdNodeResource, self).__init__(argument_spec, False)

    def _return_resource_result(self, node, resource, attach, changed):
        result = dict()

        result["id"] = node.identity
        result["name"] = node.name
        result["uuid"] = node.uuid

        if changed is True:

            if attach is True:
                result["endpoint_attached"] = resource
            else:
                result["endpoint_detached"] = resource

        self.module.exit_json(changed=changed, node=result)

    @staticmethod
    def _is_resource_attachable(node, resource):
        return True if resource in node.get_allowed_attach_endpoints() \
            else False

    @staticmethod
    def _is_resource_detachable(node, resource):
        return True if resource in node.get_allowed_detach_endpoints() \
            else False

    @staticmethod
    def _is_resource_valid(node, resource):
        if RsdNodeResource._is_resource_attachable(node, resource) or \
           RsdNodeResource._is_resource_detachable(node, resource):
            return True
        return False

    def _attach_resource(self, node, resource):
        try:
            node.attach_endpoint(resource)
            self._return_resource_result(node, resource, True, True)
        except (sushy.exceptions.InvalidParameterValueError) as e:
            self.module.fail_json(msg="Invalid Endpoint: "
                                  "{0}".format(str(e)))

    def _detach_resource(self, node, resource):
        try:
            node.detach_endpoint(resource)
            self._return_resource_result(node, resource, False, True)
        except (sushy.exceptions.InvalidParameterValueError) as e:
            self.module.fail_json(msg="Invalid Endpoint: "
                                  "{0}".format(str(e)))

    def _change_node_resource(self, node, resource, requested_state):
        if not RsdNodeResource._is_resource_valid(node, resource):
            self.module.fail_json(msg="Invalid Endpoint: {0}".format(resource))

        # Check if resource is already attached.
        attached = RsdNodeResource._is_resource_detachable(node, resource)

        if requested_state == 'attached' and not attached:
            self._attach_resource(node, resource)
        elif requested_state == 'detached' and attached:
            self._detach_resource(node, resource)
        else:
            # Nothing to be done. Exit module and report that nothing has
            # changed.
            self._return_resource_result(node, resource, False, False)

    def run(self):
        requested_state = self.module.params['state']
        resource = self.module.params['resource']
        node = self._get_node()

        self._change_node_resource(node, resource, requested_state)


def main():
    resource = RsdNodeResource()
    resource.run()


if __name__ == '__main__':
    main()
