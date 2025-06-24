#!/usr/bin/env python
"""Test suite used to verify ansible-test is able to run its containers on various container hosts."""

from __future__ import annotations

import abc
import dataclasses
import datetime
import errno
import functools
import json
import os
import pathlib
import pwd
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import time
import typing as t

UNPRIVILEGED_USER_NAME = 'ansible-test'
CGROUP_ROOT = pathlib.Path('/sys/fs/cgroup')
CGROUP_SYSTEMD = CGROUP_ROOT / 'systemd'
LOG_PATH = pathlib.Path('/tmp/results')

# The value of /proc/*/loginuid when it is not set.
# It is a reserved UID, which is the maximum 32-bit unsigned integer value.
# See: https://access.redhat.com/solutions/25404
LOGINUID_NOT_SET = 4294967295

UID = os.getuid()

try:
    LOGINUID = int(pathlib.Path('/proc/self/loginuid').read_text())
    LOGINUID_MISMATCH = LOGINUID != LOGINUID_NOT_SET and LOGINUID != UID
except FileNotFoundError:
    LOGINUID = None
    LOGINUID_MISMATCH = False


def main() -> None:
    """Main program entry point."""
    display.section('Startup check')

    try:
        bootstrap_type = pathlib.Path('/etc/ansible-test.bootstrap').read_text().strip()
    except FileNotFoundError:
        bootstrap_type = 'undefined'

    display.info(f'Bootstrap type: {bootstrap_type}')

    if bootstrap_type != 'remote':
        display.warning('Skipping destructive test on system which is not an ansible-test remote provisioned instance.')
        return

    display.info(f'UID: {UID} / {LOGINUID}')

    if UID != 0:
        raise Exception('This test must be run as root.')

    if not LOGINUID_MISMATCH:
        if LOGINUID is None:
            display.warning('Tests involving loginuid mismatch will be skipped on this host since it does not have audit support.')
        elif LOGINUID == LOGINUID_NOT_SET:
            display.warning('Tests involving loginuid mismatch will be skipped on this host since it is not set.')
        elif LOGINUID == 0:
            raise Exception('Use sudo, su, etc. as a non-root user to become root before running this test.')
        else:
            raise Exception()

    display.section(f'Bootstrapping {os_release}')

    bootstrapper = Bootstrapper.init()
    bootstrapper.run()

    result_dir = LOG_PATH

    if result_dir.exists():
        shutil.rmtree(result_dir)

    result_dir.mkdir()
    result_dir.chmod(0o777)

    scenarios = get_test_scenarios()
    results = [run_test(scenario) for scenario in scenarios]
    error_total = 0

    for name in sorted(result_dir.glob('*.log')):
        lines = name.read_text().strip().splitlines()
        error_count = len([line for line in lines if line.startswith('FAIL: ')])
        error_total += error_count

        display.section(f'Log ({error_count=}/{len(lines)}): {name.name}')

        for line in lines:
            if line.startswith('FAIL: '):
                display.show(line, display.RED)
            else:
                display.show(line)

    error_count = len([result for result in results if result.message])
    error_total += error_count

    duration = datetime.timedelta(seconds=int(sum(result.duration.total_seconds() for result in results)))

    display.section(f'Test Results ({error_count=}/{len(results)}) [{duration}]')

    for result in results:
        notes = f' <cleanup: {", ".join(result.cleanup)}>' if result.cleanup else ''

        if result.cgroup_dirs:
            notes += f' <cgroup_dirs: {len(result.cgroup_dirs)}>'

        notes += f' [{result.duration}]'

        if result.message:
            display.show(f'FAIL: {result.scenario} {result.message}{notes}', display.RED)
        elif result.duration.total_seconds() >= 90:
            display.show(f'SLOW: {result.scenario}{notes}', display.YELLOW)
        else:
            display.show(f'PASS: {result.scenario}{notes}')

    if error_total:
        sys.exit(1)


def get_container_completion_entries() -> dict[str, dict[str, str]]:
    """Parse and return the ansible-test container completion entries."""
    completion_lines = pathlib.Path(os.environ['PYTHONPATH'], '../test/lib/ansible_test/_data/completion/docker.txt').read_text().splitlines()

    # TODO: consider including testing for the collection default image
    entries = {name: value for name, value in (parse_completion_entry(line) for line in completion_lines) if name != 'default'}

    return entries


