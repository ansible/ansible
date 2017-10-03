# (C) 2017-2018, VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: GPL-3.0
# (C) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: telegraf
    callback_type: metrics
    requirements:
        - pip install pytelegraf (udp) or pip install pytelegraf[http] (http or https)
        - ansible v2
        - running telegraf reachable by ansible controller configured with desired output to a metrics collector
    short_description: Sends play events to a telegraf forwarder (to metrics collector)
    version_added: "2.4"
    description:
        - This is an ansible callback plugin that sends playbook stats to a telegraf listener input (udp/http) 
          during playbook execution.
        - Configure with <playbook root>callback_plugins/ansible-telegraf-callback/telegraf_callback.yml
        - or using the module args or options in ansible.cfg
    notes:
        - Troubleshooting
        - it's difficult to debug udp connections, so start with http
        - run with -vvvv.  In the first few lines you should see the callback is loaded
        - grep --binary-file=text changed /var/log/telegraf.log to see if telegraf is receiving 
        - ensure telegraf is running with correct input blocks in /etc/telegraf/telegraf.d/
          inputs-socket-listener.conf or inputs-http-listener.conf 
          https://github.com/influxdata/telegraf/tree/master/plugins/inputs/socket_listener

        - Installation
          - in ansible.cfg
            callback_whitelist = telegraf[,others]
            callback_plugins = <path_to>/callback_plugins
          - clone git repo into <playbook root>/callback_plugins/ansible-telegraf-callback
          - Tower http://docs.ansible.com/ansible-tower/latest/html/administration/tipsandtricks.html#using-callback-plugins-with-tower
          - if running ansible < 2.4.0 you may need to remove the ini sections from this doc blob and use ENV vars

    options:
      host:
        description: telegraf host reachable from the ansible controller
        default: localhost
        env:
          - name: ANSIBLE_TELEGRAF_CALLBACK_HOST
        ini:
          - section: callback_telegraf
            key: host
      port:
        default: 8186
        description: telegraf host reachable from the ansible controller
        env:
          - name: ANSIBLE_TELEGRAF_CALLBACK_PORT
        ini:
          - section: callback_telegraf
            key: port
        type: int
      metric_prefix:
        description: metrics prefix for all metrics sent to telegraf.
        env:
          - name: ANSIBLE_TELEGRAF_CALLBACK_METRIC_PREFIX
        default: "ansible."
        ini:
          - section: callback_telegraf
            key: metric_prefix
      metric_per_host:
        description: summarize over all tasks per host
        env:
          - name: ANSIBLE_TELEGRAF_CALLBACK_METRIC_PER_HOST
        default: True
        ini:
          - section: callback_telegraf
            key: metric_per_host
      metric_summary:
        description: summarize stats over all hosts.
        env:
          - name: ANSIBLE_TELEGRAF_CALLBACK_METRIC_SUMMARY
        default: False
        ini:
          - section: callback_telegraf
            key: metric_summary
      wire_protocol:
        description: http, https or udp.  If http you must pip install pytelegraf[http]. Default udp
        choices: ['http', 'https', 'udp']
        env:
          - name: ANSIBLE_TELEGRAF_CALLBACK_WIRE_PROTOCOL
        default: http
        ini:
          - section: callback_telegraf
            key: wire_protocol
