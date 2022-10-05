#!/usr/bin/env python
"""Test suite used to verify ansible-test is able to run its containers on various container hosts."""

from __future__ import annotations

import abc
import dataclasses
import errno
import functools
import json
import os
import pathlib
import pwd
import signal
import secrets
import shlex
import shutil
import subprocess
import sys
import time
import typing as t

UNPRIVILEGED_USER_NAME = 'ansible-test'
CGROUP_SYSTEMD = pathlib.Path('/sys/fs/cgroup/systemd')


def main() -> None:
    """Main program entry point."""
    display.section('Startup check')

    try:
        with open('/etc/ansible-test.bootstrap') as bootstrap:
            bootstrap_type = bootstrap.read().strip()
    except FileNotFoundError:
        bootstrap_type = 'undefined'

    display.info(f'Bootstrap type: {bootstrap_type}')

    if bootstrap_type != 'remote':
        display.warning('Skipping destructive test on system which is not an ansible-test remote provisioned instance.')
        return

    display.section(f'Bootstrapping {os_release}')

    bootstrapper = Bootstrapper.init()
    bootstrapper.run()

    # exp = ExperimentalTest()
    # exp.run()
    # return

    scenarios = get_test_scenarios()
    results = [run_test(scenario) for scenario in scenarios]
    error_count = len([result for result in results if result.message])

    display.section(f'Test Results ({error_count=}/{len(results)})')

    for result in results:
        notes = f' <cleanup: {", ".join(result.cleanup)}>' if result.cleanup else ''

        if result.message:
            display.fatal(f'{result.scenario} {result.message}{notes}')
        else:
            display.show(f'PASS: {result.scenario}{notes}')

    if error_count:
        sys.exit(1)


def check(a, b):
    """Verify two values are equal."""
    if a != b:
        raise Exception(f"{a} != {b}")


