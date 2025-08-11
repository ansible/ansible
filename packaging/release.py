#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Manage upstream ansible-core releases."""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import enum
import functools
import gzip
import hashlib
import http.client
import inspect
import json
import math
import os
import pathlib
import re
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import typing as t
import urllib.error
import urllib.parse
import urllib.request
import venv
import webbrowser
import zipfile

import jinja2

from packaging.version import Version, InvalidVersion

# region CLI Framework


def path_to_str(value: t.Any) -> str:
    """Return the given value converted to a string suitable for use as a command line argument."""
    return f"{value}/" if isinstance(value, pathlib.Path) and value.is_dir() else str(value)


@t.overload
def run(*args: t.Any, env: dict[str, t.Any] | None, cwd: pathlib.Path | str, capture_output: t.Literal[True]) -> CompletedProcess: ...


@t.overload
def run(*args: t.Any, env: dict[str, t.Any] | None, cwd: pathlib.Path | str, capture_output: t.Literal[False]) -> None: ...


@t.overload
def run(*args: t.Any, env: dict[str, t.Any] | None, cwd: pathlib.Path | str, capture_output: bool) -> CompletedProcess | None: ...


@t.overload
def run(*args: t.Any, env: dict[str, t.Any] | None, cwd: pathlib.Path | str) -> None: ...


def run(
    *args: t.Any,
    env: dict[str, t.Any] | None,
    cwd: pathlib.Path | str,
    capture_output: bool = False,
) -> CompletedProcess | None:
    """Run the specified command."""
    args = [arg.relative_to(cwd) if isinstance(arg, pathlib.Path) else arg for arg in args]

    str_args = tuple(path_to_str(arg) for arg in args)
    str_env = {key: path_to_str(value) for key, value in env.items()} if env is not None else None

    display.show(f"--> {shlex.join(str_args)}", color=Display.CYAN)

    try:
        p = subprocess.run(str_args, check=True, text=True, env=str_env, cwd=cwd, capture_output=capture_output)
    except subprocess.CalledProcessError as ex:
        # improve type hinting and include stdout/stderr (if any) in the message
        raise CalledProcessError(
            message=str(ex),
            cmd=str_args,
            status=ex.returncode,
            stdout=ex.stdout,
            stderr=ex.stderr,
        ) from None

    if not capture_output:
        return None

    # improve type hinting
    return CompletedProcess(
        stdout=p.stdout,
        stderr=p.stderr,
    )


@contextlib.contextmanager
def suppress_when(error_as_warning: bool) -> t.Generator[None, None, None]:
    """Conditionally convert an ApplicationError in the provided context to a warning."""
    if error_as_warning:
        try:
            yield
        except ApplicationError as ex:
            display.warning(ex)
    else:
        yield


class ApplicationError(Exception):
    """A fatal application error which will be shown without a traceback."""


class CalledProcessError(Exception):
    """Results from a failed process."""

    def __init__(self, message: str, cmd: tuple[str, ...], status: int, stdout: str | None, stderr: str | None) -> None:
        if stdout and (stdout := stdout.strip()):
            message += f"\n>>> Standard Output\n{stdout}"

        if stderr and (stderr := stderr.strip()):
            message += f"\n>>> Standard Error\n{stderr}"

        super().__init__(message)

        self.cmd = cmd
        self.status = status
        self.stdout = stdout
        self.stderr = stderr


@dataclasses.dataclass(frozen=True)
class CompletedProcess:
    """Results from a completed process."""

    stdout: str
    stderr: str


class Display:
    """Display interface for sending output to the console."""

    CLEAR = "\033[0m"
    RED = "\033[31m"
    BLUE = "\033[34m"
    PURPLE = "\033[35m"
    CYAN = "\033[36m"

    def fatal(self, message: t.Any) -> None:
        """Print a fatal message to the console."""
        self.show(f"FATAL: {message}", color=self.RED)

    def warning(self, message: t.Any) -> None:
        """Print a warning message to the console."""
        self.show(f"WARNING: {message}", color=self.PURPLE)

    def show(self, message: t.Any, color: str | None = None) -> None:
        """Print a message to the console."""
        print(f"{color or self.CLEAR}{message}{self.CLEAR}", flush=True)


