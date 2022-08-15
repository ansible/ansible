#!/usr/bin/env python

from __future__ import annotations

import dataclasses
import os
import shlex
import shutil
import subprocess
import sys
import typing as t


def main() -> None:
    """Main program entry point."""
    bootstrapper = Bootstrapper.init()
    bootstrapper.run()

    test_images()


def test_images() -> None:
    """Test each supported docker image."""

    with open(os.path.join(os.environ['PYTHONPATH'], '../test/lib/ansible_test/_data/completion/docker.txt')) as docker_file:
        entries = {key: value for key, value in [parse_completion_entry(line) for line in docker_file.read().splitlines()] if 'context' not in value}

    results: list[tuple[str, str, str]] = []

    for name, settings in entries.items():
        if name == 'fedora35':
            continue  # deprecated, no point in testing

        image = settings['image']
        command = ['ansible-test', 'integration', 'split', '--target', f'docker:{name}', '--color', '--truncate', '0', '-v']

        podman_options = []

        if bool(shutil.which('docker')):
            podman_options.append(False)

        if bool(shutil.which('podman')):
            podman_options.append(True)

        if not podman_options:
            raise Exception()

        for use_podman in podman_options:
            test_env = os.environ.copy()

            if use_podman:
                test_env.update(ANSIBLE_TEST_PREFER_PODMAN='1')

            engine = 'podman' if use_podman else 'docker'

            display.section(f'Container: {name} ({engine})')

            try:
                run_command(*command, env=test_env)
            except SubprocessError as ex:
                message = str(ex)
                display.error(f'[{name}] ({engine}) {message}')
            else:
                message = ''

            results.append((name, engine, message))

            # avoid filling up the disk by removing images after testing them
            run_command(engine, 'rmi', '-f', image)

    error_count = 0

    for name, engine, message in results:
        if message:
            display.fatal(f'[{name}] ({engine}) {message}')
            error_count += 1
        else:
            display.show(f'PASS: [{name}] ({engine})')

    if error_count:
        sys.exit(1)


def parse_completion_entry(value: str) -> tuple[str, dict[str, str]]:
    """Parse the given completion entry, returning the entry name and a dictionary of key/value settings."""
    values = value.split()

    name = values[0]
    data = {kvp[0]: kvp[1] if len(kvp) > 1 else '' for kvp in [item.split('=', 1) for item in values[1:]]}

    return name, data


@dataclasses.dataclass(frozen=True)
class SubprocessResult:
    """Result from execution of a subprocess."""

    command: list[str]
    stdout: str
    stderr: str
    status: int


class ApplicationError(Exception):
    """An application error."""

    def __init__(self, message: str) -> None:
        self.message = message

        super().__init__(message)


class SubprocessError(ApplicationError):
    """An error from executing a subprocess."""

    def __init__(self, result: SubprocessResult) -> None:
        self.result = result

        message = f'Command `{shlex.join(result.command)}` exited with status: {result.status}'

        stdout = (result.stdout or '').strip()
        stderr = (result.stderr or '').strip()

        if stdout:
            message += f'\n>>> Standard Output\n{stdout}'

        if stderr:
            message += f'\n>>> Standard Error\n{stderr}'

        super().__init__(message)


class ProgramNotFoundError(ApplicationError):
    """A required program was not found."""

    def __init__(self, name: str) -> None:
        self.name = name

        super().__init__(f'Missing program: {name}')


class Display:
    """Display interface for sending output to the console."""

    CLEAR = '\033[0m'
    RED = '\033[31m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'

    def __init__(self) -> None:
        self.sensitive: set[str] = set()

    def section(self, message: str) -> None:
        """Print a section message to the console."""
        self.show(f'==> {message}', color=self.BLUE)

    def subsection(self, message: str) -> None:
        """Print a subsection message to the console."""
        self.show(f'--> {message}', color=self.CYAN)

    def fatal(self, message: str) -> None:
        """Print a fatal message to the console."""
        self.show(f'FATAL: {message}', color=self.RED)

    def error(self, message: str) -> None:
        """Print an error message to the console."""
        self.show(f'ERROR: {message}', color=self.RED)

    def warning(self, message: str) -> None:
        """Print a warning message to the console."""
        self.show(f'WARNING: {message}', color=self.PURPLE)

    def show(self, message: str, color: str | None = None) -> None:
        """Print a message to the console."""
        for item in self.sensitive:
            message = message.replace(item, '*' * len(item))

        print(f'{color or self.CLEAR}{message}{self.CLEAR}', flush=True)


