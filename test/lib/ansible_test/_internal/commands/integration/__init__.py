"""Ansible integration test infrastructure."""

from __future__ import annotations

import collections.abc as c
import contextlib
import datetime
import json
import os
import re
import shutil
import tempfile
import time
import typing as t

from ...encoding import (
    to_bytes,
)

from ...ansible_util import (
    ansible_environment,
)

from ...executor import (
    get_changes_filter,
    AllTargetsSkipped,
    Delegate,
    ListTargets,
)

from ...python_requirements import (
    install_requirements,
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
    IntegrationTargetType,
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
    read_text_file,
)

from ...util import (
    ApplicationError,
    display,
    SubprocessError,
    remove_tree,
)

from ...util_common import (
    named_temporary_file,
    ResultType,
    run_command,
    write_json_test_results,
    check_pyyaml,
)

from ...coverage_util import (
    cover_python,
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
    PayloadConfig,
)

from ...host_configs import (
    InventoryConfig,
    OriginConfig,
)

from ...host_profiles import (
    ControllerProfile,
    ControllerHostProfile,
    HostProfile,
    PosixProfile,
    SshTargetHostProfile,
    DebuggableProfile,
)

from ...provisioning import (
    HostState,
    prepare_profiles,
)

from ...pypi_proxy import (
    configure_pypi_proxy,
)

from ...inventory import (
    create_controller_inventory,
    create_windows_inventory,
    create_network_inventory,
    create_posix_inventory,
)

from .filters import (
    get_target_filter,
)

from .coverage import (
    CoverageManager,
)

THostProfile = t.TypeVar('THostProfile', bound=HostProfile)


def generate_dependency_map(integration_targets: list[IntegrationTarget]) -> dict[str, set[IntegrationTarget]]:
    """Analyze the given list of integration test targets and return a dictionary expressing target names and the targets on which they depend."""
    targets_dict = dict((target.name, target) for target in integration_targets)
    target_dependencies = analyze_integration_target_dependencies(integration_targets)
    dependency_map: dict[str, set[IntegrationTarget]] = {}

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


def get_files_needed(target_dependencies: list[IntegrationTarget]) -> list[str]:
    """Return a list of files needed by the given list of target dependencies."""
    files_needed: list[str] = []

    for target_dependency in target_dependencies:
        files_needed += target_dependency.needs_file

    files_needed = sorted(set(files_needed))

    invalid_paths = [path for path in files_needed if not os.path.isfile(path)]

    if invalid_paths:
        raise ApplicationError('Invalid "needs/file/*" aliases:\n%s' % '\n'.join(invalid_paths))

    return files_needed


def check_inventory(args: IntegrationConfig, inventory_path: str) -> None:
    """Check the given inventory for issues."""
    if not isinstance(args.controller, OriginConfig):
        if os.path.exists(inventory_path):
            inventory = read_text_file(inventory_path)

            if 'ansible_ssh_private_key_file' in inventory:
                display.warning('Use of "ansible_ssh_private_key_file" in inventory with the --docker or --remote option is unsupported and will likely fail.')


def get_inventory_absolute_path(args: IntegrationConfig, target: InventoryConfig) -> str:
    """Return the absolute inventory path used for the given integration configuration or target inventory config (if provided)."""
    path = target.path or os.path.basename(get_inventory_relative_path(args))

    if args.host_path:
        path = os.path.join(data_context().content.root, path)  # post-delegation, path is relative to the content root
    else:
        path = os.path.join(data_context().content.root, data_context().content.integration_path, path)

    return path


def get_inventory_relative_path(args: IntegrationConfig) -> str:
    """Return the inventory path used for the given integration configuration relative to the content root."""
    inventory_names: dict[t.Type[IntegrationConfig], str] = {
        PosixIntegrationConfig: 'inventory',
        WindowsIntegrationConfig: 'inventory.winrm',
        NetworkIntegrationConfig: 'inventory.networking',
    }

    return os.path.join(data_context().content.integration_path, inventory_names[type(args)])