class CommandFramework:
    """
    Simple command line framework inspired by nox.

    Argument parsing is handled by argparse. Each function annotated with an instance of this class becomes a subcommand.
    Options are shared across all commands, and are defined by providing kwargs when creating an instance of this class.
    Options are only defined for commands which have a matching parameter.

    The name of each kwarg is the option name, which will be prefixed with `--` and with underscores converted to dashes.
    The value of each kwarg is passed as kwargs to ArgumentParser.add_argument. Passing None results in an internal only parameter.

    The following custom kwargs are recognized and are not passed to add_argument:

    name - Override the positional argument (option) passed to add_argument.
    exclusive - Put the argument in an exclusive group of the given name.
    """

    def __init__(self, **kwargs: dict[str, t.Any] | None) -> None:
        self.commands: list[t.Callable[..., None]] = []
        self.arguments = kwargs
        self.parsed_arguments: argparse.Namespace | None = None

    def __call__[T: t.Callable[..., None]](self, func: T) -> T:
        """Register the decorated function as a CLI command."""
        self.commands.append(func)
        return func

    def run(self, *args: t.Callable[..., None], **kwargs) -> None:
        """Run the specified command(s), using any provided internal args."""
        for arg in args:
            self._run(arg, **kwargs)

    def main(self) -> None:
        """Main program entry point."""
        parser = argparse.ArgumentParser(description=__doc__)
        subparsers = parser.add_subparsers(metavar="COMMAND", required=True)

        for func in self.commands:
            func_parser = subparsers.add_parser(self._format_command_name(func), description=func.__doc__, help=func.__doc__)
            func_parser.set_defaults(func=func)

            exclusive_groups = {}
            signature = inspect.signature(func)

            for name in signature.parameters:
                if name not in self.arguments:
                    raise RuntimeError(f"The '{name}' argument, used by '{func.__name__}', has not been defined.")

                if (arguments := self.arguments.get(name)) is None:
                    continue  # internal use

                arguments = arguments.copy()
                exclusive = arguments.pop("exclusive", None)

                # noinspection PyProtectedMember, PyUnresolvedReferences
                command_parser: argparse._ActionsContainer

                if exclusive:
                    if exclusive not in exclusive_groups:
                        exclusive_groups[exclusive] = func_parser.add_mutually_exclusive_group()

                    command_parser = exclusive_groups[exclusive]
                else:
                    command_parser = func_parser

                if option_name := arguments.pop("name", None):
                    arguments.update(dest=name)
                else:
                    option_name = f"--{name.replace('_', '-')}"

                command_parser.add_argument(option_name, **arguments)

        try:
            # noinspection PyUnresolvedReferences
            import argcomplete
        except ImportError:
            pass
        else:
            argcomplete.autocomplete(parser)

        self.parsed_arguments = parser.parse_args()

        try:
            self.run(self.parsed_arguments.func)
        except ApplicationError as ex:
            display.fatal(ex)
            sys.exit(1)

    def _run(self, func: t.Callable[..., None], **kwargs) -> None:
        """Run the specified command, using any provided internal args."""
        signature = inspect.signature(func)
        func_args = {name: getattr(self.parsed_arguments, name) for name in signature.parameters if hasattr(self.parsed_arguments, name)}
        func_args.update({name: value for name, value in kwargs.items() if name in signature.parameters})
        printable_args = ", ".join(f"{name}={repr(value)}" for name, value in func_args.items())
        label = f"{self._format_command_name(func)}({printable_args})"

        display.show(f"==> {label}", color=Display.BLUE)

        try:
            func(**func_args)
        except BaseException:
            display.show(f"!!! {label}", color=Display.RED)
            raise

        display.show(f"<== {label}", color=Display.BLUE)

    @staticmethod
    def _format_command_name(func: t.Callable[..., None]) -> str:
        """Return the friendly name of the given command."""
        return func.__name__.replace("_", "-")


display = Display()


# endregion
# region Data Classes


@dataclasses.dataclass(frozen=True)
class GitHubRelease:
    """Details required to create a GitHub release."""

    user: str
    repo: str
    tag: str
    target: str
    title: str
    body: str
    pre_release: bool


@dataclasses.dataclass(frozen=True)
class PullRequest:
    """Details required to create a pull request."""

    upstream_user: str
    upstream_repo: str
    upstream_branch: str
    user: str
    repo: str
    branch: str
    title: str
    body: str


@dataclasses.dataclass(frozen=True)
class Remote:
    """Details about a git remote."""

    name: str
    user: str
    repo: str


@dataclasses.dataclass(frozen=True)
class Remotes:
    """Details about git removes."""

    fork: Remote
    upstream: Remote


@dataclasses.dataclass(frozen=True)
class GitState:
    """Details about the state of the git repository."""

    remotes: Remotes
    branch: str | None
    commit: str


@dataclasses.dataclass(frozen=True)
class ReleaseArtifact:
    """Information about a release artifact on PyPI."""

    package_type: str
    package_label: str
    url: str
    size: int
    digest: str
    digest_algorithm: str


# endregion
# region Utilities


SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
CHECKOUT_DIR = SCRIPT_DIR.parent

ANSIBLE_LIB_DIR = CHECKOUT_DIR / "lib"
ANSIBLE_DIR = ANSIBLE_LIB_DIR / "ansible"
ANSIBLE_BIN_DIR = CHECKOUT_DIR / "bin"
ANSIBLE_RELEASE_FILE = ANSIBLE_DIR / "release.py"
ANSIBLE_REQUIREMENTS_FILE = CHECKOUT_DIR / "requirements.txt"
ANSIBLE_CHANGELOG_REQUIREMENTS_FILE = CHECKOUT_DIR / "test/lib/ansible_test/_data/requirements/sanity.changelog.txt"
ANSIBLE_PYPROJECT_TOML_FILE = CHECKOUT_DIR / "pyproject.toml"

DIST_DIR = CHECKOUT_DIR / "dist"
VENV_DIR = DIST_DIR / ".venv" / "release"

CHANGELOGS_DIR = CHECKOUT_DIR / "changelogs"
CHANGELOGS_FRAGMENTS_DIR = CHANGELOGS_DIR / "fragments"

ANSIBLE_VERSION_PATTERN = re.compile("^__version__ = '(?P<version>.*)'$", re.MULTILINE)
ANSIBLE_VERSION_FORMAT = "__version__ = '{version}'"

DIGEST_ALGORITHM = "sha256"

# These endpoint names match those defined as defaults in twine.
# See: https://github.com/pypa/twine/blob/9c2c0a1c535155931c3d879359330cb836950c6a/twine/utils.py#L82-L85
PYPI_ENDPOINTS = dict(
    pypi="https://pypi.org/pypi",
    testpypi="https://test.pypi.org/pypi",
)

PIP_ENV = dict(
    PIP_REQUIRE_VIRTUALENV="yes",
    PIP_DISABLE_PIP_VERSION_CHECK="yes",
)


