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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_client_config
short_description: Get OpenStack Client config
description:
  - Get I(openstack) client config data from clouds.yaml or environment
version_added: "2.0"
notes:
  - Facts are placed in the C(openstack.clouds) variable.
options:
   clouds:
     description:
        - List of clouds to limit the return list to. No value means return
          information on all configured clouds
     required: false
     default: []
requirements: [ os-client-config ]
author: "Monty Taylor (@emonty)"
'''

EXAMPLES = '''
- name: Get list of clouds that do not support security groups
  os_client_config:

- debug:
    var: "{{ item }}"
  with_items: "{{ openstack.clouds | rejectattr('secgroup_source', 'none') | list }}"

- name: Get the information back just about the mordred cloud
  os_client_config:
    clouds:
      - mordred
'''

import os_client_config
from os_client_config import exceptions


def main():
    module = AnsibleModule(argument_spec=dict(
        clouds=dict(required=False, type='list', default=[]),
    ))
    p = module.params

    try:
        config = os_client_config.OpenStackConfig()
        clouds = []
        for cloud in config.get_all_clouds():
            if not p['clouds'] or cloud.name in p['clouds']:
                cloud.config['name'] = cloud.name
                clouds.append(cloud.config)
        module.exit_json(ansible_facts=dict(openstack=dict(clouds=clouds)))
    except exceptions.OpenStackConfigException as e:
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *

if __name__ == "__main__":
    main()
