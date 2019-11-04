#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communications Cloud Infrastructure Services
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
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException

def main():
    """
    Main function
    :returns: IP Address List Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=False, type='str'),
            service_plan=dict(required=False, type='str'),
            day=dict(required=False, default=None, type='str'),
            start_hour=dict(required=False, default=None, type='str'),
            slots_available=dict(required=False, default=True, type='bool'),
            type=dict(required=False, default='window', type='str')
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    snapshot_type = module.params.get('type')
    return_data = return_object('snapshot_info')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTMCPClient(credentials, module.params.get('region'))

    try:
        if snapshot_type == 'window':
            result = client.list_snapshot_windows(
                                                  module.params.get('datacenter'),
                                                  module.params.get('service_plan'),
                                                  module.params.get('day'),
                                                  module.params.get('start_hour'),
                                                  module.params.get('slots_available')
                                                 )
        if snapshot_type == 'plan':
            result = client.list_snapshot_service_plans(
                                                        module.params.get('service_plan'),
                                                        module.params.get('slots_available')
                                                       )
        if result:
            return_data['snapshot_info'] = result
            return_data['count'] = len(return_data.get('snapshot_info'))
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not retrieve a list of Snapshot info - {0}'.format(e))

    module.exit_json(data=return_data)


if __name__ == '__main__':
    main()
