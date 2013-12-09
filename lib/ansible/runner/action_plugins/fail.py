# Copyright 2012, Dag Wieers <dag@wieers.com>
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

import ansible

from ansible import utils
from ansible.runner.return_data import ReturnData

class ActionModule(object):
    ''' Fail with custom message '''

    TRANSFERS_FILES = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        # note: the fail module does not need to pay attention to check mode
        # it always runs.

        args = {}
        if complex_args:
            args.update(complex_args)
        args.update(utils.parse_kv(module_args))
        if not 'msg' in args:
            args['msg'] = 'Failed as requested from task'

        result = dict(failed=True, msg=args['msg'])
        return ReturnData(conn=conn, result=result)