def delegate_inventory(args: IntegrationConfig, inventory_path_src: str) -> None:
    """Make the given inventory available during delegation."""
    if isinstance(args, PosixIntegrationConfig):
        return

    def inventory_callback(payload_config: PayloadConfig) -> None:
        """
        Add the inventory file to the payload file list.
        This will preserve the file during delegation even if it is ignored or is outside the content and install roots.
        """
        files = payload_config.files

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
def integration_test_environment(
    args: IntegrationConfig,
    target: IntegrationTarget,
    inventory_path_src: str,
) -> c.Iterator[IntegrationEnvironment]:
    """Context manager that prepares the integration test environment and cleans it up."""
    ansible_config_src = args.get_ansible_config()
    ansible_config_relative = os.path.join(data_context().content.integration_path, '%s.cfg' % args.command)

    if args.no_temp_workdir or 'no/temp_workdir/' in target.aliases:
        display.warning('Disabling the temp work dir is a temporary debugging feature that may be removed in the future without notice.')

        integration_dir = os.path.join(data_context().content.root, data_context().content.integration_path)
        targets_dir = os.path.join(data_context().content.root, data_context().content.integration_targets_path)
        inventory_path = inventory_path_src
        ansible_config = ansible_config_src
        vars_file = os.path.join(data_context().content.root, data_context().content.integration_vars_path)

        yield IntegrationEnvironment(data_context().content.root, integration_dir, targets_dir, inventory_path, ansible_config, vars_file)
        return

    # When testing a collection, the temporary directory must reside within the collection.
    # This is necessary to enable support for the default collection for non-collection content (playbooks and roles).
    root_temp_dir = os.path.join(ResultType.TMP.path, 'integration')

    prefix = '%s-' % target.name
    suffix = '-\u00c5\u00d1\u015a\u00cc\u03b2\u0141\u00c8'

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
                os.path.join(temp_dir, integration_targets_relative_path, target.relative_path),
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
                shutil.copytree(to_bytes(dir_src), to_bytes(dir_dst), symlinks=True)  # type: ignore[arg-type]  # incorrect type stub omits bytes path support

        for file_src, file_dst in file_copies:
            display.info('Copying %s to %s' % (file_src, file_dst), verbosity=2)

            if not args.explain:
                make_dirs(os.path.dirname(file_dst))
                shutil.copy2(file_src, file_dst)

        yield IntegrationEnvironment(temp_dir, integration_dir, targets_dir, inventory_path, ansible_config, vars_file)
    finally:
        if not args.explain:
            remove_tree(temp_dir)


@contextlib.contextmanager
def integration_test_config_file(
    args: IntegrationConfig,
    env_config: CloudEnvironmentConfig,
    integration_dir: str,
) -> c.Iterator[t.Optional[str]]:
    """Context manager that provides a config file for integration tests, if needed."""
    if not env_config:
        yield None
        return

    config_vars = (env_config.ansible_vars or {}).copy()

    config_vars.update(
        ansible_test=dict(
            environment=env_config.env_vars,
            module_defaults=env_config.module_defaults,
        )
    )

    config_file = json.dumps(config_vars, indent=4, sort_keys=True)

    with named_temporary_file(args, 'config-file-', '.json', integration_dir, config_file) as path:  # type: str
        filename = os.path.relpath(path, integration_dir)

        display.info('>>> Config File: %s\n%s' % (filename, config_file), verbosity=3)

        yield path


def create_inventory(
    args: IntegrationConfig,
    host_state: HostState,
    inventory_path: str,
    target: IntegrationTarget,
) -> None:
    """Create inventory."""
    if isinstance(args, PosixIntegrationConfig):
        if target.target_type == IntegrationTargetType.CONTROLLER:
            display.info('Configuring controller inventory.', verbosity=1)
            create_controller_inventory(args, inventory_path, host_state.controller_profile)
        elif target.target_type == IntegrationTargetType.TARGET:
            display.info('Configuring target inventory.', verbosity=1)
            create_posix_inventory(args, inventory_path, host_state.target_profiles, 'needs/ssh/' in target.aliases)
        else:
            raise Exception(f'Unhandled test type for target "{target.name}": {target.target_type.name.lower()}')
    elif isinstance(args, WindowsIntegrationConfig):
        display.info('Configuring target inventory.', verbosity=1)
        target_profiles = filter_profiles_for_target(args, host_state.target_profiles, target)
        create_windows_inventory(args, inventory_path, target_profiles)
    elif isinstance(args, NetworkIntegrationConfig):
        display.info('Configuring target inventory.', verbosity=1)
        target_profiles = filter_profiles_for_target(args, host_state.target_profiles, target)
        create_network_inventory(args, inventory_path, target_profiles)