class ExperimentalTest:
    """Tests to evaluate cgroup mount behavior."""
    def __init__(self):
        self.engine = 'podman'
        self.ssh = ['ssh', 'ansible-test@localhost']
        self.cgroup_systemd = pathlib.Path(CGROUP_SYSTEMD)

    def run(self) -> None:
        """Run all tests."""
        tests = [
            self.test_no_mount_point,
            self.test_not_mounted,
            self.test_mounted_after_prime,
            self.test_mounted_before_prime_root_owner,
            self.test_mounted_before_prime,
        ]

        self.prepare_host_for_experiment()

        try:
            for test in tests:
                try:
                    test()
                finally:
                    if have_cgroup_systemd():
                        remove_cgroup_systemd()
        finally:
            cleanup_podman()

    def prepare_host_for_experiment(self) -> None:
        """Create and remove cgroup hierarchy to ensure consistent behavior between test runs."""
        prepare_cgroup_systemd(None, self.engine)
        remove_cgroup_systemd()

    def prime(self) -> None:
        """Prepare podman for use."""
        cleanup_podman()
        run_command(*self.ssh, *prepare_prime_podman_storage())

    def query(self) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
        """Query /sys/fs/cgroup mounts and directories visible in a container."""
        mounts = self.query_mounts()
        directories = self.query_directories()

        return mounts, directories

    def query_mounts(self) -> dict[str, tuple[str, ...]]:
        """Query /sys/fs/cgroup mounts visible in a container."""
        mount = run_command(*self.ssh, shlex.join([
            self.engine, 'run', '--rm', '--systemd', 'always', '--volume', '/sys/fs/cgroup:/probe:ro', 'quay.io/ansible/ansible-test-utility-container:1.0.0',
            'cat', '/proc/self/mounts']), capture=True)

        mounts = {item[1]: item for item in [line.split() for line in mount.stdout.splitlines()]}

        targets = ('/probe', '/probe/systemd', '/sys/fs/cgroup', '/sys/fs/cgroup/systemd')

        for target in targets:
            if mount := mounts.get(target):
                print(f'{target} -> {mount}')

        return mounts

    def query_directories(self) -> dict[str, tuple[str, ...]]:
        """Query /sys/fs/cgroup directories visible in a container."""
        ls = run_command(*self.ssh, shlex.join([
            self.engine, 'run', '--rm', '--systemd', 'always', '--volume', '/sys/fs/cgroup:/probe:ro',
            'quay.io/ansible/ansible-test-utility-container:1.0.0', 'sh', '-c',
            'ls -ld /probe/systemd /sys/fs/cgroup/systemd || true']), capture=True)

        directories = {item[8]: [item[0]] + item[2:4] + [item[8]] for item in [line.split() for line in ls.stdout.splitlines()]}

        for directory, info in directories.items():
            print(f'{directory} -> {info}')

        return directories

    def test_no_mount_point(self) -> None:
        """Test without a mount point."""
        display.section('/sys/fs/cgroup/systemd directory does not exist')

        self.prime()

        mounts, directories = self.query()

        check(mounts.get('/probe', [])[0:3], ['cgroup_root', '/probe', 'tmpfs'])
        check(mounts.get('/probe/systemd'), None)
        check(mounts.get('/sys/fs/cgroup', [])[0:3], ['cgroup', '/sys/fs/cgroup', 'tmpfs'])
        check(mounts.get('/sys/fs/cgroup/systemd'), None)
        check(directories.get('/probe/systemd'), None)
        check(directories.get('/sys/fs/cgroup/systemd'), None)

    def test_not_mounted(self):
        """Test without /sys/fs/cgroup/systemd mounted."""
        display.section('/sys/fs/cgroup/systemd directory exists (owned by root) but is not mounted')

        self.cgroup_systemd.mkdir()

        self.prime()

        mounts, directories = self.query()

        self.cgroup_systemd.rmdir()

        check(mounts.get('/probe', [])[0:3], ['cgroup_root', '/probe', 'tmpfs'])
        check(mounts.get('/probe/systemd'), None)
        check(mounts.get('/sys/fs/cgroup', [])[0:3], ['cgroup', '/sys/fs/cgroup', 'tmpfs'])
        check(mounts.get('/sys/fs/cgroup/systemd'), None)
        check(directories.get('/probe/systemd'), ['drwxr-xr-x', 'nobody', 'nobody', '/probe/systemd'])
        check(directories.get('/sys/fs/cgroup/systemd'), None)

    def test_mounted_after_prime(self) -> None:
        """Test with /sys/fs/cgroup/systemd mounted after priming podman."""
        display.section('/sys/fs/cgroup/systemd mounted after prime')

        self.prime()

        prepare_cgroup_systemd(UNPRIVILEGED_USER_NAME, self.engine)

        mounts, directories = self.query()

        check(mounts.get('/probe', [])[0:3], ['cgroup_root', '/probe', 'tmpfs'])
        check(mounts.get('/probe/systemd'), None)
        check(mounts.get('/sys/fs/cgroup', [])[0:3], ['cgroup', '/sys/fs/cgroup', 'tmpfs'])
        check(mounts.get('/sys/fs/cgroup/systemd', [])[0:3], ['cgroup_root', '/sys/fs/cgroup/systemd', 'tmpfs'])
        check(directories.get('/probe/systemd'), ['drwxr-xr-x', 'nobody', 'nobody', '/probe/systemd'])
        check(directories.get('/sys/fs/cgroup/systemd'), ['drwxr-xr-x', 'nobody', 'nobody', '/sys/fs/cgroup/systemd'])

    def test_mounted_before_prime_root_owner(self) -> None:
        """Test with /sys/fs/cgroup/systemd mounted before priming podman, but owned by root."""
        display.section('/sys/fs/cgroup/systemd mounted before prime but owned by root')

        prepare_cgroup_systemd(None, self.engine)

        self.prime()

        mounts, directories = self.query()

        check(mounts.get('/probe', [])[0:3], ['cgroup_root', '/probe', 'tmpfs'])
        check(mounts.get('/probe/systemd')[0:3], ['cgroup', '/probe/systemd', 'cgroup'])
        check(mounts.get('/sys/fs/cgroup', [])[0:3], ['cgroup', '/sys/fs/cgroup', 'tmpfs'])
        check(mounts.get('/sys/fs/cgroup/systemd', [])[0:3], ['cgroup', '/sys/fs/cgroup/systemd', 'cgroup'])
        check(directories.get('/probe/systemd'), ['dr-xr-xr-x', 'nobody', 'nobody', '/probe/systemd'])
        check(directories.get('/sys/fs/cgroup/systemd'), ['dr-xr-xr-x', 'nobody', 'nobody', '/sys/fs/cgroup/systemd'])

    def test_mounted_before_prime(self) -> None:
        """Test with /sys/fs/cgroup/systemd mounted before priming podman."""
        display.section('/sys/fs/cgroup/systemd mounted before prime')

        prepare_cgroup_systemd(UNPRIVILEGED_USER_NAME, self.engine)

        self.prime()

        mounts, directories = self.query()

        check(mounts.get('/probe', [])[0:3], ['cgroup_root', '/probe', 'tmpfs'])
        check(mounts.get('/probe/systemd')[0:3], ['cgroup', '/probe/systemd', 'cgroup'])
        check(mounts.get('/sys/fs/cgroup', [])[0:3], ['cgroup', '/sys/fs/cgroup', 'tmpfs'])
        check(mounts.get('/sys/fs/cgroup/systemd', [])[0:3], ['cgroup', '/sys/fs/cgroup/systemd', 'cgroup'])
        check(directories.get('/probe/systemd'), ['dr-xr-xr-x', 'root', 'root', '/probe/systemd'])
        check(directories.get('/sys/fs/cgroup/systemd'), ['drwxr-xr-x', 'root', 'root', '/sys/fs/cgroup/systemd'])


