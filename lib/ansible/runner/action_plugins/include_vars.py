# (c) 2013-2014, Benno Joy <benno@ansible.com>
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
from ansible.utils import template
from ansible import utils
from ansible import errors
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    TRANSFERS_FILES = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        if not module_args:
            result = dict(failed=True, msg="No source file given")
            return ReturnData(conn=conn, comm_ok=True, result=result)

        source = module_args
        source = template.template(self.runner.basedir, source, inject)

        if '_original_file' in inject:
            source = utils.path_dwim_relative(inject['_original_file'], 'vars', source, self.runner.basedir)
        else:
            source = utils.path_dwim(self.runner.basedir, source)

        if os.path.exists(source):
            data = utils.parse_yaml_from_file(source, vault_password=self.runner.vault_pass)
            if data and type(data) != dict:
                raise errors.AnsibleError("%s must be stored as a dictionary/hash" % source)
            elif data is None:
                data = {}
            result = dict(ansible_facts=data)
            return ReturnData(conn=conn, comm_ok=True, result=result)
        else:
            result = dict(failed=True, msg="Source file not found.", file=source)
            return ReturnData(conn=conn, comm_ok=True, result=result)

