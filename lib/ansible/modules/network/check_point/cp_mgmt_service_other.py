#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Check Point Firewall (c) 2019
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
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_mgmt_service_other
short_description: Manages service-other objects on Check Point over Web Services API
description:
  - Manages service-other objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  accept_replies:
    description:
      - Specifies whether Other Service replies are to be accepted.
    type: bool
  action:
    description:
      - Contains an INSPECT expression that defines the action to take if a rule containing this service is matched.
        Example, set r_mhandler &open_ssl_handler sets a handler on the connection.
    type: str
  aggressive_aging:
    description:
      - Sets short (aggressive) timeouts for idle connections.
    type: dict
    suboptions:
      default_timeout:
        description:
          - Default aggressive aging timeout in seconds.
        type: int
      enable:
        description:
          - N/A
        type: bool
      timeout:
        description:
          - Aggressive aging timeout in seconds.
        type: int
      use_default_timeout:
        description:
          - N/A
        type: bool
  ip_protocol:
    description:
      - IP protocol number.
    type: int
  keep_connections_open_after_policy_installation:
    description:
      - Keep connections open after policy has been installed even if they are not allowed under the new policy. This overrides the settings in the
        Connection Persistence page. If you change this property, the change will not affect open connections, but only future connections.
    type: bool
  match:
    description:
      - Contains an INSPECT expression that defines the matching criteria. The connection is examined against the expression during the first packet.
        Example, tcp, dport = 21, direction = 0 matches incoming FTP control connections.
    type: str
  match_for_any:
    description:
      - Indicates whether this service is used when 'Any' is set as the rule's service and there are several service objects with the same source port
        and protocol.
    type: bool
  override_default_settings:
    description:
      - Indicates whether this service is a Data Domain service which has been overridden.
    type: bool
  session_timeout:
    description:
      - Time (in seconds) before the session times out.
    type: int
  sync_connections_on_cluster:
    description:
      - Enables state-synchronized High Availability or Load Sharing on a ClusterXL or OPSEC-certified cluster.
    type: bool
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  use_default_session_timeout:
    description:
      - Use default virtual session timeout.
    type: bool
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid', 'dark orange', 'dark sea green',
             'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon',
             'coral', 'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
        representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  groups:
    description:
      - Collection of group identifiers.
    type: list
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted - warnings will also be ignored.
    type: bool
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-service-other
  cp_mgmt_service_other:
    aggressive_aging:
      enable: true
      timeout: 360
      use_default_timeout: false
    ip_protocol: 51
    keep_connections_open_after_policy_installation: false
    match_for_any: true
    name: New_Service_1
    session_timeout: 0
    state: present
    sync_connections_on_cluster: true

- name: set-service-other
  cp_mgmt_service_other:
    aggressive_aging:
      default_timeout: 3600
    color: green
    name: New_Service_1
    state: present

- name: delete-service-other
  cp_mgmt_service_other:
    name: New_Service_2
    state: absent
"""

RETURN = """
cp_mgmt_service_other:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        accept_replies=dict(type='bool'),
        action=dict(type='str'),
        aggressive_aging=dict(type='dict', options=dict(
            default_timeout=dict(type='int'),
            enable=dict(type='bool'),
            timeout=dict(type='int'),
            use_default_timeout=dict(type='bool')
        )),
        ip_protocol=dict(type='int'),
        keep_connections_open_after_policy_installation=dict(type='bool'),
        match=dict(type='str'),
        match_for_any=dict(type='bool'),
        override_default_settings=dict(type='bool'),
        session_timeout=dict(type='int'),
        sync_connections_on_cluster=dict(type='bool'),
        tags=dict(type='list'),
        use_default_session_timeout=dict(type='bool'),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
                                        'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
                                        'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna',
                                        'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        groups=dict(type='list'),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'service-other'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