def get_test_scenarios() -> list[TestScenario]:
    """Generate and return a list of test scenarios."""

    supported_engines = ('docker', 'podman')
    available_engines = [engine for engine in supported_engines if shutil.which(engine)]

    if not available_engines:
        raise ApplicationError(f'No supported container engines found: {", ".join(supported_engines)}')

    with open(pathlib.Path(os.environ['PYTHONPATH'], '../test/lib/ansible_test/_data/completion/docker.txt')) as docker_file:
        # TODO: consider including testing for the collection default image
        entries = {name: value for name, value in [parse_completion_entry(line) for line in docker_file.read().splitlines()]
                   if value.get('context') != 'collection'}

    scenarios: list[TestScenario] = []

    for container_name, settings in entries.items():
        image = settings['image']
        cgroup = settings.get('cgroup', 'v2')

        for engine in available_engines:
            # TODO: figure out how to get tests passing using docker without disabling selinux
            disable_selinux = os_release.id == 'fedora' and engine == 'docker' and cgroup != 'none'
            expose_cgroup_v1 = cgroup == 'v1' and get_docker_info(engine).cgroup_version != 1

            if cgroup != 'none' and get_docker_info(engine).cgroup_version == 1 and not have_cgroup_systemd():
                expose_cgroup_v1 = True  # the host uses cgroup v1 but there is no systemd cgroup and the container requires cgroup support

            user_names = [
                # TODO: add testing for rootless docker
                UNPRIVILEGED_USER_NAME,  # rootless (podman) and "normal" docker (loginuid not set)
            ]

            if engine == 'podman':
                # TODO: test rootless podman on Alpine and Ubuntu hosts
                if os_release.id not in ('alpine', 'ubuntu'):
                    user_names.append(f'{UNPRIVILEGED_USER_NAME}@localhost')  # rootless remote podman

                user_names.append('root')  # rootfull podman over ssh (loginuid matches user)
                user_names.append('')  # rootfull podman in the current session (loginuid doesn't match uid, due to use of sudo, su, etc. to run the test suite)

            for user_name in user_names:
                scenarios.append(
                    TestScenario(
                        user_name=user_name,
                        engine=engine,
                        disable_selinux=disable_selinux,
                        container_name=container_name,
                        image=image,
                        expose_cgroup_v1=expose_cgroup_v1,
                    )
                )

    return scenarios


