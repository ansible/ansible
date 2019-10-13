#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2019, Antoine Barbare <antoinebarbare@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: scaleway_rdb_info
short_description: Gather information about the Scaleway Relational Databases (rdb) available.
description:
  - Gather information about the Scaleway Relational Databases.
version_added: "2.10"
author:
  - "Antoine Barbare (@abarbare)"
extends_documentation_fragment: scaleway
options:
  region:
    description:
      - Scaleway region to use (for example C(fr-par)).
    required: true
    choices:
      - fr-par
      - nl-ams
    type: str
  version:
    description;
      - Scaleway API version to use (for example C(v1)).
    required: false
    default: v1
    type: str
'''

EXAMPLES = r'''
- name: Gather Scaleway Relational Databases information
  scaleway_rdb_info:
    region: fr-par
  register: result

- debug:
    msg: "{{ result.scaleway_rdb_info }}"
'''

RETURN = r'''
---
scaleway_rdb_info:
  description: Response from Scaleway API
  returned: success
  type: complex
  contains:
    "scaleway_rdb_info": [
      {
        "id": "83b0d051-90b0-4878-bffa-de16e713dbd2",
        "name": "my-database",
        "organization_id": "3f709602-5e6c-4619-b80c-e324324324af",
        "status": "ready",
        "engine": "PostgreSQL-11",
        "endpoint": {
          "ip": "51.159.27.165",
          "port": 55282,
          "name": null
        },
        "tags": [
          "postgresql"
        ],
        "settings": [],
        "backup_schedule": {
          "frequency": 24,
          "retention": 7,
          "disabled": false
        },
        "is_ha_cluster": true,
        "read_replicas": [],
        "node_type": "db-gp-xs",
        "volume": {
          "type": "lssd",
          "size": "135000000000"
        },
        "created_at": "2019-10-09T12:49:35.505549Z",
        "region": "fr-par"
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import (
    Scaleway,
    ScalewayException,
    scaleway_argument_spec,
    SCALEWAY_ENDPOINT,
    SCALEWAY_REGIONS,
)


class ScalewayRdbInfo(Scaleway):

    def __init__(self, module):
        super(ScalewayRdbInfo, self).__init__(module)
        self.name = 'instances'

        region = module.params["region"]
        version = module.params["version"]
        self.module.params['api_url'] = "%s/rdb/%s/regions/%s" % (SCALEWAY_ENDPOINT, version, region)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        region=dict(required=True, choices=SCALEWAY_REGIONS),
        version=dict(required=False, type='str', default='v1')
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(
            scaleway_rdb_info=ScalewayRdbInfo(module).get_resources()
        )
    except ScalewayException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()
