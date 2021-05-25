"""Execute unit tests using pytest."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys

from ...io import (
    write_text_file,
    make_dirs,
)

from ...util import (
    ANSIBLE_TEST_DATA_ROOT,
    display,
    get_available_python_versions,
    is_subdir,
    SubprocessError,
    SUPPORTED_PYTHON_VERSIONS,
    CONTROLLER_MIN_PYTHON_VERSION,
    CONTROLLER_PYTHON_VERSIONS,
    REMOTE_ONLY_PYTHON_VERSIONS,
    ANSIBLE_LIB_ROOT,
)

from ...util_common import (
    intercept_command,
    ResultType,
    handle_layout_messages,
    create_temp_dir,
)

from ...ansible_util import (
    ansible_environment,
    check_pyyaml,
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
    coverage_context,
)

from ...data import (
    data_context,
)

from ...executor import (
    AllTargetsSkipped,
    Delegate,
    get_changes_filter,
    install_command_requirements,
)

from ...content_config import (
    get_content_config,
)


class TestContext:
    """Contexts that unit tests run in based on the type of content."""
    controller = 'controller'
    modules = 'modules'
    module_utils = 'module_utils'


def command_units(args):
    """
    :type args: UnitsConfig
    """
    handle_layout_messages(data_context().content.unit_messages)

    changes = get_changes_filter(args)
    require = args.require + changes
    include = walk_internal_targets(walk_units_targets(), args.include, args.exclude, require)

    paths = [target.path for target in include]

    content_config = get_content_config()
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

    if args.python and args.python in REMOTE_ONLY_PYTHON_VERSIONS:
        if args.python not in supported_remote_python_versions:
            display.warning('Python %s is not supported by this collection. Supported Python versions are: %s' % (
                args.python, ', '.join(content_config.python_versions)))
            raise AllTargetsSkipped()

        if not remote_paths:
            display.warning('Python %s is only supported by module and module_utils unit tests, but none were selected.' % args.python)
            raise AllTargetsSkipped()

    if args.python and args.python not in supported_remote_python_versions and not controller_paths:
        display.warning('Python %s is not supported by this collection for modules/module_utils. Supported Python versions are: %s' % (
            args.python, ', '.join(supported_remote_python_versions)))
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes, exclude=args.exclude)

    test_sets = []

    available_versions = sorted(get_available_python_versions().keys())

    for version in SUPPORTED_PYTHON_VERSIONS:
        # run all versions unless version given, in which case run only that version
        if args.python and version != args.python_version:
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

            test_candidates.append((test_context, version, paths, env))

        if not test_candidates:
            continue

        if not args.python and version not in available_versions:
            display.warning("Skipping unit tests on Python %s due to missing interpreter." % version)
            continue

        if args.requirements_mode != 'skip':
            install_command_requirements(args, version)
            check_pyyaml(args, version)

        test_sets.extend(test_candidates)

    if args.requirements_mode == 'only':
        sys.exit()

    for test_context, version, paths, env in test_sets:
        cmd = [
            'pytest',
            '--boxed',
            '-r', 'a',
            '-n', str(args.num_workers) if args.num_workers else 'auto',
            '--color',
            'yes' if args.color else 'no',
            '-p', 'no:cacheprovider',
            '-c', os.path.join(ANSIBLE_TEST_DATA_ROOT, 'pytest.ini'),
            '--junit-xml', os.path.join(ResultType.JUNIT.path, 'python%s-%s-units.xml' % (version, test_context)),
        ]

        if not data_context().content.collection:
            cmd.append('--durations=25')

        if version != '2.6':
            # added in pytest 4.5.0, which requires python 2.7+
            cmd.append('--strict-markers')

        plugins = []

        if args.coverage:
            plugins.append('ansible_pytest_coverage')

        if data_context().content.collection:
            plugins.append('ansible_pytest_collections')

        if plugins:
            env['PYTHONPATH'] += ':%s' % os.path.join(ANSIBLE_TEST_DATA_ROOT, 'pytest/plugins')
            env['PYTEST_PLUGINS'] = ','.join(plugins)

        if args.collect_only:
            cmd.append('--collect-only')

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        cmd.extend(paths)

        display.info('Unit test %s with Python %s' % (test_context, version))

        try:
            with coverage_context(args):
                intercept_command(args, cmd, target_name=test_context, env=env, python_version=version)
        except SubprocessError as ex:
            # pytest exits with status code 5 when all tests are skipped, which isn't an error for our use case
            if ex.status != 5:
                raise


def get_units_ansible_python_path(args, test_context):  # type: (UnitsConfig, str) -> str
    """
    Return a directory usable for PYTHONPATH, containing only the modules and module_utils portion of the ansible package.
    The temporary directory created will be cached for the lifetime of the process and cleaned up at exit.
    """
    if test_context == TestContext.controller:
        return get_ansible_python_path(args)

    try:
        cache = get_units_ansible_python_path.cache
    except AttributeError:
        cache = get_units_ansible_python_path.cache = {}

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
        os.symlink(os.path.join(ANSIBLE_TEST_DATA_ROOT, 'legacy_collection_loader'), os.path.join(ansible_test_path, '_internal', 'legacy_collection_loader'))
    elif test_context == TestContext.modules:
        # only non-collection ansible module tests should have access to ansible built-in modules
        os.symlink(os.path.join(ANSIBLE_LIB_ROOT, 'modules'), os.path.join(ansible_path, 'modules'))

    cache[test_context] = python_path

    return python_path
