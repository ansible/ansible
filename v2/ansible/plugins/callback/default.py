# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    def _print_banner(self, msg, color=None):
        '''
        Prints a header-looking line with stars taking up to 80 columns
        of width (3 columns, minimum)
        '''
        msg = msg.strip()
        star_len = (80 - len(msg))
        if star_len < 0:
            star_len = 3
        stars = "*" * star_len
        self._display.display("\n%s %s" % (msg, stars), color=color)

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, task, result, ignore_errors=False):
        self._display.display("fatal: [%s]: FAILED! => %s" % (result._host.get_name(), json.dumps(result._result, ensure_ascii=False)), color='red')

    def runner_on_ok(self, task, result):

        if result._task.action == 'include':
            msg = 'included: %s for %s' % (result._task.args.get('_raw_params'), result._host.name)
            color = 'cyan'
        elif result._result.get('changed', False):
            msg = "changed: [%s]" % result._host.get_name()
            color = 'yellow'
        else:
            msg = "ok: [%s]" % result._host.get_name()
            color = 'green'

        if (self._display._verbosity > 0 or 'verbose_always' in result._result) and result._task.action not in ('setup', 'include'):
            indent = None
            if 'verbose_always' in result._result:
                indent = 4
                del result._result['verbose_always']
            msg += " => %s" % json.dumps(result._result, indent=indent, ensure_ascii=False)
        self._display.display(msg, color=color)

    def runner_on_skipped(self, task, result):
        msg = "skipping: [%s]" % result._host.get_name()
        if self._display._verbosity > 0 or 'verbose_always' in result._result:
            indent = None
            if 'verbose_always' in result._result:
                indent = 4
                del result._result['verbose_always']
            msg += " => %s" % json.dumps(result._result, indent=indent, ensure_ascii=False)
        self._display.display(msg, color='cyan')

    def runner_on_unreachable(self, task, result):
        self._display.display("fatal: [%s]: UNREACHABLE! => %s" % (result._host.get_name(), result._result), color='red')

    def runner_on_no_hosts(self, task):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        pass

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        self._display.display("skipping: no hosts matched", color='cyan')

    def playbook_on_no_hosts_remaining(self):
        self._print_banner("NO MORE HOSTS LEFT")

    def playbook_on_task_start(self, name, is_conditional):
        self._print_banner("TASK [%s]" % name.strip())

    def playbook_on_cleanup_task_start(self, name):
        self._print_banner("CLEANUP TASK [%s]" % name.strip())

    def playbook_on_handler_task_start(self, name):
        self._print_banner("RUNNING HANDLER [%s]" % name.strip())

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, name):
        self._print_banner("PLAY [%s]" % name.strip())

    def playbook_on_stats(self, stats):
        pass