def get_test_scenarios() -> list[TestScenario]:
    """Generate and return a list of test scenarios."""

    supported_engines = ('docker', 'podman')
    available_engines = [engine for engine in supported_engines if shutil.which(engine)]

    if not available_engines:
        raise ApplicationError(f'No supported container engines found: {", ".join(supported_engines)}')

    entries = get_container_completion_entries()

    unprivileged_user = User.get(UNPRIVILEGED_USER_NAME)

    scenarios: list[TestScenario] = []

    for container_name, settings in entries.items():
        image = settings['image']
        cgroup = settings.get('cgroup', 'v1-v2')

        if container_name == 'centos6' and os_release.id == 'alpine':
            # Alpine kernels do not emulate vsyscall by default, which causes the centos6 container to fail during init.
            # See: https://unix.stackexchange.com/questions/478387/running-a-centos-docker-image-on-arch-linux-exits-with-code-139
            # Other distributions enable settings which trap vsyscall by default.
            # See: https://www.kernelconfig.io/config_legacy_vsyscall_xonly
            # See: https://www.kernelconfig.io/config_legacy_vsyscall_emulate
            continue

        for engine in available_engines:
            # TODO: figure out how to get tests passing using docker without disabling selinux
            disable_selinux = os_release.id == 'fedora' and engine == 'docker' and cgroup != 'none'
            debug_systemd = cgroup != 'none'

            # The sleep+pkill used to support the cgroup probe causes problems with the centos6 container.
            # It results in sshd connections being refused or reset for many, but not all, container instances.
            # The underlying cause of this issue is unknown.
            probe_cgroups = container_name != 'centos6'

            # The default RHEL 9 crypto policy prevents use of SHA-1.
            # This results in SSH errors with centos6 containers: ssh_dispatch_run_fatal: Connection to 1.2.3.4 port 22: error in libcrypto
            # See: https://access.redhat.com/solutions/6816771
            enable_sha1 = os_release.id == 'rhel' and os_release.version_id.startswith('9.') and container_name == 'centos6'

            # Starting with Fedora 40, use of /usr/sbin/unix-chkpwd fails under Ubuntu 24.04 due to AppArmor.
            # This prevents SSH logins from completing due to unix-chkpwd failing to look up the user with getpwnam.
            # Disabling the 'unix-chkpwd' profile works around the issue, but does not solve the underlying problem.
            disable_apparmor_profile_unix_chkpwd = engine == 'podman' and os_release.id == 'ubuntu' and container_name.startswith('fedora')

            cgroup_version = get_docker_info(engine).cgroup_version

            user_scenarios = [
                # TODO: test rootless docker
                UserScenario(ssh=unprivileged_user),
            ]

            if engine == 'podman':
                if os_release.id not in ('ubuntu',):
                    # rootfull podman is not supported by all systems
                    user_scenarios.append(UserScenario(ssh=ROOT_USER))

                # TODO: test podman remote on Alpine and Ubuntu hosts
                # TODO: combine remote with ssh using different unprivileged users
                if os_release.id not in ('alpine', 'ubuntu'):
                    user_scenarios.append(UserScenario(remote=unprivileged_user))

                if LOGINUID_MISMATCH and os_release.id not in ('ubuntu',):
                    # rootfull podman is not supported by all systems
                    user_scenarios.append(UserScenario())

            for user_scenario in user_scenarios:
                expose_cgroup_version: int | None = None  # by default the host is assumed to provide sufficient cgroup support for the container and scenario

                if cgroup == 'v1-only' and cgroup_version != 1:
                    expose_cgroup_version = 1  # the container requires cgroup v1 support and the host does not use cgroup v1
                elif cgroup != 'none' and not have_systemd():
                    # the container requires cgroup support and the host does not use systemd
                    if cgroup_version == 1:
                        expose_cgroup_version = 1  # cgroup v1 mount required
                    elif cgroup_version == 2 and engine == 'podman' and user_scenario.actual != ROOT_USER:
                        # Running a systemd container on a non-systemd host with cgroup v2 fails for rootless podman.
                        # It may be possible to support this scenario, but the necessary configuration to do so is unknown.
                        display.warning(f'Skipping testing of {container_name!r} with rootless podman because the host uses cgroup v2 without systemd.')
                        continue

                scenarios.append(
                    TestScenario(
                        user_scenario=user_scenario,
                        engine=engine,
                        container_name=container_name,
                        image=image,
                        disable_selinux=disable_selinux,
                        expose_cgroup_version=expose_cgroup_version,
                        enable_sha1=enable_sha1,
                        debug_systemd=debug_systemd,
                        probe_cgroups=probe_cgroups,
                        disable_apparmor_profile_unix_chkpwd=disable_apparmor_profile_unix_chkpwd,
                    )
                )

    return scenarios


