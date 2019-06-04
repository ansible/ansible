#
# Copyright (c) 2019 Ericsson AB.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import re
import platform

from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text, to_bytes
from ansible.plugins.terminal import TerminalBase
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

def load_additional_regular_setting(all_eres, all_pres):
    new_eres = []
    new_pres = []
    mode = 0
    file = None
    if platform.python_version().startswith('3'):
        python_version = 3
    else:
        python_version = 2

    try:
        config_file = C.ERIC_ECCLI_ADDITIONAL_RE_FILE
        if config_file:
            file = open(config_file, "r")
            lines = file.readlines()
            for line in lines:
                line=line.strip('\n')
                li = line.strip()
                if li == '[ERE]' :
                    mode = 1
                elif li == '[PRE]' :
                    mode = 2
                else:
                    if li and (li.startswith("#") == False):
                        if python_version == 3:
                            new_re = re.compile(bytes(line,'ascii'))
                        else:
                            new_re = re.compile(line)
                        if mode == 1:
                            if ((new_re in new_eres) == False):
                                if ((new_re in all_eres) == False):
                                    new_eres.append(new_re)
                        elif mode == 2:
                            if ((new_re in new_pres) == False):
                                if ((new_re in all_pres) == False):
                                    new_pres.append(new_re)
                        else:
                            display.vvvv(u'Regular expression loading skipping:%s' % line)
            all_eres.extend(new_eres)
            all_pres.extend(new_pres)
    except Exception as e:
        raise AnsibleConnectionFailure('Regular expression loading error:%s' % to_text(e))
    finally:
        if file in locals():
            file.close()

class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br"[\r\n]?\[.*\][a-zA-Z0-9_.-]*[>\#] ?$"),
        re.compile(br"[\r\n]?[a-zA-Z0-9_.-]*(?:\([^\)]+\))(?:[>#]) ?$"),
        re.compile(br"bash\-\d\.\d(?:[$#]) ?"),
        re.compile(br"[a-zA-Z0-9_.-]*\@[a-zA-Z0-9_.-]*\[\]\:\/flash\>")
    ]

    terminal_stderr_re = [
        #covered example syntax error: expecting
        re.compile(br"[\r\n]+syntax error: .*"),
        #Should not use Aborted: .*, for example
        #Aborted: by user, should be treated as success
        #Aborted: permission denied, should be treated as fail
        #re.compile(br"Aborted: permission denied"),
        #Current decision, still use RE Aborted: .*
        re.compile(br"Aborted: .*"),
        #covered example Error: access denied
        re.compile(br"[\r\n]+Error: .*"),
        #other errors
        re.compile(br"[\r\n]+% Error:.*"),
        re.compile(br"[\r\n]+% Invalid input.*"),
        re.compile(br"[\r\n]+% Incomplete command:.*")
    ]

    def on_open_shell(self):
        load_additional_regular_setting(TerminalModule.terminal_stderr_re, TerminalModule.terminal_stdout_re)

        try:
            for cmd in (b'screen-length 0', b'screen-width 512'):
                self._exec_cli_command(cmd)
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure('unable to set terminal parameters')

