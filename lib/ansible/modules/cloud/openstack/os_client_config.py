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
version_added: "2.0"
requirements: [ os-client-config ]
author: "Monty Taylor (@emonty)"
'''

EXAMPLES = '''
# Get list of clouds that do not support security groups
- os-client-config:
- debug: var={{ item }}
  with_items: "{{ openstack.clouds|rejectattr('secgroup_source', 'none')|list() }}"
'''


def main():
    module = AnsibleModule({})
    p = module.params

    try:
        config = os_client_config.OpenStackConfig()
        clouds = []
        for cloud in config.get_all_clouds():
            cloud.config['name'] = cloud.name
            clouds.append(cloud.config)
        module.exit_json(ansible_facts=dict(openstack=dict(clouds=clouds)))
    except exceptions.OpenStackConfigException as e:
        module.fail_json(msg=str(e)) 

# import module snippets
from ansible.module_utils.basic import *

main()