def run_test(scenario: TestScenario) -> TestResult:
    """Run a test scenario and return the test results."""
    display.section(f'Testing {scenario}')

    integration = ['ansible-test', 'integration', 'split']
    integration_options = ['--target', f'docker:{scenario.container_name}', '--color', '--truncate', '0', '-v']

    commands = [
        [*integration, *integration_options],
        [*integration, '--controller', 'docker:alpine3', *integration_options],  # use alpine3 for the controller since it doesn't require the cgroup v1 hack
    ]

    env: dict[str, str] = {}

    if scenario.engine == 'podman':
        env.update(ANSIBLE_TEST_PREFER_PODMAN='1')

    prime_storage_command = []

    if scenario.hostname:
        # Run as the current user, which is root.
        # However, we'll set CONTAINER_HOST and CONTAINER_SSHKEY so that podman-remote is used.
        env.update(
            CONTAINER_HOST=f'ssh://{scenario.user}@{scenario.hostname}/run/user/{scenario.uid}/podman/podman.sock',
            CONTAINER_SSHKEY=str(pathlib.Path('~/.ssh/id_rsa').expanduser()),
        )

        become_cmd = ['ssh', f'{scenario.user}@{scenario.hostname}']
        test_commands = [['sh', '-c'] + [f'{format_env(env)} {shlex.join(command)}'] for command in commands]
    elif scenario.user:
        # Use SSH to run the tests so that /proc/self/loginuid reflects the user we're testing as.
        # Without this, the loginuid will be set to a value other than 4294967295 (-1) even though we've switched to root after login.
        become_cmd = ['ssh', f'{scenario.user}@localhost']
        test_commands = [become_cmd + [f'cd ~/ansible; {format_env(env)} {sys.executable} bin/{shlex.join(command)}'] for command in commands]
    else:
        # Run as the current user, which is root.
        # However, our loginuid ins't root since sudo, su, etc. was used after login.
        become_cmd = ['sh', '-c']
        test_commands = [become_cmd + [f'{format_env(env)} {shlex.join(command)}'] for command in commands]

    if scenario.engine == 'podman' and scenario.user == UNPRIVILEGED_USER_NAME:
        # When testing podman we need to make sure that the overlay filesystem is used instead of vfs.
        # Using the vfs filesystem will result in running out of disk space during the tests.
        # To change the filesystem used, the existing storage directory must be removed before "priming" the storage database.
        #
        # Without this change the following message may be displayed:
        #
        #   User-selected graph driver "overlay" overwritten by graph driver "vfs" from database - delete libpod local files to resolve
        #
        # However, with this change it may be replaced with the following message:
        #
        #   User-selected graph driver "vfs" overwritten by graph driver "overlay" from database - delete libpod local files to resolve

        prime_storage_command = become_cmd + prepare_prime_podman_storage()

    message = ''

    if scenario.expose_cgroup_v1:
        prepare_cgroup_systemd(UNPRIVILEGED_USER_NAME if scenario.user == UNPRIVILEGED_USER_NAME else None, scenario.engine)

    try:
        if prime_storage_command:
            run_command(*prime_storage_command)

        if scenario.disable_selinux:
            run_command('setenforce', 'permissive')

        for test_command in test_commands:
            run_command(*test_command)
    except SubprocessError as ex:
        message = str(ex)
        display.error(f'{scenario} {message}')
    finally:
        if scenario.disable_selinux:
            run_command('setenforce', 'enforcing')

        if scenario.expose_cgroup_v1:
            remove_cgroup_systemd()

        cleanup_command = [scenario.engine, 'rmi', '-f', scenario.image]

        try:
            run_command(*become_cmd + [shlex.join(cleanup_command)])
        except SubprocessError as ex:
            display.error(str(ex))

        cleanup = cleanup_podman() if scenario.engine == 'podman' else tuple()

    return TestResult(
        scenario=scenario,
        message=message,
        cleanup=cleanup,
    )


