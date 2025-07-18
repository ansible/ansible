"""Open a shell prompt inside an ansible-test environment."""

from __future__ import annotations

import contextlib
import dataclasses
import os
import sys
import typing as t

from ...data import (
    data_context,
)

from ...util import (
    ApplicationError,
    OutputStream,
    display,
    SubprocessError,
    HostConnectionError,
)

from ...ansible_util import (
    ansible_environment,
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
    DebuggableProfile,
)

from ...provisioning import (
    prepare_profiles,
)

from ...host_configs import (
    OriginConfig,
)

from ...inventory import (
    create_controller_inventory,
    create_posix_inventory,
)

from ...python_requirements import (
    install_requirements,
)

from ...util_common import (
    get_injector_env,
)

from ...delegation import (
    metadata_context,
)


def command_shell(args: ShellConfig) -> None:
    """Entry point for the `shell` command."""
    if not args.export and not args.cmd and not sys.stdin.isatty():
        raise ApplicationError('Standard input must be a TTY to launch a shell.')

    host_state = prepare_profiles(args, skip_setup=args.raw)  # shell

    if args.delegate:
        raise Delegate(host_state=host_state)

    install_requirements(args, host_state.controller_profile, host_state.controller_profile.python)  # shell

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

    if isinstance(con, LocalConnection) and isinstance(target_profile, DebuggableProfile) and target_profile.debugging_enabled:
        # HACK: ensure the debugger port visible in the shell is the forwarded port, not the original
        args.metadata.debugger_settings = dataclasses.replace(args.metadata.debugger_settings, port=target_profile.debugger_port)

    with contextlib.nullcontext() if data_context().content.unsupported else metadata_context(args):
        if args.cmd:
            non_interactive_shell(args, target_profile, con)
        else:
            interactive_shell(args, target_profile, con)


def non_interactive_shell(
    args: ShellConfig,
    target_profile: SshTargetHostProfile,
    con: Connection,
) -> None:
    """Run a non-interactive shell command."""
    if isinstance(target_profile, PosixProfile):
        env = get_environment_variables(args, target_profile, con)
        cmd = get_env_command(env) + args.cmd
    else:
        cmd = args.cmd

    # Running a command is assumed to be non-interactive. Only a shell (no command) is interactive.
    # If we want to support interactive commands in the future, we'll need an `--interactive` command line option.
    # Command stderr output is allowed to mix with our own output, which is all sent to stderr.
    con.run(cmd, capture=False, interactive=False, output_stream=OutputStream.ORIGINAL)


def interactive_shell(
    args: ShellConfig,
    target_profile: SshTargetHostProfile,
    con: Connection,
) -> None:
    """Run an interactive shell."""
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

            env = get_environment_variables(args, target_profile, con)
            cmd = get_env_command(env)

        cmd += [shell, '-i']
    else:
        cmd = []

    try:
        con.run(cmd, capture=False, interactive=True)
    except SubprocessError as ex:
        if isinstance(con, SshConnection) and ex.status == 255:
            # 255 indicates SSH itself failed, rather than a command run on the remote host.
            # In this case, report a host connection error so additional troubleshooting output is provided.
            if not args.delegate and not args.host_path:

                def callback() -> None:
                    """Callback to run during error display."""
                    target_profile.on_target_failure()  # when the controller is not delegated, report failures immediately

            else:
                callback = None

            raise HostConnectionError(f'SSH shell connection failed for host {target_profile.config}: {ex}', callback) from ex

        raise


def get_env_command(env: dict[str, str]) -> list[str]:
    """Get an `env` command to set the given environment variables, if any."""
    if not env:
        return []

    return ['/usr/bin/env'] + [f'{name}={value}' for name, value in env.items()]


def get_environment_variables(
    args: ShellConfig,
    target_profile: PosixProfile,
    con: Connection,
) -> dict[str, str]:
    """Get the environment variables to expose to the shell."""
    if data_context().content.unsupported:
        return {}

    optional_vars = (
        'TERM',  # keep backspace working
    )

    env = {name: os.environ[name] for name in optional_vars if name in os.environ}

    if isinstance(con, LocalConnection):  # configure the controller environment
        env.update(ansible_environment(args))
        env.update(get_injector_env(target_profile.python, env))
        env.update(ANSIBLE_TEST_METADATA_PATH=os.path.abspath(args.metadata_path))

        if isinstance(target_profile, DebuggableProfile):
            env.update(target_profile.get_ansiballz_environment_variables())
            env.update(target_profile.get_ansible_cli_environment_variables())

    return env