class VersionMode(enum.Enum):
    """How to handle the ansible-core version."""

    DEFAULT = enum.auto()
    """Do not allow development versions. Do not allow post release versions."""
    STRIP_POST = enum.auto()
    """Do not allow development versions. Strip the post release from the version if present."""
    REQUIRE_POST = enum.auto()
    """Do not allow development versions. Require a post release version."""
    REQUIRE_DEV_POST = enum.auto()
    """Require a development or post release version."""
    ALLOW_DEV_POST = enum.auto()
    """Allow development and post release versions."""

    def apply(self, version: Version) -> Version:
        """Apply the mode to the given version and return the result."""
        original_version = version

        release_component_count = 3

        if len(version.release) != release_component_count:
            raise ApplicationError(f"Version {version} contains {version.release} release components instead of {release_component_count}.")

        if version.epoch:
            raise ApplicationError(f"Version {version} contains an epoch component: {version.epoch}")

        if version.local is not None:
            raise ApplicationError(f"Version {version} contains a local component: {version.local}")

        if version.is_devrelease and version.is_postrelease:
            raise ApplicationError(f"Version {version} is a development and post release version.")

        if self == VersionMode.ALLOW_DEV_POST:
            return version

        if self == VersionMode.REQUIRE_DEV_POST:
            if not version.is_devrelease and not version.is_postrelease:
                raise ApplicationError(f"Version {version} is not a development or post release version.")

            return version

        if version.is_devrelease:
            raise ApplicationError(f"Version {version} is a development release: {version.dev}")

        if self == VersionMode.STRIP_POST:
            if version.is_postrelease:
                version = Version(str(version).removesuffix(f".post{version.post}"))
                display.warning(f"Using version {version} by stripping the post release suffix from version {original_version}.")

            return version

        if self == VersionMode.REQUIRE_POST:
            if not version.is_postrelease:
                raise ApplicationError(f"Version {version} is not a post release version.")

            return version

        if version.is_postrelease:
            raise ApplicationError(f"Version {version} is a post release.")

        if self == VersionMode.DEFAULT:
            return version

        raise NotImplementedError(self)


@t.overload
def git(*args: t.Any, capture_output: t.Literal[True]) -> CompletedProcess: ...


@t.overload
def git(*args: t.Any, capture_output: t.Literal[False]) -> None: ...


@t.overload
def git(*args: t.Any) -> None: ...


def git(*args: t.Any, capture_output: bool = False) -> CompletedProcess | None:
    """Run the specified git command."""
    return run("git", *args, env=None, cwd=CHECKOUT_DIR, capture_output=capture_output)


def get_commit(rev: str | None = None) -> str:
    """Return the commit associated with the given rev, or HEAD if no rev is given."""
    try:
        return git("rev-parse", "--quiet", "--verify", "--end-of-options", f"{rev or 'HEAD'}^{{commit}}", capture_output=True).stdout.strip()
    except CalledProcessError as ex:
        if ex.status == 1 and not ex.stdout and not ex.stderr:
            raise ApplicationError(f"Could not find commit: {rev}") from None

        raise


def prepare_pull_request(version: Version, branch: str, title: str, add: t.Iterable[pathlib.Path | str], allow_stale: bool) -> PullRequest:
    """Return pull request parameters using the provided details."""
    git_state = get_git_state(version, allow_stale)

    if not git("status", "--porcelain", "--untracked-files=no", capture_output=True).stdout.strip():
        raise ApplicationError("There are no changes to commit. Did you skip a step?")

    upstream_branch = get_upstream_branch(version)
    body = create_pull_request_body(title)

    git("checkout", "-b", branch)
    git("add", *add)
    git("commit", "-m", title)
    git("push", "--set-upstream", git_state.remotes.fork.name, branch)
    git("checkout", git_state.branch or git_state.commit)
    git("branch", "-d", branch)

    pr = PullRequest(
        upstream_user=git_state.remotes.upstream.user,
        upstream_repo=git_state.remotes.upstream.repo,
        upstream_branch=upstream_branch,
        user=git_state.remotes.fork.user,
        repo=git_state.remotes.fork.repo,
        branch=branch,
        title=title,
        body=body,
    )

    return pr


def create_github_release(release: GitHubRelease) -> None:
    """Open a browser tab for creating the given GitHub release."""
    # See: https://docs.github.com/en/repositories/releasing-projects-on-github/automation-for-release-forms-with-query-parameters

    params = dict(
        tag=release.tag,
        target=release.target,
        title=release.title,
        body=release.body,
        prerelease=1 if release.pre_release else 0,
    )

    query_string = urllib.parse.urlencode(params)
    url = f"https://github.com/{release.user}/{release.repo}/releases/new?{query_string}"

    display.show("Opening release creation page in new tab using default browser ...")
    webbrowser.open_new_tab(url)


def create_pull_request(pr: PullRequest) -> None:
    """Open a browser tab for creating the given pull request."""
    # See: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/using-query-parameters-to-create-a-pull-request  # noqa

    params = dict(
        quick_pull=1,
        title=pr.title,
        body=pr.body,
    )

    query_string = urllib.parse.urlencode(params)
    url = f"https://github.com/{pr.upstream_user}/{pr.upstream_repo}/compare/{pr.upstream_branch}...{pr.user}:{pr.repo}:{pr.branch}?{query_string}"

    display.show("Opening pull request in new tab using default browser ...")
    webbrowser.open_new_tab(url)


def create_pull_request_body(title: str) -> str:
    """Return a simple pull request body created from the given title."""
    body = f"""
##### SUMMARY

{title}

##### ISSUE TYPE

Feature Pull Request
"""

    return body.lstrip()


