# (c) 2016, Matt Martz <matt@sivel.net>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: json
    short_description: Ansible screen output as JSON
    version_added: "2.2"
    description:
        - This callback converts all events into JSON output to stdout
    type: stdout
    requirements:
      - Set as stdout in config
    options:
      show_custom_stats:
        version_added: "2.6"
        name: Show custom stats
        description: 'This adds the custom stats set via the set_stats plugin to the play recap'
        default: False
        env:
          - name: ANSIBLE_SHOW_CUSTOM_STATS
        ini:
          - key: show_custom_stats
            section: defaults
        type: bool
'''

import datetime
import json

from functools import partial

from ansible.inventory.host import Host
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins.callback import CallbackBase


def current_time():
    return '%sZ' % datetime.datetime.utcnow().isoformat()


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'json'

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)
        self.results = []

    def _new_play(self, play):
        return {
            'play': {
                'name': play.get_name(),
                'id': str(play._uuid),
                'duration': {
                    'start': current_time()
                }
            },
            'tasks': []
        }

    def _new_task(self, task):
        return {
            'task': {
                'name': task.get_name(),
                'id': str(task._uuid),
                'duration': {
                    'start': current_time()
                }
            },
            'hosts': {}
        }

    def v2_playbook_on_play_start(self, play):
        self.results.append(self._new_play(play))

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.results[-1]['tasks'].append(self._new_task(task))

    def v2_playbook_on_handler_task_start(self, task):
        self.results[-1]['tasks'].append(self._new_task(task))

    def _convert_host_to_name(self, key):
        if isinstance(key, (Host,)):
            return key.get_name()
        return key

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""

        hosts = sorted(stats.processed.keys())

        summary = {}
        for h in hosts:
            s = stats.summarize(h)
            summary[h] = s

        custom_stats = {}
        global_custom_stats = {}

        if self.get_option('show_custom_stats') and stats.custom:
            custom_stats.update(dict((self._convert_host_to_name(k), v) for k, v in stats.custom.items()))
            global_custom_stats.update(custom_stats.pop('_run', {}))

        output = {
            'plays': self.results,
            'stats': summary,
            'custom_stats': custom_stats,
            'global_custom_stats': global_custom_stats,
        }

        self._display.display(json.dumps(output, cls=AnsibleJSONEncoder, indent=4, sort_keys=True))

    def _record_task_result(self, on_info, result, **kwargs):
        """This function is used as a partial to add failed/skipped info in a single method"""
        host = result._host
        task = result._task
        task_result = result._result.copy()
        task_result.update(on_info)
        task_result['action'] = task.action
        self.results[-1]['tasks'][-1]['hosts'][host.name] = task_result
        end_time = current_time()
        self.results[-1]['tasks'][-1]['task']['duration']['end'] = end_time
        self.results[-1]['play']['duration']['end'] = end_time

    def __getattribute__(self, name):
        """Return ``_record_task_result`` partial with a dict containing skipped/failed if necessary"""
        if name not in ('v2_runner_on_ok', 'v2_runner_on_failed', 'v2_runner_on_unreachable', 'v2_runner_on_skipped'):
            return object.__getattribute__(self, name)

        on = name.rsplit('_', 1)[1]

        on_info = {}
        if on in ('failed', 'skipped'):
            on_info[on] = True

        return partial(self._record_task_result, on_info)
