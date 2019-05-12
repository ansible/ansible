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

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: checkpoint_service_tcp
short_description: Manages service_tcp objects on Checkpoint over Web Services API
description:
  - Manages service_tcp objects on Checkpoint devices including creating, updating, removing service_tcp objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  aggressive_aging:
    description:
      - Sets short (aggressive) timeouts for idle connections.
    type: dict
  keep_connections_open_after_policy_installation:
    description:
      - Keep connections open after policy has been installed even if they are not allowed under the new policy.
        This overrides the settings in the Connection Persistence page. If you change this property, the change will not
        affect open connections, but only future connections.
    type: bool
  match_by_protocol_signature:
    description:
      - A value of true enables matching by the selected protocol's signature - the signature identifies the protocol as
        genuine. Select this option to limit the port to the specified protocol. If the selected protocol does not
        support matching by signature, this field cannot be set to true.
    type: bool
  match_for_any:
    description:
      - Indicates whether this service is used when 'Any' is set as the rule's service and there are several service
        objects with the same source port and protocol.
    type: bool
  override_default_settings:
    description:
      - Indicates whether this service is a Data Domain service which has been overridden.
    type: bool
  port:
    description:
      - The number of the port used to provide this service. To specify a port range, place a hyphen between the lowest
        and highest port numbers, for example 44-55.
    type: str
  protocol:
    description:
      - Select the protocol type associated with the service, and by implication, the management server (if any) that
        enforces Content Security and Authentication for the service. Selecting a Protocol Type invokes the specific
        protocol handlers for each protocol type, thus enabling higher level of security by parsing the protocol, and
        higher level of connectivity by tracking dynamic actions (such as opening of ports).
    type: str
  session_timeout:
    description:
      - Time (in seconds) before the session times out.
    type: int
  source_port:
    description:
      - Port number for the client side service. If specified, only those Source port Numbers will be Accepted, Dropped,
        or Rejected during packet inspection. Otherwise, the source port is not inspected.
    type: str
  sync_connections_on_cluster:
    description:
      - Enables state-synchronized High Availability or Load Sharing on a ClusterXL or OPSEC-certified cluster.
    type: bool
  use_default_session_timeout:
    description:
      - Use default virtual session timeout.
    type: bool
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: Add service_tcp object
  checkpoint_service_tcp:
    name: "New_TCP_Service_1"
    state: present


- name: Delete service_tcp object
  checkpoint_service_tcp:
    name: "New_TCP_Service_1"
    state: absent
"""

RETURN = """
api_result:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        aggressive_aging=dict(type='dict'),
        keep_connections_open_after_policy_installation=dict(type='bool'),
        match_by_protocol_signature=dict(type='bool'),
        match_for_any=dict(type='bool'),
        override_default_settings=dict(type='bool'),
        port=dict(type='str'),
        protocol=dict(type='str'),
        session_timeout=dict(type='int'),
        source_port=dict(type='str'),
        sync_connections_on_cluster=dict(type='bool'),
        use_default_session_timeout=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, required_one_of=[['name', 'uid']],
                           mutually_exclusive=[['name', 'uid']])
    api_call_object = "service-tcp"

    api_call(module, api_call_object)


if __name__ == '__main__':
    main()
