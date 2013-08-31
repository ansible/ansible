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
import pipes
from ansible.utils import template
from ansible import utils
from ansible import errors
from ansible.runner.return_data import ReturnData
import base64

class ActionModule(object):
    NEEDS_TMPPATH = False
    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for template operations '''

        # note: since this module just calls the copy module, the --check mode support
        # can be implemented entirely over there
	if not self.runner.is_playbook:
            raise errors.AnsibleError("in current versions of ansible, templates are only usable in playbooks")

        # load up options
        options  = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))

        source         = options.get('src', None)
	transport      = inject.get('cisco_transport', 'ssh')
        enable         = options.get('enable', None)
        commit         = options.get('commit', None)
        enable_pass    = inject.get('cisco_enable_pass', "")

        if (source is None and 'first_available_file' not in inject):
            result = dict(failed=True, msg="src and dest are required")
            return ReturnData(conn=conn, comm_ok=False, result=result)

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src

        if 'first_available_file' in inject:
            found = False
            for fn in self.runner.module_vars.get('first_available_file'):
                fn_orig = fn
                fnt = template.template(self.runner.basedir, fn, inject)
                fnd = utils.path_dwim(self.runner.basedir, fnt)
                if not os.path.exists(fnd) and '_original_file' in inject:
                    fnd = utils.path_dwim_relative(inject['_original_file'], 'templates', fnt, self.runner.basedir, check=False)
                if os.path.exists(fnd):
                    source = fnd
                    found = True
                    break
            if not found:
                result = dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(conn=conn, comm_ok=False, result=result)
        else:
            source = template.template(self.runner.basedir, source, inject)
                
            if '_original_file' in inject:
                source = utils.path_dwim_relative(inject['_original_file'], 'templates', source, self.runner.basedir)
            else:
                source = utils.path_dwim(self.runner.basedir, source)


        # template the source data locally & get ready to transfer
        try:
            resultant = template.template_from_file(self.runner.basedir, source, inject)
        except Exception, e:
            result = dict(failed=True, msg=str(e))
            return ReturnData(conn=conn, comm_ok=False, result=result)
	tmp = {"enable": enable, "transport": transport, "enable_pass": enable_pass, "commit": commit}
        return ReturnData(conn=conn, result=self.runner._low_level_exec_command(conn, resultant, tmp, sudoable=True))
