"""Open a shell prompt inside an ansible-test environment."""
from __future__ import annotations

import os
import sys
import typing as t

from ...util import (
    ApplicationError,
    OutputStream,
    display,
)

from ...config import (
    ShellConfig,
)

from ...executor import (
    Delegate,
)

from ...connections import (
    Connection,
    LocalConnection,
    SshConnection,
)

from ...host_profiles import (
    ControllerProfile,
    PosixProfile,
    SshTargetHostProfile,
)

from ...provisioning import (
    prepare_profiles,
)

from ...host_configs import (
    ControllerConfig,
    OriginConfig,
)

from ...inventory import (
    create_controller_inventory,
    create_posix_inventory,
)


def command_shell(args: ShellConfig) -> None:
    """Entry point for the `shell` command."""
    if args.raw and isinstance(args.targets[0], ControllerConfig):
        raise ApplicationError('The --raw option has no effect on the controller.')

    if not args.export and not args.cmd and not sys.stdin.isatty():
        raise ApplicationError('Standard input must be a TTY to launch a shell.')

    host_state = prepare_profiles(args, skip_setup=args.raw)  # shell

    if args.delegate:
        raise Delegate(host_state=host_state)

    if args.raw and not isinstance(args.controller, OriginConfig):
        display.warning('The --raw option will only be applied to the target.')

    target_profile = t.cast(SshTargetHostProfile, host_state.target_profiles[0])

    if isinstance(target_profile, ControllerProfile):
        # run the shell locally unless a target was requested
        con: Connection = LocalConnection(args)

        if args.export:
            display.info('Configuring controller inventory.', verbosity=1)
            create_controller_inventory(args, args.export, host_state.controller_profile)
    else:
        # a target was requested, connect to it over SSH
        con = target_profile.get_controller_target_connections()[0]

        if args.export:
            display.info('Configuring target inventory.', verbosity=1)
            create_posix_inventory(args, args.export, host_state.target_profiles, True)

    if args.export:
        return

    if args.cmd:
        # Running a command is assumed to be non-interactive. Only a shell (no command) is interactive.
        # If we want to support interactive commands in the future, we'll need an `--interactive` command line option.
        # Command stderr output is allowed to mix with our own output, which is all sent to stderr.
        con.run(args.cmd, capture=False, interactive=False, output_stream=OutputStream.ORIGINAL)
        return

    if isinstance(con, SshConnection) and args.raw:
        cmd: list[str] = []
    elif isinstance(target_profile, PosixProfile):
        cmd = []

        if args.raw:
            shell = 'sh'  # shell required for non-ssh connection
        else:
            shell = 'bash'

            python = target_profile.python  # make sure the python interpreter has been initialized before opening a shell
            display.info(f'Target Python {python.version} is at: {python.path}')

            optional_vars = (
                'TERM',  # keep backspace working
            )

            env = {name: os.environ[name] for name in optional_vars if name in os.environ}

            if env:
                cmd = ['/usr/bin/env'] + [f'{name}={value}' for name, value in env.items()]

        cmd += [shell, '-i']
    else:
        cmd = []

    con.run(cmd, capture=False, interactive=True)
