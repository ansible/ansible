# Ansible-required imports
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from datetime import datetime
import os

from ansible.plugins.callback import CallbackBase

DEFAULT_PROM_PATH = '/tmp/ansible-play.prom'

DOCUMENTATION = '''
  callback: prometheus
  callback_type: aggregate
  author: Devon Finninger (@dfinninger)
  requirements:
    - whitelist in configuration
  short_description: Export Ansible play stats to Prometheus
  version_added: "2.5"
  description:
      - Writes Ansible play stats as Prometheus Textfile metrics
  options:
    textfile_path:
      description: Path to the prometheus textfile
      env:
        - name: ANSIBLE_CALLBACK_PROMETHEUS_PATH
      default: "/tmp/ansible-play.prom"
'''


class CallbackModule(CallbackBase):
    """
    This callback module exports Play stats as Prometheus metrics.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'prometheus'

    # only needed if you ship it and don't want to enable by default
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        # make sure the expected objects are present, calling the base's __init__
        super(CallbackModule, self).__init__()

        self.start_time = datetime.utcnow()

    def v2_playbook_on_stats(self, stats):
        end_time = datetime.utcnow()
        runtime = end_time - self.start_time

        filepath = os.environ.get('ANSIBLE_CALLBACK_PROMETHEUS_PATH', DEFAULT_PROM_PATH)

        with open(filepath, 'w') as f:
            f.write('ansible_run_time {0}\n'.format(runtime.total_seconds()))
            for host in sorted(stats.processed.keys()):
                for key, value in stats.summarize(host).items():
                    f.write('ansible_play_summary{{host="{0}", status="{1}"}} {2}\n'.format(host, key, value))
