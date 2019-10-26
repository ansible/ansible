# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Cisco and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  url:
    description: NSO JSON-RPC URL, http://localhost:8080/jsonrpc
    type: str
    required: true
  username:
    description: NSO username
    type: str
    required: true
  password:
    description: NSO password
    type: str
    required: true
  timeout:
    description: JSON-RPC request timeout in seconds
    type: int
    default: 300
    version_added: "2.6"
  validate_certs:
    description: When set to true, validates the SSL certificate of NSO when
                 using SSL
    type: bool
    required: false
    default: false
'''