def get_remote(name: str, push: bool) -> Remote:
    """Return details about the specified remote."""
    remote_url = git("remote", "get-url", *(["--push"] if push else []), name, capture_output=True).stdout.strip()
    remote_match = re.search(r"[@/]github[.]com[:/](?P<user>[^/]+)/(?P<repo>[^.]+)(?:[.]git)?$", remote_url)

    if not remote_match:
        raise RuntimeError(f"Unable to identify the user and repo in the '{name}' remote: {remote_url}")

    remote = Remote(
        name=name,
        user=remote_match.group("user"),
        repo=remote_match.group("repo"),
    )

    return remote


@functools.cache
def get_remotes() -> Remotes:
    """Return details about the remotes we need to use."""
    # assume the devel branch has its upstream remote pointing to the user's fork
    fork_remote_name = git("branch", "--list", "devel", "--format=%(upstream:remotename)", capture_output=True).stdout.strip()

    if not fork_remote_name:
        raise ApplicationError("Could not determine the remote for your fork of Ansible.")

    display.show(f"Detected '{fork_remote_name}' as the remote for your fork of Ansible.")

    # assume there is only one ansible org remote, which would allow release testing using another repo in the same org without special configuration
    all_remotes = git("remote", "-v", capture_output=True).stdout.strip().splitlines()
    ansible_remote_names = set(line.split()[0] for line in all_remotes if re.search(r"[@/]github[.]com[:/]ansible/", line))

    if not ansible_remote_names:
        raise ApplicationError(f"Could not determine the remote which '{fork_remote_name}' was forked from.")

    if len(ansible_remote_names) > 1:
        raise ApplicationError(f"Found multiple candidates for the remote from which '{fork_remote_name}' was forked from: {', '.join(ansible_remote_names)}")

    upstream_remote_name = ansible_remote_names.pop()

    display.show(f"Detected '{upstream_remote_name}' as the remote from which '{fork_remote_name}' was forked from.")

    if fork_remote_name == upstream_remote_name:
        raise ApplicationError("The remote for your fork of Ansible cannot be the same as the remote from which it was forked.")

    remotes = Remotes(
        fork=get_remote(fork_remote_name, push=True),
        upstream=get_remote(upstream_remote_name, push=False),
    )

    return remotes


def get_upstream_branch(version: Version) -> str:
    """Return the upstream branch name for the given version."""
    return f"stable-{version.major}.{version.minor}"


def get_git_state(version: Version, allow_stale: bool) -> GitState:
    """Return information about the current state of the git repository."""
    remotes = get_remotes()
    upstream_branch = get_upstream_branch(version)

    git("fetch", remotes.upstream.name, upstream_branch)

    upstream_ref = f"{remotes.upstream.name}/{upstream_branch}"
    upstream_commit = get_commit(upstream_ref)

    commit = get_commit()

    if commit != upstream_commit:
        with suppress_when(allow_stale):
            raise ApplicationError(f"The current commit ({commit}) does not match {upstream_ref} ({upstream_commit}).")

    branch = git("branch", "--show-current", capture_output=True).stdout.strip() or None

    state = GitState(
        remotes=remotes,
        branch=branch,
        commit=commit,
    )

    return state


@functools.cache
def ensure_venv(requirements_content: str) -> dict[str, t.Any]:
    """Ensure the release venv is ready and return the env vars needed to use it."""
    requirements_hash = hashlib.sha256(requirements_content.encode()).hexdigest()[:8]

    python_version = ".".join(map(str, sys.version_info[:2]))

    venv_dir = VENV_DIR / python_version / requirements_hash
    venv_bin_dir = venv_dir / "bin"
    venv_requirements_file = venv_dir / "requirements.txt"
    venv_marker_file = venv_dir / "marker.txt"

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)  # avoid interference from ansible being injected into the environment
    env.update(
        PATH=os.pathsep.join((str(venv_bin_dir), env["PATH"])),
    )

    if not venv_marker_file.exists():
        display.show(f"Creating a Python {python_version} virtual environment ({requirements_hash}) ...")

        if venv_dir.exists():
            shutil.rmtree(venv_dir)

        venv.create(venv_dir, with_pip=True)

        venv_requirements_file.write_text(requirements_content)

        run("pip", "install", "-r", venv_requirements_file, env=env | PIP_ENV, cwd=CHECKOUT_DIR)

        venv_marker_file.touch()

    return env


def get_pypi_project(repository: str, project: str, version: Version | None = None) -> dict[str, t.Any]:
    """Return the project JSON from PyPI for the specified repository, project and version (optional)."""
    endpoint = PYPI_ENDPOINTS[repository]

    if version:
        url = f"{endpoint}/{project}/{version}/json"
    else:
        url = f"{endpoint}/{project}/json"

    opener = urllib.request.build_opener()
    response: http.client.HTTPResponse

    try:
        with opener.open(url) as response:
            data = json.load(response)
    except urllib.error.HTTPError as ex:
        if version:
            target = f'{project!r} version {version}'
        else:
            target = f'{project!r}'

        if ex.status == http.HTTPStatus.NOT_FOUND:
            raise ApplicationError(f"Could not find {target} on PyPI.") from None

        raise RuntimeError(f"Failed to get {target} from PyPI.") from ex

    return data


def get_ansible_version(version: str | None = None, /, commit: str | None = None, mode: VersionMode = VersionMode.DEFAULT) -> Version:
    """Parse and return the current ansible-core version, the provided version or the version from the provided commit."""
    if version and commit:
        raise ValueError("Specify only one of: version, commit")

    if version:
        source = ""
    else:
        if commit:
            current = git("show", f"{commit}:{ANSIBLE_RELEASE_FILE.relative_to(CHECKOUT_DIR)}", capture_output=True).stdout
        else:
            current = ANSIBLE_RELEASE_FILE.read_text()

        if not (match := ANSIBLE_VERSION_PATTERN.search(current)):
            raise RuntimeError("Failed to get the ansible-core version.")

        version = match.group("version")
        source = f" in '{ANSIBLE_RELEASE_FILE}'"

    try:
        parsed_version = Version(version)
    except InvalidVersion:
        raise ApplicationError(f"Invalid version{source}: {version}") from None

    parsed_version = mode.apply(parsed_version)

    return parsed_version