def prepare_prime_podman_storage() -> list[str]:
    """Partially prime podman storage and return a command to complete the remainder."""
    prime_storage_command = ['rm -rf ~/.local/share/containers; STORAGE_DRIVER=overlay podman pull quay.io/bedrock/alpine:3.16.2']

    test_containers = pathlib.Path(f'~{UNPRIVILEGED_USER_NAME}/.local/share/containers').expanduser()

    if test_containers.is_dir():
        # First remove the directory as root, since the user may not have permissions on all the files.
        # The directory will be removed again after login, before initializing the database.
        rmtree(test_containers)

    return prime_storage_command


def cleanup_podman() -> tuple[str, ...]:
    """Cleanup podman processes and files on disk."""
    cleanup = []

    for remaining in range(3, -1, -1):
        processes = [(int(item[0]), item[1]) for item in
                     [item.split(maxsplit=1) for item in run_command('ps', '-A', '-o', 'pid,comm', capture=True).stdout.splitlines()]
                     if pathlib.Path(item[1].split()[0]).name in ('catatonit', 'podman')]

        if not processes:
            break

        for pid, name in processes:
            display.info(f'Killing "{name}" ({pid}) ...')
            os.kill(pid, signal.SIGTERM if remaining > 1 else signal.SIGKILL)

            cleanup.append(name)

        time.sleep(1)
    else:
        raise Exception('failed to kill all matching processes')

    uid = pwd.getpwnam(UNPRIVILEGED_USER_NAME).pw_uid

    container_tmp = pathlib.Path(f'/tmp/containers-user-{uid}')
    podman_tmp = pathlib.Path(f'/tmp/podman-run-{uid}')

    user_config = pathlib.Path(f'~{UNPRIVILEGED_USER_NAME}/.config').expanduser()
    user_local = pathlib.Path(f'~{UNPRIVILEGED_USER_NAME}/.local').expanduser()

    if container_tmp.is_dir():
        rmtree(container_tmp)

    if podman_tmp.is_dir():
        rmtree(podman_tmp)

    if user_config.is_dir():
        rmtree(user_config)

    if user_local.is_dir():
        rmtree(user_local)

    return tuple(sorted(set(cleanup)))


def have_cgroup_systemd() -> bool:
    """Return True if the container host has a systemd cgroup."""
    return pathlib.Path(CGROUP_SYSTEMD).is_dir()


def prepare_cgroup_systemd(unprivileged_user: str | None, engine: str) -> None:
    """Prepare the systemd cgroup."""
    CGROUP_SYSTEMD.mkdir(exist_ok=True)

    run_command('mount', 'cgroup', '-t', 'cgroup', str(CGROUP_SYSTEMD), '-o', 'none,name=systemd,xattr', capture=True)

    if engine == 'podman':
        chown_user = unprivileged_user or 'root'
        run_command('chown', '-R', f'{chown_user}:{chown_user}', str(CGROUP_SYSTEMD))


def remove_cgroup_systemd() -> None:
    """Remove the systemd cgroup."""
    for sleep_seconds in range(1, 10):
        try:
            for dirpath, dirnames, filenames in os.walk(CGROUP_SYSTEMD, topdown=False):
                for dirname in dirnames:
                    pathlib.Path(dirpath, dirname).rmdir()
        except OSError as ex:
            if ex.errno != errno.EBUSY:
                raise

            error = str(ex)
        else:
            break

        display.warning(f'{error} -- sleeping for {sleep_seconds} second(s) before trying again ...')  # pylint: disable=used-before-assignment

        time.sleep(sleep_seconds)

    time.sleep(1)  # allow time for cgroups to be fully removed before unmounting

    run_command('umount', str(CGROUP_SYSTEMD))

    CGROUP_SYSTEMD.rmdir()

    time.sleep(1)  # allow time for cgroup hierarchy to be removed after unmounting

    with open('/proc/self/cgroup') as cgroup_file:
        cgroup = cgroup_file.read()

    if 'systemd' in cgroup:
        raise Exception('systemd hierarchy detected')


