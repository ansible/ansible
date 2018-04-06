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


'''
playbook: play.yml

  play #1 (localhost): localhost        TAGS: []
    tasks:
      debug     TAGS: []
      pause     TAGS: []
      pause     TAGS: []
      pause     TAGS: []
      pause     TAGS: []
      debug     TAGS: []
'''
from ansible import constants as C
from os.path import basename
from ansible.plugins.callback import CallbackBase
from ansible.utils.color import colorize, hostcolor


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'list'

    def __init__(self):

        self._play = 1
        self._last_task_banner = None
        super(CallbackModule, self).__init__()

    def v2_playbook_on_start(self, playbook):
        self._display.display('playbook: %s\n' % basename(playbook._file_name))

    def v2_playbook_on_play_start(self, play):
        self._display.display('  play #%d (%s): %s TAGS:[%s]' % (self._play, ', '.join(play.hosts), play.get_name().strip(), ', '.join(play.tags)))

        #if self._options.listhosts:
        #    playhosts = set(inventory.get_hosts(play.hosts))
        #    msg += "\n    pattern: %s\n    hosts (%d):" % (play.hosts, len(playhosts))
        #    for host in playhosts:
        #        msg += "\n      %s" % host

        self._display.display('    tasks:')
        self._play += 1

    def v2_playbook_on_include(self, included_file):
        msg = 'included: %s for %s' % (included_file._filename, ", ".join([h.name for h in included_file._hosts]))
        self._display.display(msg, color=C.COLOR_SKIP)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._display.display('      %s TAGS: [%s]' % (task.get_name(), ', '.join(task.tags)))

    def v2_playbook_on_stats(self, stats):

        return

        self._display.banner("PLAY RECAP")

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR)),
                screen_only=True
            )

            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t, False),
                colorize(u'ok', t['ok'], None),
                colorize(u'changed', t['changed'], None),
                colorize(u'unreachable', t['unreachable'], None),
                colorize(u'failed', t['failures'], None)),
                log_only=True
            )

        self._display.display("", screen_only=True)
