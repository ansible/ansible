#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Ken Sinfield <ken.sinfield@cis.ntt.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}
DOCUMENTATION = '''
---
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Create a Preview Server in the same datacenter
    ntt_mcp_user_info:
      region: na
      datacenter: NA9
      id: 112b7faa-ffff-ffff-ffff-dc273085cbe4
      server: My_Preview_Server
      description: A new server from a snapshot
      connect_network: True

  - name: Create a Replicated Preview Server in a remote datacenter
    ntt_mcp_snapshot_preview:
      region: na
      datacenter: NA12
      network_domain: My_Remote_CND
      id: 222b7faa-ffff-ffff-ffff-dc273085cbe5
      server: My_Replicated_Server
      description: A new server from a replicated snapshot
      connect_network: True
      preserve_mac: True
      networks:
        - nic: 0
          vlan: my_remote_vlan
          privateIpv4: 10.0.0.100
        - nic: 1
          vlan: my_other_remote_vlan

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException

def main():
    """
    Main function
    :returns: IP Address List Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            username=dict(default=None, type='str'),
            country_code=dict(default=None, type='str'),
            phone_number=dict(default=None, type='str'),
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    try:
        client = NTTMCPClient(credentials, module.params.get('region'))
    except NTTMCPAPIException as e:
        module.fail_json(msg=e.msg)

    try:

        client.update_user(username=module.params.get('username'),
                         country_code=module.params.get('country_code'),
                         phone_number=module.params.get('phone_number'))
        module.exit_json(msg='The user was successfully udpated')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not update the user - {0}'.format(e))


if __name__ == '__main__':
    main()
