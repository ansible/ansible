"""Provision hosts for running tests."""
from __future__ import annotations

import collections.abc as c
import dataclasses
import functools
import itertools
import os
import pickle
import sys
import time
import traceback
import typing as t

from .config import (
    EnvironmentConfig,
)

from .util import (
    ApplicationError,
    HostConnectionError,
    display,
    open_binary_file,
    verify_sys_executable,
    version_to_str,
    type_guard,
)

from .util_common import (
    ExitHandler,
)

from .thread import (
    WrappedThread,
)

from .host_profiles import (
    ControllerHostProfile,
    DockerProfile,
    HostProfile,
    SshConnection,
    SshTargetHostProfile,
    create_host_profile,
)

from .pypi_proxy import (
    run_pypi_proxy,
)

THostProfile = t.TypeVar('THostProfile', bound=HostProfile)
TEnvironmentConfig = t.TypeVar('TEnvironmentConfig', bound=EnvironmentConfig)


class PrimeContainers(ApplicationError):
    """Exception raised to end execution early after priming containers."""


@dataclasses.dataclass(frozen=True)
class HostState:
    """State of hosts and profiles to be passed to ansible-test during delegation."""

    controller_profile: ControllerHostProfile
    target_profiles: list[HostProfile]

    @property
    def profiles(self) -> list[HostProfile]:
        """Return all the profiles as a list."""
        return [t.cast(HostProfile, self.controller_profile)] + self.target_profiles

    def serialize(self, path: str) -> None:
        """Serialize the host state to the given path."""
        with open_binary_file(path, 'wb') as state_file:
            pickle.dump(self, state_file)

    @staticmethod
    def deserialize(args: EnvironmentConfig, path: str) -> HostState:
        """Deserialize host state from the given args and path."""
        with open_binary_file(path) as state_file:
            host_state: HostState = pickle.load(state_file)

        host_state.controller_profile.args = args

        for target in host_state.target_profiles:
            target.args = args

        return host_state

    def get_controller_target_connections(self) -> list[SshConnection]:
        """Return SSH connection(s) for accessing all target hosts from the controller."""
        return list(itertools.chain.from_iterable([target.get_controller_target_connections() for
                                                   target in self.target_profiles if isinstance(target, SshTargetHostProfile)]))

    def targets(self, profile_type: t.Type[THostProfile]) -> list[THostProfile]:
        """The list of target(s), verified to be of the specified type."""
        if not self.target_profiles:
            raise Exception('No target profiles found.')

        assert type_guard(self.target_profiles, profile_type)

        return t.cast(list[THostProfile], self.target_profiles)


def prepare_profiles(
    args: TEnvironmentConfig,
    targets_use_pypi: bool = False,
    skip_setup: bool = False,
    requirements: t.Optional[c.Callable[[HostProfile], None]] = None,
) -> HostState:
    """
    Create new profiles, or load existing ones, and return them.
    If a requirements callback was provided, it will be used before configuring hosts if delegation has already been performed.
    """
    if args.host_path:
        host_state = HostState.deserialize(args, os.path.join(args.host_path, 'state.dat'))
    else:
        run_pypi_proxy(args, targets_use_pypi)

        host_state = HostState(
            controller_profile=t.cast(ControllerHostProfile, create_host_profile(args, args.controller, True)),
            target_profiles=[create_host_profile(args, target, False) for target in args.targets],
        )

        if args.prime_containers:
            for host_profile in host_state.profiles:
                if isinstance(host_profile, DockerProfile):
                    host_profile.provision()

            raise PrimeContainers()

        ExitHandler.register(functools.partial(cleanup_profiles, host_state))

        def provision(profile: HostProfile) -> None:
            """Provision the given profile."""
            profile.provision()

            if not skip_setup:
                profile.setup()

        dispatch_jobs([(profile, WrappedThread(functools.partial(provision, profile))) for profile in host_state.profiles])

        host_state.controller_profile.configure()

    if not args.delegate:
        check_controller_python(args, host_state)

        if requirements:
            requirements(host_state.controller_profile)

        def configure(profile: HostProfile) -> None:
            """Configure the given profile."""
            profile.wait()

            if not skip_setup:
                profile.configure()

            if requirements:
                requirements(profile)

        dispatch_jobs([(profile, WrappedThread(functools.partial(configure, profile))) for profile in host_state.target_profiles])

    return host_state


def check_controller_python(args: EnvironmentConfig, host_state: HostState) -> None:
    """Check the running environment to make sure it is what we expected."""
    sys_version = version_to_str(sys.version_info[:2])
    controller_python = host_state.controller_profile.python

    if expected_executable := verify_sys_executable(controller_python.path):
        raise ApplicationError(f'Running under Python interpreter "{sys.executable}" instead of "{expected_executable}".')

    expected_version = controller_python.version

    if expected_version != sys_version:
        raise ApplicationError(f'Running under Python version {sys_version} instead of {expected_version}.')

    args.controller_python = controller_python


def cleanup_profiles(host_state: HostState) -> None:
    """Cleanup provisioned hosts when exiting."""
    for profile in host_state.profiles:
        profile.deprovision()


def dispatch_jobs(jobs: list[tuple[HostProfile, WrappedThread]]) -> None:
    """Run the given profile job threads and wait for them to complete."""
    for profile, thread in jobs:
        thread.daemon = True
        thread.start()

    while any(thread.is_alive() for profile, thread in jobs):
        time.sleep(1)

    failed = False
    connection_failures = 0

    for profile, thread in jobs:
        try:
            thread.wait_for_result()
        except HostConnectionError as ex:
            display.error(f'Host {profile.config} connection failed:\n{ex}')
            failed = True
            connection_failures += 1
        except ApplicationError as ex:
            display.error(f'Host {profile.config} job failed:\n{ex}')
            failed = True
        except Exception as ex:  # pylint: disable=broad-except
            name = f'{"" if ex.__class__.__module__ == "builtins" else ex.__class__.__module__ + "."}{ex.__class__.__qualname__}'
            display.error(f'Host {profile.config} job failed:\nTraceback (most recent call last):\n'
                          f'{"".join(traceback.format_tb(ex.__traceback__)).rstrip()}\n{name}: {ex}')
            failed = True

    if connection_failures:
        raise HostConnectionError(f'Host job(s) failed, including {connection_failures} connection failure(s). See previous error(s) for details.')

    if failed:
        raise ApplicationError('Host job(s) failed. See previous error(s) for details.')