def rmtree(path: pathlib.Path) -> None:
    """Wrapper around shutil.rmtree with additional error handling."""
    for retries in range(10, -1, -1):
        try:
            display.info(f'rmtree: {path} ({retries} attempts remaining) ... ')
            shutil.rmtree(path)
        except Exception:
            if not path.exists():
                display.info(f'rmtree: {path} (not found)')
                return

            if not path.is_dir():
                display.info(f'rmtree: {path} (not a directory)')
                return

            if retries:
                continue

            raise
        else:
            display.info(f'rmtree: {path} (done)')
            return


def format_env(env: dict[str, str]) -> str:
    """Format an env dict for injection into a shell command and return the resulting string."""
    return ' '.join(f'{shlex.quote(key)}={shlex.quote(value)}' for key, value in env.items())


class DockerInfo:
    """The results of `docker info` for the container runtime."""

    def __init__(self, data: dict[str, t.Any]) -> None:
        self.data = data

    @property
    def cgroup_version(self) -> int:
        """The cgroup version of the container host."""
        data = self.data
        host = data.get('host')

        if host:
            version = int(host['cgroupVersion'].lstrip('v'))  # podman
        else:
            version = int(data['CgroupVersion'])  # docker

        return version


@functools.lru_cache
def get_docker_info(engine: str) -> DockerInfo:
    """Return info for the current container runtime. The results are cached."""
    return DockerInfo(json.loads(run_command(engine, 'info', '--format', '{{ json . }}', capture=True).stdout))


@dataclasses.dataclass(frozen=True)
class TestScenario:
    engine: str
    user_name: str
    container_name: str
    image: str
    disable_selinux: bool
    expose_cgroup_v1: bool

    @property
    def user(self) -> str:
        return self.user_name.split('@', maxsplit=1)[0]

    @property
    def hostname(self) -> str | None:
        parts = self.user_name.split('@', maxsplit=1)

        if len(parts) > 1:
            return parts[1]

        return None

    @property
    def uid(self) -> int:
        return pwd.getpwnam(self.user).pw_uid

    @property
    def tags(self) -> tuple[str, ...]:
        tags = []

        if self.hostname:
            tags.append(f'remote: {self.user_name}')
        elif self.user_name:
            tags.append(f'ssh: {self.user_name}')

        if self.disable_selinux:
            tags.append('selinux: permissive')

        if self.expose_cgroup_v1:
            tags.append('cgroup: v1')

        return tuple(tags)

    @property
    def tag_label(self) -> str:
        return ' '.join(f'[{tag}]' for tag in self.tags)

    def __str__(self):
        return f'[{self.container_name}] ({self.engine}) {self.tag_label}'.strip()


@dataclasses.dataclass(frozen=True)
class TestResult:
    scenario: TestScenario
    message: str
    cleanup: tuple[str, ...]


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
    YELLOW = '\033[33m'
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

    def info(self, message: str) -> None:
        """Print an info message to the console."""
        self.show(f'INFO: {message}', color=self.YELLOW)

    def show(self, message: str, color: str | None = None) -> None:
        """Print a message to the console."""
        for item in self.sensitive:
            message = message.replace(item, '*' * len(item))

        print(f'{color or self.CLEAR}{message}{self.CLEAR}', flush=True)


def run_module(
    module: str,
    args: dict[str, t.Any],
) -> SubprocessResult:
    """Run the specified Ansible module and return the result."""
    return run_command('ansible', '-m', module, '-v', '-a', json.dumps(args), 'localhost')


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


