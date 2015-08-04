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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast

from six import string_types

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean

def isidentifier(ident):
    """
    Determines, if string is valid Python identifier using the ast module.
    Orignally posted at: http://stackoverflow.com/a/29586366
    """

    if not isinstance(ident, string_types):
        return False

    try:
        root = ast.parse(ident)
    except SyntaxError:
        return False

    if not isinstance(root, ast.Module):
        return False

    if len(root.body) != 1:
        return False

    if not isinstance(root.body[0], ast.Expr):
        return False

    if not isinstance(root.body[0].value, ast.Name):
        return False

    if root.body[0].value.id != ident:
        return False

    return True

class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=dict()):
        facts = dict()
        if self._task.args:
            for (k, v) in self._task.args.iteritems():
                k = self._templar.template(k)

                if not isidentifier(k):
                    return dict(failed=True, msg="The variable name '%s' is not valid. Variables must start with a letter or underscore character, and contain only letters, numbers and underscores." % k)

                if isinstance(v, basestring) and v.lower() in ('true', 'false', 'yes', 'no'):
                    v = boolean(v)
                facts[k] = v
        return dict(changed=False, ansible_facts=facts)
