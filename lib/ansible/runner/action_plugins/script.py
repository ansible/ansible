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
import traceback
import shlex

import ansible.constants as C
from ansible import utils
from ansible import errors
from ansible import module_common
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject):
        ''' handler for file transfer operations '''

        # load up options
        options = utils.parse_kv(module_args)

        tokens  = shlex.split(module_args)
        source  = tokens[0]
        # FIXME: error handling
        args    = " ".join(tokens[1:])
        source  = utils.template(self.runner.basedir, source, inject)
        source  = utils.path_dwim(self.runner.basedir, source)

        exec_rc = None

        # transfer the file to a remote tmp location
        source  = source.replace('\x00','') # why does this happen here?
        args    = args.replace('\x00','') # why does this happen here?
        tmp_src = os.path.join(tmp, os.path.basename(source))
        tmp_src = tmp_src.replace('\x00', '') 

        conn.put_file(source, tmp_src)

        # fix file permissions when the copy is done as a different user
        if self.runner.sudo and self.runner.sudo_user != 'root':
            self.runner._low_level_exec_command(conn, "chmod a+r %s" % tmp_src, tmp)

        # make executable
        self.runner._low_level_exec_command(conn, "chmod +x %s" % tmp_src, tmp)

        # run it through the command module
        module_args = tmp_src + " " + args + " #USE_SHELL"
        return self.runner._execute_module(conn, tmp, 'command', module_args, inject=inject)

