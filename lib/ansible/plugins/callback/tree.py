# (c) 2012-2014, Ansible, Inc
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.plugins.callback import CallbackBase
from ansible.utils.path import makedirs_safe
from ansible.utils.unicode import to_bytes
from ansible.constants import TREE_DIR


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
            self._display.warning("Unable to write to %s's file: %s" % (hostname, str(e)))

    def result_to_tree(self, result):
        if self.tree:
            self.write_tree_file(result._host.get_name(), self._dump_results(result._result))

    def v2_runner_on_ok(self, result):
        self.result_to_tree(result)

    def v2_runner_on_failed(self, result):
        self.result_to_tree(result)

    def v2_runner_on_unreachable(self, result):
        self.result_to_tree(result)

