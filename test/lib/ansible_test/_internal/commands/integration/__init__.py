"""Ansible integration test infrastructure."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import contextlib
import json
import os
import shutil
import tempfile

from .. import types as t

from ..encoding import (
    to_bytes,
)

from ..target import (
    analyze_integration_target_dependencies,
    walk_integration_targets,
)

from ..config import (
    IntegrationConfig,
    NetworkIntegrationConfig,
    PosixIntegrationConfig,
    WindowsIntegrationConfig,
)

from ..io import (
    make_dirs,
    write_text_file,
    read_text_file,
)

from ..util import (
    ApplicationError,
    display,
    COVERAGE_CONFIG_NAME,
    MODE_DIRECTORY,
    MODE_DIRECTORY_WRITE,
    MODE_FILE,
)

from ..util_common import (
    named_temporary_file,
    ResultType,
)

from ..coverage_util import (
    generate_coverage_config,
)

from ..cache import (
    CommonCache,
)

from ..cloud import (
    CloudEnvironmentConfig,
)

from ..data import (
    data_context,
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

    if args.coverage:
        coverage_config_path = os.path.join(path, COVERAGE_CONFIG_NAME)

        coverage_config = generate_coverage_config(args)

        write_text_file(coverage_config_path, coverage_config)

        os.chmod(coverage_config_path, MODE_FILE)

        coverage_output_path = os.path.join(path, ResultType.COVERAGE.name)

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


def check_inventory(args, inventory_path):  # type: (IntegrationConfig, str) -> None
    """Check the given inventory for issues."""
    if args.docker or args.remote:
        if os.path.exists(inventory_path):
            inventory = read_text_file(inventory_path)

            if 'ansible_ssh_private_key_file' in inventory:
                display.warning('Use of "ansible_ssh_private_key_file" in inventory with the --docker or --remote option is unsupported and will likely fail.')


def get_inventory_relative_path(args):  # type: (IntegrationConfig) -> str
    """Return the inventory path used for the given integration configuration relative to the content root."""
    inventory_names = {
        PosixIntegrationConfig: 'inventory',
        WindowsIntegrationConfig: 'inventory.winrm',
        NetworkIntegrationConfig: 'inventory.networking',
    }  # type: t.Dict[t.Type[IntegrationConfig], str]

    return os.path.join(data_context().content.integration_path, inventory_names[type(args)])


def delegate_inventory(args, inventory_path_src):  # type: (IntegrationConfig, str) -> None
    """Make the given inventory available during delegation."""
    if isinstance(args, PosixIntegrationConfig):
        return

    def inventory_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
        """
        Add the inventory file to the payload file list.
        This will preserve the file during delegation even if it is ignored or is outside the content and install roots.
        """
        inventory_path = get_inventory_relative_path(args)
        inventory_tuple = inventory_path_src, inventory_path

        if os.path.isfile(inventory_path_src) and inventory_tuple not in files:
            originals = [item for item in files if item[1] == inventory_path]

            if originals:
                for original in originals:
                    files.remove(original)

                display.warning('Overriding inventory file "%s" with "%s".' % (inventory_path, inventory_path_src))
            else:
                display.notice('Sourcing inventory file "%s" from "%s".' % (inventory_path, inventory_path_src))

            files.append(inventory_tuple)

    data_context().register_payload_callback(inventory_callback)


@contextlib.contextmanager
def integration_test_environment(args, target, inventory_path_src):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type inventory_path_src: str
    """
    ansible_config_src = args.get_ansible_config()
    ansible_config_relative = os.path.join(data_context().content.integration_path, '%s.cfg' % args.command)

    if args.no_temp_workdir or 'no/temp_workdir/' in target.aliases:
        display.warning('Disabling the temp work dir is a temporary debugging feature that may be removed in the future without notice.')

        integration_dir = os.path.join(data_context().content.root, data_context().content.integration_path)
        targets_dir = os.path.join(data_context().content.root, data_context().content.integration_targets_path)
        inventory_path = inventory_path_src
        ansible_config = ansible_config_src
        vars_file = os.path.join(data_context().content.root, data_context().content.integration_vars_path)

        yield IntegrationEnvironment(integration_dir, targets_dir, inventory_path, ansible_config, vars_file)
        return

    # When testing a collection, the temporary directory must reside within the collection.
    # This is necessary to enable support for the default collection for non-collection content (playbooks and roles).
    root_temp_dir = os.path.join(ResultType.TMP.path, 'integration')

    prefix = '%s-' % target.name
    suffix = u'-\u00c5\u00d1\u015a\u00cc\u03b2\u0141\u00c8'

    if args.no_temp_unicode or 'no/temp_unicode/' in target.aliases:
        display.warning('Disabling unicode in the temp work dir is a temporary debugging feature that may be removed in the future without notice.')
        suffix = '-ansible'

    if args.explain:
        temp_dir = os.path.join(root_temp_dir, '%stemp%s' % (prefix, suffix))
    else:
        make_dirs(root_temp_dir)
        temp_dir = tempfile.mkdtemp(prefix=prefix, suffix=suffix, dir=root_temp_dir)

    try:
        display.info('Preparing temporary directory: %s' % temp_dir, verbosity=2)

        inventory_relative_path = get_inventory_relative_path(args)
        inventory_path = os.path.join(temp_dir, inventory_relative_path)

        cache = IntegrationCache(args)

        target_dependencies = sorted([target] + list(cache.dependency_map.get(target.name, set())))

        files_needed = get_files_needed(target_dependencies)

        integration_dir = os.path.join(temp_dir, data_context().content.integration_path)
        targets_dir = os.path.join(temp_dir, data_context().content.integration_targets_path)
        ansible_config = os.path.join(temp_dir, ansible_config_relative)

        vars_file_src = os.path.join(data_context().content.root, data_context().content.integration_vars_path)
        vars_file = os.path.join(temp_dir, data_context().content.integration_vars_path)

        file_copies = [
            (ansible_config_src, ansible_config),
            (inventory_path_src, inventory_path),
        ]

        if os.path.exists(vars_file_src):
            file_copies.append((vars_file_src, vars_file))

        file_copies += [(path, os.path.join(temp_dir, path)) for path in files_needed]

        integration_targets_relative_path = data_context().content.integration_targets_path

        directory_copies = [
            (
                os.path.join(integration_targets_relative_path, target.relative_path),
                os.path.join(temp_dir, integration_targets_relative_path, target.relative_path)
            )
            for target in target_dependencies
        ]

        directory_copies = sorted(set(directory_copies))
        file_copies = sorted(set(file_copies))

        if not args.explain:
            make_dirs(integration_dir)

        for dir_src, dir_dst in directory_copies:
            display.info('Copying %s/ to %s/' % (dir_src, dir_dst), verbosity=2)

            if not args.explain:
                shutil.copytree(to_bytes(dir_src), to_bytes(dir_dst), symlinks=True)

        for file_src, file_dst in file_copies:
            display.info('Copying %s to %s' % (file_src, file_dst), verbosity=2)

            if not args.explain:
                make_dirs(os.path.dirname(file_dst))
                shutil.copy2(file_src, file_dst)

        yield IntegrationEnvironment(integration_dir, targets_dir, inventory_path, ansible_config, vars_file)
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


class IntegrationEnvironment:
    """Details about the integration environment."""
    def __init__(self, integration_dir, targets_dir, inventory_path, ansible_config, vars_file):
        self.integration_dir = integration_dir
        self.targets_dir = targets_dir
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