def command_integration_filtered(
    args: IntegrationConfig,
    host_state: HostState,
    targets: tuple[IntegrationTarget, ...],
    all_targets: tuple[IntegrationTarget, ...],
    inventory_path: str,
    pre_target: t.Optional[c.Callable[[IntegrationTarget], None]] = None,
    post_target: t.Optional[c.Callable[[IntegrationTarget], None]] = None,
):
    """Run integration tests for the specified targets."""
    found = False
    passed = []
    failed = []

    targets_iter = iter(targets)
    all_targets_dict = dict((target.name, target) for target in all_targets)

    setup_errors = []
    setup_targets_executed: set[str] = set()

    for target in all_targets:
        for setup_target in target.setup_once + target.setup_always:
            if setup_target not in all_targets_dict:
                setup_errors.append('Target "%s" contains invalid setup target: %s' % (target.name, setup_target))

    if setup_errors:
        raise ApplicationError('Found %d invalid setup aliases:\n%s' % (len(setup_errors), '\n'.join(setup_errors)))

    check_pyyaml(host_state.controller_profile.python)

    test_dir = os.path.join(ResultType.TMP.path, 'output_dir')

    if not args.explain and any('needs/ssh/' in target.aliases for target in targets):
        max_tries = 20
        display.info('SSH connection to controller required by tests. Checking the connection.')
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

    target_profile = host_state.target_profiles[0]

    if isinstance(target_profile, PosixProfile):
        target_python = target_profile.python

        if isinstance(target_profile, ControllerProfile):
            if host_state.controller_profile.python.path != target_profile.python.path:
                install_requirements(args, target_profile, target_python, command=True, controller=False)  # integration
        elif isinstance(target_profile, SshTargetHostProfile):
            connection = target_profile.get_controller_target_connections()[0]
            install_requirements(args, target_profile, target_python, command=True, controller=False, connection=connection)  # integration

    coverage_manager = CoverageManager(args, host_state, inventory_path)
    coverage_manager.setup()

    try:
        for target in targets_iter:
            if args.start_at and not found:
                found = target.name == args.start_at

                if not found:
                    continue

            create_inventory(args, host_state, inventory_path, target)

            tries = 2 if args.retry_on_error else 1
            verbosity = args.verbosity

            cloud_environment = get_cloud_environment(args, target)

            try:
                while tries:
                    tries -= 1

                    try:
                        if cloud_environment:
                            cloud_environment.setup_once()

                        run_setup_targets(args, host_state, test_dir, target.setup_once, all_targets_dict, setup_targets_executed, inventory_path,
                                          coverage_manager, False)

                        start_time = time.time()

                        if pre_target:
                            pre_target(target)

                        run_setup_targets(args, host_state, test_dir, target.setup_always, all_targets_dict, setup_targets_executed, inventory_path,
                                          coverage_manager, True)

                        if not args.explain:
                            # create a fresh test directory for each test target
                            remove_tree(test_dir)
                            make_dirs(test_dir)

                        try:
                            if target.script_path:
                                command_integration_script(args, host_state, target, test_dir, inventory_path, coverage_manager)
                            else:
                                command_integration_role(args, host_state, target, start_at_task, test_dir, inventory_path, coverage_manager)
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
                        )

                        break
                    except SubprocessError:
                        if cloud_environment:
                            cloud_environment.on_failure(target, tries)

                        if not tries:
                            raise

                        if target.retry_never:
                            display.warning(f'Skipping retry of test target "{target.name}" since it has been excluded from retries.')
                            raise

                        display.warning('Retrying test target "%s" with maximum verbosity.' % target.name)
                        display.verbosity = args.verbosity = 6

                passed.append(target)
            except Exception as ex:
                failed.append(target)

                if args.continue_on_error:
                    display.error(str(ex))
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
            coverage_manager.teardown()

            result_name = '%s-%s.json' % (
                args.command, re.sub(r'[^0-9]', '-', str(datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0, tzinfo=None))))

            data = dict(
                targets=results,
            )

            write_json_test_results(ResultType.DATA, result_name, data)

    if failed:
        raise ApplicationError('The %d integration test(s) listed below (out of %d) failed. See error output above for details:\n%s' % (
            len(failed), len(passed) + len(failed), '\n'.join(target.name for target in failed)))


