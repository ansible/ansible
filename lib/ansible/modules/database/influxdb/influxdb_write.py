#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: influxdb_write
short_description: Write data points into InfluxDB.
description:
  - Write data points into InfluxDB.
version_added: 2.5
author: "René Moser (@resmo)"
requirements:
  - "python >= 2.6"
  - "influxdb >= 0.9"
options:
  data_points:
    description:
      - Data points as dict to write into the database.
    required: true
  database_name:
    description:
      - Name of the database.
    required: true
extends_documentation_fragment: influxdb
'''

EXAMPLES = r'''
- name: Write points into database
  influxdb_write:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"
      data_points:
        - measurement: connections
          tags:
            host: server01
            region: us-west
          time: "{{ ansible_date_time.iso8601 }}"
          fields:
            value: 2000
        - measurement: connections
          tags:
            host: server02
            region: us-east
          time: "{{ ansible_date_time.iso8601 }}"
          fields:
            value: 3000
'''

RETURN = r'''
# only defaults
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.influxdb import InfluxDb


class AnsibleInfluxDBWrite(InfluxDb):

    def write_data_point(self, data_points):
        client = self.connect_to_influxdb()
        client.write_points(data_points)

        try:
            client.write_points(data_points)
        except Exception as e:
            self.module.fail_json(msg=to_native(e))


def main():
    argument_spec = InfluxDb.influxdb_argument_spec()
    argument_spec.update(
        data_points=dict(required=True, type='list'),
        database_name=dict(required=True, type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    influx = AnsibleInfluxDBWrite(module)
    data_points = module.params.get('data_points')
    influx.write_data_point(data_points)
    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