class Bootstrapper(metaclass=abc.ABCMeta):
    """Bootstrapper for remote instances."""

    @classmethod
    def install_podman(cls) -> bool:
        """Return True if podman will be installed."""
        return False

    @classmethod
    def install_docker(cls) -> bool:
        """Return True if docker will be installed."""
        return False

    @classmethod
    def usable(cls) -> bool:
        """Return True if the bootstrapper can be used, otherwise False."""
        return False

    @classmethod
    def init(cls) -> t.Type[Bootstrapper]:
        """Return a bootstrapper type appropriate for the current system."""
        for bootstrapper in cls.__subclasses__():
            if bootstrapper.usable():
                return bootstrapper

        display.warning('No supported bootstrapper found.')
        return Bootstrapper

    @classmethod
    def run(cls) -> None:
        """Run the bootstrapper."""
        cls.configure_root_user()
        cls.configure_unprivileged_user()
        cls.configure_source_trees()
        cls.configure_ssh_keys()
        cls.configure_podman_remote()

    @classmethod
    def configure_root_user(cls) -> None:
        """Configure the root user to run tests."""
        root_password_status = run_command('passwd', '--status', 'root', capture=True)
        root_password_set = root_password_status.stdout.split()[1]

        if root_password_set not in ('P', 'PS'):
            root_password = run_command('openssl', 'passwd', '-5', '-stdin', data=secrets.token_hex(8), capture=True).stdout.strip()

            run_module(
                'user',
                dict(
                    user='root',
                    password=root_password,
                ),
            )

    @classmethod
    def configure_unprivileged_user(cls) -> None:
        """Configure the unprivileged user to run tests."""
        unprivileged_password = run_command('openssl', 'passwd', '-5', '-stdin', data=secrets.token_hex(8), capture=True).stdout.strip()

        run_module(
            'user',
            dict(
                user=UNPRIVILEGED_USER_NAME,
                password=unprivileged_password,
                groups=['docker'] if cls.install_docker() else [],
                append=True,
            ),
        )

        if os_release.id == 'alpine':
            # Most distros handle this automatically, but not Alpine.
            # See: https://www.redhat.com/sysadmin/rootless-podman
            start = 165535
            end = start + 65535
            id_range = f'{start}-{end}'

            run_command(
                'usermod',
                '--add-subuids',
                id_range,
                '--add-subgids',
                id_range,
                UNPRIVILEGED_USER_NAME,
            )

    @classmethod
    def configure_source_trees(cls):
        """Configure the source trees needed to run tests for both root and the unprivileged user."""
        current_ansible = pathlib.Path(os.environ['PYTHONPATH']).parent

        root_ansible = pathlib.Path('~').expanduser() / 'ansible'
        test_ansible = pathlib.Path(f'~{UNPRIVILEGED_USER_NAME}').expanduser() / 'ansible'

        if current_ansible != root_ansible:
            display.info(f'copying {current_ansible} -> {root_ansible} ...')
            rmtree(root_ansible)
            shutil.copytree(current_ansible, root_ansible)
            run_command('chown', '-R', 'root:root', str(root_ansible))

        display.info(f'copying {current_ansible} -> {test_ansible} ...')
        rmtree(test_ansible)
        shutil.copytree(current_ansible, test_ansible)
        run_command('chown', '-R', f'{UNPRIVILEGED_USER_NAME}:{UNPRIVILEGED_USER_NAME}', str(test_ansible))

        paths = [pathlib.Path(test_ansible)]

        for root, dir_names, file_names in os.walk(test_ansible):
            paths.extend(pathlib.Path(root, dir_name) for dir_name in dir_names)
            paths.extend(pathlib.Path(root, file_name) for file_name in file_names)

        user = pwd.getpwnam(UNPRIVILEGED_USER_NAME)
        uid = user.pw_uid
        gid = user.pw_gid

        for path in paths:
            os.chown(path, uid, gid)

    @classmethod
    def configure_ssh_keys(cls) -> None:
        """Configure SSH keys needed to run tests."""
        user = pwd.getpwnam(UNPRIVILEGED_USER_NAME)
        uid = user.pw_uid
        gid = user.pw_gid

        current_rsa_pub = pathlib.Path('~/.ssh/id_rsa.pub').expanduser()

        test_authorized_keys = pathlib.Path(f'~{UNPRIVILEGED_USER_NAME}/.ssh/authorized_keys').expanduser()

        test_authorized_keys.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        os.chown(test_authorized_keys.parent, uid, gid)

        shutil.copyfile(current_rsa_pub, test_authorized_keys)
        os.chown(test_authorized_keys, uid, gid)
        test_authorized_keys.chmod(mode=0o644)

    @classmethod
    def configure_podman_remote(cls) -> None:
        """Configure podman remote support."""
        # TODO: figure out how to support remote podman without systemd (Alpine)
        # TODO: figure out how to support remote podman on Ubuntu
        if os_release.id in ('alpine', 'ubuntu'):
            return

        # Support podman remote on any host with systemd available.
        run_command('ssh', f'{UNPRIVILEGED_USER_NAME}@localhost', 'systemctl', '--user', 'enable', '--now', 'podman.socket')
        run_command('loginctl', 'enable-linger', UNPRIVILEGED_USER_NAME)


