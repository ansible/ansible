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
# but WITHOUT ANY WARRANTY; without even the implied warranty of`
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_secprof_waf
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: FortiManager web application firewall security profile
description:
  -  Manage web application firewall security profiles for FGTs via FMG

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  host:
    description:
      - The FortiManager's Address.
    required: true

  username:
    description:
      - The username associated with the account.
    required: true

  password:
    description:
      - The password associated with the username account.
    required: true

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  name:
    description:
      - WAF Profile name.
    required: false

  external:
    description:
      - Disable/Enable external HTTP Inspection.
      - choice | disable | Disable external inspection.
      - choice | enable | Enable external inspection.
    required: false
    choices: ["disable", "enable"]

  extended_log:
    description:
      - Enable/disable extended logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  comment:
    description:
      - Comment.
    required: false

  address_list:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  address_list_blocked_address:
    description:
      - Blocked address.
    required: false

  address_list_blocked_log:
    description:
      - Enable/disable logging on blocked addresses.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  address_list_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  address_list_status:
    description:
      - Status.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  address_list_trusted_address:
    description:
      - Trusted address.
    required: false

  constraint:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  constraint_content_length_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_content_length_length:
    description:
      - Length of HTTP content in bytes (0 to 2147483647).
    required: false

  constraint_content_length_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_content_length_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_content_length_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_address:
    description:
      - Host address.
    required: false

  constraint_exception_content_length:
    description:
      - HTTP content length in request.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_header_length:
    description:
      - HTTP header length in request.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_hostname:
    description:
      - Enable/disable hostname check.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_line_length:
    description:
      - HTTP line length in request.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_malformed:
    description:
      - Enable/disable malformed HTTP request check.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_max_cookie:
    description:
      - Maximum number of cookies in HTTP request.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_max_header_line:
    description:
      - Maximum number of HTTP header line.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_max_range_segment:
    description:
      - Maximum number of range segments in HTTP range line.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_max_url_param:
    description:
      - Maximum number of parameters in URL.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_method:
    description:
      - Enable/disable HTTP method check.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_param_length:
    description:
      - Maximum length of parameter in URL, HTTP POST request or HTTP body.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_pattern:
    description:
      - URL pattern.
    required: false

  constraint_exception_regex:
    description:
      - Enable/disable regular expression based pattern match.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_url_param_length:
    description:
      - Maximum length of parameter in URL.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_exception_version:
    description:
      - Enable/disable HTTP version check.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_header_length_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_header_length_length:
    description:
      - Length of HTTP header in bytes (0 to 2147483647).
    required: false

  constraint_header_length_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_header_length_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_header_length_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_hostname_action:
    description:
      - Action for a hostname constraint.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_hostname_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_hostname_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_hostname_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_line_length_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_line_length_length:
    description:
      - Length of HTTP line in bytes (0 to 2147483647).
    required: false

  constraint_line_length_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_line_length_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_line_length_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_malformed_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_malformed_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_malformed_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_malformed_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_max_cookie_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_max_cookie_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_max_cookie_max_cookie:
    description:
      - Maximum number of cookies in HTTP request (0 to 2147483647).
    required: false

  constraint_max_cookie_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_max_cookie_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_max_header_line_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_max_header_line_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_max_header_line_max_header_line:
    description:
      - Maximum number HTTP header lines (0 to 2147483647).
    required: false

  constraint_max_header_line_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_max_header_line_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_max_range_segment_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_max_range_segment_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_max_range_segment_max_range_segment:
    description:
      - Maximum number of range segments in HTTP range line (0 to 2147483647).
    required: false

  constraint_max_range_segment_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_max_range_segment_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_max_url_param_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_max_url_param_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_max_url_param_max_url_param:
    description:
      - Maximum number of parameters in URL (0 to 2147483647).
    required: false

  constraint_max_url_param_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_max_url_param_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_method_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_method_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_method_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_method_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_param_length_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_param_length_length:
    description:
      - Maximum length of parameter in URL, HTTP POST request or HTTP body in bytes (0 to 2147483647).
    required: false

  constraint_param_length_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_param_length_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_param_length_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_url_param_length_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_url_param_length_length:
    description:
      - Maximum length of URL parameter in bytes (0 to 2147483647).
    required: false

  constraint_url_param_length_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_url_param_length_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_url_param_length_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_version_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
    required: false
    choices: ["allow", "block"]

  constraint_version_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  constraint_version_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  constraint_version_status:
    description:
      - Enable/disable the constraint.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  method:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  method_default_allowed_methods:
    description:
      - Methods.
      - FLAG Based Options. Specify multiple in list form.
      - flag | delete | HTTP DELETE method.
      - flag | get | HTTP GET method.
      - flag | head | HTTP HEAD method.
      - flag | options | HTTP OPTIONS method.
      - flag | post | HTTP POST method.
      - flag | put | HTTP PUT method.
      - flag | trace | HTTP TRACE method.
      - flag | others | Other HTTP methods.
      - flag | connect | HTTP CONNECT method.
    required: false
    choices: ["delete", "get", "head", "options", "post", "put", "trace", "others", "connect"]

  method_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  method_severity:
    description:
      - Severity.
      - choice | low | low severity
      - choice | medium | medium severity
      - choice | high | High severity
    required: false
    choices: ["low", "medium", "high"]

  method_status:
    description:
      - Status.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  method_method_policy_address:
    description:
      - Host address.
    required: false

  method_method_policy_allowed_methods:
    description:
      - Allowed Methods.
      - FLAG Based Options. Specify multiple in list form.
      - flag | delete | HTTP DELETE method.
      - flag | get | HTTP GET method.
      - flag | head | HTTP HEAD method.
      - flag | options | HTTP OPTIONS method.
      - flag | post | HTTP POST method.
      - flag | put | HTTP PUT method.
      - flag | trace | HTTP TRACE method.
      - flag | others | Other HTTP methods.
      - flag | connect | HTTP CONNECT method.
    required: false
    choices: ["delete", "get", "head", "options", "post", "put", "trace", "others", "connect"]

  method_method_policy_pattern:
    description:
      - URL pattern.
    required: false

  method_method_policy_regex:
    description:
      - Enable/disable regular expression based pattern match.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  signature:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  signature_credit_card_detection_threshold:
    description:
      - The minimum number of Credit cards to detect violation.
    required: false

  signature_disabled_signature:
    description:
      - Disabled signatures
    required: false

  signature_disabled_sub_class:
    description:
      - Disabled signature subclasses.
    required: false

  signature_custom_signature_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
      - choice | erase | Erase credit card numbers.
    required: false
    choices: ["allow", "block", "erase"]

  signature_custom_signature_case_sensitivity:
    description:
      - Case sensitivity in pattern.
      - choice | disable | Case insensitive in pattern.
      - choice | enable | Case sensitive in pattern.
    required: false
    choices: ["disable", "enable"]

  signature_custom_signature_direction:
    description:
      - Traffic direction.
      - choice | request | Match HTTP request.
      - choice | response | Match HTTP response.
    required: false
    choices: ["request", "response"]

  signature_custom_signature_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  signature_custom_signature_name:
    description:
      - Signature name.
    required: false

  signature_custom_signature_pattern:
    description:
      - Match pattern.
    required: false

  signature_custom_signature_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  signature_custom_signature_status:
    description:
      - Status.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  signature_custom_signature_target:
    description:
      - Match HTTP target.
      - FLAG Based Options. Specify multiple in list form.
      - flag | arg | HTTP arguments.
      - flag | arg-name | Names of HTTP arguments.
      - flag | req-body | HTTP request body.
      - flag | req-cookie | HTTP request cookies.
      - flag | req-cookie-name | HTTP request cookie names.
      - flag | req-filename | HTTP request file name.
      - flag | req-header | HTTP request headers.
      - flag | req-header-name | HTTP request header names.
      - flag | req-raw-uri | Raw URI of HTTP request.
      - flag | req-uri | URI of HTTP request.
      - flag | resp-body | HTTP response body.
      - flag | resp-hdr | HTTP response headers.
      - flag | resp-status | HTTP response status.
    required: false
    choices: ["arg","arg-name","req-body","req-cookie","req-cookie-name","req-filename","req-header","req-header-name",
      "req-raw-uri","req-uri","resp-body","resp-hdr","resp-status"]

  signature_main_class_action:
    description:
      - Action.
      - choice | allow | Allow.
      - choice | block | Block.
      - choice | erase | Erase credit card numbers.
    required: false
    choices: ["allow", "block", "erase"]

  signature_main_class_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  signature_main_class_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  signature_main_class_status:
    description:
      - Status.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  url_access:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  url_access_action:
    description:
      - Action.
      - choice | bypass | Allow the HTTP request, also bypass further WAF scanning.
      - choice | permit | Allow the HTTP request, and continue further WAF scanning.
      - choice | block | Block HTTP request.
    required: false
    choices: ["bypass", "permit", "block"]

  url_access_address:
    description:
      - Host address.
    required: false

  url_access_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  url_access_severity:
    description:
      - Severity.
      - choice | low | Low severity.
      - choice | medium | Medium severity.
      - choice | high | High severity.
    required: false
    choices: ["low", "medium", "high"]

  url_access_access_pattern_negate:
    description:
      - Enable/disable match negation.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  url_access_access_pattern_pattern:
    description:
      - URL pattern.
    required: false

  url_access_access_pattern_regex:
    description:
      - Enable/disable regular expression based pattern match.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  url_access_access_pattern_srcaddr:
    description:
      - Source address.
    required: false

