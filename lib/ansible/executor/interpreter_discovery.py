# Copyright: (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible.utils.plugin_docs import get_versioned_doclink
from traceback import format_exc

display = Display()
foundre = re.compile(r'FOUND(.*)ENDFOUND', flags=re.DOTALL)


class InterpreterDiscoveryRequiredError(Exception):
    def __init__(self, message, interpreter_name, discovery_mode):
        super(InterpreterDiscoveryRequiredError, self).__init__(message)
        self.interpreter_name = interpreter_name
        self.discovery_mode = discovery_mode


def discover_interpreter(action, interpreter_name, discovery_mode, task_vars):
    """Probe the target host for a Python interpreter from the `INTERPRETER_PYTHON_FALLBACK` list, returning the first found or `/usr/bin/python3` if none."""
    host = task_vars.get('inventory_hostname', 'unknown')
    res = None
    found_interpreters = [u'/usr/bin/python3']  # fallback value
    is_silent = discovery_mode.endswith('_silent')

    if discovery_mode.startswith('auto_legacy'):
        action._discovery_deprecation_warnings.append(dict(
            msg=f"The '{discovery_mode}' option for 'INTERPRETER_PYTHON' now has the same effect as 'auto'.",
            version='2.21',
        ))

    try:
        bootstrap_python_list = C.config.get_config_value('INTERPRETER_PYTHON_FALLBACK', variables=task_vars)

        display.vvv(msg=f"Attempting {interpreter_name} interpreter discovery.", host=host)

        # not all command -v impls accept a list of commands, so we have to call it once per python
        command_list = ["command -v '%s'" % py for py in bootstrap_python_list]
        shell_bootstrap = "echo FOUND; {0}; echo ENDFOUND".format('; '.join(command_list))

        # FUTURE: in most cases we probably don't want to use become, but maybe sometimes we do?
        res = action._low_level_execute_command(shell_bootstrap, sudoable=False)

        raw_stdout = res.get('stdout', u'')

        match = foundre.match(raw_stdout)

        if not match:
            display.debug(u'raw interpreter discovery output: {0}'.format(raw_stdout), host=host)
            raise ValueError('unexpected output from Python interpreter discovery')

        found_interpreters = [interp.strip() for interp in match.groups()[0].splitlines() if interp.startswith('/')]

        display.debug(u"found interpreters: {0}".format(found_interpreters), host=host)

        if not found_interpreters:
            if not is_silent:
                action._discovery_warnings.append(u'No python interpreters found for '
                                                  u'host {0} (tried {1})'.format(host, bootstrap_python_list))
            # this is lame, but returning None or throwing an exception is uglier
            return u'/usr/bin/python3'
    except AnsibleError:
        raise
    except Exception as ex:
        if not is_silent:
            action._discovery_warnings.append(f'Unhandled error in Python interpreter discovery for host {host}: {ex}')
            display.debug(msg=f'Interpreter discovery traceback:\n{format_exc()}', host=host)
            if res and res.get('stderr'):  # it may not be possible to reach this point without having res and stderr
                display.vvv(msg=f"Interpreter discovery remote stderr:\n{res.get('stderr')}", host=host)

    if not is_silent:
        action._discovery_warnings.append(
            f"Host {host} is using the discovered Python interpreter at {found_interpreters[0]}, "
            "but future installation of another Python interpreter could change the meaning of that path. "
            f"See {get_versioned_doclink('reference_appendices/interpreter_discovery.html')} for more information."
        )

    return found_interpreters[0]