def run_test(scenario: TestScenario) -> TestResult:
    """Run a test scenario and return the test results."""
    display.section(f'Testing {scenario} Started')

    start = time.monotonic()

    integration = ['ansible-test', 'integration', 'split']
    integration_options = ['--target', f'docker:{scenario.container_name}', '--color', '--truncate', '0', '-v']
    target_only_options = []

    if scenario.debug_systemd:
        integration_options.append('--dev-systemd-debug')

    if scenario.probe_cgroups:
        target_only_options = ['--dev-probe-cgroups', str(LOG_PATH)]

    entries = get_container_completion_entries()
    alpine_container = [name for name in entries if name.startswith('alpine')][0]

    commands = [
        # The cgroup probe is only performed for the first test of the target.
        # There's no need to repeat the probe again for the same target.
        # The controller will be tested separately as a target.
        # This ensures that both the probe and no-probe code paths are functional.
        [*integration, *integration_options, *target_only_options],
        # For the split test we'll use Alpine Linux as the controller. There are two reasons for this:
        # 1) It doesn't require the cgroup v1 hack, so we can test a target that doesn't need that.
        # 2) It doesn't require disabling selinux, so we can test a target that doesn't need that.
        [*integration, '--controller', f'docker:{alpine_container}', *integration_options],
    ]

    common_env: dict[str, str] = {}
    test_env: dict[str, str] = {}

    if scenario.engine == 'podman':
        if scenario.user_scenario.remote:
            common_env.update(
                # Podman 4.3.0 has a regression which requires a port for remote connections to work.
                # See: https://github.com/containers/podman/issues/16509
                CONTAINER_HOST=f'ssh://{scenario.user_scenario.remote.name}@localhost:22'
                               f'/run/user/{scenario.user_scenario.remote.pwnam.pw_uid}/podman/podman.sock',
                CONTAINER_SSHKEY=str(pathlib.Path('~/.ssh/id_rsa').expanduser()),  # TODO: add support for ssh + remote when the ssh user is not root
            )

        test_env.update(ANSIBLE_TEST_PREFER_PODMAN='1')

    test_env.update(common_env)

    if scenario.user_scenario.ssh:
        client_become_cmd = ['ssh', f'{scenario.user_scenario.ssh.name}@localhost']
        test_commands = [client_become_cmd + [f'cd ~/ansible; {format_env(test_env)}{sys.executable} bin/{shlex.join(command)}'] for command in commands]
    else:
        client_become_cmd = ['sh', '-c']
        test_commands = [client_become_cmd + [f'{format_env(test_env)}{shlex.join(command)}'] for command in commands]

    prime_storage_command = []

    if scenario.engine == 'podman' and scenario.user_scenario.actual.name == UNPRIVILEGED_USER_NAME:
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

        actual_become_cmd = ['ssh', f'{scenario.user_scenario.actual.name}@localhost']
        prime_storage_command = actual_become_cmd + prepare_prime_podman_storage()

    message = ''

    if scenario.expose_cgroup_version == 1:
        prepare_cgroup_systemd(scenario.user_scenario.actual.name, scenario.engine)

    try:
        if prime_storage_command:
            retry_command(lambda: run_command(*prime_storage_command), retry_any_error=True)

        if scenario.disable_selinux:
            run_command('setenforce', 'permissive')

        if scenario.enable_sha1:
            run_command('update-crypto-policies', '--set', 'DEFAULT:SHA1')

        if scenario.disable_apparmor_profile_unix_chkpwd:
            os.symlink('/etc/apparmor.d/unix-chkpwd', '/etc/apparmor.d/disable/unix-chkpwd')
            run_command('apparmor_parser', '-R', '/etc/apparmor.d/unix-chkpwd')

        for test_command in test_commands:
            def run_test_command() -> SubprocessResult:
                if os_release.id == 'alpine' and scenario.user_scenario.actual.name != 'root':
                    # Make sure rootless networking works on Alpine.
                    # NOTE: The path used below differs slightly from the referenced issue.
                    # See: https://gitlab.alpinelinux.org/alpine/aports/-/issues/16137
                    actual_pwnam = scenario.user_scenario.actual.pwnam
                    root_path = pathlib.Path(f'/tmp/storage-run-{actual_pwnam.pw_uid}')
                    run_path = root_path / 'containers/networks/rootless-netns/run'
                    run_path.mkdir(mode=0o755, parents=True, exist_ok=True)

                    while run_path.is_relative_to(root_path):
                        os.chown(run_path, actual_pwnam.pw_uid, actual_pwnam.pw_gid)
                        run_path = run_path.parent

                return run_command(*test_command)

            retry_command(run_test_command)
    except SubprocessError as ex:
        message = str(ex)
        display.error(f'{scenario} {message}')
    finally:
        if scenario.disable_apparmor_profile_unix_chkpwd:
            os.unlink('/etc/apparmor.d/disable/unix-chkpwd')
            run_command('apparmor_parser', '/etc/apparmor.d/unix-chkpwd')

        if scenario.enable_sha1:
            run_command('update-crypto-policies', '--set', 'DEFAULT')

        if scenario.disable_selinux:
            run_command('setenforce', 'enforcing')

        if scenario.expose_cgroup_version == 1:
            dirs = remove_cgroup_systemd()
        else:
            dirs = list_group_systemd()

        cleanup_command = [scenario.engine, 'rmi', '-f', scenario.image]

        try:
            retry_command(lambda: run_command(*client_become_cmd + [f'{format_env(common_env)}{shlex.join(cleanup_command)}']), retry_any_error=True)
        except SubprocessError as ex:
            display.error(str(ex))

        cleanup = cleanup_podman() if scenario.engine == 'podman' else tuple()

    finish = time.monotonic()
    duration = datetime.timedelta(seconds=int(finish - start))

    display.section(f'Testing {scenario} Completed in {duration}')

    return TestResult(
        scenario=scenario,
        message=message,
        cleanup=cleanup,
        duration=duration,
        cgroup_dirs=tuple(str(path) for path in dirs),
    )