'''

import os.path
import socket
from datetime import datetime, timedelta
from ansible.module_utils.six import iteritems


try:
    # Ansible v2
    from ansible.plugins.callback import CallbackBase
except ImportError:
    # Ansible v1
    CallbackBase = object


class CallbackModule(CallbackBase):
    """
    This is an ansible callback plugin that sends metrics
    to a collector via telegraf.  Which collector depends on telegraf config.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'metrics'  # https://groups.google.com/forum/#!topic/ansible-devel/G9mJUmaM-Eg
    CALLBACK_NAME = 'telegraf'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()
        if self._display.verbosity > 1:
            self._display.display('Playbook telegraf_callback init')

        # the ansible controller running the callback
        self._controller_hostname = socket.gethostname()

        self._playbook_name = None

        self.start_timer()

        # self.playbook is either set by Ansible (v1), or by us in the `playbook_start` callback method (v2)
        self.playbook = None
        # self.play is either set by Ansible (v1), or by us in the `playbook_on_play_start` callback method (v2)
        self.play = None

        # pytelegraf makes asyc calls to telegraf so doesn't raise errors.  Check once.
        self._connection_tested = False

    def set_options(self, options):

        super(CallbackModule, self).set_options(options)

        self._metric_summary = self._plugin_options['metric_summary']
        self._metric_prefix = self._plugin_options['metric_prefix']
        self._metric_per_host = self._plugin_options['metric_per_host']

        if self._display.verbosity > 2:
            self._display.display('metric_summary {}, metric_prefix {}, metric_per_host {}'.format(
                self._metric_summary, self._metric_prefix, self._metric_per_host))

        self._host = self._plugin_options['host']
        self._port = self._plugin_options['port']
        self._wire_protocol = self._plugin_options['wire_protocol']
        self._display.display('host {}, port {}, wire_protocol {}'.format(self._host, self._port, self._wire_protocol))
        if self._display.verbosity > 1:
            self._display.display('Using wire protocol {}, host {}, port {}'.format(
                self._wire_protocol, self._host, self._port))

        if self._wire_protocol.startswith('http'):
            try:
                from telegraf import HttpClient
                try:
                    self.client = HttpClient(host=self._host, port=self._port)
                except Exception as err:
                    self._display.error('Failed to make http connection to telegraf \n {}'.format(err))
                    self.disabled = True
            except ImportError:
                self._display.warning('''WARNING: Could not import telegraf HttpClient
                                         please pip install pytelegraf[http].  Using udp''')
                self._wire_protocol = 'udp'
        elif self._wire_protocol.startswith('udp'):
            try:
                from telegraf.client import TelegrafClient
                self.client = TelegrafClient(host=self._host, port=self._port)
            except ImportError as err:
                self._display.error('Could not import telegraf.client. pip install pytelegraf')
                self.disabled = True
                raise(err)

        if not self._connection_tested:
            import contextlib
            if self._wire_protocol.startswith('http'):
                with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                    if sock.connect_ex((self._host, self._port)) == 0:
                        self._display.display("Telegraf http connection succeeded!")
                        self._connection_tested = True
                    else:
                        error_msg = '''Telegraf port connection failed!
                                       Disabling telegraf callback.
                                       Check connection to {}:{} '''.format(self._host, self._port)
                        self._display.error(error_msg)
                        self.disabled = True
            elif self._wire_protocol.startswith('udp'):
                self._display.display('''wire_protocol = udp.  Cannot verify udp port is available.
                                         Check telegraf.log''')
                self._connection_tested = True

    # Send ansible metric to Telegraf
    def send_metric(self, metric, value, host=None, tags=None):
        """
        @metric: '.' separated string metric name
        @value: int, float or string
        @tags: dict of point tags
        @host: If set, over-ride source of metric (wavefront)
        """
        # Records a single value with one tag
        # self.client.metric('some_metric', 123, tags={'server_name': 'my-server'})
        merged_tags = self.default_tags
        merged_tags.update(tags or {})
        if host:
            merged_tags['hostname'] = host

        if self._metric_prefix:
            metric = ".".join([self._metric_prefix, metric])
            if self._display.verbosity > 2:
                self._display.display('Sending metric "{}" to telegraf'.format(metric))
            self.client.metric(
                metric,
                value,
                tags=merged_tags,
            )

    # Default tags sent with metrics
    @property
    def default_tags(self):
        return {'playbook': self._playbook_name, 'controller': self._controller_hostname}

    # Start timer to measure playbook running time
    def start_timer(self):
        self._start_time = datetime.now()

    # Get the time elapsed since the timer was started
    def get_elapsed_time(self):
        return timedelta.total_seconds(datetime.now() - self._start_time)

    # Handle `playbook_on_start` callback, common to Ansible v1 & v2
    def _handle_playbook_on_start(self, playbook_file_name, inventory):
        self.start_timer()

        # Set the playbook name from its filename
        self._playbook_name, _ = os.path.splitext(
            os.path.basename(playbook_file_name))

    # Implementation compatible with Ansible v1 only
    def playbook_on_start(self):
        playbook_file_name = self.playbook.filename
        inventory = self.playbook.inventory.host_list

        self._handle_playbook_on_start(playbook_file_name, inventory)

    def playbook_on_stats(self, stats):
        total_tasks = 0
        total_changed = 0
        total_errors = 0
        error_hosts = []
        for host in stats.processed:
            summary = stats.summarize(host)
            if self._metric_summary:
                # Aggregations for the summary text
                total_tasks += sum([summary['ok'], summary['failures'], summary['skipped']])
                total_changed += summary['changed']
                errors = sum([summary['failures'], summary['unreachable']])
                if errors > 0:
                    error_hosts.append((host, summary['failures'], summary['unreachable']))
                    total_errors += errors

            if self._metric_per_host:
                # Send metrics for this host
                for metric, value in summary.iteritems():
                    self.send_metric('task.{0}'.format(metric), value, host=host)


        if self._metric_summary:
            # Send playbook summarized over hosts
            summaries = {'playbook-summary.runtime': self.get_elapsed_time(),
                         'playbook-summary.changed': total_changed,
                         'playbook-summary.tasks': total_tasks,
                         'playbook-summary.errors': total_errors
                        }
            for key, val in summaries.iteritems():
                if key == 'playbook-summary.errors':
                    tags = {}
                    tags['failingHosts'] = ",".join([x[0] for x in error_hosts])
                    self.send_metric(key, val, tags=tags)
                else:
                    self.send_metric(key, val)

    # Ansible callbacks
    # v2_ versions call to these, which mostly just call to v1_ versions

    # Implementation compatible with Ansible v2 only
    def v2_playbook_on_start(self, playbook):
        # On Ansible v2, Ansible doesn't set `self.playbook` automatically
        self.playbook = playbook

        playbook_file_name = self.playbook._file_name
        inventory = None

        self._handle_playbook_on_start(playbook_file_name, inventory)

    def v2_playbook_on_play_start(self, play):
        # On Ansible v2, Ansible doesn't set `self.play` automatically
        self.play = play

    def v2_playbook_on_stats(self, stats):
        self._display.display("Playbook sending metrics to telegraf")
        self.playbook_on_stats(stats)
