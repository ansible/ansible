# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import os
import pwd
import random
import traceback
import tempfile

import ansible.constants as C
from ansible import utils
from ansible import errors
from ansible import module_common
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject):
        ''' transfer the given module name, plus the async module, then run it '''

        # shell and command module are the same
        if module_name == 'shell':
            module_name = 'command'
            module_args += " #USE_SHELL"

        (module_path, is_new_style) = self.runner._copy_module(conn, tmp, module_name, module_args, inject)
        self.runner._low_level_exec_command(conn, "chmod a+rx %s" % module_path, tmp)

        return self.runner._execute_module(conn, tmp, 'async_wrapper', module_args,
           async_module=module_path,
           async_jid=self.runner.generated_jid,
           async_limit=self.runner.background,
           inject=inject
        )