def get_next_version(version: Version, /, final: bool = False, pre: str | None = None, mode: VersionMode = VersionMode.DEFAULT) -> Version:
    """Return the next version after the specified version."""

    # TODO: consider using development versions instead of post versions after a release is published

    pre = pre or ""
    micro = version.micro

    if version.is_devrelease:
        # The next version of a development release is the same version without the development component.
        if final:
            pre = ""
        elif not pre and version.pre is not None:
            pre = f"{version.pre[0]}{version.pre[1]}"
        elif not pre:
            pre = "b1"  # when there is no existing pre and none specified, advance to b1

    elif version.is_postrelease:
        # The next version of a post release is the next pre-release *or* micro release component.
        if final:
            pre = ""
        elif not pre and version.pre is not None:
            pre = f"{version.pre[0]}{version.pre[1] + 1}"
        elif not pre:
            pre = "rc1"  # when there is no existing pre and none specified, advance to rc1

        if version.pre is None:
            micro = version.micro + 1
    else:
        raise ApplicationError(f"Version {version} is not a development or post release version.")

    version = f"{version.major}.{version.minor}.{micro}{pre}"

    return get_ansible_version(version, mode=mode)


def check_ansible_version(current_version: Version, requested_version: Version) -> None:
    """Verify the requested version is valid for the current version."""
    if requested_version.release[:2] != current_version.release[:2]:
        raise ApplicationError(f"Version {requested_version} does not match the major and minor portion of the current version: {current_version}")

    if requested_version < current_version:
        raise ApplicationError(f"Version {requested_version} is older than the current version: {current_version}")

    # TODO: consider additional checks to avoid mistakes when incrementing the release version


def set_ansible_version(current_version: Version, requested_version: Version) -> None:
    """Set the current ansible-core version."""
    check_ansible_version(current_version, requested_version)

    if requested_version == current_version:
        return

    display.show(f"Updating version {current_version} to {requested_version} ...")

    current = ANSIBLE_RELEASE_FILE.read_text()
    updated = ANSIBLE_VERSION_PATTERN.sub(ANSIBLE_VERSION_FORMAT.format(version=requested_version), current)

    if current == updated:
        raise RuntimeError("Failed to set the ansible-core version.")

    ANSIBLE_RELEASE_FILE.write_text(updated)


def get_latest_setuptools_version() -> Version:
    """Return the latest setuptools version found on PyPI."""
    data = get_pypi_project('pypi', 'setuptools')
    version = Version(data['info']['version'])

    return version


def set_setuptools_upper_bound(requested_version: Version) -> None:
    """Set the upper bound on setuptools in pyproject.toml."""
    current = ANSIBLE_PYPROJECT_TOML_FILE.read_text()
    pattern = re.compile(r'^(?P<begin>requires = \["setuptools >= )(?P<lower>[^,]+)(?P<middle>, <= )(?P<upper>[^"]+)(?P<end>".*)$', re.MULTILINE)
    match = pattern.search(current)

    if not match:
        raise ApplicationError(f"Unable to find the 'requires' entry in: {ANSIBLE_PYPROJECT_TOML_FILE.relative_to(CHECKOUT_DIR)}")

    current_version = Version(match.group('upper'))

    if requested_version == current_version:
        return

    display.show(f"Updating setuptools upper bound from {current_version} to {requested_version} ...")

    updated = pattern.sub(fr'\g<begin>\g<lower>\g<middle>{requested_version}\g<end>', current)

    if current == updated:
        raise RuntimeError("Failed to set the setuptools upper bound.")

    ANSIBLE_PYPROJECT_TOML_FILE.write_text(updated)


def create_reproducible_sdist(original_path: pathlib.Path, output_path: pathlib.Path, mtime: int) -> None:
    """Read the specified sdist and write out a new copy with uniform file metadata at the specified location."""
    with tarfile.open(original_path) as original_archive:
        with tempfile.TemporaryDirectory() as temp_dir:
            tar_file = pathlib.Path(temp_dir) / "sdist.tar"

            with tarfile.open(tar_file, mode="w") as tar_archive:
                for original_info in original_archive.getmembers():  # type: tarfile.TarInfo
                    tar_archive.addfile(create_reproducible_tar_info(original_info, mtime), original_archive.extractfile(original_info))

            with tar_file.open("rb") as tar_archive:
                with gzip.GzipFile(output_path, "wb", mtime=mtime) as output_archive:
                    shutil.copyfileobj(tar_archive, output_archive)


def create_reproducible_tar_info(original: tarfile.TarInfo, mtime: int) -> tarfile.TarInfo:
    """Return a copy of the given TarInfo with uniform file metadata."""
    sanitized = tarfile.TarInfo()
    sanitized.name = original.name
    sanitized.size = original.size
    sanitized.mtime = mtime
    sanitized.mode = (original.mode & ~(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)) | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR
    sanitized.type = original.type
    sanitized.linkname = original.linkname
    sanitized.uid = 0
    sanitized.gid = 0
    sanitized.uname = "root"
    sanitized.gname = "root"

    if original.mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        sanitized.mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH

    return sanitized


