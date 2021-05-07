"""Open a shell prompt inside an ansible-test environment."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ...util_common import (
    run_command,
)

from ...config import (
    ShellConfig,
)

from ...executor import (
    Delegate,
    create_shell_command,
    install_command_requirements,
)


def command_shell(args):
    """
    :type args: ShellConfig
    """
    if args.delegate:
        raise Delegate()

    install_command_requirements(args)

    cmd = create_shell_command(['bash', '-i'])
    run_command(args, cmd)
