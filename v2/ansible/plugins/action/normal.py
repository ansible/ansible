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

from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=dict()):

        # FIXME: a lot of this should pretty much go away with module
        #        args being stored within the task being run itself

        #if self.runner.noop_on_check(inject):
        #    if module_name in [ 'shell', 'command' ]:
        #        return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True, msg='check mode not supported for %s' % module_name))
        #    # else let the module parsing code decide, though this will only be allowed for AnsibleModuleCommon using
        #    # python modules for now
        #    module_args += " CHECKMODE=True"

        #if self.runner.no_log:
        #    module_args += " NO_LOG=True"

        #vv("REMOTE_MODULE %s %s" % (module_name, module_args), host=conn.host)
        return self._execute_module(tmp)


