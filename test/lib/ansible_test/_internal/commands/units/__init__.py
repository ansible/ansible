"""Execute unit tests using pytest."""
from __future__ import annotations

import os
import sys
import typing as t

from ...constants import (
    CONTROLLER_MIN_PYTHON_VERSION,
    CONTROLLER_PYTHON_VERSIONS,
    REMOTE_ONLY_PYTHON_VERSIONS,
    SUPPORTED_PYTHON_VERSIONS,
)

from ...io import (
    write_text_file,
    make_dirs,
)

from ...util import (
    ANSIBLE_TEST_DATA_ROOT,
    display,
    is_subdir,
    str_to_version,
    SubprocessError,
    ANSIBLE_LIB_ROOT,
    ANSIBLE_TEST_TARGET_ROOT,
)

from ...util_common import (
    ResultType,
    handle_layout_messages,
    create_temp_dir,
)

from ...ansible_util import (
    ansible_environment,
    get_ansible_python_path,
)

from ...target import (
    walk_internal_targets,
    walk_units_targets,
)

from ...config import (
    UnitsConfig,
)

from ...coverage_util import (
    cover_python,
)

from ...data import (
    data_context,
)

from ...executor import (
    AllTargetsSkipped,
    Delegate,
    get_changes_filter,
)

from ...python_requirements import (
    install_requirements,
)

from ...content_config import (
    get_content_config,
)

from ...host_configs import (
    PosixConfig,
)

from ...provisioning import (
    prepare_profiles,
)

from ...pypi_proxy import (
    configure_pypi_proxy,
)

from ...host_profiles import (
    PosixProfile,
)


class TestContext:
    """Contexts that unit tests run in based on the type of content."""

    controller = 'controller'
    modules = 'modules'
    module_utils = 'module_utils'


def command_units(args: UnitsConfig) -> None:
    """Run unit tests."""
    handle_layout_messages(data_context().content.unit_messages)

    changes = get_changes_filter(args)
    require = args.require + changes
    include = walk_internal_targets(walk_units_targets(), args.include, args.exclude, require)

    paths = [target.path for target in include]

    content_config = get_content_config(args)
    supported_remote_python_versions = content_config.modules.python_versions

    if content_config.modules.controller_only:
        # controller-only collections run modules/module_utils unit tests as controller-only tests
        module_paths = []
        module_utils_paths = []
    else:
        # normal collections run modules/module_utils unit tests isolated from controller code due to differences in python version requirements
        module_paths = [path for path in paths if is_subdir(path, data_context().content.unit_module_path)]
        module_utils_paths = [path for path in paths if is_subdir(path, data_context().content.unit_module_utils_path)]

    controller_paths = sorted(path for path in set(paths) - set(module_paths) - set(module_utils_paths))

    remote_paths = module_paths or module_utils_paths

    test_context_paths = {
        TestContext.modules: module_paths,
        TestContext.module_utils: module_utils_paths,
        TestContext.controller: controller_paths,
    }

    if not paths:
        raise AllTargetsSkipped()

    targets = t.cast(list[PosixConfig], args.targets)
    target_versions: dict[str, PosixConfig] = {target.python.version: target for target in targets}
    skipped_versions = args.host_settings.skipped_python_versions
    warn_versions = []

    # requested python versions that are remote-only and not supported by this collection
    test_versions = [version for version in target_versions if version in REMOTE_ONLY_PYTHON_VERSIONS and version not in supported_remote_python_versions]

    if test_versions:
        for version in test_versions:
            display.warning(f'Skipping unit tests on Python {version} because it is not supported by this collection.'
                            f' Supported Python versions are: {", ".join(content_config.python_versions)}')

        warn_versions.extend(test_versions)

        if warn_versions == list(target_versions):
            raise AllTargetsSkipped()

    if not remote_paths:
        # all selected unit tests are controller tests

        # requested python versions that are remote-only
        test_versions = [version for version in target_versions if version in REMOTE_ONLY_PYTHON_VERSIONS and version not in warn_versions]

        if test_versions:
            for version in test_versions:
                display.warning(f'Skipping unit tests on Python {version} because it is only supported by module/module_utils unit tests.'
                                ' No module/module_utils unit tests were selected.')

            warn_versions.extend(test_versions)

            if warn_versions == list(target_versions):
                raise AllTargetsSkipped()

    if not controller_paths:
        # all selected unit tests are remote tests

        # requested python versions that are not supported by remote tests for this collection
        test_versions = [version for version in target_versions if version not in supported_remote_python_versions and version not in warn_versions]

        if test_versions:
            for version in test_versions:
                display.warning(f'Skipping unit tests on Python {version} because it is not supported by module/module_utils unit tests of this collection.'
                                f' Supported Python versions are: {", ".join(supported_remote_python_versions)}')

            warn_versions.extend(test_versions)

            if warn_versions == list(target_versions):
                raise AllTargetsSkipped()

    host_state = prepare_profiles(args, targets_use_pypi=True)  # units

    if args.delegate:
        raise Delegate(host_state=host_state, require=changes, exclude=args.exclude)

    test_sets = []

    if args.requirements_mode != 'skip':
        configure_pypi_proxy(args, host_state.controller_profile)  # units

    for version in SUPPORTED_PYTHON_VERSIONS:
        if version not in target_versions and version not in skipped_versions:
            continue

        test_candidates = []

        for test_context, paths in test_context_paths.items():
            if test_context == TestContext.controller:
                if version not in CONTROLLER_PYTHON_VERSIONS:
                    continue
            else:
                if version not in supported_remote_python_versions:
                    continue

            if not paths:
                continue

            env = ansible_environment(args)

            env.update(
                PYTHONPATH=get_units_ansible_python_path(args, test_context),
                ANSIBLE_CONTROLLER_MIN_PYTHON_VERSION=CONTROLLER_MIN_PYTHON_VERSION,
            )

            test_candidates.append((test_context, paths, env))

        if not test_candidates:
            continue

        if version in skipped_versions:
            display.warning("Skipping unit tests on Python %s because it could not be found." % version)
            continue

        target_profiles: dict[str, PosixProfile] = {profile.config.python.version: profile for profile in host_state.targets(PosixProfile)}
        target_profile = target_profiles[version]

        final_candidates = [(test_context, target_profile.python, paths, env) for test_context, paths, env in test_candidates]
        controller = any(test_context == TestContext.controller for test_context, python, paths, env in final_candidates)

        if args.requirements_mode != 'skip':
            install_requirements(args, target_profile.python, ansible=controller, command=True, controller=False)  # units

        test_sets.extend(final_candidates)

    if args.requirements_mode == 'only':
        sys.exit()

    for test_context, python, paths, env in test_sets:
        # When using pytest-mock, make sure that features introduced in Python 3.8 are available to older Python versions.
        # This is done by enabling the mock_use_standalone_module feature, which forces use of mock even when unittest.mock is available.
        # Later Python versions have not introduced additional unittest.mock features, so use of mock is not needed as of Python 3.8.
        # If future Python versions introduce new unittest.mock features, they will not be available to older Python versions.
        # Having the cutoff at Python 3.8 also eases packaging of ansible-core since no supported controller version requires the use of mock.
        #
        # NOTE: This only affects use of pytest-mock.
        #       Collection unit tests may directly import mock, which will be provided by ansible-test when it installs requirements using pip.
        #       Although mock is available for ansible-core unit tests, they should import unittest.mock instead.
        if str_to_version(python.version) < (3, 8):
            config_name = 'legacy.ini'
        else:
            config_name = 'default.ini'

        cmd = [
            'pytest',
            '-r', 'a',
            '-n', str(args.num_workers) if args.num_workers else 'auto',
            '--color', 'yes' if args.color else 'no',
            '-p', 'no:cacheprovider',
            '-c', os.path.join(ANSIBLE_TEST_DATA_ROOT, 'pytest', 'config', config_name),
            '--junit-xml', os.path.join(ResultType.JUNIT.path, 'python%s-%s-units.xml' % (python.version, test_context)),
            '--strict-markers',  # added in pytest 4.5.0
            '--rootdir', data_context().content.root,
            '--confcutdir', data_context().content.root,  # avoid permission errors when running from an installed version and using pytest >= 8
        ]  # fmt:skip

        if not data_context().content.collection:
            cmd.append('--durations=25')

        plugins = []

        if args.coverage:
            plugins.append('ansible_pytest_coverage')

        if data_context().content.collection:
            plugins.append('ansible_pytest_collections')

        plugins.append('ansible_forked')

        if plugins:
            env['PYTHONPATH'] += ':%s' % os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'pytest/plugins')
            env['PYTEST_PLUGINS'] = ','.join(plugins)

        if args.collect_only:
            cmd.append('--collect-only')

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        cmd.extend(paths)

        display.info('Unit test %s with Python %s' % (test_context, python.version))

        try:
            cover_python(args, python, cmd, test_context, env, capture=False)
        except SubprocessError as ex:
            # pytest exits with status code 5 when all tests are skipped, which isn't an error for our use case
            if ex.status != 5:
                raise


