# Copyright: (c) 2018, Johannes Brunswicker <johannes.brunswicker@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    callback: influxdb
    type: notification
    requirements:
      - "python >= 2.6"
      - "influxdb >= 0.9"
    short_description: create influxdb datapoint per tasks, role, play and host
    description:
      - This callback module will track and save the duration of ansible tasks per hosts, role and play. It will write
        the data into an influxdb database which makes it possible to create dashboards to pinpoint exactly which
        task/role/play is taking the longest.
      - To make the most out of the data we recommend to name all tasks and plays. The names will be provided as tags
        in the influxdb
    author:
      - Johannes Brunswicker (@MatrixCrawler)
    version_added: "2.8"
    options:
      influx_host:
        description: The hostname of the influxDB.
        required: True
        env:
          - name: INFLUX_HOST
        ini:
          - section: callback_influxdb
            key: influx_host
      influx_port:
        description: The port of the influxDB.
        required: False
        type: int
        default: 8086
        env:
          - name: INFLUX_PORT
        ini:
          - section: callback_influxdb
            key: influx_port
      influx_database:
        description: The database name in the influxDB in which the measurement shall be stored. Has to exist.
        required: True
        env:
          - name: INFLUX_DATABASE
        ini:
          - section: callback_influxdb
            key: influx_database
      influx_username:
        description: The username for the influxDB.
        required: True
        env:
          - name: INFLUX_USERNAME
        ini:
          - section: callback_influxdb
            key: influx_username
      influx_password:
        description: The password for the influxDB.
        required: True
        env:
          - name: INFLUX_PASSWORD
        ini:
          - section: callback_influxdb
            key: influx_password
      influx_use_ssl:
        description: Whether to use SSL or not.
        required: False
        type: bool
        default: False
        env:
          - name: INFLUX_USE_SSL
        ini:
          - section: callback_influxdb
            key: influx_use_ssl
      influx_verify_ssl:
        description: Whether to verify the SSL Certificate or not.
        required: False
        type: bool
        default: True
        env:
          - name: INFLUX_VERIFY_SSL
        ini:
          - section: callback_influxdb
            key: influx_verify_ssl
      influx_timeout:
        description: The timeout for the influxDB connection in seconds.
        required: False
        type: int
        default: 5
        env:
          - name: INFLUX_TIMEOUT
        ini:
          - section: callback_influxdb
            key: influx_timeout
      influx_retries:
        description: The retries for the influxDB action.
        required: False
        type: int
        default: 3
        env:
          - name: INFLUX_RETRIES
        ini:
          - section: callback_influxdb
            key: influx_retries
      influx_measurement_name:
        description: The name for the measurement stored into influxDB.
        required: False
        type: str
        default: ansible_plays
        env:
          - name: INFLUX_MEASUREMENT_NAME
        ini:
          - section: callback_influxdb
            key: influx_measurement_name
      influx_digest_write:
        description:
          - Whether to collect all data points before sending them to the influxDB.
          - Setting this to true will collect all data and send them only on playbook_stats. Leaving this on False will
            send data after every task. This could affect your overall performance.
        required: False
        type: bool
        default: False
        env:
          - name: INFLUX_DIGEST_WRITE
        ini:
          - section: callback_influxdb
            key: influx_digest_write