def test_built_artifact(path: pathlib.Path) -> None:
    """Test the specified built artifact by installing it in a venv and running some basic commands."""
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)

        venv_dir = temp_dir / "venv"
        venv_bin_dir = venv_dir / "bin"

        venv.create(venv_dir, with_pip=True)

        env = os.environ.copy()
        env.pop("PYTHONPATH", None)  # avoid interference from ansible being injected into the environment
        env.update(
            PATH=os.pathsep.join((str(venv_bin_dir), env["PATH"])),
        )

        run("pip", "install", path, env=env | PIP_ENV, cwd=CHECKOUT_DIR)

        run("ansible", "--version", env=env, cwd=CHECKOUT_DIR)
        run("ansible-test", "--version", env=env, cwd=CHECKOUT_DIR)


def get_sdist_path(version: Version, dist_dir: pathlib.Path = DIST_DIR) -> pathlib.Path:
    """Return the path to the sdist file."""
    return dist_dir / f"ansible_core-{version}.tar.gz"


def get_wheel_path(version: Version, dist_dir: pathlib.Path = DIST_DIR) -> pathlib.Path:
    """Return the path to the wheel file."""
    return dist_dir / f"ansible_core-{version}-py3-none-any.whl"


def calculate_digest(path: pathlib.Path) -> str:
    """Return the digest for the specified file."""
    with open(path, "rb") as f:
        digest = hashlib.file_digest(f, DIGEST_ALGORITHM)
    return digest.hexdigest()


@functools.cache
def get_release_artifact_details(repository: str, version: Version, validate: bool) -> list[ReleaseArtifact]:
    """Return information about the release artifacts hosted on PyPI."""
    data = get_pypi_project(repository, 'ansible-core', version)
    artifacts = [describe_release_artifact(version, item, validate) for item in data["urls"]]

    expected_artifact_types = {"bdist_wheel", "sdist"}
    found_artifact_types = set(artifact.package_type for artifact in artifacts)

    if found_artifact_types != expected_artifact_types:
        raise RuntimeError(f"Expected {expected_artifact_types} artifact types, but found {found_artifact_types} instead.")

    return artifacts


def describe_release_artifact(version: Version, item: dict[str, t.Any], validate: bool) -> ReleaseArtifact:
    """Return release artifact details extracted from the given PyPI data."""
    package_type = item["packagetype"]

    # The artifact URL is documented as stable, so is safe to put in release notes.
    # See: https://github.com/pypi/warehouse/blame/c95be4a1055f4b36a8852715eb80318c81fc00ca/docs/api-reference/integration-guide.rst#L86-L90
    url = item["url"]

    pypi_size = item["size"]
    pypi_digest = item["digests"][DIGEST_ALGORITHM]

    if package_type == "bdist_wheel":
        local_artifact_file = get_wheel_path(version)
        package_label = "Built Distribution"
    elif package_type == "sdist":
        local_artifact_file = get_sdist_path(version)
        package_label = "Source Distribution"
    else:
        raise NotImplementedError(f"Package type '{package_type}' is not supported.")

    if validate:
        try:
            local_size = local_artifact_file.stat().st_size
            local_digest = calculate_digest(local_artifact_file)
        except FileNotFoundError:
            raise ApplicationError(f"Missing local artifact: {local_artifact_file.relative_to(CHECKOUT_DIR)}") from None

        if local_size != pypi_size:
            raise ApplicationError(f"The {version} local {package_type} size {local_size} does not match the PyPI size {pypi_size}.")

        if local_digest != pypi_digest:
            raise ApplicationError(f"The {version} local {package_type} digest '{local_digest}' does not match the PyPI digest '{pypi_digest}'.")

    return ReleaseArtifact(
        package_type=package_type,
        package_label=package_label,
        url=url,
        size=pypi_size,
        digest=pypi_digest,
        digest_algorithm=DIGEST_ALGORITHM.upper(),
    )


def get_next_release_date(start: datetime.date, step: int, after: datetime.date) -> datetime.date:
    """Return the next release date."""
    if start > after:
        raise ValueError(f"{start=} is greater than {after=}")

    current_delta = after - start
    release_delta = datetime.timedelta(days=(math.floor(current_delta.days / step) + 1) * step)

    release = start + release_delta

    return release


def create_template_environment() -> jinja2.Environment:
    """Create and return a jinja2 environment."""
    env = jinja2.Environment()
    env.filters.update(
        basename=os.path.basename,
    )

    return env


def create_github_release_notes(upstream: Remote, repository: str, version: Version, validate: bool) -> str:
    """Create and return GitHub release notes."""
    env = create_template_environment()
    template = env.from_string(GITHUB_RELEASE_NOTES_TEMPLATE)

    variables = dict(
        version=version,
        releases=get_release_artifact_details(repository, version, validate),
        changelog=f"https://github.com/{upstream.user}/{upstream.repo}/blob/v{version}/changelogs/CHANGELOG-v{version.major}.{version.minor}.rst",
    )

    release_notes = template.render(**variables).strip()

    return release_notes


# endregion
# region Templates


GITHUB_RELEASE_NOTES_TEMPLATE = """
# Changelog

See the [full changelog]({{ changelog }}) for the changes included in this release.

# Release Artifacts

{%- for release in releases %}
* {{ release.package_label }}: [{{ release.url|basename }}]({{ release.url }}) - &zwnj;{{ release.size }} bytes
  * {{ release.digest }} ({{ release.digest_algorithm }})
{%- endfor %}
"""


# endregion
# region Commands


command = CommandFramework(
    repository=dict(metavar="REPO", choices=tuple(PYPI_ENDPOINTS), default="pypi", help="PyPI repository to use: %(choices)s [%(default)s]"),
    version=dict(exclusive="version", help="version to set"),
    pre=dict(exclusive="version", help="increment version to the specified pre-release (aN, bN, rcN)"),
    final=dict(exclusive="version", action="store_true", help="increment version to the next final release"),
    commit=dict(help="commit to tag"),
    validate=dict(name="--no-validate", action="store_false", help="disable validation of PyPI artifacts against local ones"),
    prompt=dict(name="--no-prompt", action="store_false", help="disable interactive prompt before publishing with twine"),
    setuptools=dict(name='--no-setuptools', action="store_false", help="disable updating setuptools upper bound"),
    allow_tag=dict(action="store_true", help="allow an existing release tag (for testing)"),
    allow_stale=dict(action="store_true", help="allow a stale checkout (for testing)"),
    allow_dirty=dict(action="store_true", help="allow untracked files and files with changes (for testing)"),
)


