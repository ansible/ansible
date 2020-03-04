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
module: cp_mgmt_threat_rule
short_description: Manages threat-rule objects on Check Point over Web Services API
description:
  - Manages threat-rule objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  position:
    description:
      - Position in the rulebase.
    type: str
  layer:
    description:
      - Layer that the rule belongs to identified by the name or UID.
    type: str
  name:
    description:
      - Object name.
    type: str
    required: True
  action:
    description:
      - Action-the enforced profile.
    type: str
  destination:
    description:
      - Collection of Network objects identified by the name or UID.
    type: list
  destination_negate:
    description:
      - True if negate is set for destination.
    type: bool
  enabled:
    description:
      - Enable/Disable the rule.
    type: bool
  install_on:
    description:
      - Which Gateways identified by the name or UID to install the policy on.
    type: list
  protected_scope:
    description:
      - Collection of objects defining Protected Scope identified by the name or UID.
    type: list
  protected_scope_negate:
    description:
      - True if negate is set for Protected Scope.
    type: bool
  service:
    description:
      - Collection of Network objects identified by the name or UID.
    type: list
  service_negate:
    description:
      - True if negate is set for Service.
    type: bool
  source:
    description:
      - Collection of Network objects identified by the name or UID.
    type: list
  source_negate:
    description:
      - True if negate is set for source.
    type: bool
  track:
    description:
      - Packet tracking.
    type: str
  track_settings:
    description:
      - Threat rule track settings.
    type: dict
    suboptions:
      packet_capture:
        description:
          - Packet capture.
        type: bool
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
- name: add-threat-rule
  cp_mgmt_threat_rule:
    comments: ''
    install_on: Policy Targets
    layer: New Layer 1
    name: First threat rule
    position: 1
    protected_scope: All_Internet
    state: present
    track: None

- name: set-threat-rule
  cp_mgmt_threat_rule:
    action: New Profile 1
    comments: commnet for the first rule
    install_on: Policy Targets
    layer: New Layer 1
    name: Rule Name
    position: 1
    protected_scope: All_Internet
    state: present

- name: delete-threat-rule
  cp_mgmt_threat_rule:
    layer: New Layer 1
    name: Rule Name
    state: absent
"""

RETURN = """
cp_mgmt_threat_rule:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call, api_call_for_rule


def main():
    argument_spec = dict(
        position=dict(type='str'),
        layer=dict(type='str'),
        name=dict(type='str', required=True),
        action=dict(type='str'),
        destination=dict(type='list'),
        destination_negate=dict(type='bool'),
        enabled=dict(type='bool'),
        install_on=dict(type='list'),
        protected_scope=dict(type='list'),
        protected_scope_negate=dict(type='bool'),
        service=dict(type='list'),
        service_negate=dict(type='bool'),
        source=dict(type='list'),
        source_negate=dict(type='bool'),
        track=dict(type='str'),
        track_settings=dict(type='dict', options=dict(
            packet_capture=dict(type='bool')
        )),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'threat-rule'

    if module.params['position'] is None:
        result = api_call(module, api_call_object)
    else:
        result = api_call_for_rule(module, api_call_object)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
