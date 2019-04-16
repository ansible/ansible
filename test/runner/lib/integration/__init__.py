"""Ansible integration test infrastructure."""

from __future__ import absolute_import, print_function

import contextlib
import json
import os
import shutil
import stat
import tempfile

from lib.target import (
    analyze_integration_target_dependencies,
    walk_integration_targets,
)

from lib.config import (
    NetworkIntegrationConfig,
    PosixIntegrationConfig,
    WindowsIntegrationConfig,
)

from lib.util import (
    ApplicationError,
    display,
    make_dirs,
    named_temporary_file,
    COVERAGE_CONFIG_PATH,
    COVERAGE_OUTPUT_PATH,
    MODE_DIRECTORY,
    MODE_DIRECTORY_WRITE,
    MODE_FILE,
)

from lib.cache import (
    CommonCache,
)

from lib.cloud import (
    CloudEnvironmentConfig,
)


def setup_common_temp_dir(args, path):
    """
    :type args: IntegrationConfig
    :type path: str
    """
    if args.explain:
        return

    os.mkdir(path)
    os.chmod(path, MODE_DIRECTORY)

    coverage_config_path = os.path.join(path, COVERAGE_CONFIG_PATH)

    shutil.copy(COVERAGE_CONFIG_PATH, coverage_config_path)
    os.chmod(coverage_config_path, MODE_FILE)

    coverage_output_path = os.path.join(path, COVERAGE_OUTPUT_PATH)

    os.mkdir(coverage_output_path)
    os.chmod(coverage_output_path, MODE_DIRECTORY_WRITE)


def generate_dependency_map(integration_targets):
    """
    :type integration_targets: list[IntegrationTarget]
    :rtype: dict[str, set[IntegrationTarget]]
    """
    targets_dict = dict((target.name, target) for target in integration_targets)
    target_dependencies = analyze_integration_target_dependencies(integration_targets)
    dependency_map = {}

    invalid_targets = set()

    for dependency, dependents in target_dependencies.items():
        dependency_target = targets_dict.get(dependency)

        if not dependency_target:
            invalid_targets.add(dependency)
            continue

        for dependent in dependents:
            if dependent not in dependency_map:
                dependency_map[dependent] = set()

            dependency_map[dependent].add(dependency_target)

    if invalid_targets:
        raise ApplicationError('Non-existent target dependencies: %s' % ', '.join(sorted(invalid_targets)))

    return dependency_map


def get_files_needed(target_dependencies):
    """
    :type target_dependencies: list[IntegrationTarget]
    :rtype: list[str]
    """
    files_needed = []

    for target_dependency in target_dependencies:
        files_needed += target_dependency.needs_file

    files_needed = sorted(set(files_needed))

    invalid_paths = [path for path in files_needed if not os.path.isfile(path)]

    if invalid_paths:
        raise ApplicationError('Invalid "needs/file/*" aliases:\n%s' % '\n'.join(invalid_paths))

    return files_needed


