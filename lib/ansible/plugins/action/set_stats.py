# Copyright 2016 Ansible (RedHat, Inc)
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.utils.vars import isidentifier


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    # TODO: document this in non-empty set_stats.py module
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        stats = {'data': {}, 'per_host': False, 'aggregate': True}

        if self._task.args:
            data = self._task.args.get('data', {})

            if not isinstance(data, dict):
                data = self._templar.template(data, convert_bare=False, fail_on_undefined=True)

            if not isinstance(data, dict):
                result['failed'] = True
                result['msg'] = "The 'data' option needs to be a dictionary/hash"
                return result

            # set boolean options, defaults are set above in stats init
            for opt in ['per_host', 'aggregate']:
                val = self._task.args.get(opt, None)
                if val is not None:
                    if not isinstance(val, bool):
                        stats[opt] = boolean(self._templar.template(val), strict=False)
                    else:
                        stats[opt] = val

            for (k, v) in iteritems(data):

                k = self._templar.template(k)

                if not isidentifier(k):
                    result['failed'] = True
                    result['msg'] = ("The variable name '%s' is not valid. Variables must start with a letter or underscore character, and contain only "
                                     "letters, numbers and underscores." % k)
                    return result

                stats['data'][k] = self._templar.template(v)

        result['changed'] = False
        result['ansible_stats'] = stats

        return result