'''

import time
from datetime import datetime

from ansible.plugins.callback import CallbackBase

try:
    from influxdb import InfluxDBClient
    from influxdb import __version__ as influxdb_version
    from influxdb import exceptions

    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'influxdb'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None, options=None):
        super(CallbackModule, self).__init__(display=display, options=options)
        if not HAS_INFLUXDB:
            self._display.warning("The required python influxdb library (influxdb) is not installed. "
                                  "pip install influxdb")
            self.disabled = True

        self.influx = {}
        self.task_start_times = {}
        self.data_points = []

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys, var_options, direct)
        self.influx["host"] = self.get_option('influx_host')
        self.influx["port"] = self.get_option('influx_port') or 8086
        self.influx["database"] = self.get_option('influx_database')
        self.influx["username"] = self.get_option('influx_username')
        self.influx["password"] = self.get_option('influx_password')
        self.influx["ssl"] = self.get_option('influx_use_ssl') or False
        self.influx["verify_ssl"] = self.get_option('influx_verify_ssl') or True
        self.influx["timeout"] = self.get_option('influx_timeout') or 5
        self.influx["retries"] = self.get_option('influx_retries') or 3
        self.influx["measurement"] = self.get_option('influx_measurement_name') or "ansible_plays"
        self.influx["digest_write"] = self.get_option('influx_digest_write') or False

        if self.influx["host"] is None:
            self._display.warning(
                "No Influx Host provided. Can be provided with the `INFLUX_HOST` environment variable or in the ini")
            self.disabled = True

        if self.influx["database"] is None:
            self._display.warning(
                "No Influx database provided. Can be provided with the `INFLUX_DATABASE` environment variable"
                " or in the ini")
            self.disabled = True

        self._display.info("Influx Host: %s", self.influx["host"])

    def v2_playbook_on_stats(self, stats):
        if self.influx["digest_write"]:
            influxdb = self._connect_to_influxdb()
            influxdb.write_points(self.data_points)
            influxdb.close()

    def v2_runner_on_async_failed(self, result):
        self._create_data_point(result, "failed")

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._create_data_point(result, "failed")

    def v2_runner_on_skipped(self, result):
        self._create_data_point(result, "skipped")

    def v2_runner_on_unreachable(self, result):
        self._create_data_point(result, "unreachable")

    def v2_runner_on_async_ok(self, result):
        self._create_data_point(result, "ok")

    def v2_playbook_on_task_start(self, task, is_conditional):
        """
        Will create a start point in milliseconds for the task.
        :param task:
        :param is_conditional:
        """
        self.task_start_times[task._uuid] = self._time_in_milliseconds()

    def v2_runner_on_ok(self, result):
        self._create_data_point(result, "ok")

    def _connect_to_influxdb(self):
        """
        This will connect to influxDB
        :return: InfluxDBClient
        """
        args = dict(
            host=self.influx["host"],
            port=self.influx["port"],
            username=self.influx["username"],
            password=self.influx["password"],
            database=self.influx["database"],
            ssl=self.influx["ssl"],
            verify_ssl=self.influx["verify_ssl"],
            timeout=self.influx["timeout"],
        )
        influxdb_api_version = tuple(influxdb_version.split("."))
        if influxdb_api_version >= ('4', '1', '0'):
            # retries option is added in version 4.1.0
            args.update(retries=self.influx["retries"])

        return InfluxDBClient(**args)

    def _create_data_point(self, result, state="ok"):
        """
        This will create a measurement point for the duration of a task.
        If digest_write is true, the measurmenet point will be stored into a list which will be
        used to send all results at once on the end of the playbook (playbook_on_stats)
        The default is, that every data_point will be sent immediately to the influxdb. This has
        the advantage that you'll see the progress of long running plays.
        :param result:
        :param state:
        """
        if result._task._role is None:
            play = "None"
            play_uuid = "None"
            role_uuid = "None"
        else:
            play = str(result._task._role._play)
            play_uuid = str(result._task._role._play._uuid)
            role_uuid = str(result._task._role._uuid)

        data_point = dict(
            measurement=self.influx["measurement"],
            tags=dict(
                host=result._host,
                play=play,
                play_uuid=play_uuid,
                role=str(result._task._role),
                role_uuid=role_uuid,
                task_name=str(result._task.name),
                task_uuid=str(result._task._uuid),
            ),
            time=str(datetime.utcnow()),
            fields=dict(
                duration=self._time_in_milliseconds() - self.task_start_times[result._task._uuid],
                state=state
            )
        )
        if self.influx["digest_write"]:
            self.data_points.append(data_point)
        else:
            influxdb = self._connect_to_influxdb()
            influxdb.write_points([data_point])
            influxdb.close()

    @staticmethod
    def _time_in_milliseconds():
        return int(round(time.time() * 1000))
