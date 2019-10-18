#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloud_init_data_facts
short_description: Retrieve facts of cloud-init.
description:
  - Gathers facts by reading the status.json and result.json of cloud-init.
version_added: 2.6
author: René Moser (@resmo)
options:
  filter:
    description:
      - Filter facts
    choices: [ status, result ]
notes:
  - See http://cloudinit.readthedocs.io/ for more information about cloud-init.
'''

EXAMPLES = '''
- name: Gather all facts of cloud init
  cloud_init_data_facts:
  register: result

- debug:
    var: result

- name: Wait for cloud init to finish
  cloud_init_data_facts:
    filter: status
  register: res
  until: "res.cloud_init_data_facts.status.v1.stage is defined and not res.cloud_init_data_facts.status.v1.stage"
  retries: 50
  delay: 5
'''

RETURN = '''
---
cloud_init_data_facts:
  description: Facts of result and status.
  returned: success
  type: dict
  sample: '{
    "status": {
        "v1": {
            "datasource": "DataSourceCloudStack",
            "errors": []
        },
    "result": {
        "v1": {
            "datasource": "DataSourceCloudStack",
            "init": {
                "errors": [],
                "finished": 1522066377.0185432,
                "start": 1522066375.2648022
            },
            "init-local": {
                "errors": [],
                "finished": 1522066373.70919,
                "start": 1522066373.4726632
            },
            "modules-config": {
                "errors": [],
                "finished": 1522066380.9097016,
                "start": 1522066379.0011985
            },
            "modules-final": {
                "errors": [],
                "finished": 1522066383.56594,
                "start": 1522066382.3449218
            },
            "stage": null
        }
    }'
'''

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text


CLOUD_INIT_PATH = "/var/lib/cloud/data/"


def gather_cloud_init_data_facts(module):
    res = {
        'cloud_init_data_facts': dict()
    }

    for i in ['result', 'status']:
        filter = module.params.get('filter')
        if filter is None or filter == i:
            res['cloud_init_data_facts'][i] = dict()
            json_file = CLOUD_INIT_PATH + i + '.json'

            if os.path.exists(json_file):
                f = open(json_file, 'rb')
                contents = to_text(f.read(), errors='surrogate_or_strict')
                f.close()

                if contents:
                    res['cloud_init_data_facts'][i] = module.from_json(contents)
    return res


def main():
    module = AnsibleModule(
        argument_spec=dict(
            filter=dict(choices=['result', 'status']),
        ),
        supports_check_mode=True,
    )

    facts = gather_cloud_init_data_facts(module)
    result = dict(changed=False, ansible_facts=facts, **facts)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