def get_units_ansible_python_path(args: UnitsConfig, test_context: str) -> str:
    """
    Return a directory usable for PYTHONPATH, containing only the modules and module_utils portion of the ansible package.
    The temporary directory created will be cached for the lifetime of the process and cleaned up at exit.
    """
    if test_context == TestContext.controller:
        return get_ansible_python_path(args)

    try:
        cache = get_units_ansible_python_path.cache  # type: ignore[attr-defined]
    except AttributeError:
        cache = get_units_ansible_python_path.cache = {}  # type: ignore[attr-defined]

    python_path = cache.get(test_context)

    if python_path:
        return python_path

    python_path = create_temp_dir(prefix='ansible-test-')
    ansible_path = os.path.join(python_path, 'ansible')
    ansible_test_path = os.path.join(python_path, 'ansible_test')

    write_text_file(os.path.join(ansible_path, '__init__.py'), '', True)
    os.symlink(os.path.join(ANSIBLE_LIB_ROOT, 'module_utils'), os.path.join(ansible_path, 'module_utils'))

    if data_context().content.collection:
        # built-in runtime configuration for the collection loader
        make_dirs(os.path.join(ansible_path, 'config'))
        os.symlink(os.path.join(ANSIBLE_LIB_ROOT, 'config', 'ansible_builtin_runtime.yml'), os.path.join(ansible_path, 'config', 'ansible_builtin_runtime.yml'))

        # current collection loader required by all python versions supported by the controller
        write_text_file(os.path.join(ansible_path, 'utils', '__init__.py'), '', True)
        os.symlink(os.path.join(ANSIBLE_LIB_ROOT, 'utils', 'collection_loader'), os.path.join(ansible_path, 'utils', 'collection_loader'))

        # legacy collection loader required by all python versions not supported by the controller
        write_text_file(os.path.join(ansible_test_path, '__init__.py'), '', True)
        write_text_file(os.path.join(ansible_test_path, '_internal', '__init__.py'), '', True)
    elif test_context == TestContext.modules:
        # only non-collection ansible module tests should have access to ansible built-in modules
        os.symlink(os.path.join(ANSIBLE_LIB_ROOT, 'modules'), os.path.join(ansible_path, 'modules'))

    cache[test_context] = python_path

    return python_path
