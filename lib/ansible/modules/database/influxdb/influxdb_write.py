#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: influxdb_write
short_description: Write json data points into InfluxDB
description:
    - Write json data points into InfluxDB
version_added: 2.5
author: "René Moser (@resmo)"
requirements:
  - "python >= 2.6"
  - "influxdb >= 0.9"
options:
  hostname:
    description:
      - The hostname or IP address on which InfluxDB server is listening.
    required: true
  username:
    description:
      - Username that will be used to authenticate against InfluxDB server.
    default: root
  password:
    description:
      - Password that will be used to authenticate against InfluxDB server.
    default: root
  port:
    description:
      - The port on which InfluxDB server is listening.
    default: 8086
  database_name:
    description:
      - Name of the database where the points are written into.
    required: true
  data_points:
    description:
      - Data points to write into the database in JSON format.
    required: true
'''

EXAMPLES = '''

# Example influxdb_database command from Ansible Playbooks
- name: Write points into database
  influxdb_write:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"
      data_points: "{{ data_dict }}"
'''

RETURN = '''
# only defaults
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.database.influxdb import (
    influxdb_argument_spec,
    AnsibleInfluxDB
)


class AnsibleInfluxDBWrite(AnsibleInfluxDB):

    def write_data_point(self, data_points):
        client = self.connect()
        client.write_points(data_points)

        try:
            client.write_points(data_points)
        except Exception as e:
            self.module.fail_json(msg=to_native(e))


def main():
    argument_spec = influxdb_argument_spec()
    argument_spec.update(
        data_points=dict(type='list')
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
