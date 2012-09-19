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

    def run(self, conn, tmp, module_name, inject):
        ''' handler for template operations '''

        if not self.runner.is_playbook:
            raise errors.AnsibleError("in current versions of ansible, templates are only usable in playbooks")

        # load up options
        options  = utils.parse_kv(self.runner.module_args)
        source   = options.get('src', None)
        dest     = options.get('dest', None)
        if (source is None and 'first_available_file' not in inject) or dest is None:
            result = dict(failed=True, msg="src and dest are required")
            return ReturnData(conn=conn, comm_ok=False, result=result)

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        if 'first_available_file' in inject:
            found = False
            for fn in self.runner.module_vars.get('first_available_file'):
                fn = utils.template(self.runner.basedir, fn, inject)
                if os.path.exists(fn):
                    source = fn
                    found = True
                    break
            if not found:
                result = dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(conn=conn, comm_ok=False, result=result)

        source = utils.template(self.runner.basedir, source, inject)

        # template the source data locally & transfer
        try:
            resultant = utils.template_from_file(self.runner.basedir, source, inject)
        except Exception, e:
            result = dict(failed=True, msg=str(e))
            return ReturnData(conn=conn, comm_ok=False, result=result)

        xfered = self.runner._transfer_str(conn, tmp, 'source', resultant)
        # fix file permissions when the copy is done as a different user
        if self.runner.sudo and self.runner.sudo_user != 'root':
            self.runner._low_level_exec_command(conn, "chmod a+r %s" % xfered, tmp)
        # run the copy module, queue the file module
        self.runner.module_args = "%s src=%s dest=%s" % (self.runner.module_args, xfered, dest)
        return self.runner._execute_module(conn, tmp, 'copy', self.runner.module_args, inject=inject).daisychain('file')