def prepare_prime_podman_storage() -> list[str]:
    """Partially prime podman storage and return a command to complete the remainder."""
    prime_storage_command = ['rm -rf ~/.local/share/containers; STORAGE_DRIVER=overlay podman pull public.ecr.aws/docker/library/alpine:3.21.2']

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
                     if pathlib.Path(item[1].split()[0]).name in ('catatonit', 'podman', 'conmon')]

        if not processes:
            break

        for pid, name in processes:
            display.info(f'Killing "{name}" ({pid}) ...')

            try:
                os.kill(pid, signal.SIGTERM if remaining > 1 else signal.SIGKILL)
            except ProcessLookupError:
                pass

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


def have_systemd() -> bool:
    """Return True if the host uses systemd."""
    return pathlib.Path('/run/systemd/system').is_dir()


def prepare_cgroup_systemd(username: str, engine: str) -> None:
    """Prepare the systemd cgroup."""
    CGROUP_SYSTEMD.mkdir()

    run_command('mount', 'cgroup', '-t', 'cgroup', str(CGROUP_SYSTEMD), '-o', 'none,name=systemd,xattr', capture=True)

    if engine == 'podman':
        run_command('chown', '-R', f'{username}:{username}', str(CGROUP_SYSTEMD))

    run_command('find', str(CGROUP_SYSTEMD), '-type', 'd', '-exec', 'ls', '-l', '{}', ';')


def list_group_systemd() -> list[pathlib.Path]:
    """List the systemd cgroup."""
    dirs = set()

    for dirpath, dirnames, filenames in os.walk(CGROUP_SYSTEMD, topdown=False):
        for dirname in dirnames:
            target_path = pathlib.Path(dirpath, dirname)
            display.info(f'dir: {target_path}')
            dirs.add(target_path)

    return sorted(dirs)


def remove_cgroup_systemd() -> list[pathlib.Path]:
    """Remove the systemd cgroup."""
    dirs = set()

    for sleep_seconds in range(1, 10):
        try:
            for dirpath, dirnames, filenames in os.walk(CGROUP_SYSTEMD, topdown=False):
                for dirname in dirnames:
                    target_path = pathlib.Path(dirpath, dirname)
                    display.info(f'rmdir: {target_path}')
                    dirs.add(target_path)
                    target_path.rmdir()
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

    cgroup = pathlib.Path('/proc/self/cgroup').read_text()

    if 'systemd' in cgroup:
        raise Exception('systemd hierarchy detected')

    return sorted(dirs)


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
    if env:
        return ' '.join(f'{shlex.quote(key)}={shlex.quote(value)}' for key, value in env.items()) + ' '

    return ''


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
class User:
    name: str
    pwnam: pwd.struct_passwd

    @classmethod
    def get(cls, name: str) -> User:
        return User(
            name=name,
            pwnam=pwd.getpwnam(name),
        )


@dataclasses.dataclass(frozen=True)
class UserScenario:
    ssh: User = None
    remote: User = None

    @property
    def actual(self) -> User:
        return self.remote or self.ssh or ROOT_USER


