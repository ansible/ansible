# (c) 2012-2014, Ansible, Inc
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: tree
    callback_type: notification
    requirements:
      - invoked in the command line
    short_description: Save host events to files
    version_added: "2.0"
    description:
        - "This callback is used by the Ansible (adhoc) command line option `-t|--tree`"
        - This produces a JSON dump of events in a directory, a file for each host, the directory used MUST be passed as a command line option.
'''

import os

from ansible.constants import TREE_DIR
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.callback import CallbackBase
from ansible.utils.path import makedirs_safe


class CallbackModule(CallbackBase):
    '''
    This callback puts results into a host specific file in a directory in json format.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'tree'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        self.tree = TREE_DIR
        if not self.tree:
            self.tree = os.path.expanduser("~/.ansible/tree")
            self._display.warning("The tree callback is defaulting to ~/.ansible/tree, as an invalid directory was provided: %s" % self.tree)

    def write_tree_file(self, hostname, buf):
        ''' write something into treedir/hostname '''

        buf = to_bytes(buf)
        try:
            makedirs_safe(self.tree)
            path = os.path.join(self.tree, hostname)
            with open(path, 'wb+') as fd:
                fd.write(buf)
        except (OSError, IOError) as e:
            self._display.warning(u"Unable to write to %s's file: %s" % (hostname, to_text(e)))

    def result_to_tree(self, result):
        if self.tree:
            self.write_tree_file(result._host.get_name(), self._dump_results(result._result))

    def v2_runner_on_ok(self, result):
        self.result_to_tree(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.result_to_tree(result)

    def v2_runner_on_unreachable(self, result):
        self.result_to_tree(result)
