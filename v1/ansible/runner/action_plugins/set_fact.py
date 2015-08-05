# Copyright 2013 Dag Wieers <dag@wieers.com>
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

from ansible import utils
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    TRANSFERS_FILES = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for running operations on master '''

        # load up options
        options  = {}
        if complex_args:
            options.update(complex_args)

        # parse the k=v arguments and convert any special boolean
        # strings into proper booleans (issue #8629)
        parsed_args = utils.parse_kv(module_args)
        for k,v in parsed_args.iteritems():
            # convert certain strings to boolean values
            if isinstance(v, basestring) and v.lower() in ('true', 'false', 'yes', 'no'):
                parsed_args[k] = utils.boolean(v)

        # and finally update the options with the parsed/modified args
        options.update(parsed_args)

        return ReturnData(conn=conn, result=dict(ansible_facts=options))
