# (c) 2015, Andrew Gaffney <andrew@agaffney.org>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: actionable
    type: stdout
    short_description: shows only items that need attention
    description:
      - Use this callback when you dont care about OK nor Skipped.
      - This callback suppresses any non Failed or Changed status.
    version_added: "2.1"
    deprecated:
        why: The 'default' callback plugin now supports this functionality
        removed_in: '2.11'
        alternative: "'default' callback plugin with 'display_skipped_hosts = no' and 'display_ok_hosts = no' options"
    extends_documentation_fragment:
      - default_callback
    requirements:
      - set as stdout callback in configuration
'''

from ansible import constants as C
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default


class CallbackModule(CallbackModule_default):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'actionable'

    def __init__(self):
        self.super_ref = super(CallbackModule, self)
        self.super_ref.__init__()
        self.last_play = None
        self.shown_play = False
        self.shown_title = False
        self.anything_shown = False

    def v2_playbook_on_handler_task_start(self, task):
        self.super_ref.v2_playbook_on_handler_task_start(task)
        self.shown_title = True

    def v2_playbook_on_play_start(self, play):
        self.last_play = play
        self.shown_play = False

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.shown_title = False

    def display_task_banner(self, task):
        if not self.shown_play:
            self.super_ref.v2_playbook_on_play_start(self.last_play)
            self.shown_play = True
        if not self.shown_title:
            self.super_ref.v2_playbook_on_task_start(task, None)
            self.shown_title = True
        self.anything_shown = True

    def _print_task_banner(self, task):
        self._display.banner(self.last_task_banner)
        self._print_task_path(self.last_task)
        self._last_task_banner = self.last_task._uuid

    def _print_task_path(self, task):
        if self._display.verbosity >= 2:
            path = task.get_path()
            if path:
                self._display.display(u"task path: %s" % path, color=C.COLOR_DEBUG)

    def _get_task_banner(self, task):
        # args can be specified as no_log in several places: in the task or in
        # the argument spec.  We can check whether the task is no_log but the
        # argument spec can't be because that is only run on the target
        # machine and we haven't run it thereyet at this time.
        #
        # So we give people a config option to affect display of the args so
        # that they can secure this if they feel that their stdout is insecure
        # (shoulder surfing, logging stdout straight to a file, etc).
        args = ''
        if not task.no_log and C.DISPLAY_ARGS_TO_STDOUT:
            args = u', '.join(u'%s=%s' % a for a in task.args.items())
            args = u' %s' % args

        return u"TASK [%s%s]" % (task.get_name().strip(), args)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.display_task_banner(result._task)
        self.super_ref.v2_runner_on_failed(result, ignore_errors)

    def v2_runner_on_ok(self, result):
        if result._result.get('changed', False):
            self.display_task_banner(result._task)
            self.super_ref.v2_runner_on_ok(result)

    def v2_runner_on_unreachable(self, result):
        self.display_task_banner(result._task)
        self.super_ref.v2_runner_on_unreachable(result)

    def v2_runner_on_skipped(self, result):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        pass

    def v2_playbook_on_include(self, included_file):
        pass

    def v2_playbook_on_stats(self, stats):
        if self.anything_shown:
            self.super_ref.v2_playbook_on_stats(stats)

    def v2_on_file_diff(self, result):
        if 'diff' in result._result and result._result['diff'] and result._result.get('changed', False):
            diff = self._get_diff(result._result['diff'])
            if diff:
                self.display_task_banner(result._task)
                self._display.display(diff)

    def v2_runner_item_on_ok(self, result):
        if result._result.get('changed', False):
            self.display_task_banner(result._task)
            self.super_ref.v2_runner_item_on_ok(result)

    def v2_runner_item_on_skipped(self, result):
        pass

    def v2_runner_item_on_failed(self, result):
        self.display_task_banner(result._task)
        self.super_ref.v2_runner_item_on_failed(result)
