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
module: cp_mgmt_threat_profile
short_description: Manages threat-profile objects on Check Point over Web Services API
description:
  - Manages threat-profile objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  active_protections_performance_impact:
    description:
      - Protections with this performance impact only will be activated in the profile.
    type: str
    choices: ['high', 'medium', 'low', 'very_low']
  active_protections_severity:
    description:
      - Protections with this severity only will be activated in the profile.
    type: str
    choices: ['Critical', 'High', 'Medium or above', 'Low or above']
  confidence_level_high:
    description:
      - Action for protections with high confidence level.
    type: str
    choices: ['Inactive', 'Ask', 'Prevent', 'Detect']
  confidence_level_low:
    description:
      - Action for protections with low confidence level.
    type: str
    choices: ['Inactive', 'Ask', 'Prevent', 'Detect']
  confidence_level_medium:
    description:
      - Action for protections with medium confidence level.
    type: str
    choices: ['Inactive', 'Ask', 'Prevent', 'Detect']
  indicator_overrides:
    description:
      - Indicators whose action will be overridden in this profile.
    type: list
    suboptions:
      action:
        description:
          - The indicator's action in this profile.
        type: str
        choices: ['Inactive', 'Ask', 'Prevent', 'Detect']
      indicator:
        description:
          - The indicator whose action is to be overridden.
        type: str
  ips_settings:
    description:
      - IPS blade settings.
    type: dict
    suboptions:
      exclude_protection_with_performance_impact:
        description:
          - Whether to exclude protections depending on their level of performance impact.
        type: bool
      exclude_protection_with_performance_impact_mode:
        description:
          - Exclude protections with this level of performance impact.
        type: str
        choices: ['very low', 'low or lower', 'medium or lower', 'high or lower']
      exclude_protection_with_severity:
        description:
          - Whether to exclude protections depending on their level of severity.
        type: bool
      exclude_protection_with_severity_mode:
        description:
          - Exclude protections with this level of severity.
        type: str
        choices: ['low or above', 'medium or above', 'high or above', 'critical']
      newly_updated_protections:
        description:
          - Activation of newly updated protections.
        type: str
        choices: ['active', 'inactive', 'staging']
  malicious_mail_policy_settings:
    description:
      - Malicious Mail Policy for MTA Gateways.
    type: dict
    suboptions:
      add_customized_text_to_email_body:
        description:
          - Add customized text to the malicious email body.
        type: bool
      add_email_subject_prefix:
        description:
          - Add a prefix to the malicious email subject.
        type: bool
      add_x_header_to_email:
        description:
          - Add an X-Header to the malicious email.
        type: bool
      email_action:
        description:
          - Block - block the entire malicious email<br>Allow - pass the malicious email and apply email changes (like, remove attachments and
            links, add x-header, etc...).
        type: str
        choices: ['allow', 'block']
      email_body_customized_text:
        description:
          - Customized text for the malicious email body.<br> Available predefined fields,<br> $verdicts$ - the malicious/error attachments/links verdict.
        type: str
      email_subject_prefix_text:
        description:
          - Prefix for the malicious email subject.
        type: str
      failed_to_scan_attachments_text:
        description:
          - Replace attachments that failed to be scanned with this text.<br> Available predefined fields,<br> $filename$ - the malicious file
            name.<br> $md5$ - MD5 of the malicious file.
        type: str
      malicious_attachments_text:
        description:
          - Replace malicious attachments with this text.<br> Available predefined fields,<br> $filename$ - the malicious file name.<br> $md5$ -
            MD5 of the malicious file.
        type: str
      malicious_links_text:
        description:
          - Replace malicious links with this text.<br> Available predefined fields,<br> $neutralized_url$ - neutralized malicious link.
        type: str
      remove_attachments_and_links:
        description:
          - Remove attachments and links from the malicious email.
        type: bool
      send_copy:
        description:
          - Send a copy of the malicious email to the recipient list.
        type: bool
      send_copy_list:
        description:
          - Recipient list to send a copy of the malicious email.
        type: list
  overrides:
    description:
      - Overrides per profile for this protection.
    type: list
    suboptions:
      action:
        description:
          - Protection action.
        type: str
        choices: ['Threat Cloud: Inactive', 'Detect', 'Prevent <br> Core: Drop', 'Inactive', 'Accept']
      protection:
        description:
          - IPS protection identified by name or UID.
        type: str
      capture_packets:
        description:
          - Capture packets.
        type: bool
      track:
        description:
          - Tracking method for protection.
        type: str
        choices: ['none', 'log', 'alert', 'mail', 'snmp trap', 'user alert', 'user alert 1', 'user alert 2']
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  use_indicators:
    description:
      - Indicates whether the profile should make use of indicators.
    type: bool
  anti_bot:
    description:
      - Is Anti-Bot blade activated.
    type: bool
  anti_virus:
    description:
      - Is Anti-Virus blade activated.
    type: bool
  ips:
    description:
      - Is IPS blade activated.
    type: bool
  threat_emulation:
    description:
      - Is Threat Emulation blade activated.
    type: bool
  activate_protections_by_extended_attributes:
    description:
      - Activate protections by these extended attributes.
    type: list
    suboptions:
      name:
        description:
          - IPS tag name.
        type: str
      category:
        description:
          - IPS tag category name.
        type: str
  deactivate_protections_by_extended_attributes:
    description:
      - Deactivate protections by these extended attributes.
    type: list
    suboptions:
      name:
        description:
          - IPS tag name.
        type: str
      category:
        description:
          - IPS tag category name.
        type: str
  use_extended_attributes:
    description:
      - Whether to activate/deactivate IPS protections according to the extended attributes.
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
- name: add-threat-profile
  cp_mgmt_threat_profile:
    active_protections_performance_impact: low
    active_protections_severity: low or above
    anti_bot: true
    anti_virus: true
    confidence_level_high: prevent
    confidence_level_medium: prevent
    ips: true
    ips_settings:
      exclude_protection_with_performance_impact: true
      exclude_protection_with_performance_impact_mode: high or lower
      newly_updated_protections: staging
    name: New Profile 1
    state: present
    threat_emulation: true

