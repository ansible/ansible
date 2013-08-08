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
import shlex

import ansible.constants as C
from ansible.utils import template
from ansible import utils
from ansible import errors
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for file transfer operations '''

        if self.runner.check:
            # in check mode, always skip this module
            return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True, msg='check mode not supported for this module'))

        tokens  = shlex.split(module_args)
        source  = tokens[0]
        # FIXME: error handling
        args    = " ".join(tokens[1:])
        source  = template.template(self.runner.basedir, source, inject)
        if '_original_file' in inject:
            source = utils.path_dwim_relative(inject['_original_file'], 'files', source, self.runner.basedir)
        else:
            source = utils.path_dwim(self.runner.basedir, source)

        # transfer the file to a remote tmp location
        source  = source.replace('\x00','') # why does this happen here?
        args    = args.replace('\x00','') # why does this happen here?
        tmp_src = os.path.join(tmp, os.path.basename(source))
        tmp_src = tmp_src.replace('\x00', '') 

        conn.put_file(source, tmp_src)

        # fix file permissions when the copy is done as a different user
        if self.runner.sudo and self.runner.sudo_user != 'root':
            prepcmd = 'chmod a+rx %s' % tmp_src
        else:
            prepcmd = 'chmod +x %s' % tmp_src

        # add preparation steps to one ssh roundtrip executing the script
        env_string = self.runner._compute_environment_string(inject)
        module_args = prepcmd + '; ' + env_string + tmp_src + ' ' + args

        handler = utils.plugins.action_loader.get('raw', self.runner)
        result = handler.run(conn, tmp, 'raw', module_args, inject)

        # clean up after
        if tmp.find("tmp") != -1 and not C.DEFAULT_KEEP_REMOTE_FILES:
            self.runner._low_level_exec_command(conn, 'rm -rf %s >/dev/null 2>&1' % tmp, tmp)

        return result
