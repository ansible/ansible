"""Ansible integration test infrastructure."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import contextlib
import datetime
import difflib
import filecmp
import json
import os
import random
import re
import shutil
import string
import tempfile
import time

from ... import types as t

from ...encoding import (
    to_bytes,
)

from ...ansible_util import (
    ansible_environment,
    check_pyyaml,
)

from ...executor import (
    get_python_version,
    get_changes_filter,
    AllTargetsSkipped,
    Delegate,
    install_command_requirements,
)

from ...ci import (
    get_ci_provider,
)

from ...target import (
    analyze_integration_target_dependencies,
    walk_integration_targets,
    IntegrationTarget,
    walk_internal_targets,
    TIntegrationTarget,
)

from ...config import (
    IntegrationConfig,
    NetworkIntegrationConfig,
    PosixIntegrationConfig,
    WindowsIntegrationConfig,
    TIntegrationConfig,
)

from ...io import (
    make_dirs,
    write_text_file,
    read_text_file,
    open_text_file,
)

from ...util import (
    ApplicationError,
    display,
    COVERAGE_CONFIG_NAME,
    MODE_DIRECTORY,
    MODE_DIRECTORY_WRITE,
    MODE_FILE,
    SubprocessError,
    remove_tree,
    find_executable,
    raw_command,
    ANSIBLE_TEST_TOOLS_ROOT,
    SUPPORTED_PYTHON_VERSIONS,
    get_hash,
)

from ...util_common import (
    named_temporary_file,
    ResultType,
    get_docker_completion,
    get_remote_completion,
    intercept_command,
    run_command,
    write_json_test_results,
)

from ...coverage_util import (
    generate_coverage_config,
)

from ...cache import (
    CommonCache,
)

from .cloud import (
    CloudEnvironmentConfig,
    cloud_filter,
    cloud_init,
    get_cloud_environment,
    get_cloud_platforms,
)

from ...data import (
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


def get_integration_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    if args.docker:
        return get_integration_docker_filter(args, targets)

    if args.remote:
        return get_integration_remote_filter(args, targets)

    return get_integration_local_filter(args, targets)


def common_integration_filter(args, targets, exclude):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :type exclude: list[str]
    """
    override_disabled = set(target for target in args.include if target.startswith('disabled/'))

    if not args.allow_disabled:
        skip = 'disabled/'
        override = [target.name for target in targets if override_disabled & set(target.aliases)]
        skipped = [target.name for target in targets if skip in target.aliases and target.name not in override]
        if skipped:
            exclude.extend(skipped)
            display.warning('Excluding tests marked "%s" which require --allow-disabled or prefixing with "disabled/": %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    override_unsupported = set(target for target in args.include if target.startswith('unsupported/'))

    if not args.allow_unsupported:
        skip = 'unsupported/'
        override = [target.name for target in targets if override_unsupported & set(target.aliases)]
        skipped = [target.name for target in targets if skip in target.aliases and target.name not in override]
        if skipped:
            exclude.extend(skipped)
            display.warning('Excluding tests marked "%s" which require --allow-unsupported or prefixing with "unsupported/": %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    override_unstable = set(target for target in args.include if target.startswith('unstable/'))

    if args.allow_unstable_changed:
        override_unstable |= set(args.metadata.change_description.focused_targets or [])

    if not args.allow_unstable:
        skip = 'unstable/'
        override = [target.name for target in targets if override_unstable & set(target.aliases)]
        skipped = [target.name for target in targets if skip in target.aliases and target.name not in override]
        if skipped:
            exclude.extend(skipped)
            display.warning('Excluding tests marked "%s" which require --allow-unstable or prefixing with "unstable/": %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    # only skip a Windows test if using --windows and all the --windows versions are defined in the aliases as skip/windows/%s
    if isinstance(args, WindowsIntegrationConfig) and args.windows:
        all_skipped = []
        not_skipped = []

        for target in targets:
            if "skip/windows/" not in target.aliases:
                continue

            skip_valid = []
            skip_missing = []
            for version in args.windows:
                if "skip/windows/%s/" % version in target.aliases:
                    skip_valid.append(version)
                else:
                    skip_missing.append(version)

            if skip_missing and skip_valid:
                not_skipped.append((target.name, skip_valid, skip_missing))
            elif skip_valid:
                all_skipped.append(target.name)

        if all_skipped:
            exclude.extend(all_skipped)
            skip_aliases = ["skip/windows/%s/" % w for w in args.windows]
            display.warning('Excluding tests marked "%s" which are set to skip with --windows %s: %s'
                            % ('", "'.join(skip_aliases), ', '.join(args.windows), ', '.join(all_skipped)))

        if not_skipped:
            for target, skip_valid, skip_missing in not_skipped:
                # warn when failing to skip due to lack of support for skipping only some versions
                display.warning('Including test "%s" which was marked to skip for --windows %s but not %s.'
                                % (target, ', '.join(skip_valid), ', '.join(skip_missing)))


def get_integration_local_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    exclude = []

    common_integration_filter(args, targets, exclude)

    if not args.allow_root and os.getuid() != 0:
        skip = 'needs/root/'
        skipped = [target.name for target in targets if skip in target.aliases]
        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require --allow-root or running as root: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    override_destructive = set(target for target in args.include if target.startswith('destructive/'))

    if not args.allow_destructive:
        skip = 'destructive/'
        override = [target.name for target in targets if override_destructive & set(target.aliases)]
        skipped = [target.name for target in targets if skip in target.aliases and target.name not in override]
        if skipped:
            exclude.extend(skipped)
            display.warning('Excluding tests marked "%s" which require --allow-destructive or prefixing with "destructive/" to run locally: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    exclude_targets_by_python_version(targets, args.python_version, exclude)

    return exclude


def get_integration_docker_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    exclude = []

    common_integration_filter(args, targets, exclude)

    skip = 'skip/docker/'
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which cannot run under docker: %s'
                        % (skip.rstrip('/'), ', '.join(skipped)))

    if not args.docker_privileged:
        skip = 'needs/privileged/'
        skipped = [target.name for target in targets if skip in target.aliases]
        if skipped:
            exclude.append(skip)
            display.warning('Excluding tests marked "%s" which require --docker-privileged to run under docker: %s'
                            % (skip.rstrip('/'), ', '.join(skipped)))

    python_version = get_python_version(args, get_docker_completion(), args.docker_raw)

    exclude_targets_by_python_version(targets, python_version, exclude)

    return exclude


def get_integration_remote_filter(args, targets):
    """
    :type args: IntegrationConfig
    :type targets: tuple[IntegrationTarget]
    :rtype: list[str]
    """
    remote = args.parsed_remote

    exclude = []

    common_integration_filter(args, targets, exclude)

    skips = {
        'skip/%s' % remote.platform: remote.platform,
        'skip/%s/%s' % (remote.platform, remote.version): '%s %s' % (remote.platform, remote.version),
        'skip/%s%s' % (remote.platform, remote.version): '%s %s' % (remote.platform, remote.version),  # legacy syntax, use above format
    }

    if remote.arch:
        skips.update({
            'skip/%s/%s' % (remote.arch, remote.platform): '%s on %s' % (remote.platform, remote.arch),
            'skip/%s/%s/%s' % (remote.arch, remote.platform, remote.version): '%s %s on %s' % (remote.platform, remote.version, remote.arch),
        })

    for skip, description in skips.items():
        skipped = [target.name for target in targets if skip in target.skips]
        if skipped:
            exclude.append(skip + '/')
            display.warning('Excluding tests marked "%s" which are not supported on %s: %s' % (skip, description, ', '.join(skipped)))

    python_version = get_python_version(args, get_remote_completion(), args.remote)

    exclude_targets_by_python_version(targets, python_version, exclude)

    return exclude


def exclude_targets_by_python_version(targets, python_version, exclude):
    """
    :type targets: tuple[IntegrationTarget]
    :type python_version: str
    :type exclude: list[str]
    """
    if not python_version:
        display.warning('Python version unknown. Unable to skip tests based on Python version.')
        return

    python_major_version = python_version.split('.')[0]

    skip = 'skip/python%s/' % python_version
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on python %s: %s'
                        % (skip.rstrip('/'), python_version, ', '.join(skipped)))

    skip = 'skip/python%s/' % python_major_version
    skipped = [target.name for target in targets if skip in target.aliases]
    if skipped:
        exclude.append(skip)
        display.warning('Excluding tests marked "%s" which are not supported on python %s: %s'
                        % (skip.rstrip('/'), python_version, ', '.join(skipped)))


def command_integration_filter(args,  # type: TIntegrationConfig
                               targets,  # type: t.Iterable[TIntegrationTarget]
                               init_callback=None,  # type: t.Callable[[TIntegrationConfig, t.Tuple[TIntegrationTarget, ...]], None]
                               ):  # type: (...) -> t.Tuple[TIntegrationTarget, ...]
    """Filter the given integration test targets."""
    targets = tuple(target for target in targets if 'hidden/' not in target.aliases)
    changes = get_changes_filter(args)

    # special behavior when the --changed-all-target target is selected based on changes
    if args.changed_all_target in changes:
        # act as though the --changed-all-target target was in the include list
        if args.changed_all_mode == 'include' and args.changed_all_target not in args.include:
            args.include.append(args.changed_all_target)
            args.delegate_args += ['--include', args.changed_all_target]
        # act as though the --changed-all-target target was in the exclude list
        elif args.changed_all_mode == 'exclude' and args.changed_all_target not in args.exclude:
            args.exclude.append(args.changed_all_target)

    require = args.require + changes
    exclude = args.exclude

    internal_targets = walk_internal_targets(targets, args.include, exclude, require)
    environment_exclude = get_integration_filter(args, internal_targets)

    environment_exclude += cloud_filter(args, internal_targets)

    if environment_exclude:
        exclude += environment_exclude
        internal_targets = walk_internal_targets(targets, args.include, exclude, require)

    if not internal_targets:
        raise AllTargetsSkipped()

    if args.start_at and not any(target.name == args.start_at for target in internal_targets):
        raise ApplicationError('Start at target matches nothing: %s' % args.start_at)

    if init_callback:
        init_callback(args, internal_targets)

    cloud_init(args, internal_targets)

    vars_file_src = os.path.join(data_context().content.root, data_context().content.integration_vars_path)

    if os.path.exists(vars_file_src):
        def integration_config_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
            """
            Add the integration config vars file to the payload file list.
            This will preserve the file during delegation even if the file is ignored by source control.
            """
            files.append((vars_file_src, data_context().content.integration_vars_path))

        data_context().register_payload_callback(integration_config_callback)

    if args.delegate:
        raise Delegate(require=require, exclude=exclude)

    extra_requirements = []

    for cloud_platform in get_cloud_platforms(args):
        extra_requirements.append('%s.cloud.%s' % (args.command, cloud_platform))

    install_command_requirements(args, extra_requirements=extra_requirements)

    return internal_targets


def command_integration_filtered(
        args,  # type: IntegrationConfig
        targets,  # type: t.Tuple[IntegrationTarget]
        all_targets,  # type: t.Tuple[IntegrationTarget]
        inventory_path,  # type: str
        pre_target=None,  # type: t.Optional[t.Callable[IntegrationTarget]]
        post_target=None,  # type: t.Optional[t.Callable[IntegrationTarget]]
        remote_temp_path=None,  # type: t.Optional[str]
):
    """Run integration tests for the specified targets."""
    found = False
    passed = []
    failed = []

    targets_iter = iter(targets)
    all_targets_dict = dict((target.name, target) for target in all_targets)

    setup_errors = []
    setup_targets_executed = set()

    for target in all_targets:
        for setup_target in target.setup_once + target.setup_always:
            if setup_target not in all_targets_dict:
                setup_errors.append('Target "%s" contains invalid setup target: %s' % (target.name, setup_target))

    if setup_errors:
        raise ApplicationError('Found %d invalid setup aliases:\n%s' % (len(setup_errors), '\n'.join(setup_errors)))

    check_pyyaml(args, args.python_version)

    test_dir = os.path.join(ResultType.TMP.path, 'output_dir')

    if not args.explain and any('needs/ssh/' in target.aliases for target in targets):
        max_tries = 20
        display.info('SSH service required for tests. Checking to make sure we can connect.')
        for i in range(1, max_tries + 1):
            try:
                run_command(args, ['ssh', '-o', 'BatchMode=yes', 'localhost', 'id'], capture=True)
                display.info('SSH service responded.')
                break
            except SubprocessError:
                if i == max_tries:
                    raise
                seconds = 3
                display.warning('SSH service not responding. Waiting %d second(s) before checking again.' % seconds)
                time.sleep(seconds)

    start_at_task = args.start_at_task

    results = {}

    current_environment = None  # type: t.Optional[EnvironmentDescription]

    # common temporary directory path that will be valid on both the controller and the remote
    # it must be common because it will be referenced in environment variables that are shared across multiple hosts
    common_temp_path = '/tmp/ansible-test-%s' % ''.join(random.choice(string.ascii_letters + string.digits) for _idx in range(8))

    setup_common_temp_dir(args, common_temp_path)

    try:
        for target in targets_iter:
            if args.start_at and not found:
                found = target.name == args.start_at

                if not found:
                    continue

            if args.list_targets:
                print(target.name)
                continue

            tries = 2 if args.retry_on_error else 1
            verbosity = args.verbosity

            cloud_environment = get_cloud_environment(args, target)

            original_environment = current_environment if current_environment else EnvironmentDescription(args)
            current_environment = None

            display.info('>>> Environment Description\n%s' % original_environment, verbosity=3)

            try:
                while tries:
                    tries -= 1

                    try:
                        if cloud_environment:
                            cloud_environment.setup_once()

                        run_setup_targets(args, test_dir, target.setup_once, all_targets_dict, setup_targets_executed, inventory_path, common_temp_path, False)

                        start_time = time.time()

                        if pre_target:
                            pre_target(target)

                        run_setup_targets(args, test_dir, target.setup_always, all_targets_dict, setup_targets_executed, inventory_path, common_temp_path, True)

                        if not args.explain:
                            # create a fresh test directory for each test target
                            remove_tree(test_dir)
                            make_dirs(test_dir)

                        try:
                            if target.script_path:
                                command_integration_script(args, target, test_dir, inventory_path, common_temp_path,
                                                           remote_temp_path=remote_temp_path)
                            else:
                                command_integration_role(args, target, start_at_task, test_dir, inventory_path,
                                                         common_temp_path, remote_temp_path=remote_temp_path)
                                start_at_task = None
                        finally:
                            if post_target:
                                post_target(target)

                        end_time = time.time()

                        results[target.name] = dict(
                            name=target.name,
                            type=target.type,
                            aliases=target.aliases,
                            modules=target.modules,
                            run_time_seconds=int(end_time - start_time),
                            setup_once=target.setup_once,
                            setup_always=target.setup_always,
                            coverage=args.coverage,
                            coverage_label=args.coverage_label,
                            python_version=args.python_version,
                        )

                        break
                    except SubprocessError:
                        if cloud_environment:
                            cloud_environment.on_failure(target, tries)

                        if not original_environment.validate(target.name, throw=False):
                            raise

                        if not tries:
                            raise

                        display.warning('Retrying test target "%s" with maximum verbosity.' % target.name)
                        display.verbosity = args.verbosity = 6

                start_time = time.time()
                current_environment = EnvironmentDescription(args)
                end_time = time.time()

                EnvironmentDescription.check(original_environment, current_environment, target.name, throw=True)

                results[target.name]['validation_seconds'] = int(end_time - start_time)

                passed.append(target)
            except Exception as ex:
                failed.append(target)

                if args.continue_on_error:
                    display.error(ex)
                    continue

                display.notice('To resume at this test target, use the option: --start-at %s' % target.name)

                next_target = next(targets_iter, None)

                if next_target:
                    display.notice('To resume after this test target, use the option: --start-at %s' % next_target.name)

                raise
            finally:
                display.verbosity = args.verbosity = verbosity

    finally:
        if not args.explain:
            if args.coverage:
                coverage_temp_path = os.path.join(common_temp_path, ResultType.COVERAGE.name)
                coverage_save_path = ResultType.COVERAGE.path

                for filename in os.listdir(coverage_temp_path):
                    shutil.copy(os.path.join(coverage_temp_path, filename), os.path.join(coverage_save_path, filename))

            remove_tree(common_temp_path)

            result_name = '%s-%s.json' % (
                args.command, re.sub(r'[^0-9]', '-', str(datetime.datetime.utcnow().replace(microsecond=0))))

            data = dict(
                targets=results,
            )

            write_json_test_results(ResultType.DATA, result_name, data)

    if failed:
        raise ApplicationError('The %d integration test(s) listed below (out of %d) failed. See error output above for details:\n%s' % (
            len(failed), len(passed) + len(failed), '\n'.join(target.name for target in failed)))


def command_integration_script(args, target, test_dir, inventory_path, temp_path, remote_temp_path=None):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type test_dir: str
    :type inventory_path: str
    :type temp_path: str
    :type remote_temp_path: str | None
    """
    display.info('Running %s integration test script' % target.name)

    env_config = None

    if isinstance(args, PosixIntegrationConfig):
        cloud_environment = get_cloud_environment(args, target)

        if cloud_environment:
            env_config = cloud_environment.get_environment_config()

    if env_config:
        display.info('>>> Environment Config\n%s' % json.dumps(dict(
            env_vars=env_config.env_vars,
            ansible_vars=env_config.ansible_vars,
            callback_plugins=env_config.callback_plugins,
            module_defaults=env_config.module_defaults,
        ), indent=4, sort_keys=True), verbosity=3)

    with integration_test_environment(args, target, inventory_path) as test_env:
        cmd = ['./%s' % os.path.basename(target.script_path)]

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config)
        cwd = os.path.join(test_env.targets_dir, target.relative_path)

        env.update(dict(
            # support use of adhoc ansible commands in collections without specifying the fully qualified collection name
            ANSIBLE_PLAYBOOK_DIR=cwd,
        ))

        if env_config and env_config.env_vars:
            env.update(env_config.env_vars)

        with integration_test_config_file(args, env_config, test_env.integration_dir) as config_path:
            if config_path:
                cmd += ['-e', '@%s' % config_path]

            module_coverage = 'non_local/' not in target.aliases

            intercept_command(args, cmd, target_name=target.name, env=env, cwd=cwd, temp_path=temp_path,
                              remote_temp_path=remote_temp_path, module_coverage=module_coverage)


def command_integration_role(args, target, start_at_task, test_dir, inventory_path, temp_path, remote_temp_path=None):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type start_at_task: str | None
    :type test_dir: str
    :type inventory_path: str
    :type temp_path: str
    :type remote_temp_path: str | None
    """
    display.info('Running %s integration test role' % target.name)

    env_config = None

    vars_files = []
    variables = dict(
        output_dir=test_dir,
    )

    if isinstance(args, WindowsIntegrationConfig):
        hosts = 'windows'
        gather_facts = False
        variables.update(dict(
            win_output_dir=r'C:\ansible_testing',
        ))
    elif isinstance(args, NetworkIntegrationConfig):
        hosts = target.network_platform
        gather_facts = False
    else:
        hosts = 'testhost'
        gather_facts = True

    if not isinstance(args, NetworkIntegrationConfig):
        cloud_environment = get_cloud_environment(args, target)

        if cloud_environment:
            env_config = cloud_environment.get_environment_config()

    if env_config:
        display.info('>>> Environment Config\n%s' % json.dumps(dict(
            env_vars=env_config.env_vars,
            ansible_vars=env_config.ansible_vars,
            callback_plugins=env_config.callback_plugins,
            module_defaults=env_config.module_defaults,
        ), indent=4, sort_keys=True), verbosity=3)

    with integration_test_environment(args, target, inventory_path) as test_env:
        if os.path.exists(test_env.vars_file):
            vars_files.append(os.path.relpath(test_env.vars_file, test_env.integration_dir))

        play = dict(
            hosts=hosts,
            gather_facts=gather_facts,
            vars_files=vars_files,
            vars=variables,
            roles=[
                target.name,
            ],
        )

        if env_config:
            if env_config.ansible_vars:
                variables.update(env_config.ansible_vars)

            play.update(dict(
                environment=env_config.env_vars,
                module_defaults=env_config.module_defaults,
            ))

        playbook = json.dumps([play], indent=4, sort_keys=True)

        with named_temporary_file(args=args, directory=test_env.integration_dir, prefix='%s-' % target.name, suffix='.yml', content=playbook) as playbook_path:
            filename = os.path.basename(playbook_path)

            display.info('>>> Playbook: %s\n%s' % (filename, playbook.strip()), verbosity=3)

            cmd = ['ansible-playbook', filename, '-i', os.path.relpath(test_env.inventory_path, test_env.integration_dir)]

            if start_at_task:
                cmd += ['--start-at-task', start_at_task]

            if args.tags:
                cmd += ['--tags', args.tags]

            if args.skip_tags:
                cmd += ['--skip-tags', args.skip_tags]

            if args.diff:
                cmd += ['--diff']

            if isinstance(args, NetworkIntegrationConfig):
                if args.testcase:
                    cmd += ['-e', 'testcase=%s' % args.testcase]

            if args.verbosity:
                cmd.append('-' + ('v' * args.verbosity))

            env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config)
            cwd = test_env.integration_dir

            env.update(dict(
                # support use of adhoc ansible commands in collections without specifying the fully qualified collection name
                ANSIBLE_PLAYBOOK_DIR=cwd,
            ))

            if env_config and env_config.env_vars:
                env.update(env_config.env_vars)

            env['ANSIBLE_ROLES_PATH'] = test_env.targets_dir

            module_coverage = 'non_local/' not in target.aliases
            intercept_command(args, cmd, target_name=target.name, env=env, cwd=cwd, temp_path=temp_path,
                              remote_temp_path=remote_temp_path, module_coverage=module_coverage)


def run_setup_targets(args, test_dir, target_names, targets_dict, targets_executed, inventory_path, temp_path, always):
    """
    :type args: IntegrationConfig
    :type test_dir: str
    :type target_names: list[str]
    :type targets_dict: dict[str, IntegrationTarget]
    :type targets_executed: set[str]
    :type inventory_path: str
    :type temp_path: str
    :type always: bool
    """
    for target_name in target_names:
        if not always and target_name in targets_executed:
            continue

        target = targets_dict[target_name]

        if not args.explain:
            # create a fresh test directory for each test target
            remove_tree(test_dir)
            make_dirs(test_dir)

        if target.script_path:
            command_integration_script(args, target, test_dir, inventory_path, temp_path)
        else:
            command_integration_role(args, target, None, test_dir, inventory_path, temp_path)

        targets_executed.add(target_name)


def integration_environment(args, target, test_dir, inventory_path, ansible_config, env_config):
    """
    :type args: IntegrationConfig
    :type target: IntegrationTarget
    :type test_dir: str
    :type inventory_path: str
    :type ansible_config: str | None
    :type env_config: CloudEnvironmentConfig | None
    :rtype: dict[str, str]
    """
    env = ansible_environment(args, ansible_config=ansible_config)

    callback_plugins = ['junit'] + (env_config.callback_plugins or [] if env_config else [])

    integration = dict(
        JUNIT_OUTPUT_DIR=ResultType.JUNIT.path,
        ANSIBLE_CALLBACKS_ENABLED=','.join(sorted(set(callback_plugins))),
        ANSIBLE_TEST_CI=args.metadata.ci_provider or get_ci_provider().code,
        ANSIBLE_TEST_COVERAGE='check' if args.coverage_check else ('yes' if args.coverage else ''),
        OUTPUT_DIR=test_dir,
        INVENTORY_PATH=os.path.abspath(inventory_path),
    )

    if args.debug_strategy:
        env.update(dict(ANSIBLE_STRATEGY='debug'))

    if 'non_local/' in target.aliases:
        if args.coverage:
            display.warning('Skipping coverage reporting on Ansible modules for non-local test: %s' % target.name)

        env.update(dict(ANSIBLE_TEST_REMOTE_INTERPRETER=''))

    env.update(integration)

    return env


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


class EnvironmentDescription:
    """Description of current running environment."""
    def __init__(self, args):
        """Initialize snapshot of environment configuration.
        :type args: IntegrationConfig
        """
        self.args = args

        if self.args.explain:
            self.data = {}
            return

        warnings = []

        versions = ['']
        versions += SUPPORTED_PYTHON_VERSIONS
        versions += list(set(v.split('.', 1)[0] for v in SUPPORTED_PYTHON_VERSIONS))

        version_check = os.path.join(ANSIBLE_TEST_TOOLS_ROOT, 'versions.py')
        python_paths = dict((v, find_executable('python%s' % v, required=False)) for v in sorted(versions))
        pip_paths = dict((v, find_executable('pip%s' % v, required=False)) for v in sorted(versions))
        program_versions = dict((v, self.get_version([python_paths[v], version_check], warnings)) for v in sorted(python_paths) if python_paths[v])
        pip_interpreters = dict((v, self.get_shebang(pip_paths[v])) for v in sorted(pip_paths) if pip_paths[v])
        known_hosts_hash = get_hash(os.path.expanduser('~/.ssh/known_hosts'))

        for version in sorted(versions):
            self.check_python_pip_association(version, python_paths, pip_paths, pip_interpreters, warnings)

        for warning in warnings:
            display.warning(warning, unique=True)

        self.data = dict(
            python_paths=python_paths,
            pip_paths=pip_paths,
            program_versions=program_versions,
            pip_interpreters=pip_interpreters,
            known_hosts_hash=known_hosts_hash,
            warnings=warnings,
        )

    @staticmethod
    def check_python_pip_association(version, python_paths, pip_paths, pip_interpreters, warnings):
        """
        :type version: str
        :param python_paths: dict[str, str]
        :param pip_paths:  dict[str, str]
        :param pip_interpreters:  dict[str, str]
        :param warnings: list[str]
        """
        python_label = 'Python%s' % (' %s' % version if version else '')

        pip_path = pip_paths.get(version)
        python_path = python_paths.get(version)

        if not python_path or not pip_path:
            # skip checks when either python or pip are missing for this version
            return

        pip_shebang = pip_interpreters.get(version)

        match = re.search(r'#!\s*(?P<command>[^\s]+)', pip_shebang)

        if not match:
            warnings.append('A %s pip was found at "%s", but it does not have a valid shebang: %s' % (python_label, pip_path, pip_shebang))
            return

        pip_interpreter = os.path.realpath(match.group('command'))
        python_interpreter = os.path.realpath(python_path)

        if pip_interpreter == python_interpreter:
            return

        try:
            identical = filecmp.cmp(pip_interpreter, python_interpreter)
        except OSError:
            identical = False

        if identical:
            return

        warnings.append('A %s pip was found at "%s", but it uses interpreter "%s" instead of "%s".' % (
            python_label, pip_path, pip_interpreter, python_interpreter))

    def __str__(self):
        """
        :rtype: str
        """
        return json.dumps(self.data, sort_keys=True, indent=4)

    def validate(self, target_name, throw):
        """
        :type target_name: str
        :type throw: bool
        :rtype: bool
        """
        current = EnvironmentDescription(self.args)

        return self.check(self, current, target_name, throw)

    @staticmethod
    def check(original, current, target_name, throw):
        """
        :type original: EnvironmentDescription
        :type current: EnvironmentDescription
        :type target_name: str
        :type throw: bool
        :rtype: bool
        """
        original_json = str(original)
        current_json = str(current)

        if original_json == current_json:
            return True

        unified_diff = '\n'.join(difflib.unified_diff(
            a=original_json.splitlines(),
            b=current_json.splitlines(),
            fromfile='original.json',
            tofile='current.json',
            lineterm='',
        ))

        message = ('Test target "%s" has changed the test environment!\n'
                   'If these changes are necessary, they must be reverted before the test finishes.\n'
                   '>>> Original Environment\n'
                   '%s\n'
                   '>>> Current Environment\n'
                   '%s\n'
                   '>>> Environment Diff\n'
                   '%s'
                   % (target_name, original_json, current_json, unified_diff))

        if throw:
            raise ApplicationError(message)

        display.error(message)

        return False

    @staticmethod
    def get_version(command, warnings):
        """
        :type command: list[str]
        :type warnings: list[text]
        :rtype: list[str]
        """
        try:
            stdout, stderr = raw_command(command, capture=True, cmd_verbosity=2)
        except SubprocessError as ex:
            warnings.append(u'%s' % ex)
            return None  # all failures are equal, we don't care why it failed, only that it did

        return [line.strip() for line in ((stdout or '').strip() + (stderr or '').strip()).splitlines()]

    @staticmethod
    def get_shebang(path):
        """
        :type path: str
        :rtype: str
        """
        with open_text_file(path) as script_fd:
            return script_fd.readline().strip()
