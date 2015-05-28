#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

import os_client_config
from os_client_config import exceptions

DOCUMENTATION = '''
---
module: os_client_config
short_description: Get OpenStack Client config
description:
  - Get I(openstack) client config data from clouds.yaml or environment
options:
   regions:
     description:
        - Include regions in the returned data
     required: false
     default: 'yes'
version_added: "2.0"
requirements: [ os-client-config ]
author: Monty Taylor
'''

EXAMPLES = '''
# Inject facts about OpenStack clouds
- os-client-config
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            regions = dict(default=True, required=False, type='bool'),
            action  = dict(default='list', choices=['list']),
        ),
    )
    p = module.params

    try:
        config = os_client_config.OpenStackConfig()
        clouds = {}
        for cloud in config.get_all_clouds():
            if p['regions']:
                cloud_region = clouds.get(cloud.name, {})
                cloud_region[cloud.region] = cloud.config
                clouds[cloud.name] = cloud_region
            else:
                clouds[cloud.name] = cloud.config
        module.exit_json(clouds=clouds)
    except exceptions.OpenStackConfigException as e:
        module.fail_json(msg=str(e)) 

# import module snippets
from ansible.module_utils.basic import *

main()
