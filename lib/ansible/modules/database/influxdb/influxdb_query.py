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
module: influxdb_query
short_description: Query data points from InfluxDB
description:
  - Query data points from InfluxDB.
version_added: 2.5
author: "René Moser (@resmo)"
requirements:
  - "python >= 2.6"
  - "influxdb >= 0.9"
options:
  query:
    description:
      - Query to be executed.
    required: true
    type: str
  database_name:
    description:
      - Name of the database.
    required: true
    type: str
extends_documentation_fragment: influxdb
'''

EXAMPLES = r'''
- name: Query connections
  influxdb_query:
    hostname: "{{ influxdb_ip_address }}"
    database_name: "{{ influxdb_database_name }}"
    query: "select mean(value) from connections"
  register: connection

- name: Query connections with tags filters
  influxdb_query:
    hostname: "{{ influxdb_ip_address }}"
    database_name: "{{ influxdb_database_name }}"
    query: "select mean(value) from connections where region='zue01' and host='server01'"
  register: connection

- name: Print results from the query
  debug:
    var: connection.query_results
'''

RETURN = r'''
query_results:
  description: Result from the query
  returned: success
  type: list
  sample:
    - mean: 1245.5333333333333
      time: "1970-01-01T00:00:00Z"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.influxdb import InfluxDb


class AnsibleInfluxDBRead(InfluxDb):

    def read_by_query(self, query):
        client = self.connect_to_influxdb()
        try:
            rs = client.query(query)
            if rs:
                return list(rs.get_points())
        except Exception as e:
            self.module.fail_json(msg=to_native(e))


def main():
    argument_spec = InfluxDb.influxdb_argument_spec()
    argument_spec.update(
        query=dict(type='str', required=True),
        database_name=dict(required=True, type='str'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    influx = AnsibleInfluxDBRead(module)
    query = module.params.get('query')
    results = influx.read_by_query(query)
    module.exit_json(changed=True, query_results=results)


if __name__ == '__main__':
    main()
