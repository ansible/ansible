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
from ansible.utils import template
from ansible.runner.return_data import ReturnData

class ActionModule(object):
    ''' Print statements during execution '''

    TRANSFERS_FILES = False

    def __init__(self, runner):
        self.runner = runner
        self.basedir = runner.basedir

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        args = {}
        if complex_args:
            args.update(complex_args)

        # attempt to prevent confusing messages when the variable didn't interpolate
        module_args = module_args.replace("{{ ","{{").replace(" }}","}}")

        kv = utils.parse_kv(module_args)
        args.update(kv)

        if not 'msg' in args and not 'var' in args:
            args['msg'] = 'Hello world!'

        result = {}
        if 'msg' in args:
            if 'fail' in args and utils.boolean(args['fail']):
                result = dict(failed=True, msg=args['msg'])
            else:
                result = dict(msg=args['msg'])
        elif 'var' in args and not utils.LOOKUP_REGEX.search(args['var']):
            results = template.template(self.basedir, args['var'], inject, convert_bare=True)
            result['var'] = { args['var']: results }

        # force flag to make debug output module always verbose
        result['verbose_always'] = True

        return ReturnData(conn=conn, result=result)
