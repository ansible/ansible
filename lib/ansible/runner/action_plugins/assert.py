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

from ansible import utils, errors
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

        msg = None
        if 'msg' in args:
            msg = args['msg']

        if not 'that' in args:
            raise errors.AnsibleError('conditional required in "that" string')

        if not isinstance(args['that'], list):
            args['that'] = [ args['that'] ]

        for that in args['that']:
            test_result = utils.check_conditional(that, self.runner.basedir, inject, fail_on_undefined=True)
            if not test_result:
                result = dict(
                   failed       = True,
                   evaluated_to = test_result,
                   assertion    = that,
                )
                if msg:
                    result['msg'] = msg
                return ReturnData(conn=conn, result=result)

        return ReturnData(conn=conn, result=dict(msg='all assertions passed'))