def command_integration_script(
    args: IntegrationConfig,
    host_state: HostState,
    target: IntegrationTarget,
    test_dir: str,
    inventory_path: str,
    coverage_manager: CoverageManager,
):
    """Run an integration test script."""
    display.info('Running %s integration test script' % target.name)

    if not os.access(target.script_path, os.X_OK):
        raise ApplicationError(f'Unable to run non-executable script {target.script_path!r}. Did you forget to run "chmod +x" on it?')

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

    with integration_test_environment(args, target, inventory_path) as test_env:  # type: IntegrationEnvironment
        cmd = ['./%s' % os.path.basename(target.script_path)]

        if args.verbosity:
            cmd.append('-' + ('v' * args.verbosity))

        env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config, test_env, host_state)
        cwd = os.path.join(test_env.targets_dir, target.relative_path)

        env.update(
            # support use of adhoc ansible commands in collections without specifying the fully qualified collection name
            ANSIBLE_PLAYBOOK_DIR=cwd,
        )

        if env_config and env_config.env_vars:
            env.update(env_config.env_vars)

        with integration_test_config_file(args, env_config, test_env.integration_dir) as config_path:  # type: t.Optional[str]
            if config_path:
                cmd += ['-e', '@%s' % config_path]

            env.update(coverage_manager.get_environment(target.name, target.aliases))
            cover_python(args, host_state.controller_profile.python, cmd, target.name, env, cwd=cwd, capture=False)


def command_integration_role(
    args: IntegrationConfig,
    host_state: HostState,
    target: IntegrationTarget,
    start_at_task: t.Optional[str],
    test_dir: str,
    inventory_path: str,
    coverage_manager: CoverageManager,
):
    """Run an integration test role."""
    display.info('Running %s integration test role' % target.name)

    env_config = None

    vars_files = []
    variables = dict(
        output_dir=test_dir,
    )

    if isinstance(args, WindowsIntegrationConfig):
        hosts = 'windows'
        gather_facts = False
        variables.update(
            win_output_dir=r'C:\ansible_testing',
        )
    elif isinstance(args, NetworkIntegrationConfig):
        hosts = target.network_platform
        gather_facts = False
    else:
        hosts = 'testhost'
        gather_facts = True

    if 'gather_facts/yes/' in target.aliases:
        gather_facts = True
    elif 'gather_facts/no/' in target.aliases:
        gather_facts = False

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

    with integration_test_environment(args, target, inventory_path) as test_env:  # type: IntegrationEnvironment
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

            play.update(
                environment=env_config.env_vars,
                module_defaults=env_config.module_defaults,
            )

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

            env = integration_environment(args, target, test_dir, test_env.inventory_path, test_env.ansible_config, env_config, test_env, host_state)
            cwd = test_env.integration_dir

            env.update(
                # support use of adhoc ansible commands in collections without specifying the fully qualified collection name
                ANSIBLE_PLAYBOOK_DIR=cwd,
            )

            if env_config and env_config.env_vars:
                env.update(env_config.env_vars)

            env['ANSIBLE_ROLES_PATH'] = test_env.targets_dir

            env.update(coverage_manager.get_environment(target.name, target.aliases))
            cover_python(args, host_state.controller_profile.python, cmd, target.name, env, cwd=cwd, capture=False)


