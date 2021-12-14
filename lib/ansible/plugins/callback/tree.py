# (c) 2012-2014, Ansible, Inc
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: tree
    type: notification
    requirements:
      - invoked in the command line
    short_description: Save host events to files
    version_added: "2.0"
    options:
        directory:
            version_added: '2.11'
            description: directory that will contain the per host JSON files. Also set by the C(--tree) option when using adhoc.
            ini:
                - section: callback_tree
                  key: directory
            env:
                - name: ANSIBLE_CALLBACK_TREE_DIR
            default: "~/.ansible/tree"
            type: path
    description:
        - "This callback is used by the Ansible (adhoc) command line option C(-t|--tree)."
        - This produces a JSON dump of events in a directory, a file for each host, the directory used MUST be passed as a command line option.
'''

import os

from ansible.constants import TREE_DIR
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.callback import CallbackBase
from ansible.utils.path import makedirs_safe, unfrackpath


class CallbackModule(CallbackBase):
    '''
    This callback puts results into a host specific file in a directory in json format.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'tree'
    CALLBACK_NEEDS_ENABLED = True

    def set_options(self, task_keys=None, var_options=None, direct=None):
        ''' override to set self.tree '''

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        if TREE_DIR:
            # TREE_DIR comes from the CLI option --tree, only avialable for adhoc
            self.tree = unfrackpath(TREE_DIR)
        else:
            self.tree = self.get_option('directory')

    def write_tree_file(self, hostname, buf):
        ''' write something into treedir/hostname '''

        buf = to_bytes(buf)
        try:
            makedirs_safe(self.tree)
        except (OSError, IOError) as e:
            self._display.warning(u"Unable to access or create the configured directory (%s): %s" % (to_text(self.tree), to_text(e)))

        try:
            path = to_bytes(os.path.join(self.tree, hostname))
            with open(path, 'wb+') as fd:
                fd.write(buf)
        except (OSError, IOError) as e:
            self._display.warning(u"Unable to write to %s's file: %s" % (hostname, to_text(e)))

    def result_to_tree(self, result):
        self.write_tree_file(result._host.get_name(), self._dump_results(result._result))

    def v2_runner_on_ok(self, result):
        self.result_to_tree(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.result_to_tree(result)

    def v2_runner_on_unreachable(self, result):
        self.result_to_tree(result)
