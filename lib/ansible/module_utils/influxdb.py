# -*- coding: utf-8 -*-
# Copyright: (c) 2017, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import requests.exceptions
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from influxdb import InfluxDBClient
    from influxdb import exceptions
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False


class InfluxDb():
    def __init__(self, module):
        self.module = module
        self.params = self.module.params
        self.check_lib()
        self.hostname = self.params['hostname']
        self.port = self.params['port']
        self.username = self.params['username']
        self.password = self.params['password']
        self.database_name = self.params['database_name']

    def check_lib(self):
        if not HAS_REQUESTS:
            self.module.fail_json(msg='This module requires "requests" module.')

        if not HAS_INFLUXDB:
            self.module.fail_json(msg='This module requires influxdb python package.')

    @staticmethod
    def influxdb_argument_spec():
        return dict(
            hostname=dict(required=True, type='str'),
            port=dict(default=8086, type='int'),
            username=dict(default='root', type='str'),
            password=dict(default='root', type='str', no_log=True),
            database_name=dict(required=True, type='str'),
            ssl=dict(default=False, type='bool'),
            validate_certs=dict(default=True, type='bool'),
            timeout=dict(type='int'),
            retries=dict(default=3, type='int'),
            proxies=dict(default={}, type='dict'),
            use_udp=dict(default=False, type='bool'),
            udp_port=dict(type=int)
        )

    def connect_to_influxdb(self):
        return InfluxDBClient(
            host=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database_name,
            ssl=self.params['ssl'],
            verify_ssl=self.params['validate_certs'],
            timeout=self.params['timeout'],
            retries=self.params['retries'],
            use_udp=self.params['use_udp'],
            udp_port=self.params['udp_port'],
            proxies=self.params['proxies'],
        )
