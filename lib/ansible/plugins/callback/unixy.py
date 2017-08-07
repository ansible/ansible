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

from ansible.plugins.callback import CallbackBase
from ansible.utils.color import colorize, hostcolor
from ansible import constants as C
from os.path import basename


class CallbackModule(CallbackBase):

    '''
    Print consolidated output that looks like a *NIX startup log
    Always dump full, pretty-printed result on failures
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'unixy'

    #def _get_task_banner(self, task):


    def _get_task_display_name(self, task):
        display_name = task.get_name().strip().split(" : ")

        if len(display_name) > 1:
            display_name_index = 1
        else:
            display_name_index = 0

        self.task_display_name = display_name[display_name_index].capitalize()

    def v2_playbook_on_task_start(self, task, is_conditional):
        # TODO only display task if it will not be skipped for any hosts
        # Should be able to achieve this by only running display on ok, changed, and failed
        self._get_task_display_name(task)
        self._display.display("%s..." % self.task_display_name)

    def v2_playbook_on_handler_task_start(self, task):
        self._get_task_display_name(task)
        self._display.display("%s (via handler)... " % self.task_display_name)

    def v2_playbook_on_play_start(self, play):
        # TODO display name of play and list of play hosts
        # TODO don't display play name if no hosts in play
        name = play.get_name().strip()
        if not name:
            msg = u"---"
        else:
            msg = u"\n- %s -" % name

        self._display.display(msg)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._handle_exception(result._result)
        self._handle_warnings(result._result)

        self._display.display("%s failed: %s" % (result._host.get_name(), self._dump_results(result._result, indent=4)), color=C.COLOR_ERROR)

    def v2_runner_on_ok(self, result):
        self._clean_results(result._result, result._task.action)
        self._handle_warnings(result._result)
        # TODO: handle delegated tasks

        result_was_changed = ('changed' in result._result
                                and result._result['changed'])

        run_is_verbose = ((self._display.verbosity > 0
                            or '_ansible_verbose_always' in result._result)
                            and '_ansible_verbose_override' not in result._result)

        if result_was_changed:
            msg = "done"
            display_color = C.COLOR_CHANGED
        else:
            msg = "ok"
            display_color = C.COLOR_OK

        if run_is_verbose:
            self._display.display("  %s %s: %s" % (result._host.get_name(), msg, self._dump_results(result._result, indent=4)), color=display_color)
        else:
            self._display.display("  %s %s" % (result._host.get_name(), msg), color=display_color)

    def v2_runner_on_skipped(self, result):
        run_is_verbose = ((self._display.verbosity > 0
                            or '_ansible_verbose_always' in result._result)
                            and '_ansible_verbose_override' not in result._result)

        if run_is_verbose:
            if self._display.verbosity > 1:
                skip_detail = self._dump_results(result._result, indent=4)

            elif self._display.verbosity == 1:
                skip_detail = result._result.get('skipped_reason')

            self._display.display("  %s skipped: %s" % (result._host.get_name(), skip_detail), color=C.COLOR_SKIP)

    def v2_runner_on_unreachable(self, result):
        self._display.display("  %s unreachable: %s" % (result._host.get_name(), self._dump_results(result._result, indent=4)), color=C.COLOR_UNREACHABLE)

    def v2_on_file_diff(self, result):
        if result._task.loop and 'results' in result._result:
            for res in result._result['results']:
                if 'diff' in res and res['diff'] and res.get('changed', False):
                    diff = self._get_diff(res['diff'])
                    if diff:
                        self._display.display(diff)
        elif 'diff' in result._result and result._result['diff'] and result._result.get('changed', False):
            diff = self._get_diff(result._result['diff'])
            if diff:
                self._display.display(diff)

    def v2_playbook_on_stats(self, stats):
        self._display.display("\n- Play recap -", screen_only=True)

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            # TODO how else can we display these?
            t = stats.summarize(h)

            self._display.display(u"  %s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR)),
                screen_only=True
            )

            self._display.display(u"  %s : %s %s %s %s" % (
                hostcolor(h, t, False),
                colorize(u'ok', t['ok'], None),
                colorize(u'changed', t['changed'], None),
                colorize(u'unreachable', t['unreachable'], None),
                colorize(u'failed', t['failures'], None)),
                log_only=True
            )

        # print custom stats
        if C.SHOW_CUSTOM_STATS and stats.custom:
            self._display.banner("Custom Stats: ")
            # per host
            # TODO: come up with 'pretty format'
            for k in sorted(stats.custom.keys()):
                if k == '_run':
                    continue
                self._display.display('\t%s: %s' % (k, self._dump_results(stats.custom[k], indent=1).replace('\n', '')))

            # print per run custom stats
            if '_run' in stats.custom:
                self._display.display("", screen_only=True)
                self._display.display('\tRun: %s' % self._dump_results(stats.custom['_run'], indent=1).replace('\n', ''))
            self._display.display("", screen_only=True)

    def v2_playbook_on_no_hosts_matched(self):
        self._display.display("  No hosts found!", color=C.COLOR_DEBUG)
        return

    def v2_playbook_on_no_hosts_remaining(self):
        self._display.display("Ran out of hosts!", color=C.COLOR_ERROR)

    def v2_playbook_on_start(self, playbook):
        # TODO display whether this run is happening in check mode
        self._display.display("Executing playbook %s" % basename(playbook._file_name))

        if self._display.verbosity > 3:
            if self._options is not None:
                for option in dir(self._options):
                    if option.startswith('_') or option in ['read_file', 'ensure_value', 'read_module']:
                        continue
                    val = getattr(self._options, option)
                    if val:
                        self._display.vvvv('%s: %s' % (option, val))

    def v2_runner_retry(self, result):
        msg = "Retrying... (%d of %d)" % (result._result['attempts'], result._result['retries'])
        if (self._display.verbosity > 2 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
            msg += "Result was: %s" % self._dump_results(result._result)
        self._display.display(msg, color=C.COLOR_DEBUG)