def run_command(
    *command: str,
    data: str | None = None,
    stdin: int | t.IO[bytes] | None = None,
    env: dict[str, str] | None = None,
    capture: bool = False,
) -> SubprocessResult:
    """Run the specified command and return the result."""
    stdin = subprocess.PIPE if data else stdin or subprocess.DEVNULL
    stdout = subprocess.PIPE if capture else None
    stderr = subprocess.PIPE if capture else None

    display.subsection(f'Run command: {shlex.join(command)}')

    try:
        with subprocess.Popen(args=command, stdin=stdin, stdout=stdout, stderr=stderr, env=env, text=True) as process:
            process_stdout, process_stderr = process.communicate(data)
            process_status = process.returncode
    except FileNotFoundError:
        raise ProgramNotFoundError(command[0]) from None

    result = SubprocessResult(
        command=list(command),
        stdout=process_stdout,
        stderr=process_stderr,
        status=process_status,
    )

    if process.returncode != 0:
        raise SubprocessError(result)

    return result


class Bootstrapper:
    """Bootstrapper for remote instances."""

    @classmethod
    def usable(cls) -> bool:
        """Return True if the bootstrapper can be used, otherwise False."""
        return False

    @staticmethod
    def run() -> None:
        """Run the bootstrapper."""

    @classmethod
    def init(cls) -> t.Type[Bootstrapper]:
        """Return a bootstrapper type appropriate for the current system."""
        for bootstrapper in cls.__subclasses__():
            if bootstrapper.usable():
                return bootstrapper

        display.warning('No supported bootstrapper found.')
        return Bootstrapper


class DnfBootstrapper(Bootstrapper):
    """Bootstrapper for dnf based systems."""

    @classmethod
    def usable(cls) -> bool:
        """Return True if the bootstrapper can be used, otherwise False."""
        return bool(shutil.which('dnf'))

    @staticmethod
    def run() -> None:
        """Run the bootstrapper."""
        packages = ['podman']

        if os_release.id != 'rhel':
            packages.append('moby-engine')

        run_command('dnf', 'install', '-y', *packages)

        if os_release.id != 'rhel':
            run_command('service', 'docker', 'start')


class AptBootstrapper(Bootstrapper):
    """Bootstrapper for apt based systems."""

    @classmethod
    def usable(cls) -> bool:
        """Return True if the bootstrapper can be used, otherwise False."""
        return bool(shutil.which('apt-get'))

    @staticmethod
    def run() -> None:
        """Run the bootstrapper."""
        apt_env = os.environ.copy()
        apt_env.update(
            DEBIAN_FRONTEND='noninteractive',
        )

        packages = ['docker.io']

        if os_release.id != 'ubuntu' or os_release.version_id != '20.04':
            packages.append('podman')

        run_command('apt-get', 'install', *packages, '-y', '--no-install-recommends', env=apt_env)


class ApkBootstrapper(Bootstrapper):
    """Bootstrapper for apk based systems."""

    @classmethod
    def usable(cls) -> bool:
        """Return True if the bootstrapper can be used, otherwise False."""
        return bool(shutil.which('apk'))

    @staticmethod
    def run() -> None:
        """Run the bootstrapper."""
        packages = ['docker', 'podman']

        run_command('apk', 'add', *packages)
        run_command('service', 'docker', 'start')


@dataclasses.dataclass(frozen=True)
class OsRelease:
    id: str
    version_id: str

    @staticmethod
    def init() -> OsRelease:
        """Detect the current OS release and return the result."""
        lines = run_command('sh', '-c', '. /etc/os-release && echo $ID && echo $VERSION_ID', capture=True).stdout.splitlines()

        result = OsRelease(
            id=lines[0],
            version_id=lines[1],
        )

        display.show(f'Detected OS "{result.id}" version "{result.version_id}".')

        return result


display = Display()
os_release = OsRelease.init()

if __name__ == '__main__':
    main()
