# (c) 2014, Chris Church <chris@ninemoreminutes.com>
#
# This file is part of Ansible.
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

from ansible.plugins.shell import ShellBase

class ShellModule(ShellBase):

    # Common shell filenames that this plugin handles
    COMPATIBLE_SHELLS = frozenset(('csh', 'tcsh'))
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'csh'

    # How to end lines in a python script one-liner
    _SHELL_EMBEDDED_PY_EOL = '\\\n'
    _SHELL_REDIRECT_ALLNULL = '>& /dev/null'
    _SHELL_AND = '&&'
    _SHELL_OR = '||'
    _SHELL_SUB_LEFT = '"`'
    _SHELL_SUB_RIGHT = '`"'
    _SHELL_GROUP_LEFT = '('
    _SHELL_GROUP_RIGHT = ')'

    def env_prefix(self, **kwargs):
        return 'env %s' % super(ShellModule, self).env_prefix(**kwargs)
