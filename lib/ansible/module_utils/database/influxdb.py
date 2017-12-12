# -*- coding: utf-8 -*-
# Copyright (c) 2016, Kamil Szczygiel <kamil.szczygiel () intel.com>
# Copyright (c) 2017, René Moser <mail@renemoser.net>

# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    from influxdb import InfluxDBClient
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False


def influxdb_argument_spec():
    return dict(
        hostname=dict(required=True, type='str'),
        port=dict(default=8086, type='int'),
        username=dict(default='root', type='str'),
        password=dict(default='root', type='str', no_log=True),
        database_name=dict(required=True, type='str')
    )


class AnsibleInfluxDB:

    def __init__(self, module):
        self.module = module
        self.influxdb_client = None

        if not HAS_INFLUXDB:
            module.fail_json(msg='influxdb python package is required for this module')

    def connect(self):
        if self.influxdb_client is None:
            self.influxdb_client = InfluxDBClient(
                host=self.module.params['hostname'],
                port=self.module.params['port'],
                username=self.module.params['username'],
                password=self.module.params['password'],
                database=self.module.params['database_name']
            )
        return self.influxdb_client