class DnfBootstrapper(Bootstrapper):
    """Bootstrapper for dnf based systems."""

    @classmethod
    def install_podman(cls) -> bool:
        """Return True if podman will be installed."""
        return True

    @classmethod
    def install_docker(cls) -> bool:
        """Return True if docker will be installed."""
        return os_release.id != 'rhel'

    @classmethod
    def usable(cls) -> bool:
        """Return True if the bootstrapper can be used, otherwise False."""
        return bool(shutil.which('dnf'))

    @classmethod
    def run(cls) -> None:
        """Run the bootstrapper."""
        # NOTE: Install crun to make it available to podman, otherwise installing moby-engine can cause podman to use runc instead.
        packages = ['podman', 'crun']

        if cls.install_docker():
            packages.append('moby-engine')

        run_command('dnf', 'install', '-y', *packages)

        if os_release.id != 'rhel':
            run_command('systemctl', 'start', 'docker')

        super().run()


class AptBootstrapper(Bootstrapper):
    """Bootstrapper for apt based systems."""

    @classmethod
    def install_podman(cls) -> bool:
        """Return True if podman will be installed."""
        return not (os_release.id == 'ubuntu' and os_release.version_id == '20.04')

    @classmethod
    def install_docker(cls) -> bool:
        """Return True if docker will be installed."""
        return True

    @classmethod
    def usable(cls) -> bool:
        """Return True if the bootstrapper can be used, otherwise False."""
        return bool(shutil.which('apt-get'))

    @classmethod
    def run(cls) -> None:
        """Run the bootstrapper."""
        apt_env = os.environ.copy()
        apt_env.update(
            DEBIAN_FRONTEND='noninteractive',
        )

        packages = ['docker.io']

        if cls.install_podman():
            # NOTE: Install crun to make it available to podman, otherwise installing docker.io can cause podman to use runc instead.
            # Using podman rootless requires the `newuidmap` and `slirp4netns` commands.
            packages.extend(('podman', 'crun', 'uidmap', 'slirp4netns'))

        run_command('apt-get', 'install', *packages, '-y', '--no-install-recommends', env=apt_env)

        super().run()


class ApkBootstrapper(Bootstrapper):
    """Bootstrapper for apk based systems."""

    @classmethod
    def install_podman(cls) -> bool:
        """Return True if podman will be installed."""
        return True

    @classmethod
    def install_docker(cls) -> bool:
        """Return True if docker will be installed."""
        return True

    @classmethod
    def usable(cls) -> bool:
        """Return True if the bootstrapper can be used, otherwise False."""
        return bool(shutil.which('apk'))

    @classmethod
    def run(cls) -> None:
        """Run the bootstrapper."""
        # The `openssl` package is used to generate hashed passwords.
        packages = ['docker', 'podman', 'openssl']

        run_command('apk', 'add', *packages)
        run_command('service', 'docker', 'start')
        run_command('modprobe', 'tun')

        super().run()


@dataclasses.dataclass(frozen=True)
class OsRelease:
    """Operating system identification."""

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