'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_waf:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_WAF_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_waf:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_WAF_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "set"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager

    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


###############
# START METHODS
###############


def fmgr_waf_profile_addsetdelete(fmg, paramgram):

    mode = paramgram["mode"]
    adom = paramgram["adom"]
    # INIT A BASIC OBJECTS
    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/waf/profile'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/waf/profile/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if mode == "set":
        response = fmg.set(url, datagram)
    # IF MODE = UPDATE -- USER THE 'UPDATE' API CALL MODE
    elif mode == "update":
        response = fmg.update(url, datagram)
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    elif mode == "add":
        response = fmg.add(url, datagram)
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    elif mode == "delete":
        response = fmg.delete(url, datagram)

    return response


# ADDITIONAL COMMON FUNCTIONS
# FUNCTION/METHOD FOR LOGGING OUT AND ANALYZING ERROR CODES
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """
    # pydevd.settrace('10.0.0.122', port=54654, stdoutToServer=True, stderrToServer=True)
    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except BaseException:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except BaseException:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

        if results[0] not in good_codes:
            if logout_on_fail:
                fmg.logout()
                module.fail_json(msg=msg, **results[1])
            else:
                return msg
        else:
            if logout_on_success:
                fmg.logout()
                module.exit_json(msg="API Called worked, but logout handler has been asked to logout on success",
                                 **results[1])
            else:
                return msg


# FUNCTION/METHOD FOR CONVERTING CIDR TO A NETMASK
# DID NOT USE IP ADDRESS MODULE TO KEEP INCLUDES TO A MINIMUM
def fmgr_cidr_to_netmask(cidr):
    cidr = int(cidr)
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    return (str((0xff000000 & mask) >> 24) + '.' +
            str((0x00ff0000 & mask) >> 16) + '.' +
            str((0x0000ff00 & mask) >> 8) + '.' +
            str((0x000000ff & mask)))


# utility function: removing keys wih value of None, nothing in playbook for that key
def fmgr_del_none(obj):
    if isinstance(obj, dict):
        return type(obj)((fmgr_del_none(k), fmgr_del_none(v))
                         for k, v in obj.items() if k is not None and (v is not None and not fmgr_is_empty_dict(v)))
    else:
        return obj


# utility function: remove keys that are need for the logic but the FMG API won't accept them
def fmgr_prepare_dict(obj):
    list_of_elems = ["mode", "adom", "host", "username", "password"]
    if isinstance(obj, dict):
        obj = dict((key, fmgr_prepare_dict(value)) for (key, value) in obj.items() if key not in list_of_elems)
    return obj


def fmgr_is_empty_dict(obj):
    return_val = False
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, dict):
                    if len(v) == 0:
                        return_val = True
                    elif len(v) > 0:
                        for k1, v1 in v.items():
                            if v1 is None:
                                return_val = True
                            elif v1 is not None:
                                return_val = False
                                return return_val
                elif v is None:
                    return_val = True
                elif v is not None:
                    return_val = False
                    return return_val
        elif len(obj) == 0:
            return_val = True

    return return_val


def fmgr_split_comma_strings_into_lists(obj):
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, str):
                    new_list = list()
                    if "," in v:
                        new_items = v.split(",")
                        for item in new_items:
                            new_list.append(item.strip())
                        obj[k] = new_list

    return obj


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        name=dict(required=False, type="str"),
        external=dict(required=False, type="str", choices=["disable", "enable"]),
        extended_log=dict(required=False, type="str", choices=["disable", "enable"]),
        comment=dict(required=False, type="str"),
        address_list=dict(required=False, type="list"),
        address_list_blocked_address=dict(required=False, type="str"),
        address_list_blocked_log=dict(required=False, type="str", choices=["disable", "enable"]),
        address_list_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        address_list_status=dict(required=False, type="str", choices=["disable", "enable"]),
        address_list_trusted_address=dict(required=False, type="str"),
        constraint=dict(required=False, type="list"),

        constraint_content_length_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_content_length_length=dict(required=False, type="int"),
        constraint_content_length_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_content_length_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_content_length_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_exception_address=dict(required=False, type="str"),
        constraint_exception_content_length=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_header_length=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_hostname=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_line_length=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_malformed=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_max_cookie=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_max_header_line=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_max_range_segment=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_max_url_param=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_method=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_param_length=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_pattern=dict(required=False, type="str"),
        constraint_exception_regex=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_url_param_length=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_exception_version=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_header_length_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_header_length_length=dict(required=False, type="int"),
        constraint_header_length_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_header_length_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_header_length_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_hostname_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_hostname_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_hostname_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_hostname_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_line_length_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_line_length_length=dict(required=False, type="int"),
        constraint_line_length_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_line_length_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_line_length_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_malformed_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_malformed_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_malformed_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_malformed_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_max_cookie_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_max_cookie_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_max_cookie_max_cookie=dict(required=False, type="int"),
        constraint_max_cookie_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_max_cookie_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_max_header_line_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_max_header_line_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_max_header_line_max_header_line=dict(required=False, type="int"),
        constraint_max_header_line_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_max_header_line_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_max_range_segment_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_max_range_segment_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_max_range_segment_max_range_segment=dict(required=False, type="int"),
        constraint_max_range_segment_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_max_range_segment_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_max_url_param_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_max_url_param_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_max_url_param_max_url_param=dict(required=False, type="int"),
        constraint_max_url_param_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_max_url_param_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_method_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_method_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_method_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_method_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_param_length_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_param_length_length=dict(required=False, type="int"),
        constraint_param_length_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_param_length_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_param_length_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_url_param_length_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_url_param_length_length=dict(required=False, type="int"),
        constraint_url_param_length_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_url_param_length_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_url_param_length_status=dict(required=False, type="str", choices=["disable", "enable"]),

        constraint_version_action=dict(required=False, type="str", choices=["allow", "block"]),
        constraint_version_log=dict(required=False, type="str", choices=["disable", "enable"]),
        constraint_version_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        constraint_version_status=dict(required=False, type="str", choices=["disable", "enable"]),
        method=dict(required=False, type="list"),
        method_default_allowed_methods=dict(required=False, type="str", choices=["delete",
                                                                                 "get",
                                                                                 "head",
                                                                                 "options",
                                                                                 "post",
                                                                                 "put",
                                                                                 "trace",
                                                                                 "others",
                                                                                 "connect"]),
        method_log=dict(required=False, type="str", choices=["disable", "enable"]),
        method_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        method_status=dict(required=False, type="str", choices=["disable", "enable"]),

        method_method_policy_address=dict(required=False, type="str"),
        method_method_policy_allowed_methods=dict(required=False, type="str", choices=["delete",
                                                                                       "get",
                                                                                       "head",
                                                                                       "options",
                                                                                       "post",
                                                                                       "put",
                                                                                       "trace",
                                                                                       "others",
                                                                                       "connect"]),
        method_method_policy_pattern=dict(required=False, type="str"),
        method_method_policy_regex=dict(required=False, type="str", choices=["disable", "enable"]),
        signature=dict(required=False, type="list"),
        signature_credit_card_detection_threshold=dict(required=False, type="int"),
        signature_disabled_signature=dict(required=False, type="str"),
        signature_disabled_sub_class=dict(required=False, type="str"),

        signature_custom_signature_action=dict(required=False, type="str", choices=["allow", "block", "erase"]),
        signature_custom_signature_case_sensitivity=dict(required=False, type="str", choices=["disable", "enable"]),
        signature_custom_signature_direction=dict(required=False, type="str", choices=["request", "response"]),
        signature_custom_signature_log=dict(required=False, type="str", choices=["disable", "enable"]),
        signature_custom_signature_name=dict(required=False, type="str"),
        signature_custom_signature_pattern=dict(required=False, type="str"),
        signature_custom_signature_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        signature_custom_signature_status=dict(required=False, type="str", choices=["disable", "enable"]),
        signature_custom_signature_target=dict(required=False, type="str", choices=["arg",
                                                                                    "arg-name",
                                                                                    "req-body",
                                                                                    "req-cookie",
                                                                                    "req-cookie-name",
                                                                                    "req-filename",
                                                                                    "req-header",
                                                                                    "req-header-name",
                                                                                    "req-raw-uri",
                                                                                    "req-uri",
                                                                                    "resp-body",
                                                                                    "resp-hdr",
                                                                                    "resp-status"]),

        signature_main_class_action=dict(required=False, type="str", choices=["allow", "block", "erase"]),
        signature_main_class_log=dict(required=False, type="str", choices=["disable", "enable"]),
        signature_main_class_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),
        signature_main_class_status=dict(required=False, type="str", choices=["disable", "enable"]),
        url_access=dict(required=False, type="list"),
        url_access_action=dict(required=False, type="str", choices=["bypass", "permit", "block"]),
        url_access_address=dict(required=False, type="str"),
        url_access_log=dict(required=False, type="str", choices=["disable", "enable"]),
        url_access_severity=dict(required=False, type="str", choices=["low", "medium", "high"]),

        url_access_access_pattern_negate=dict(required=False, type="str", choices=["disable", "enable"]),
        url_access_access_pattern_pattern=dict(required=False, type="str"),
        url_access_access_pattern_regex=dict(required=False, type="str", choices=["disable", "enable"]),
        url_access_access_pattern_srcaddr=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "name": module.params["name"],
        "external": module.params["external"],
        "extended-log": module.params["extended_log"],
        "comment": module.params["comment"],
        "address-list": {
            "blocked-address": module.params["address_list_blocked_address"],
            "blocked-log": module.params["address_list_blocked_log"],
            "severity": module.params["address_list_severity"],
            "status": module.params["address_list_status"],
            "trusted-address": module.params["address_list_trusted_address"],
        },
        "constraint": {
            "content-length": {
                "action": module.params["constraint_content_length_action"],
                "length": module.params["constraint_content_length_length"],
                "log": module.params["constraint_content_length_log"],
                "severity": module.params["constraint_content_length_severity"],
                "status": module.params["constraint_content_length_status"],
            },
            "exception": {
                "address": module.params["constraint_exception_address"],
                "content-length": module.params["constraint_exception_content_length"],
                "header-length": module.params["constraint_exception_header_length"],
                "hostname": module.params["constraint_exception_hostname"],
                "line-length": module.params["constraint_exception_line_length"],
                "malformed": module.params["constraint_exception_malformed"],
                "max-cookie": module.params["constraint_exception_max_cookie"],
                "max-header-line": module.params["constraint_exception_max_header_line"],
                "max-range-segment": module.params["constraint_exception_max_range_segment"],
                "max-url-param": module.params["constraint_exception_max_url_param"],
                "method": module.params["constraint_exception_method"],
                "param-length": module.params["constraint_exception_param_length"],
                "pattern": module.params["constraint_exception_pattern"],
                "regex": module.params["constraint_exception_regex"],
                "url-param-length": module.params["constraint_exception_url_param_length"],
                "version": module.params["constraint_exception_version"],
            },
            "header-length": {
                "action": module.params["constraint_header_length_action"],
                "length": module.params["constraint_header_length_length"],
                "log": module.params["constraint_header_length_log"],
                "severity": module.params["constraint_header_length_severity"],
                "status": module.params["constraint_header_length_status"],
            },
            "hostname": {
                "action": module.params["constraint_hostname_action"],
                "log": module.params["constraint_hostname_log"],
                "severity": module.params["constraint_hostname_severity"],
                "status": module.params["constraint_hostname_status"],
            },
            "line-length": {
                "action": module.params["constraint_line_length_action"],
                "length": module.params["constraint_line_length_length"],
                "log": module.params["constraint_line_length_log"],
                "severity": module.params["constraint_line_length_severity"],
                "status": module.params["constraint_line_length_status"],
            },
            "malformed": {
                "action": module.params["constraint_malformed_action"],
                "log": module.params["constraint_malformed_log"],
                "severity": module.params["constraint_malformed_severity"],
                "status": module.params["constraint_malformed_status"],
            },
            "max-cookie": {
                "action": module.params["constraint_max_cookie_action"],
                "log": module.params["constraint_max_cookie_log"],
                "max-cookie": module.params["constraint_max_cookie_max_cookie"],
                "severity": module.params["constraint_max_cookie_severity"],
                "status": module.params["constraint_max_cookie_status"],
            },
            "max-header-line": {
                "action": module.params["constraint_max_header_line_action"],
                "log": module.params["constraint_max_header_line_log"],
                "max-header-line": module.params["constraint_max_header_line_max_header_line"],
                "severity": module.params["constraint_max_header_line_severity"],
                "status": module.params["constraint_max_header_line_status"],
            },
            "max-range-segment": {
                "action": module.params["constraint_max_range_segment_action"],
                "log": module.params["constraint_max_range_segment_log"],
                "max-range-segment": module.params["constraint_max_range_segment_max_range_segment"],
                "severity": module.params["constraint_max_range_segment_severity"],
                "status": module.params["constraint_max_range_segment_status"],
            },
            "max-url-param": {
                "action": module.params["constraint_max_url_param_action"],
                "log": module.params["constraint_max_url_param_log"],
                "max-url-param": module.params["constraint_max_url_param_max_url_param"],
                "severity": module.params["constraint_max_url_param_severity"],
                "status": module.params["constraint_max_url_param_status"],
            },
            "method": {
                "action": module.params["constraint_method_action"],
                "log": module.params["constraint_method_log"],
                "severity": module.params["constraint_method_severity"],
                "status": module.params["constraint_method_status"],
            },
            "param-length": {
                "action": module.params["constraint_param_length_action"],
                "length": module.params["constraint_param_length_length"],
                "log": module.params["constraint_param_length_log"],
                "severity": module.params["constraint_param_length_severity"],
                "status": module.params["constraint_param_length_status"],
            },
            "url-param-length": {
                "action": module.params["constraint_url_param_length_action"],
                "length": module.params["constraint_url_param_length_length"],
                "log": module.params["constraint_url_param_length_log"],
                "severity": module.params["constraint_url_param_length_severity"],
                "status": module.params["constraint_url_param_length_status"],
            },
            "version": {
                "action": module.params["constraint_version_action"],
                "log": module.params["constraint_version_log"],
                "severity": module.params["constraint_version_severity"],
                "status": module.params["constraint_version_status"],
            },
        },
        "method": {
            "default-allowed-methods": module.params["method_default_allowed_methods"],
            "log": module.params["method_log"],
            "severity": module.params["method_severity"],
            "status": module.params["method_status"],
            "method-policy": {
                "address": module.params["method_method_policy_address"],
                "allowed-methods": module.params["method_method_policy_allowed_methods"],
                "pattern": module.params["method_method_policy_pattern"],
                "regex": module.params["method_method_policy_regex"],
            },
        },
        "signature": {
            "credit-card-detection-threshold": module.params["signature_credit_card_detection_threshold"],
            "disabled-signature": module.params["signature_disabled_signature"],
            "disabled-sub-class": module.params["signature_disabled_sub_class"],
            "custom-signature": {
                "action": module.params["signature_custom_signature_action"],
                "case-sensitivity": module.params["signature_custom_signature_case_sensitivity"],
                "direction": module.params["signature_custom_signature_direction"],
                "log": module.params["signature_custom_signature_log"],
                "name": module.params["signature_custom_signature_name"],
                "pattern": module.params["signature_custom_signature_pattern"],
                "severity": module.params["signature_custom_signature_severity"],
                "status": module.params["signature_custom_signature_status"],
                "target": module.params["signature_custom_signature_target"],
            },
            "main-class": {
                "action": module.params["signature_main_class_action"],
                "log": module.params["signature_main_class_log"],
                "severity": module.params["signature_main_class_severity"],
                "status": module.params["signature_main_class_status"],
            },
        },
        "url-access": {
            "action": module.params["url_access_action"],
            "address": module.params["url_access_address"],
            "log": module.params["url_access_log"],
            "severity": module.params["url_access_severity"],
            "access-pattern": {
                "negate": module.params["url_access_access_pattern_negate"],
                "pattern": module.params["url_access_access_pattern_pattern"],
                "regex": module.params["url_access_access_pattern_regex"],
                "srcaddr": module.params["url_access_access_pattern_srcaddr"],
            }
        }
    }

    list_overrides = ['address-list', 'constraint', 'method', 'signature', 'url-access']
    for list_variable in list_overrides:
        override_data = list()
        try:
            override_data = module.params[list_variable]
        except BaseException:
            pass
        try:
            if override_data:
                del paramgram[list_variable]
                paramgram[list_variable] = override_data
        except BaseException:
            pass

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    password = module.params["password"]
    username = module.params["username"]
    if host is None or username is None or password is None:
        module.fail_json(msg="Host and username and password are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])

    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    results = fmgr_waf_profile_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
