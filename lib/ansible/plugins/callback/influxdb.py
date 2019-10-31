# (c) 2019, Jason Neurohr, <jason@jasonneurohr.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: influxdb
    callback_type: aggregate
    requirements:
      - whitelist in configuration
    short_description: Adds play duration to InfluxDB
    version_added: "2.10"
    description:
        - This callback captures the total play duration and submits it to InfluxDB.
    options:
      influxdb_addr:
        required: False
        description: InfluxDB address in the form FQDN, FQDN:PORT, IP, or IP:PORT
        env:
          - name: INFLUXDB_ADDR
        ini:
          - section: callback_influxdb
            key: influxdb_addr
      influxdb_db:
        required: False
        description: InfluxDB database name
        env:
          - name: INFLUXDB_DB
        ini:
          - section: callback_influxdb
            key: influxdb_db
      influxdb_username:
        required: False
        description: InfluxDB database username name
        env:
          - name: INFLUXDB_USERNAME
        ini:
          - section: callback_influxdb
            key: influxdb_username
      influxdb_password:
        required: False
        description: InfluxDB database password
        env:
          - name: INFLUXDB_PASSWORD
        ini:
          - section: callback_influxdb
            key: influxdb_password
      influxdb_tls:
        required: False
        description: use TLS to connect to InfluxDB. (HTTPS)
        env:
          - name: INFLUXDB_TLS
        ini:
          - section: callback_influxdb
            key: influxdb_tls
        default: True
        type: bool
      influxdb_validate_cert:
        required: False
        description: validate the TLS certificate of the InfluxDB server. (For HTTPS URLs)
        env:
          - name: INFLUXDB_VALIDATE_CERT
        ini:
          - section: callback_influxdb
            key: influxdb_validate_cert
        default: True
        type: bool

'''
import os

from ansible import context
from datetime import datetime

from ansible.module_utils._text import to_text
from ansible.plugins.callback import CallbackBase
from ansible.module_utils.urls import open_url


class CallbackModule(CallbackBase):
    """
    This callback module adds play duration to InfluxDB
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'influx'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        self.start_time = datetime.utcnow()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.influxdb_addr = self.get_option('influxdb_addr')
        self.influxdb_db = self.get_option('influxdb_db')
        self.influxdb_username = self.get_option('influxdb_username')
        self.influxdb_password = self.get_option('influxdb_password')
        self.influxdb_tls = self.get_option('influxdb_tls')
        self.validate_certs = self.get_option('influxdb_validate_cert')

        if self.influxdb_addr is None:
            self.disabled = True
            self._display.warning('InfluxDB address was not provided. The '
                                  'InfluxDB address can be provided using '
                                  'the `INFLUXDB_ADDR` environment '
                                  'variable. Telemetry data not captured.')

        if self.influxdb_db is None:
            self.disabled = True
            self._display.warning('InfluxDB database name was not provided. The '
                                  'InfluxDB database name can be provided using '
                                  'the `INFLUXDB_DB` environment '
                                  'variable. Telemetry data not captured.')

        if str(self.influxdb_tls).lower() == 'true':
            self.influx_constructed_url = 'https://%s/write?db=%s' % (self.influxdb_addr, self.influxdb_db)

        elif str(self.influxdb_tls).lower() == 'false':
            self.influx_constructed_url = 'http://%s/write?db=%s' % (self.influxdb_addr, self.influxdb_db)

        elif str(self.influxdb_tls).lower() != 'true' or self.influxdb_tls is None:
            self._display.warning(u'Environment variable INFLUXDB_TLS is not set or is '
                                  'invalid. Proceeding using TLS')
            self.influx_constructed_url = 'https://%s/write?db=%s' % (self.influxdb_addr, self.influxdb_db)

        if str(self.validate_certs).lower() == 'true':
            self.validate_certs = True

        elif str(self.validate_certs).lower() == 'false':
            self.validate_certs = False

        elif str(self.validate_certs).lower() != 'true' or self.validate_certs is None:
            self._display.warning(u'Environment variable INFLUXDB_VALIDATE_CERT is not set or is '
                                  'invalid. Proceeding using TLS')
            self.validate_certs = True

    def send_msg(self, role_name, duration):
        payload = 'role_duration,role=%s duration=%s' % (self.playbook_name, duration)

        self._display.debug(payload)
        self._display.debug(self.influx_constructed_url)
        try:
            if self.influxdb_username is not None and self.influxdb_password is not None:
                response = open_url(self.influx_constructed_url, data=payload, validate_certs=self.validate_certs,
                                    url_username=self.influxdb_username, url_password=self.influxdb_password)
                return response.read()

            response = open_url(self.influx_constructed_url, data=payload, validate_certs=self.validate_certs)
            return response.read()
        except Exception as e:
            self._display.warning(u'Could not submit telemetry data to InfluxDB: %s' % to_text(e))

    def playbook_on_stats(self, stats):
        self.v2_playbook_on_stats(stats)

    def v2_playbook_on_stats(self, stats):
        end_time = datetime.utcnow()
        runtime = end_time - self.start_time
        self.send_msg(role_name=self.playbook_name, duration=runtime.seconds)

    def v2_playbook_on_start(self, playbook):
        self.playbook_name = os.path.basename(playbook._basedir)