def run_setup_targets(
    args: IntegrationConfig,
    host_state: HostState,
    test_dir: str,
    target_names: c.Sequence[str],
    targets_dict: dict[str, IntegrationTarget],
    targets_executed: set[str],
    inventory_path: str,
    coverage_manager: CoverageManager,
    always: bool,
):
    """Run setup targets."""
    for target_name in target_names:
        if not always and target_name in targets_executed:
            continue

        target = targets_dict[target_name]

        if not args.explain:
            # create a fresh test directory for each test target
            remove_tree(test_dir)
            make_dirs(test_dir)

        if target.script_path:
            command_integration_script(args, host_state, target, test_dir, inventory_path, coverage_manager)
        else:
            command_integration_role(args, host_state, target, None, test_dir, inventory_path, coverage_manager)

        targets_executed.add(target_name)


def integration_environment(
    args: IntegrationConfig,
    target: IntegrationTarget,
    test_dir: str,
    inventory_path: str,
    ansible_config: t.Optional[str],
    env_config: t.Optional[CloudEnvironmentConfig],
    test_env: IntegrationEnvironment,
    host_state: HostState,
) -> dict[str, str]:
    """Return a dictionary of environment variables to use when running the given integration test target."""
    env = ansible_environment(args, ansible_config=ansible_config)

    callback_plugins = ['junit'] + (env_config.callback_plugins or [] if env_config else [])

    integration = dict(
        JUNIT_OUTPUT_DIR=ResultType.JUNIT.path,
        JUNIT_TASK_RELATIVE_PATH=test_env.test_dir,
        JUNIT_REPLACE_OUT_OF_TREE_PATH='out-of-tree:',
        ANSIBLE_CALLBACKS_ENABLED=','.join(sorted(set(callback_plugins))),
        ANSIBLE_TEST_CI=args.metadata.ci_provider or get_ci_provider().code,
        ANSIBLE_TEST_COVERAGE='check' if args.coverage_check else ('yes' if args.coverage else ''),
        OUTPUT_DIR=test_dir,
        INVENTORY_PATH=os.path.abspath(inventory_path),
    )

    if args.debug_strategy:
        env.update(ANSIBLE_STRATEGY='debug')

    if isinstance(host_state.controller_profile, DebuggableProfile):
        env.update(host_state.controller_profile.get_ansible_cli_environment_variables())

    if 'non_local/' in target.aliases:
        if args.coverage:
            display.warning('Skipping coverage reporting on Ansible modules for non-local test: %s' % target.name)

        env.update(ANSIBLE_TEST_REMOTE_INTERPRETER='')

    env.update(integration)
    env.update(target.env_set)

    return env


class IntegrationEnvironment:
    """Details about the integration environment."""

    def __init__(self, test_dir: str, integration_dir: str, targets_dir: str, inventory_path: str, ansible_config: str, vars_file: str) -> None:
        self.test_dir = test_dir
        self.integration_dir = integration_dir
        self.targets_dir = targets_dir
        self.inventory_path = inventory_path
        self.ansible_config = ansible_config
        self.vars_file = vars_file


class IntegrationCache(CommonCache):
    """Integration cache."""

    @property
    def integration_targets(self) -> list[IntegrationTarget]:
        """The list of integration test targets."""
        return self.get('integration_targets', lambda: list(walk_integration_targets()))

    @property
    def dependency_map(self) -> dict[str, set[IntegrationTarget]]:
        """The dependency map of integration test targets."""
        return self.get('dependency_map', lambda: generate_dependency_map(self.integration_targets))


def filter_profiles_for_target(args: IntegrationConfig, profiles: list[THostProfile], target: IntegrationTarget) -> list[THostProfile]:
    """Return a list of profiles after applying target filters."""
    if target.target_type == IntegrationTargetType.CONTROLLER:
        profile_filter = get_target_filter(args, [args.controller], True)
    elif target.target_type == IntegrationTargetType.TARGET:
        profile_filter = get_target_filter(args, args.targets, False)
    else:
        raise Exception(f'Unhandled test type for target "{target.name}": {target.target_type.name.lower()}')

    profiles = profile_filter.filter_profiles(profiles, target)

    return profiles


