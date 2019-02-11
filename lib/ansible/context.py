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

from ansible.module_utils.common._collections_compat import Mapping, Set
from ansible.module_utils.common.collections import is_sequence
from ansible.utils.context_objects import CLIArgs, GlobalCLIArgs


__all__ = ('CLIARGS',)

# Note: this is not the singleton version.  The Singleton is only created once the program has
# actually parsed the args
CLIARGS = CLIArgs({})


# This should be called immediately after cli_args are processed (parsed, validated, and any
# normalization performed on them).  No other code should call it
def _init_global_context(cli_args):
    """Initialize the global context objects"""
    global CLIARGS
    CLIARGS = GlobalCLIArgs.from_options(cli_args)


def cliargs_deferred_get(key, default=None, shallowcopy=False):
    """Closure over getting a key from CLIARGS with shallow copy functionality

    Primarily used in ``FieldAttribute`` where we need to defer setting the default
    until after the CLI arguments have been parsed

    This function is not directly bound to ``CliArgs`` so that it works with
    ``CLIARGS`` being replaced
    """
    def inner():
        value = CLIARGS.get(key, default=default)
        if not shallowcopy:
            return value
        elif is_sequence(value):
            return value[:]
        elif isinstance(value, (Mapping, Set)):
            return value.copy()
        return value
    return inner
