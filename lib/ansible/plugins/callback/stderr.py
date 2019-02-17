# (c) 2017, Frederic Van Espen <github@freh.be>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: stderr
    callback_type: stdout
    requirements:
      - set as main display callback
    short_description: Splits output, sending failed tasks to stderr
    version_added: "2.4"
    deprecated:
        why: The 'default' callback plugin now supports this functionality
        removed_in: '2.11'
        alternative: "'default' callback plugin with 'display_failed_stderr = yes' option"
    extends_documentation_fragment:
      - default_callback
    description:
        - This is the stderr callback plugin, it behaves like the default callback plugin but sends error output to stderr.
        - Also it does not output skipped host/task/item status
'''

from ansible import constants as C
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default


class CallbackModule(CallbackModule_default):

    '''
    This is the stderr callback plugin, which reuses the default
    callback plugin but sends error output to stderr.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'stderr'

    def __init__(self):

        self.super_ref = super(CallbackModule, self)
        self.super_ref.__init__()

    def v2_runner_on_failed(self, result, ignore_errors=False):

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        self._handle_exception(result._result, use_stderr=True)
        self._handle_warnings(result._result)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)

        else:
            if delegated_vars:
                self._display.display("fatal: [%s -> %s]: FAILED! => %s" % (result._host.get_name(), delegated_vars['ansible_host'],
                                                                            self._dump_results(result._result)), color=C.COLOR_ERROR,
                                      stderr=True)
            else:
                self._display.display("fatal: [%s]: FAILED! => %s" % (result._host.get_name(), self._dump_results(result._result)),
                                      color=C.COLOR_ERROR, stderr=True)

        if ignore_errors:
            self._display.display("...ignoring", color=C.COLOR_SKIP)