@command
def instructions() -> None:
    """Show instructions for the release process."""
    message = """
Releases must be performed using an up-to-date checkout of a fork of the Ansible repository.

1. Make sure your checkout is up-to-date.
2. Run the `prepare` command [1], then:
   a. Submit the PR opened in the browser.
   b. Wait for CI to pass.
   c. Merge the PR.
3. Update your checkout to include the commit from the PR which was just merged.
4. Run the `complete` command [2], then:
   a. Submit the GitHub release opened in the browser.
   b. Submit the PR opened in the browser.
   c. Wait for CI to pass.
   d. Merge the PR.

[1] Use the `--final`, `--pre` or `--version` option for control over the version.
[2] During the `publish` step, `twine` may prompt for credentials.
"""

    display.show(message.strip())


@command
def show_version(final: bool = False, pre: str | None = None) -> None:
    """Show the current and next ansible-core version."""
    current_version = get_ansible_version(mode=VersionMode.ALLOW_DEV_POST)
    display.show(f"Current version: {current_version}")

    try:
        next_version = get_next_version(current_version, final=final, pre=pre)
    except ApplicationError as ex:
        display.show(f"   Next version: Unknown - {ex}")
    else:
        display.show(f"   Next version: {next_version}")

        check_ansible_version(current_version, next_version)


@command
def check_state(allow_stale: bool = False) -> None:
    """Verify the git repository is in a usable state for creating a pull request."""
    get_git_state(get_ansible_version(), allow_stale)


# noinspection PyUnusedLocal
@command
def prepare(final: bool = False, pre: str | None = None, version: str | None = None, setuptools: bool | None = None) -> None:
    """Prepare a release."""
    command.run(
        update_version,
        update_setuptools,
        check_state,
        generate_summary,
        generate_changelog,
        create_release_pr,
    )


@command
def update_version(final: bool = False, pre: str | None = None, version: str | None = None) -> None:
    """Update the version embedded in the source code."""
    current_version = get_ansible_version(mode=VersionMode.REQUIRE_DEV_POST)

    if version:
        requested_version = get_ansible_version(version)
    else:
        requested_version = get_next_version(current_version, final=final, pre=pre)

    set_ansible_version(current_version, requested_version)


@command
def update_setuptools(setuptools: bool) -> None:
    """Update the setuptools upper bound in pyproject.toml."""
    if not setuptools:
        return

    requested_version = get_latest_setuptools_version()
    set_setuptools_upper_bound(requested_version)


@command
def generate_summary() -> None:
    """Generate a summary changelog fragment for this release."""
    version = get_ansible_version()
    release_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    summary_path = CHANGELOGS_FRAGMENTS_DIR / f"{version}_summary.yaml"
    major_minor = f"{version.major}.{version.minor}"

    content = f"""
release_summary: |
   | Release Date: {release_date}
   | `Porting Guide <https://docs.ansible.com/ansible-core/{major_minor}/porting_guides/porting_guide_core_{major_minor}.html>`__
"""

    summary_path.write_text(content.lstrip())


@command
def generate_changelog() -> None:
    """Generate the changelog and validate the results."""
    changelog_requirements = (
        ANSIBLE_CHANGELOG_REQUIREMENTS_FILE.read_text()
        + ANSIBLE_REQUIREMENTS_FILE.read_text()  # TODO: consider pinning the ansible requirements and dependencies
    )

    env = ensure_venv(changelog_requirements)
    env.update(
        PATH=os.pathsep.join((str(ANSIBLE_BIN_DIR), env["PATH"])),
        PYTHONPATH=ANSIBLE_LIB_DIR,
    )

    # TODO: consider switching back to the original changelog generator instead of using antsibull-changelog

    run("antsibull-changelog", "release", "-vv", "--use-ansible-doc", env=env, cwd=CHECKOUT_DIR)
    run("antsibull-changelog", "generate", "-vv", "--use-ansible-doc", env=env, cwd=CHECKOUT_DIR)

    run("ansible-test", "sanity", CHANGELOGS_DIR, ANSIBLE_RELEASE_FILE, env=env, cwd=CHECKOUT_DIR)


@command
def create_release_pr(allow_stale: bool = False) -> None:
    """Create a branch and open a browser tab for creating a release pull request."""
    version = get_ansible_version()

    pr = prepare_pull_request(
        version=version,
        branch=f"release-{version}-{secrets.token_hex(4)}",
        title=f"New release v{version}",
        add=(
            CHANGELOGS_DIR,
            ANSIBLE_RELEASE_FILE,
            ANSIBLE_PYPROJECT_TOML_FILE,
        ),
        allow_stale=allow_stale,
    )

    create_pull_request(pr)


# noinspection PyUnusedLocal
@command
def complete(repository: str, allow_dirty: bool = False) -> None:
    """Complete a release after the prepared changes have been merged."""
    command.run(
        check_state,
        build,
        test,
        publish,
        tag_release,
        post_version,
        create_post_pr,
    )


