"""Utility code for facilitating collection of code coverage when running tests."""
from __future__ import annotations

import atexit
import os
import tempfile
import typing as t

from .config import (
    IntegrationConfig,
    SanityConfig,
    TestConfig,
)

from .io import (
    write_text_file,
    make_dirs,
)

from .util import (
    COVERAGE_CONFIG_NAME,
    remove_tree,
    sanitize_host_name,
)

from .data import (
    data_context,
)

from .util_common import (
    intercept_python,
    ResultType,
)

from .host_configs import (
    DockerConfig,
    HostConfig,
    OriginConfig,
    PosixRemoteConfig,
    PosixSshConfig,
    PythonConfig,
)


def cover_python(
        args,  # type: TestConfig
        python,  # type: PythonConfig
        cmd,  # type: t.List[str]
        target_name,  # type: str
        env,  # type: t.Dict[str, str]
        capture=False,  # type: bool
        data=None,  # type: t.Optional[str]
        cwd=None,  # type: t.Optional[str]
):  # type: (...) -> t.Tuple[t.Optional[str], t.Optional[str]]
    """Run a command while collecting Python code coverage."""
    if args.coverage:
        env.update(get_coverage_environment(args, target_name, python.version))

    return intercept_python(args, python, cmd, env, capture, data, cwd)


def get_coverage_platform(config):  # type: (HostConfig) -> str
    """Return the platform label for the given host config."""
    if isinstance(config, PosixRemoteConfig):
        platform = f'remote-{sanitize_host_name(config.name)}'
    elif isinstance(config, DockerConfig):
        platform = f'docker-{sanitize_host_name(config.name)}'
    elif isinstance(config, PosixSshConfig):
        platform = f'ssh-{sanitize_host_name(config.host)}'
    elif isinstance(config, OriginConfig):
        platform = 'origin'  # previous versions of ansible-test used "local-{python_version}"
    else:
        raise NotImplementedError(f'Coverage platform label not defined for type: {type(config)}')

    return platform


def get_coverage_environment(
        args,  # type: TestConfig
        target_name,  # type: str
        version,  # type: str
):  # type: (...) -> t.Dict[str, str]
    """Return environment variables needed to collect code coverage."""
    # unit tests, sanity tests and other special cases (localhost only)
    # config is in a temporary directory
    # results are in the source tree
    config_file = get_coverage_config(args)
    coverage_name = '='.join((args.command, target_name, get_coverage_platform(args.controller), f'python-{version}', 'coverage'))
    coverage_dir = os.path.join(data_context().content.root, data_context().content.results_path, ResultType.COVERAGE.name)
    coverage_file = os.path.join(coverage_dir, coverage_name)

    make_dirs(coverage_dir)

    if args.coverage_check:
        # cause the 'coverage' module to be found, but not imported or enabled
        coverage_file = ''

    # Enable code coverage collection on local Python programs (this does not include Ansible modules).
    # Used by the injectors to support code coverage.
    # Used by the pytest unit test plugin to support code coverage.
    # The COVERAGE_FILE variable is also used directly by the 'coverage' module.
    env = dict(
        COVERAGE_CONF=config_file,
        COVERAGE_FILE=coverage_file,
    )

    return env


def get_coverage_config(args):  # type: (TestConfig) -> str
    """Return the path to the coverage config, creating the config if it does not already exist."""
    try:
        return get_coverage_config.path
    except AttributeError:
        pass

    coverage_config = generate_coverage_config(args)

    if args.explain:
        temp_dir = '/tmp/coverage-temp-dir'
    else:
        temp_dir = tempfile.mkdtemp()
        atexit.register(lambda: remove_tree(temp_dir))

    path = get_coverage_config.path = os.path.join(temp_dir, COVERAGE_CONFIG_NAME)

    if not args.explain:
        write_text_file(path, coverage_config)

    return path


def generate_coverage_config(args):  # type: (TestConfig) -> str
    """Generate code coverage configuration for tests."""
    if data_context().content.collection:
        coverage_config = generate_collection_coverage_config(args)
    else:
        coverage_config = generate_ansible_coverage_config()

    return coverage_config


def generate_ansible_coverage_config():  # type: () -> str
    """Generate code coverage configuration for Ansible tests."""
    coverage_config = '''
[run]
branch = True
concurrency = multiprocessing
parallel = True

omit =
    */python*/dist-packages/*
    */python*/site-packages/*
    */python*/distutils/*
    */pyshared/*
    */pytest
    */AnsiballZ_*.py
    */test/results/*
'''

    return coverage_config


def generate_collection_coverage_config(args):  # type: (TestConfig) -> str
    """Generate code coverage configuration for Ansible Collection tests."""
    coverage_config = '''
[run]
branch = True
concurrency = multiprocessing
parallel = True
disable_warnings =
    no-data-collected
'''

    if isinstance(args, IntegrationConfig):
        coverage_config += '''
include =
    %s/*
    */%s/*
''' % (data_context().content.root, data_context().content.collection.directory)
    elif isinstance(args, SanityConfig):
        # temporary work-around for import sanity test
        coverage_config += '''
include =
    %s/*

omit =
    %s/*
''' % (data_context().content.root, os.path.join(data_context().content.root, data_context().content.results_path))
    else:
        coverage_config += '''
include =
     %s/*
''' % data_context().content.root

    return coverage_config