@dataclasses.dataclass(frozen=True)
class TestScenario:
    user_scenario: UserScenario
    engine: str
    container_name: str
    image: str
    disable_selinux: bool
    expose_cgroup_version: int | None
    enable_sha1: bool
    debug_systemd: bool
    probe_cgroups: bool
    disable_apparmor_profile_unix_chkpwd: bool

    @property
    def tags(self) -> tuple[str, ...]:
        tags = []

        if self.user_scenario.ssh:
            tags.append(f'ssh: {self.user_scenario.ssh.name}')

        if self.user_scenario.remote:
            tags.append(f'remote: {self.user_scenario.remote.name}')

        if self.disable_selinux:
            tags.append('selinux: permissive')

        if self.expose_cgroup_version is not None:
            tags.append(f'cgroup: {self.expose_cgroup_version}')

        if self.enable_sha1:
            tags.append('sha1: enabled')

        if self.disable_apparmor_profile_unix_chkpwd:
            tags.append('apparmor(unix-chkpwd): disabled')

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
    duration: datetime.timedelta
    cgroup_dirs: tuple[str, ...]


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
    GREEN = '\033[32m'
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


def retry_command(func: t.Callable[[], SubprocessResult], attempts: int = 3, retry_any_error: bool = False) -> SubprocessResult:
    """Run the given command function up to the specified number of attempts when the failure is due to an SSH error."""
    for attempts_remaining in range(attempts - 1, -1, -1):
        try:
            return func()
        except SubprocessError as ex:
            if ex.result.command[0] == 'ssh' and ex.result.status == 255 and attempts_remaining:
                # SSH connections on our Ubuntu 22.04 host sometimes fail for unknown reasons.
                # This retry should allow the test suite to continue, maintaining CI stability.
                # TODO: Figure out why local SSH connections sometimes fail during the test run.
                display.warning('Command failed due to an SSH error. Waiting a few seconds before retrying.')
                time.sleep(3)
                continue

            if retry_any_error:
                display.warning('Command failed. Waiting a few seconds before retrying.')
                time.sleep(3)
                continue

            raise


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
        retry_command(lambda: run_command('ssh', f'{UNPRIVILEGED_USER_NAME}@localhost', 'systemctl', '--user', 'enable', '--now', 'podman.socket'))
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

        if os_release.id == 'rhel':
            # As of the release of RHEL 9.1, installing podman on RHEL 9.0 results in a non-fatal error at install time:
            #
            #   libsemanage.semanage_pipe_data: Child process /usr/libexec/selinux/hll/pp failed with code: 255. (No such file or directory).
            #   container: libsepol.policydb_read: policydb module version 21 does not match my version range 4-20
            #   container: libsepol.sepol_module_package_read: invalid module in module package (at section 0)
            #   container: Failed to read policy package
            #   libsemanage.semanage_direct_commit: Failed to compile hll files into cil files.
            #    (No such file or directory).
            #   /usr/sbin/semodule:  Failed!
            #
            # Unfortunately this is then fatal when running podman, resulting in no error message and a 127 return code.
            # The solution is to update the policycoreutils package *before* installing podman.
            #
            # NOTE: This work-around can probably be removed once we're testing on RHEL 9.1, as the updated packages should already be installed.
            #       Unfortunately at this time there is no RHEL 9.1 AMI available (other than the Beta release).

            run_command('dnf', 'update', '-y', 'policycoreutils')

        run_command('dnf', 'install', '-y', *packages)

        if cls.install_docker():
            run_command('systemctl', 'start', 'docker')

        super().run()


class AptBootstrapper(Bootstrapper):
    """Bootstrapper for apt based systems."""

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
        # The `crun` package must be explicitly installed since podman won't install it as dep if `runc` is present.
        packages = ['docker', 'podman', 'openssl', 'crun']

        if os_release.version_id.startswith('3.18.'):
            # The 3.19 `crun` package installed below requires `ip6tables`, but depends on the `iptables` package.
            # In 3.19, the `iptables` package includes `ip6tables`, but in 3.18 they are separate packages.
            # Remove once 3.18 is no longer tested.
            packages.append('ip6tables')

        run_command('apk', 'add', *packages)

        if os_release.version_id.startswith('3.18.'):
            # 3.18 only contains `crun` 1.8.4, to get a newer version that resolves the run/shm issue, install `crun` from 3.19.
            # Remove once 3.18 is no longer tested.
            run_command('apk', 'upgrade', '-U', '--repository=http://dl-cdn.alpinelinux.org/alpine/v3.19/community', 'crun')

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

ROOT_USER = User.get('root')

if __name__ == '__main__':
    main()
