# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.shell import ShellBase

DOCUMENTATION = '''
    name: csh
    plugin_type: shell
    version_added: ""
    short_description: C shell (/bin/csh)
    description:
      - When you have no other option than to use csh
    extends_documentation_fragment:
      - shell_common
'''


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
