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

from __future__ import absolute_import

from ..return_data import ReturnData
from ...callbacks import vv


class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' transfer & execute a module that is not 'copy' or 'template' '''

        module_args = self.runner._complex_args_hack(complex_args, module_args)

        if self.runner.noop_on_check(inject):
            if module_name in [ 'shell', 'command' ]:
                return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True, msg='check mode not supported for %s' % module_name))
            # else let the module parsing code decide, though this will only be allowed for AnsibleModuleCommon using
            # python modules for now
            module_args += " CHECKMODE=True"

        if self.runner.no_log:
            module_args += " NO_LOG=True"

        # shell and command are the same module
        if module_name == 'shell':
            module_name = 'command'
            module_args += " #USE_SHELL"

        vv("REMOTE_MODULE %s %s" % (module_name, module_args), host=conn.host)
        return self.runner._execute_module(conn, tmp, module_name, module_args, inject=inject, complex_args=complex_args)


