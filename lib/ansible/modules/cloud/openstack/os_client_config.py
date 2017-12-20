#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
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

try:
    import os_client_config
    from os_client_config import exceptions
    HAS_OS_CLIENT_CONFIG = True
except ImportError:
    HAS_OS_CLIENT_CONFIG = False

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(argument_spec=dict(
        clouds=dict(required=False, type='list', default=[]),
    ))

    if not HAS_OS_CLIENT_CONFIG:
        module.fail_json(msg='os-client-config is required for this module')

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


if __name__ == "__main__":
    main()
