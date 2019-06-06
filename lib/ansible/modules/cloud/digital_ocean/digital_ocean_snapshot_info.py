#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: digital_ocean_snapshot_info
short_description: Gather information about DigitalOcean Snapshot
description:
    - This module can be used to gather information about snapshot information based upon provided values such as droplet, volume and snapshot id.
    - This module was called C(digital_ocean_snapshot_facts) before Ansible 2.9. The usage did not change.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
options:
  snapshot_type:
    description:
     - Specifies the type of snapshot information to be retrived.
     - If set to C(droplet), then information are gathered related to snapshots based on Droplets only.
     - If set to C(volume), then information are gathered related to snapshots based on volumes only.
     - If set to C(by_id), then information are gathered related to snapshots based on snapshot id only.
     - If not set to any of the above, then information are gathered related to all snapshots.
    default: 'all'
    choices: [ 'all', 'droplet', 'volume', 'by_id']
    required: false
  snapshot_id:
    description:
     - To retrieve information about a snapshot, please specify this as a snapshot id.
     - If set to actual snapshot id, then information are gathered related to that particular snapshot only.
     - This is required parameter, if C(snapshot_type) is set to C(by_id).
    required: false
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather information about all snapshots
  digital_ocean_snapshot_info:
    snapshot_type: all
    oauth_token: "{{ oauth_token }}"

- name: Gather information about droplet snapshots
  digital_ocean_snapshot_info:
    snapshot_type: droplet
    oauth_token: "{{ oauth_token }}"

- name: Gather information about volume snapshots
  digital_ocean_snapshot_info:
    snapshot_type: volume
    oauth_token: "{{ oauth_token }}"

- name: Gather information about snapshot by snapshot id
  digital_ocean_snapshot_info:
    snapshot_type: by_id
    snapshot_id: 123123123
    oauth_token: "{{ oauth_token }}"

- name: Get information about snapshot named big-data-snapshot1
  digital_ocean_snapshot_info:
  register: resp_out
- set_fact:
    snapshot_id: "{{ item.id }}"
  loop: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?name=='big-data-snapshot1']"
- debug: var=snapshot_id

'''


RETURN = '''
data:
    description: DigitalOcean snapshot information
    returned: success
    type: list
    sample: [
        {
            "id": "4f60fc64-85d1-11e6-a004-000f53315871",
            "name": "big-data-snapshot1",
            "regions": [
                "nyc1"
            ],
            "created_at": "2016-09-28T23:14:30Z",
            "resource_id": "89bcc42f-85cf-11e6-a004-000f53315871",
            "resource_type": "volume",
            "min_disk_size": 10,
            "size_gigabytes": 0
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    snapshot_type = module.params['snapshot_type']

    rest = DigitalOceanHelper(module)

    base_url = 'snapshots?'
    snapshot = []

    if snapshot_type == 'by_id':
        base_url += "/{0}".format(module.params.get('snapshot_id'))
        response = rest.get(base_url)
        status_code = response.status_code

        if status_code != 200:
            module.fail_json(msg="Failed to fetch snapshot information due to error : %s" % response.json['message'])

        snapshot.extend(response.json["snapshot"])
    else:
        if snapshot_type == 'droplet':
            base_url += "resource_type=droplet&"
        elif snapshot_type == 'volume':
            base_url += "resource_type=volume&"

        snapshot = rest.get_paginated_data(base_url=base_url, data_key_name='snapshots')
    module.exit_json(changed=False, data=snapshot)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        snapshot_type=dict(type='str',
                           required=False,
                           choices=['all', 'droplet', 'volume', 'by_id'],
                           default='all'),
        snapshot_id=dict(type='str',
                         required=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ['snapshot_type', 'by_id', ['snapshot_id']],
        ],
    )
    if module._name == 'digital_ocean_snapshot_facts':
        module.deprecate("The 'digital_ocean_snapshot_facts' module has been renamed to 'digital_ocean_snapshot_info'", version='2.13')

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
