# Copyright: (c) 2018, Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
Context of the running Ansible.

In the future we *may* create Context objects to allow running multiple Ansible plays in parallel
with different contexts but that is currently out of scope as the Ansible library is just for
running the ansible command line tools.

These APIs are still in flux so do not use them unless you are willing to update them with every Ansible release
"""

from ansible import arguments


# Note: this is not the singleton version.  That is only created once the program has actually
# parsed the args
CLIARGS = arguments.CLIArgs({})


class _Context:
    """
    Not yet ready for Prime Time

    Eventually this may allow for code which needs to run under different contexts (for instance, as
    if they were run with different command line args or from different current working directories)
    to exist in the same process.  But at the moment, we don't need that so this code has not been
    tested for suitability.
    """
    def __init__(self):
        global CLIARGS
        self._CLIARGS = arguments.CLIArgs(CLIARGS)

    @property
    def CLIARGS(self):
        return self._CLIARGS

    @CLIARGS.setter
    def CLIARGS_set(self, new_cli_args):
        if not isinstance(new_cli_args, arguments.CLIArgs):
            raise TypeError('CLIARGS must be of type (ansible.arguments.CLIArgs)')
        self._CLIARGS = new_cli_args


def _init_global_context(cli_args):
    """Initialize the global context objects"""
    global CLIARGS
    CLIARGS = arguments.GlobalCLIArgs.from_options(cli_args)
