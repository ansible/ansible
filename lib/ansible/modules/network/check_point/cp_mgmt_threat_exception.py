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
module: cp_mgmt_threat_exception
short_description: Manages threat-exception objects on Check Point over Web Services API
description:
  - Manages threat-exception objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - The name of the exception.
    type: str
    required: True
  position:
    description:
      - Position in the rulebase.
    type: str
  exception_group_uid:
    description:
      - The UID of the exception-group.
    type: str
  exception_group_name:
    description:
      - The name of the exception-group.
    type: str
  layer:
    description:
      - Layer that the rule belongs to identified by the name or UID.
    type: str
  rule_name:
    description:
      - The name of the parent rule.
    type: str
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
  protection_or_site:
    description:
      - Name of the protection or site.
    type: list
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
- name: add-threat-exception
  cp_mgmt_threat_exception:
    layer: New Layer 1
    name: Exception Rule
    position: 1
    protected_scope: All_Internet
    rule_name: Threat Rule 1
    state: present
    track: Log

- name: set-threat-exception
  cp_mgmt_threat_exception:
    layer: New Layer 1
    name: Exception Rule
    rule_name: Threat Rule 1
    state: present

- name: delete-threat-exception
  cp_mgmt_threat_exception:
    name: Exception Rule
    layer: New Layer 1
    rule_name: Threat Rule 1
    state: absent
"""

RETURN = """
cp_mgmt_threat_exception:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call, api_call_for_rule


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        position=dict(type='str'),
        exception_group_uid=dict(type='str'),
        exception_group_name=dict(type='str'),
        layer=dict(type='str'),
        rule_name=dict(type='str'),
        action=dict(type='str'),
        destination=dict(type='list'),
        destination_negate=dict(type='bool'),
        enabled=dict(type='bool'),
        install_on=dict(type='list'),
        protected_scope=dict(type='list'),
        protected_scope_negate=dict(type='bool'),
        protection_or_site=dict(type='list'),
        service=dict(type='list'),
        service_negate=dict(type='bool'),
        source=dict(type='list'),
        source_negate=dict(type='bool'),
        track=dict(type='str'),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'threat-exception'

    if module.params['position'] is None:
        result = api_call(module, api_call_object)
    else:
        result = api_call_for_rule(module, api_call_object)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
