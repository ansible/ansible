# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: list
    type: stdout
    short_description: Used to list tasks/hosts
    version_added: "2.6"
    description:
        - This is used by the CLI --list options
    requirements:
      - set as stdout in configuration
'''

from os.path import basename

from ansible import constants as C
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'list'

    def __init__(self):

        super(CallbackModule, self).__init__()

        self._opts = {'tasks': False, 'hosts': False, 'tags': False}
        self._playbooks = []
        self._current = {'playbook': '', 'play': '', 'task': ''}

    def _add_host(self, host):

        if host not in self._current['play']['hosts']:
            self._current['play']['hosts'].append(host)

    def list_options(self, opts):
        self._opts = opts

    def v2_playbook_on_start(self, playbook):
        name = basename(playbook._file_name)
        pb = {'name': name, 'plays': []}
        self._current['playbook'] = pb
        self._playbooks.append(pb)

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip() or 'play #%d' % (len(self._current['playbook']['plays']) + 1)
        play = {'name': name, 'pattern': ', '.join(play.hosts), 'tags': ', '.join(play.tags), 'tasks': [], 'hosts': []}
        self._current['playbook']['plays'].append(play)
        self._current['play'] = play

    def v2_playbook_on_include(self, included_file):
        name = 'task #%d' % (len(self._current['play']['tasks']) + 1)
        task = {'name': name, 'included': included_file._filename}
        print(included_file)
        for host in included_file._hosts:
            self._add_host(host.name)
        self._current['play']['tasks'].append(task)

    def v2_playbook_on_task_start(self, task, is_conditional):
        name = task.get_name().strip() or 'task #%d' % (len(self._current['play']['tasks']) + 1)
        task = {'name': name, 'tags': ', '.join(task.tags)}
        self._current['play']['tasks'].append(task)

    def v2_runner_on_ok(self, result):
        self._add_host(result._host.get_name())

    # not really needed
    v2_runner_on_failed = v2_runner_on_skipped = v2_runner_on_unreachable = v2_runner_on_ok

    def v2_playbook_on_stats(self, stats):

        # print all
        for playbook in self._playbooks:
            self._display.display('\nplaybook: %s\n' % playbook['name'])
            for play in playbook['plays']:

                msg = '  play: %(name)s'
                if self._opts['hosts']:
                    msg += ' hosts=%(pattern)s'
                if self._opts['tags']:
                    msg += ' tags=[%(tags)s]'
                self._display.display(msg % play)

                if self._opts['hosts']:
                    self._display.display('    selected: %d' % len(play['hosts']))
                    for host in play['hosts']:
                        self._display.display('      %s' % host)

                if self._opts['tags'] or self._opts['tasks']:
                    self._display.display('    tasks:')
                    for task in play['tasks']:
                        if 'included' in task:
                            self._display.display('        included=%(included)s' % (task), color=C.COLOR_SKIP)
                        elif self._opts['tags']:
                            self._display.display('      %(name)s tags=[%(tags)s]' % (task))
                        elif self._opts['tasks']:
                            self._display.display('      %(name)s' % (task))

        self._display.display("", screen_only=True)
