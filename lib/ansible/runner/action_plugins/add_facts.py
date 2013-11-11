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
import shlex
from ansible import utils
from ansible.runner.return_data import ReturnData

class ActionModule(object):
    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for adding groups of facts to the target host '''
        margs = self.parse_module_args(module_args)

        aggregate_key = margs.get('aggregate_key', None)
        if aggregate_key is None:
            return ReturnData(conn=conn, result=dict(failed=True, msg="an aggregate_key is required to add_facts"))

        role_key = margs.get('role_key', None)
        if role_key is None:
            return ReturnData(conn=conn, result=dict(failed=True, msg="a role_key is required to add_facts"))

        aggregate_facts, targetMap = self.get_map_for_facts(aggregate_key, inject, role_key)
        self.aggregate_arguments(margs, targetMap)
        return ReturnData(conn=conn, result=dict(ansible_facts={aggregate_key: aggregate_facts}))

    def get_or_create(self, map, key):
        return map[key] if key in map else {}

    def parse_module_args(self, module_args):
        # attempt to prevent confusing messages when the variable didn't interpolate
        module_args = module_args.replace("{{ ", "{{").replace(" }}", "}}")
        margs = {}
        margs.update(utils.parse_kv(module_args))
        return margs

    def aggregate_arguments(self, margs, targetMap):
        # iterate through the args if its not a key add it to the target map.
        # when adding, check if its present and add as list if already there
        # aggregates are always held in lists as it greatly simplifies iterating
        # through them in templates
        for k in margs.keys():
            if k != 'aggregate_key' and k != 'role_key':
                arg_value = self.to_json_if_possible(margs[k])
                if k in targetMap:
                    targetMap[k].append(arg_value)
                else:
                    targetMap[k] = [arg_value]

    def get_map_for_facts(self, aggregate_key, inject, role_key):
        aggregate_facts = self.get_or_create(inject, aggregate_key)
        # make sure the aggregate facts is in the injected so that it gets found on the next
        # iteration if this is a list
        inject[aggregate_key] = aggregate_facts
        by_role = self.get_or_create(aggregate_facts, role_key)
        aggregate_facts[role_key] = by_role
        targetMap = by_role
        return aggregate_facts, targetMap


    def to_json_if_possible(self, arg):
        parsed = utils.parse_json(arg.replace("'", "\""))
        parse_failed = 'failed' in parsed and parsed['failed'] and 'parsed' in parsed and not parsed['parsed']
        return arg if parse_failed else parsed