@command
def build(allow_dirty: bool = False) -> None:
    """Build the sdist and wheel."""
    version = get_ansible_version(mode=VersionMode.ALLOW_DEV_POST)

    # TODO: consider pinning the build requirement and its dependencies
    build_requirements = """
build
"""
    env = ensure_venv(build_requirements)

    dirty = git("status", "--porcelain", "--untracked-files=all", capture_output=True).stdout.strip().splitlines()

    if dirty:
        with suppress_when(allow_dirty):
            raise ApplicationError(f"There are {len(dirty)} files which are untracked and/or have changes, which will be omitted from the build.")

    sdist_file = get_sdist_path(version)
    wheel_file = get_wheel_path(version)

    with tempfile.TemporaryDirectory(dir=DIST_DIR, prefix=f"build-{version}-", suffix=".tmp") as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)
        dist_dir = temp_dir / "dist"

        commit_time = int(git("show", "-s", "--format=%ct", capture_output=True).stdout)

        env.update(
            SOURCE_DATE_EPOCH=commit_time,
        )

        git("worktree", "add", "-d", temp_dir)

        try:
            run("python", "-m", "build", env=env, cwd=temp_dir)

            create_reproducible_sdist(get_sdist_path(version, dist_dir), sdist_file, commit_time)
            get_wheel_path(version, dist_dir).rename(wheel_file)
        finally:
            git("worktree", "remove", temp_dir)


@command
def test() -> None:
    """Test the sdist and wheel."""
    command.run(
        test_sdist,
        test_wheel,
    )


@command
def test_sdist() -> None:
    """Test the sdist."""
    version = get_ansible_version(mode=VersionMode.ALLOW_DEV_POST)
    sdist_file = get_sdist_path(version)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)

        with contextlib.ExitStack() as stack:
            try:
                sdist = stack.enter_context(tarfile.open(sdist_file))
            except FileNotFoundError:
                raise ApplicationError(f"Missing sdist: {sdist_file.relative_to(CHECKOUT_DIR)}") from None

            sdist.extractall(temp_dir, filter='data')

        pyc_glob = "*.pyc*"
        pyc_files = sorted(path.relative_to(temp_dir) for path in temp_dir.rglob(pyc_glob))

        if pyc_files:
            raise ApplicationError(f"Found {len(pyc_files)} '{pyc_glob}' file(s): {', '.join(map(str, pyc_files))}")

    test_built_artifact(sdist_file)


@command
def test_wheel() -> None:
    """Test the wheel."""
    version = get_ansible_version(mode=VersionMode.ALLOW_DEV_POST)
    wheel_file = get_wheel_path(version)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)

        with contextlib.ExitStack() as stack:
            try:
                wheel = stack.enter_context(zipfile.ZipFile(wheel_file))
            except FileNotFoundError:
                raise ApplicationError(f"Missing wheel for version {version}: {wheel_file}") from None

            wheel.extractall(temp_dir)

    test_built_artifact(wheel_file)


@command
def publish(repository: str, prompt: bool = True) -> None:
    """Publish to PyPI."""
    version = get_ansible_version()
    sdist_file = get_sdist_path(version)
    wheel_file = get_wheel_path(version)

    # TODO: consider pinning the twine requirement and its dependencies
    publish_requirements = """
twine
"""
    env = ensure_venv(publish_requirements)

    if prompt:
        try:
            while input(f"Do you want to publish {version} to the '{repository}' repository?\nEnter the repository name to confirm: ") != repository:
                pass
        except KeyboardInterrupt:
            display.show("")
            raise ApplicationError("Publishing was aborted by the user.") from None

    run("twine", "upload", "-r", repository, sdist_file, wheel_file, env=env, cwd=CHECKOUT_DIR)


@command
def tag_release(repository: str, commit: str | None = None, validate: bool = True, allow_tag: bool = False) -> None:
    """Create a GitHub release using the current or specified commit."""
    upstream = get_remotes().upstream

    if commit:
        git("fetch", upstream.name)  # fetch upstream to make sure the commit can be found

    commit = get_commit(commit)
    version = get_ansible_version(commit=commit)
    tag = f"v{version}"

    if upstream_tag := git("ls-remote", "--tags", upstream.name, tag, capture_output=True).stdout.strip():
        with suppress_when(allow_tag):
            raise ApplicationError(f"Version {version} has already been tagged: {upstream_tag}")

    upstream_branch = get_upstream_branch(version)
    upstream_refs = git("branch", "-r", "--format=%(refname)", "--contains", commit, capture_output=True).stdout.strip().splitlines()
    upstream_ref = f"refs/remotes/{upstream.name}/{upstream_branch}"

    if upstream_ref not in upstream_refs:
        raise ApplicationError(f"Commit {upstream_ref} not found. Found {len(upstream_refs)} upstream ref(s): {', '.join(upstream_refs)}")

    body = create_github_release_notes(upstream, repository, version, validate)

    release = GitHubRelease(
        user=upstream.user,
        repo=upstream.repo,
        target=commit,
        tag=tag,
        title=tag,
        body=body,
        pre_release=version.pre is not None,
    )

    create_github_release(release)


@command
def post_version() -> None:
    """Set the post release version."""
    current_version = get_ansible_version()
    requested_version = get_ansible_version(f"{current_version}.post0", mode=VersionMode.REQUIRE_POST)

    set_ansible_version(current_version, requested_version)


@command
def create_post_pr(allow_stale: bool = False) -> None:
    """Create a branch and open a browser tab for creating a post release pull request."""
    version = get_ansible_version(mode=VersionMode.REQUIRE_POST)

    pr = prepare_pull_request(
        version=version,
        branch=f"release-{version}-{secrets.token_hex(4)}",
        title=f"Update Ansible release version to v{version}.",
        add=(ANSIBLE_RELEASE_FILE,),
        allow_stale=allow_stale,
    )

    create_pull_request(pr)


# endregion


if __name__ == "__main__":
    command.main()