@contextlib.contextmanager
def integration_test_environment(args, target, inventory_path):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type inventory_path: str
    """
    vars_file = 'integration_config.yml'

    if args.no_temp_workdir or 'no/temp_workdir/' in target.aliases:
        display.warning('Disabling the temp work dir is a temporary debugging feature that may be removed in the future without notice.')

        integration_dir = os.path.abspath('test/integration')
        inventory_path = os.path.abspath(inventory_path)
        ansible_config = os.path.join(integration_dir, '%s.cfg' % args.command)
        vars_file = os.path.join(integration_dir, vars_file)

        yield IntegrationEnvironment(integration_dir, inventory_path, ansible_config, vars_file)
        return

    root_temp_dir = os.path.expanduser('~/.ansible/test/tmp')

    prefix = '%s-' % target.name
    suffix = u'-\u00c5\u00d1\u015a\u00cc\u03b2\u0141\u00c8'

    if args.no_temp_unicode or 'no/temp_unicode/' in target.aliases:
        display.warning('Disabling unicode in the temp work dir is a temporary debugging feature that may be removed in the future without notice.')
        suffix = '-ansible'

    if isinstance('', bytes):
        suffix = suffix.encode('utf-8')

    if args.explain:
        temp_dir = os.path.join(root_temp_dir, '%stemp%s' % (prefix, suffix))
    else:
        make_dirs(root_temp_dir)
        temp_dir = tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=root_temp_dir)

    try:
        display.info('Preparing temporary directory: %s' % temp_dir, verbosity=2)

        inventory_names = {
            PosixIntegrationConfig: 'inventory',
            WindowsIntegrationConfig: 'inventory.winrm',
            NetworkIntegrationConfig: 'inventory.networking',
        }

        inventory_name = inventory_names[type(args)]

        cache = IntegrationCache(args)

        target_dependencies = sorted([target] + list(cache.dependency_map.get(target.name, set())))

        files_needed = get_files_needed(target_dependencies)

        integration_dir = os.path.join(temp_dir, 'test/integration')
        ansible_config = os.path.join(integration_dir, '%s.cfg' % args.command)

        file_copies = [
            ('test/integration/%s.cfg' % args.command, ansible_config),
            ('test/integration/integration_config.yml', os.path.join(integration_dir, vars_file)),
            (inventory_path, os.path.join(integration_dir, inventory_name)),
        ]

        file_copies += [(path, os.path.join(temp_dir, path)) for path in files_needed]

        directory_copies = [
            (os.path.join('test/integration/targets', target.name), os.path.join(integration_dir, 'targets', target.name)) for target in target_dependencies
        ]

        inventory_dir = os.path.dirname(inventory_path)

        host_vars_dir = os.path.join(inventory_dir, 'host_vars')
        group_vars_dir = os.path.join(inventory_dir, 'group_vars')

        if os.path.isdir(host_vars_dir):
            directory_copies.append((host_vars_dir, os.path.join(integration_dir, os.path.basename(host_vars_dir))))

        if os.path.isdir(group_vars_dir):
            directory_copies.append((group_vars_dir, os.path.join(integration_dir, os.path.basename(group_vars_dir))))

        directory_copies = sorted(set(directory_copies))
        file_copies = sorted(set(file_copies))

        if not args.explain:
            make_dirs(integration_dir)

        for dir_src, dir_dst in directory_copies:
            display.info('Copying %s/ to %s/' % (dir_src, dir_dst), verbosity=2)

            if not args.explain:
                shutil.copytree(dir_src, dir_dst, symlinks=True)

        for file_src, file_dst in file_copies:
            display.info('Copying %s to %s' % (file_src, file_dst), verbosity=2)

            if not args.explain:
                make_dirs(os.path.dirname(file_dst))
                shutil.copy2(file_src, file_dst)

        inventory_path = os.path.join(integration_dir, inventory_name)
        vars_file = os.path.join(integration_dir, vars_file)

        yield IntegrationEnvironment(integration_dir, inventory_path, ansible_config, vars_file)
    finally:
        if not args.explain:
            shutil.rmtree(temp_dir)


@contextlib.contextmanager
def integration_test_config_file(args, env_config, integration_dir):
    """
    :type args: IntegrationConfig
    :type env_config: CloudEnvironmentConfig
    :type integration_dir: str
    """
    if not env_config:
        yield None
        return

    config_vars = (env_config.ansible_vars or {}).copy()

    config_vars.update(dict(
        ansible_test=dict(
            environment=env_config.env_vars,
            module_defaults=env_config.module_defaults,
        )
    ))

    config_file = json.dumps(config_vars, indent=4, sort_keys=True)

    with named_temporary_file(args, 'config-file-', '.json', integration_dir, config_file) as path:
        filename = os.path.relpath(path, integration_dir)

        display.info('>>> Config File: %s\n%s' % (filename, config_file), verbosity=3)

        yield path


class IntegrationEnvironment(object):
    """Details about the integration environment."""
    def __init__(self, integration_dir, inventory_path, ansible_config, vars_file):
        self.integration_dir = integration_dir
        self.inventory_path = inventory_path
        self.ansible_config = ansible_config
        self.vars_file = vars_file


class IntegrationCache(CommonCache):
    """Integration cache."""
    @property
    def integration_targets(self):
        """
        :rtype: list[IntegrationTarget]
        """
        return self.get('integration_targets', lambda: list(walk_integration_targets()))

    @property
    def dependency_map(self):
        """
        :rtype: dict[str, set[IntegrationTarget]]
        """
        return self.get('dependency_map', lambda: generate_dependency_map(self.integration_targets))