- name: set-threat-profile
  cp_mgmt_threat_profile:
    active_protections_performance_impact: low
    active_protections_severity: low or above
    anti_bot: true
    anti_virus: false
    comments: update recommended profile
    confidence_level_high: prevent
    confidence_level_low: prevent
    confidence_level_medium: prevent
    ips: false
    ips_settings:
      exclude_protection_with_performance_impact: true
      exclude_protection_with_performance_impact_mode: high or lower
      newly_updated_protections: active
    name: New Profile 1
    state: present
    threat_emulation: true

- name: delete-threat-profile
  cp_mgmt_threat_profile:
    name: New Profile 1
    state: absent
"""

RETURN = """
cp_mgmt_threat_profile:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        active_protections_performance_impact=dict(type='str', choices=['high', 'medium', 'low', 'very_low']),
        active_protections_severity=dict(type='str', choices=['Critical', 'High', 'Medium or above', 'Low or above']),
        confidence_level_high=dict(type='str', choices=['Inactive', 'Ask', 'Prevent', 'Detect']),
        confidence_level_low=dict(type='str', choices=['Inactive', 'Ask', 'Prevent', 'Detect']),
        confidence_level_medium=dict(type='str', choices=['Inactive', 'Ask', 'Prevent', 'Detect']),
        indicator_overrides=dict(type='list', options=dict(
            action=dict(type='str', choices=['Inactive', 'Ask', 'Prevent', 'Detect']),
            indicator=dict(type='str')
        )),
        ips_settings=dict(type='dict', options=dict(
            exclude_protection_with_performance_impact=dict(type='bool'),
            exclude_protection_with_performance_impact_mode=dict(type='str', choices=['very low', 'low or lower', 'medium or lower', 'high or lower']),
            exclude_protection_with_severity=dict(type='bool'),
            exclude_protection_with_severity_mode=dict(type='str', choices=['low or above', 'medium or above', 'high or above', 'critical']),
            newly_updated_protections=dict(type='str', choices=['active', 'inactive', 'staging'])
        )),
        malicious_mail_policy_settings=dict(type='dict', options=dict(
            add_customized_text_to_email_body=dict(type='bool'),
            add_email_subject_prefix=dict(type='bool'),
            add_x_header_to_email=dict(type='bool'),
            email_action=dict(type='str', choices=['allow', 'block']),
            email_body_customized_text=dict(type='str'),
            email_subject_prefix_text=dict(type='str'),
            failed_to_scan_attachments_text=dict(type='str'),
            malicious_attachments_text=dict(type='str'),
            malicious_links_text=dict(type='str'),
            remove_attachments_and_links=dict(type='bool'),
            send_copy=dict(type='bool'),
            send_copy_list=dict(type='list')
        )),
        overrides=dict(type='list', options=dict(
            action=dict(type='str', choices=['Threat Cloud: Inactive', 'Detect', 'Prevent <br> Core: Drop', 'Inactive', 'Accept']),
            protection=dict(type='str'),
            capture_packets=dict(type='bool'),
            track=dict(type='str', choices=['none', 'log', 'alert', 'mail', 'snmp trap', 'user alert', 'user alert 1', 'user alert 2'])
        )),
        tags=dict(type='list'),
        use_indicators=dict(type='bool'),
        anti_bot=dict(type='bool'),
        anti_virus=dict(type='bool'),
        ips=dict(type='bool'),
        threat_emulation=dict(type='bool'),
        activate_protections_by_extended_attributes=dict(type='list', options=dict(
            name=dict(type='str'),
            category=dict(type='str')
        )),
        deactivate_protections_by_extended_attributes=dict(type='list', options=dict(
            name=dict(type='str'),
            category=dict(type='str')
        )),
        use_extended_attributes=dict(type='bool'),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
                                        'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
                                        'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna',
                                        'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'threat-profile'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
