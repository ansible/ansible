# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import missing_required_lib

REQUESTS_IMP_ERR = None
try:
    import requests.exceptions
    HAS_REQUESTS = True
except ImportError:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_REQUESTS = False

INFLUXDB_IMP_ERR = None
try:
    from influxdb import InfluxDBClient
    from influxdb import __version__ as influxdb_version
    from influxdb import exceptions
    HAS_INFLUXDB = True
except ImportError:
    INFLUXDB_IMP_ERR = traceback.format_exc()
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
        self.database_name = self.params.get('database_name')

    def check_lib(self):
        if not HAS_REQUESTS:
            self.module.fail_json(msg=missing_required_lib('requests'), exception=REQUESTS_IMP_ERR)

        if not HAS_INFLUXDB:
            self.module.fail_json(msg=missing_required_lib('influxdb'), exception=INFLUXDB_IMP_ERR)

    @staticmethod
    def influxdb_argument_spec():
        return dict(
            hostname=dict(type='str', default='localhost'),
            port=dict(type='int', default=8086),
            username=dict(type='str', default='root', aliases=['login_username']),
            password=dict(type='str', default='root', no_log=True, aliases=['login_password']),
            ssl=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
            timeout=dict(type='int'),
            retries=dict(type='int', default=3),
            proxies=dict(type='dict', default={}),
            use_udp=dict(type='bool', default=False),
            udp_port=dict(type='int', default=4444),
        )

    def connect_to_influxdb(self):
        args = dict(
            host=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database_name,
            ssl=self.params['ssl'],
            verify_ssl=self.params['validate_certs'],
            timeout=self.params['timeout'],
            use_udp=self.params['use_udp'],
            udp_port=self.params['udp_port'],
            proxies=self.params['proxies'],
        )
        influxdb_api_version = tuple(influxdb_version.split("."))
        if influxdb_api_version >= ('4', '1', '0'):
            # retries option is added in version 4.1.0
            args.update(retries=self.params['retries'])

        return InfluxDBClient(**args)
