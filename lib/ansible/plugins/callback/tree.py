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
from ansible.constants import TREE_DIR


class CallbackModule(CallbackBase):
    '''
    This callback puts results into a host specific file in a directory in json format.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'tree'

    def write_tree_file(self, tree, hostname, buf):
        ''' write something into treedir/hostname '''

        makedirs_safe(tree)
        try:
            path = os.path.join(tree, hostname)
            fd = open(path, "a+")
            fd.write(buf)
            fd.close()
        except (OSError, IOError) as e:
            self._display.warnings("Unable to write to %s's file: %s" % (hostname, str(e)))

    def result_to_tree(self, result):
        tree = TREE_DIR
        if tree:
            self.write_tree_file(tree, result._host.get_name(), self._dump_results(result._result))
        else:
            self._display.warnings("Invalid directory provided to tree option: %s" % tree)

    def v2_runner_on_ok(self, result):
        self.result_to_tree(result)

    def v2_runner_on_failed(self, result):
        self.result_to_tree(result)

    def v2_runner_on_unreachable(self, result):
        self.result_to_tree(result)