def get_integration_filter(args: IntegrationConfig, targets: list[IntegrationTarget]) -> set[str]:
    """Return a list of test targets to skip based on the host(s) that will be used to run the specified test targets."""
    invalid_targets = sorted(target.name for target in targets if target.target_type not in (IntegrationTargetType.CONTROLLER, IntegrationTargetType.TARGET))

    if invalid_targets and not args.list_targets:
        message = f'''Unable to determine context for the following test targets: {", ".join(invalid_targets)}

Make sure the test targets are correctly named:

 - Modules - The target name should match the module name.
 - Plugins - The target name should be "{{plugin_type}}_{{plugin_name}}".

If necessary, context can be controlled by adding entries to the "aliases" file for a test target:

 - Add the name(s) of modules which are tested.
 - Add "context/target" for module and module_utils tests (these will run on the target host).
 - Add "context/controller" for other test types (these will run on the controller).'''

        raise ApplicationError(message)

    invalid_targets = sorted(target.name for target in targets if target.actual_type not in (IntegrationTargetType.CONTROLLER, IntegrationTargetType.TARGET))

    if invalid_targets:
        if data_context().content.is_ansible:
            display.warning(f'Unable to determine context for the following test targets: {", ".join(invalid_targets)}')
        else:
            display.warning(f'Unable to determine context for the following test targets, they will be run on the target host: {", ".join(invalid_targets)}')

    exclude: set[str] = set()

    controller_targets = [target for target in targets if target.target_type == IntegrationTargetType.CONTROLLER]
    target_targets = [target for target in targets if target.target_type == IntegrationTargetType.TARGET]

    controller_filter = get_target_filter(args, [args.controller], True)
    target_filter = get_target_filter(args, args.targets, False)

    controller_filter.filter_targets(controller_targets, exclude)
    target_filter.filter_targets(target_targets, exclude)

    return exclude


def command_integration_filter(
    args: TIntegrationConfig,
    targets: c.Iterable[TIntegrationTarget],
) -> tuple[HostState, tuple[TIntegrationTarget, ...]]:
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
    environment_exclude = get_integration_filter(args, list(internal_targets))

    environment_exclude |= set(cloud_filter(args, internal_targets))

    if environment_exclude:
        exclude = sorted(set(exclude) | environment_exclude)
        internal_targets = walk_internal_targets(targets, args.include, exclude, require)

    if not internal_targets:
        raise AllTargetsSkipped()

    if args.start_at and not any(target.name == args.start_at for target in internal_targets):
        raise ApplicationError('Start at target matches nothing: %s' % args.start_at)

    cloud_init(args, internal_targets)

    vars_file_src = os.path.join(data_context().content.root, data_context().content.integration_vars_path)

    if os.path.exists(vars_file_src):

        def integration_config_callback(payload_config: PayloadConfig) -> None:
            """
            Add the integration config vars file to the payload file list.
            This will preserve the file during delegation even if the file is ignored by source control.
            """
            files = payload_config.files
            files.append((vars_file_src, data_context().content.integration_vars_path))

        data_context().register_payload_callback(integration_config_callback)

    if args.list_targets:
        raise ListTargets([target.name for target in internal_targets])

    # requirements are installed using a callback since the windows-integration and network-integration host status checks depend on them
    host_state = prepare_profiles(args, targets_use_pypi=True, requirements=requirements)  # integration, windows-integration, network-integration

    if args.delegate:
        raise Delegate(host_state=host_state, require=require, exclude=exclude)

    return host_state, internal_targets


def requirements(host_profile: HostProfile) -> None:
    """Install requirements after bootstrapping and delegation."""
    if isinstance(host_profile, ControllerHostProfile) and host_profile.controller:
        configure_pypi_proxy(host_profile.args, host_profile)  # integration, windows-integration, network-integration

        install_requirements(  # integration, windows-integration, network-integration
            args=host_profile.args,
            host_profile=host_profile,
            python=host_profile.python,
            ansible=True,
            command=True,
        )
    elif isinstance(host_profile, PosixProfile) and not isinstance(host_profile, ControllerProfile):
        configure_pypi_proxy(host_profile.args, host_profile)  # integration
