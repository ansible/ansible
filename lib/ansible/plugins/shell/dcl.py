# Copyright (c) 2014, Chris Church <chris@ninemoreminutes.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import text_type
from ansible.module_utils.six.moves import shlex_quote
from ansible.plugins.shell.sh import ShellModule as ShModule

DOCUMENTATION = '''
    name: dcl
    plugin_type: shell
    version_added: ""
    short_description: DCL shell OpenVMS COmmand line, no separate command...
    description:
      - This is to support OpenVMS, ( initialy based on fish)
    extends_documentation_fragment:
      - shell_common
'''


class ShellModule(ShModule):

    # Common shell filenames that this plugin handles
    COMPATIBLE_SHELLS = frozenset(('dcl',))
    # Family of shells this has.  Must match the filename without extension
    SHELL_FAMILY = 'dcl'
    IS_OPENVMS = True

    # This is needed for?
    _SHELL_EMBEDDED_PY_EOL = '\n'
    # The next can be done by prepending command with a few extra lines
    #     $ sts = $STATUS  ! keep status
    #     $ DEFINE/USER SYS$OUTPUT NL:  ! these will clobber the dcl status
    #     $ DEFINE/USER SYS$ERROR NL:
    #     $ $STATUS = sts  ! restor previous command's status
    # when generating a script the $ prefix is mandatory, when issuing commands they should be left out.
    _SHELL_REDIRECT_ALLNULL = '\nsts = $STATUS\nDEFINE/USER SYS$OUTPUT NL:\nDEFINE/USER SYS$ERROR NL:\n$STATUS = sts'
    # The next should be prepended to the command
    _SHELL_AND = '\nIF $status THEN '
    # Following are unsupported....
    _SHELL_OR = ''
    _SHELL_SUB_LEFT = ''
    _SHELL_SUB_RIGHT = ''
    _SHELL_GROUP_LEFT = ''
    _SHELL_GROUP_RIGHT = ''

    # can only be done by adding assignment before the command...
    # NOT AFTER IF ... THEN... Quoting will be an issue....
    # strings: "......"
    # variable expansion: 'var' (early, before CLI parsing) &var (late, during CLI parsing)
    #                     ''var'    when variables are inside a string.
    # escaping a "  double up..  "what""ever"""   will show as: what"ever" when printed...
    def env_prefix(self, **kwargs):
        env = self.env.copy()
        env.update(kwargs)
        return ' '.join(['\n$ %s=%s' % (k, shlex_quote(text_type(v))) for k, v in env.items()])
        