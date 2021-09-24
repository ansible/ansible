"""Classify changes in Ansible code."""
from __future__ import annotations

import collections
import os
import re
import time
import typing as t

from ..target import (
    walk_module_targets,
    walk_integration_targets,
    walk_units_targets,
    walk_compile_targets,
    walk_sanity_targets,
    load_integration_prefixes,
    analyze_integration_target_dependencies,
)

from ..util import (
    display,
    is_subdir,
)

from .python import (
    get_python_module_utils_imports,
    get_python_module_utils_name,
)

from .csharp import (
    get_csharp_module_utils_imports,
    get_csharp_module_utils_name,
)

from .powershell import (
    get_powershell_module_utils_imports,
    get_powershell_module_utils_name,
)

from ..config import (
    TestConfig,
    IntegrationConfig,
)

from ..metadata import (
    ChangeDescription,
)

from ..data import (
    data_context,
)

FOCUSED_TARGET = '__focused__'


def categorize_changes(args, paths, verbose_command=None):  # type: (TestConfig, t.List[str], t.Optional[str]) -> ChangeDescription
    """Categorize the given list of changed paths and return a description of the changes."""
    mapper = PathMapper(args)

    commands = {
        'sanity': set(),
        'units': set(),
        'integration': set(),
        'windows-integration': set(),
        'network-integration': set(),
    }

    focused_commands = collections.defaultdict(set)

    deleted_paths = set()
    original_paths = set()
    additional_paths = set()
    no_integration_paths = set()

    for path in paths:
        if not os.path.exists(path):
            deleted_paths.add(path)
            continue

        original_paths.add(path)

        dependent_paths = mapper.get_dependent_paths(path)

        if not dependent_paths:
            continue

        display.info('Expanded "%s" to %d dependent file(s):' % (path, len(dependent_paths)), verbosity=2)

        for dependent_path in dependent_paths:
            display.info(dependent_path, verbosity=2)
            additional_paths.add(dependent_path)

    additional_paths -= set(paths)  # don't count changed paths as additional paths

    if additional_paths:
        display.info('Expanded %d changed file(s) into %d additional dependent file(s).' % (len(paths), len(additional_paths)))
        paths = sorted(set(paths) | additional_paths)

    display.info('Mapping %d changed file(s) to tests.' % len(paths))

    none_count = 0

    for path in paths:
        tests = mapper.classify(path)

        if tests is None:
            focused_target = False

            display.info('%s -> all' % path, verbosity=1)
            tests = all_tests(args)  # not categorized, run all tests
            display.warning('Path not categorized: %s' % path)
        else:
            focused_target = tests.pop(FOCUSED_TARGET, False) and path in original_paths

            tests = dict((key, value) for key, value in tests.items() if value)

            if focused_target and not any('integration' in command for command in tests):
                no_integration_paths.add(path)  # path triggers no integration tests

            if verbose_command:
                result = '%s: %s' % (verbose_command, tests.get(verbose_command) or 'none')

                # identify targeted integration tests (those which only target a single integration command)
                if 'integration' in verbose_command and tests.get(verbose_command):
                    if not any('integration' in command for command in tests if command != verbose_command):
                        if focused_target:
                            result += ' (focused)'

                        result += ' (targeted)'
            else:
                result = '%s' % tests

            if not tests.get(verbose_command):
                # minimize excessive output from potentially thousands of files which do not trigger tests
                none_count += 1
                verbosity = 2
            else:
                verbosity = 1

            if args.verbosity >= verbosity:
                display.info('%s -> %s' % (path, result), verbosity=1)

        for command, target in tests.items():
            commands[command].add(target)

            if focused_target:
                focused_commands[command].add(target)

    if none_count > 0 and args.verbosity < 2:
        display.notice('Omitted %d file(s) that triggered no tests.' % none_count)

    for command, targets in commands.items():
        targets.discard('none')

        if any(target == 'all' for target in targets):
            commands[command] = {'all'}

    commands = dict((c, sorted(targets)) for c, targets in commands.items() if targets)
    focused_commands = dict((c, sorted(targets)) for c, targets in focused_commands.items())

    for command, targets in commands.items():
        if targets == ['all']:
            commands[command] = []  # changes require testing all targets, do not filter targets

    changes = ChangeDescription()
    changes.command = verbose_command
    changes.changed_paths = sorted(original_paths)
    changes.deleted_paths = sorted(deleted_paths)
    changes.regular_command_targets = commands
    changes.focused_command_targets = focused_commands
    changes.no_integration_paths = sorted(no_integration_paths)

    return changes


class PathMapper:
    """Map file paths to test commands and targets."""
    def __init__(self, args):  # type: (TestConfig) -> None
        self.args = args
        self.integration_all_target = get_integration_all_target(self.args)

        self.integration_targets = list(walk_integration_targets())
        self.module_targets = list(walk_module_targets())
        self.compile_targets = list(walk_compile_targets())
        self.units_targets = list(walk_units_targets())
        self.sanity_targets = list(walk_sanity_targets())
        self.powershell_targets = [target for target in self.sanity_targets if os.path.splitext(target.path)[1] in ('.ps1', '.psm1')]
        self.csharp_targets = [target for target in self.sanity_targets if os.path.splitext(target.path)[1] == '.cs']

        self.units_modules = set(target.module for target in self.units_targets if target.module)
        self.units_paths = set(a for target in self.units_targets for a in target.aliases)
        self.sanity_paths = set(target.path for target in self.sanity_targets)

        self.module_names_by_path = dict((target.path, target.module) for target in self.module_targets)
        self.integration_targets_by_name = dict((target.name, target) for target in self.integration_targets)
        self.integration_targets_by_alias = dict((a, target) for target in self.integration_targets for a in target.aliases)

        self.posix_integration_by_module = dict((m, target.name) for target in self.integration_targets
                                                if 'posix/' in target.aliases for m in target.modules)
        self.windows_integration_by_module = dict((m, target.name) for target in self.integration_targets
                                                  if 'windows/' in target.aliases for m in target.modules)
        self.network_integration_by_module = dict((m, target.name) for target in self.integration_targets
                                                  if 'network/' in target.aliases for m in target.modules)

        self.prefixes = load_integration_prefixes()
        self.integration_dependencies = analyze_integration_target_dependencies(self.integration_targets)

        self.python_module_utils_imports = {}  # populated on first use to reduce overhead when not needed
        self.powershell_module_utils_imports = {}  # populated on first use to reduce overhead when not needed
        self.csharp_module_utils_imports = {}  # populated on first use to reduce overhead when not needed

        self.paths_to_dependent_targets = {}

        for target in self.integration_targets:
            for path in target.needs_file:
                if path not in self.paths_to_dependent_targets:
                    self.paths_to_dependent_targets[path] = set()

                self.paths_to_dependent_targets[path].add(target)

    def get_dependent_paths(self, path):  # type: (str) -> t.List[str]
        """Return a list of paths which depend on the given path, recursively expanding dependent paths as well."""
        unprocessed_paths = set(self.get_dependent_paths_non_recursive(path))
        paths = set()

        while unprocessed_paths:
            queued_paths = list(unprocessed_paths)
            paths |= unprocessed_paths
            unprocessed_paths = set()

            for queued_path in queued_paths:
                new_paths = self.get_dependent_paths_non_recursive(queued_path)

                for new_path in new_paths:
                    if new_path not in paths:
                        unprocessed_paths.add(new_path)

        return sorted(paths)

    def get_dependent_paths_non_recursive(self, path):  # type: (str) -> t.List[str]
        """Return a list of paths which depend on the given path, including dependent integration test target paths."""
        paths = self.get_dependent_paths_internal(path)
        paths += [target.path + '/' for target in self.paths_to_dependent_targets.get(path, set())]
        paths = sorted(set(paths))

        return paths

    def get_dependent_paths_internal(self, path):  # type: (str) -> t.List[str]
        """Return a list of paths which depend on the given path."""
        ext = os.path.splitext(os.path.split(path)[1])[1]

        if is_subdir(path, data_context().content.module_utils_path):
            if ext == '.py':
                return self.get_python_module_utils_usage(path)

            if ext == '.psm1':
                return self.get_powershell_module_utils_usage(path)

            if ext == '.cs':
                return self.get_csharp_module_utils_usage(path)

        if is_subdir(path, data_context().content.integration_targets_path):
            return self.get_integration_target_usage(path)

        return []

    def get_python_module_utils_usage(self, path):  # type: (str) -> t.List[str]
        """Return a list of paths which depend on the given path which is a Python module_utils file."""
        if not self.python_module_utils_imports:
            display.info('Analyzing python module_utils imports...')
            before = time.time()
            self.python_module_utils_imports = get_python_module_utils_imports(self.compile_targets)
            after = time.time()
            display.info('Processed %d python module_utils in %d second(s).' % (len(self.python_module_utils_imports), after - before))

        name = get_python_module_utils_name(path)

        return sorted(self.python_module_utils_imports[name])

    def get_powershell_module_utils_usage(self, path):  # type: (str) -> t.List[str]
        """Return a list of paths which depend on the given path which is a PowerShell module_utils file."""
        if not self.powershell_module_utils_imports:
            display.info('Analyzing powershell module_utils imports...')
            before = time.time()
            self.powershell_module_utils_imports = get_powershell_module_utils_imports(self.powershell_targets)
            after = time.time()
            display.info('Processed %d powershell module_utils in %d second(s).' % (len(self.powershell_module_utils_imports), after - before))

        name = get_powershell_module_utils_name(path)

        return sorted(self.powershell_module_utils_imports[name])

    def get_csharp_module_utils_usage(self, path):  # type: (str) -> t.List[str]
        """Return a list of paths which depend on the given path which is a C# module_utils file."""
        if not self.csharp_module_utils_imports:
            display.info('Analyzing C# module_utils imports...')
            before = time.time()
            self.csharp_module_utils_imports = get_csharp_module_utils_imports(self.powershell_targets, self.csharp_targets)
            after = time.time()
            display.info('Processed %d C# module_utils in %d second(s).' % (len(self.csharp_module_utils_imports), after - before))

        name = get_csharp_module_utils_name(path)

        return sorted(self.csharp_module_utils_imports[name])

    def get_integration_target_usage(self, path):  # type: (str) -> t.List[str]
        """Return a list of paths which depend on the given path which is an integration target file."""
        target_name = path.split('/')[3]
        dependents = [os.path.join(data_context().content.integration_targets_path, target) + os.path.sep
                      for target in sorted(self.integration_dependencies.get(target_name, set()))]

        return dependents

    def classify(self, path):  # type: (str) -> t.Optional[t.Dict[str, str]]
        """Classify the given path and return an optional dictionary of the results."""
        result = self._classify(path)

        # run all tests when no result given
        if result is None:
            return None

        # run sanity on path unless result specified otherwise
        if path in self.sanity_paths and 'sanity' not in result:
            result['sanity'] = path

        return result

    def _classify(self, path):  # type: (str) -> t.Optional[t.Dict[str, str]]
        """Return the classification for the given path."""
        if data_context().content.is_ansible:
            return self._classify_ansible(path)

        if data_context().content.collection:
            return self._classify_collection(path)

        return None

    def _classify_common(self, path):  # type: (str) -> t.Optional[t.Dict[str, str]]
        """Return the classification for the given path using rules common to all layouts."""
        dirname = os.path.dirname(path)
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)

        minimal = {}

        if os.path.sep not in path:
            if filename in (
                    'azure-pipelines.yml',
            ):
                return all_tests(self.args)  # test infrastructure, run all tests

        if is_subdir(path, '.azure-pipelines'):
            return all_tests(self.args)  # test infrastructure, run all tests

        if is_subdir(path, '.github'):
            return minimal

        if is_subdir(path, data_context().content.integration_targets_path):
            if not os.path.exists(path):
                return minimal

            target = self.integration_targets_by_name.get(path.split('/')[3])

            if not target:
                display.warning('Unexpected non-target found: %s' % path)
                return minimal

            if 'hidden/' in target.aliases:
                return minimal  # already expanded using get_dependent_paths

            return {
                'integration': target.name if 'posix/' in target.aliases else None,
                'windows-integration': target.name if 'windows/' in target.aliases else None,
                'network-integration': target.name if 'network/' in target.aliases else None,
                FOCUSED_TARGET: True,
            }

        if is_subdir(path, data_context().content.integration_path):
            if dirname == data_context().content.integration_path:
                for command in (
                        'integration',
                        'windows-integration',
                        'network-integration',
                ):
                    if name == command and ext == '.cfg':
                        return {
                            command: self.integration_all_target,
                        }

                    if name == command + '.requirements' and ext == '.txt':
                        return {
                            command: self.integration_all_target,
                        }

            return {
                'integration': self.integration_all_target,
                'windows-integration': self.integration_all_target,
                'network-integration': self.integration_all_target,
            }

        if is_subdir(path, data_context().content.sanity_path):
            return {
                'sanity': 'all',  # test infrastructure, run all sanity checks
            }

        if is_subdir(path, data_context().content.unit_path):
            if path in self.units_paths:
                return {
                    'units': path,
                }

            # changes to files which are not unit tests should trigger tests from the nearest parent directory

            test_path = os.path.dirname(path)

            while test_path:
                if test_path + '/' in self.units_paths:
                    return {
                        'units': test_path + '/',
                    }

                test_path = os.path.dirname(test_path)

        if is_subdir(path, data_context().content.module_path):
            module_name = self.module_names_by_path.get(path)

            if module_name:
                return {
                    'units': module_name if module_name in self.units_modules else None,
                    'integration': self.posix_integration_by_module.get(module_name) if ext == '.py' else None,
                    'windows-integration': self.windows_integration_by_module.get(module_name) if ext in ['.cs', '.ps1'] else None,
                    'network-integration': self.network_integration_by_module.get(module_name),
                    FOCUSED_TARGET: True,
                }

            return minimal

        if is_subdir(path, data_context().content.module_utils_path):
            if ext == '.cs':
                return minimal  # already expanded using get_dependent_paths

            if ext == '.psm1':
                return minimal  # already expanded using get_dependent_paths

            if ext == '.py':
                return minimal  # already expanded using get_dependent_paths

        if is_subdir(path, data_context().content.plugin_paths['action']):
            if ext == '.py':
                if name.startswith('net_'):
                    network_target = 'network/.*_%s' % name[4:]

                    if any(re.search(r'^%s$' % network_target, alias) for alias in self.integration_targets_by_alias):
                        return {
                            'network-integration': network_target,
                            'units': 'all',
                        }

                    return {
                        'network-integration': self.integration_all_target,
                        'units': 'all',
                    }

                if self.prefixes.get(name) == 'network':
                    network_platform = name
                elif name.endswith('_config') and self.prefixes.get(name[:-7]) == 'network':
                    network_platform = name[:-7]
                elif name.endswith('_template') and self.prefixes.get(name[:-9]) == 'network':
                    network_platform = name[:-9]
                else:
                    network_platform = None

                if network_platform:
                    network_target = 'network/%s/' % network_platform

                    if network_target in self.integration_targets_by_alias:
                        return {
                            'network-integration': network_target,
                            'units': 'all',
                        }

                    display.warning('Integration tests for "%s" not found.' % network_target, unique=True)

                    return {
                        'units': 'all',
                    }

        if is_subdir(path, data_context().content.plugin_paths['connection']):
            units_dir = os.path.join(data_context().content.unit_path, 'plugins', 'connection')
            if name == '__init__':
                return {
                    'integration': self.integration_all_target,
                    'windows-integration': self.integration_all_target,
                    'network-integration': self.integration_all_target,
                    'units': os.path.join(units_dir, ''),
                }

            units_path = os.path.join(units_dir, 'test_%s.py' % name)

            if units_path not in self.units_paths:
                units_path = None

            integration_name = 'connection_%s' % name

            if integration_name not in self.integration_targets_by_name:
                integration_name = None

            windows_integration_name = 'connection_windows_%s' % name

            if windows_integration_name not in self.integration_targets_by_name:
                windows_integration_name = None

            # entire integration test commands depend on these connection plugins

            if name in ['winrm', 'psrp']:
                return {
                    'windows-integration': self.integration_all_target,
                    'units': units_path,
                }

            if name == 'local':
                return {
                    'integration': self.integration_all_target,
                    'network-integration': self.integration_all_target,
                    'units': units_path,
                }

            if name == 'network_cli':
                return {
                    'network-integration': self.integration_all_target,
                    'units': units_path,
                }

            if name == 'paramiko_ssh':
                return {
                    'integration': integration_name,
                    'network-integration': self.integration_all_target,
                    'units': units_path,
                }

            # other connection plugins have isolated integration and unit tests

            return {
                'integration': integration_name,
                'windows-integration': windows_integration_name,
                'units': units_path,
            }

        if is_subdir(path, data_context().content.plugin_paths['doc_fragments']):
            return {
                'sanity': 'all',
            }

        if is_subdir(path, data_context().content.plugin_paths['inventory']):
            if name == '__init__':
                return all_tests(self.args)  # broad impact, run all tests

            # These inventory plugins are enabled by default (see INVENTORY_ENABLED).
            # Without dedicated integration tests for these we must rely on the incidental coverage from other tests.
            test_all = [
                'host_list',
                'script',
                'yaml',
                'ini',
                'auto',
            ]

            if name in test_all:
                posix_integration_fallback = get_integration_all_target(self.args)
            else:
                posix_integration_fallback = None

            target = self.integration_targets_by_name.get('inventory_%s' % name)
            units_dir = os.path.join(data_context().content.unit_path, 'plugins', 'inventory')
            units_path = os.path.join(units_dir, 'test_%s.py' % name)

            if units_path not in self.units_paths:
                units_path = None

            return {
                'integration': target.name if target and 'posix/' in target.aliases else posix_integration_fallback,
                'windows-integration': target.name if target and 'windows/' in target.aliases else None,
                'network-integration': target.name if target and 'network/' in target.aliases else None,
                'units': units_path,
                FOCUSED_TARGET: target is not None,
            }

        if is_subdir(path, data_context().content.plugin_paths['filter']):
            return self._simple_plugin_tests('filter', name)

        if is_subdir(path, data_context().content.plugin_paths['lookup']):
            return self._simple_plugin_tests('lookup', name)

        if (is_subdir(path, data_context().content.plugin_paths['terminal']) or
                is_subdir(path, data_context().content.plugin_paths['cliconf']) or
                is_subdir(path, data_context().content.plugin_paths['netconf'])):
            if ext == '.py':
                if name in self.prefixes and self.prefixes[name] == 'network':
                    network_target = 'network/%s/' % name

                    if network_target in self.integration_targets_by_alias:
                        return {
                            'network-integration': network_target,
                            'units': 'all',
                        }

                    display.warning('Integration tests for "%s" not found.' % network_target, unique=True)

                    return {
                        'units': 'all',
                    }

                return {
                    'network-integration': self.integration_all_target,
                    'units': 'all',
                }

        if is_subdir(path, data_context().content.plugin_paths['test']):
            return self._simple_plugin_tests('test', name)

        return None

    def _classify_collection(self, path):  # type: (str) -> t.Optional[t.Dict[str, str]]
        """Return the classification for the given path using rules specific to collections."""
        result = self._classify_common(path)

        if result is not None:
            return result

        filename = os.path.basename(path)
        dummy, ext = os.path.splitext(filename)

        minimal = {}

        if path.startswith('changelogs/'):
            return minimal

        if path.startswith('docs/'):
            return minimal

        if '/' not in path:
            if path in (
                    '.gitignore',
                    'COPYING',
                    'LICENSE',
                    'Makefile',
            ):
                return minimal

            if ext in (
                    '.in',
                    '.md',
                    '.rst',
                    '.toml',
                    '.txt',
            ):
                return minimal

        return None

    def _classify_ansible(self, path):  # type: (str) -> t.Optional[t.Dict[str, str]]
        """Return the classification for the given path using rules specific to Ansible."""
        if path.startswith('test/units/compat/'):
            return {
                'units': 'test/units/',
            }

        result = self._classify_common(path)

        if result is not None:
            return result

        dirname = os.path.dirname(path)
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)

        minimal = {}

        if path.startswith('bin/'):
            return all_tests(self.args)  # broad impact, run all tests

        if path.startswith('changelogs/'):
            return minimal

        if path.startswith('docs/'):
            return minimal

        if path.startswith('examples/'):
            if path == 'examples/scripts/ConfigureRemotingForAnsible.ps1':
                return {
                    'windows-integration': 'connection_winrm',
                }

            return minimal

        if path.startswith('hacking/'):
            return minimal

        if path.startswith('lib/ansible/executor/powershell/'):
            units_path = 'test/units/executor/powershell/'

            if units_path not in self.units_paths:
                units_path = None

            return {
                'windows-integration': self.integration_all_target,
                'units': units_path,
            }

        if path.startswith('lib/ansible/'):
            return all_tests(self.args)  # broad impact, run all tests

        if path.startswith('licenses/'):
            return minimal

        if path.startswith('packaging/'):
            return minimal

        if path.startswith('test/ansible_test/'):
            return minimal  # these tests are not invoked from ansible-test

        if path.startswith('test/lib/ansible_test/config/'):
            if name.startswith('cloud-config-'):
                # noinspection PyTypeChecker
                cloud_target = 'cloud/%s/' % name.split('-')[2].split('.')[0]

                if cloud_target in self.integration_targets_by_alias:
                    return {
                        'integration': cloud_target,
                    }

        if path.startswith('test/lib/ansible_test/_data/completion/'):
            if path == 'test/lib/ansible_test/_data/completion/docker.txt':
                return all_tests(self.args, force=True)  # force all tests due to risk of breaking changes in new test environment

        if path.startswith('test/lib/ansible_test/_internal/commands/integration/cloud/'):
            cloud_target = 'cloud/%s/' % name

            if cloud_target in self.integration_targets_by_alias:
                return {
                    'integration': cloud_target,
                }

            return all_tests(self.args)  # test infrastructure, run all tests

        if path.startswith('test/lib/ansible_test/_internal/commands/sanity/'):
            return {
                'sanity': 'all',  # test infrastructure, run all sanity checks
                'integration': 'ansible-test',  # run ansible-test self tests
            }

        if path.startswith('test/lib/ansible_test/_internal/commands/units/'):
            return {
                'units': 'all',  # test infrastructure, run all unit tests
                'integration': 'ansible-test',  # run ansible-test self tests
            }

        if path.startswith('test/lib/ansible_test/_data/requirements/'):
            if name in (
                    'integration',
                    'network-integration',
                    'windows-integration',
            ):
                return {
                    name: self.integration_all_target,
                }

            if name in (
                    'sanity',
                    'units',
            ):
                return {
                    name: 'all',
                }

        if path.startswith('test/lib/ansible_test/_util/controller/sanity/') or path.startswith('test/lib/ansible_test/_util/target/sanity/'):
            return {
                'sanity': 'all',  # test infrastructure, run all sanity checks
                'integration': 'ansible-test',  # run ansible-test self tests
            }

        if path.startswith('test/lib/ansible_test/_util/target/pytest/'):
            return {
                'units': 'all',  # test infrastructure, run all unit tests
                'integration': 'ansible-test',  # run ansible-test self tests
            }

        if path.startswith('test/lib/'):
            return all_tests(self.args)  # test infrastructure, run all tests

        if path.startswith('test/support/'):
            return all_tests(self.args)  # test infrastructure, run all tests

        if path.startswith('test/utils/shippable/'):
            if dirname == 'test/utils/shippable':
                test_map = {
                    'cloud.sh': 'integration:cloud/',
                    'linux.sh': 'integration:all',
                    'network.sh': 'network-integration:all',
                    'remote.sh': 'integration:all',
                    'sanity.sh': 'sanity:all',
                    'units.sh': 'units:all',
                    'windows.sh': 'windows-integration:all',
                }

                test_match = test_map.get(filename)

                if test_match:
                    test_command, test_target = test_match.split(':')

                    return {
                        test_command: test_target,
                    }

                cloud_target = 'cloud/%s/' % name

                if cloud_target in self.integration_targets_by_alias:
                    return {
                        'integration': cloud_target,
                    }

            return all_tests(self.args)  # test infrastructure, run all tests

        if path.startswith('test/utils/'):
            return minimal

        if '/' not in path:
            if path in (
                    '.gitattributes',
                    '.gitignore',
                    '.mailmap',
                    'COPYING',
                    'Makefile',
            ):
                return minimal

            if path in (
                    'setup.py',
            ):
                return all_tests(self.args)  # broad impact, run all tests

            if ext in (
                    '.in',
                    '.md',
                    '.rst',
                    '.toml',
                    '.txt',
            ):
                return minimal

        return None  # unknown, will result in fall-back to run all tests

    def _simple_plugin_tests(self, plugin_type, plugin_name):  # type: (str, str) -> t.Dict[str, t.Optional[str]]
        """
        Return tests for the given plugin type and plugin name.
        This function is useful for plugin types which do not require special processing.
        """
        if plugin_name == '__init__':
            return all_tests(self.args, True)

        integration_target = self.integration_targets_by_name.get('%s_%s' % (plugin_type, plugin_name))

        if integration_target:
            integration_name = integration_target.name
        else:
            integration_name = None

        units_path = os.path.join(data_context().content.unit_path, 'plugins', plugin_type, 'test_%s.py' % plugin_name)

        if units_path not in self.units_paths:
            units_path = None

        return dict(
            integration=integration_name,
            units=units_path,
        )


def all_tests(args, force=False):  # type: (TestConfig, bool) -> t.Dict[str, str]
    """Return the targets for each test command when all tests should be run."""
    if force:
        integration_all_target = 'all'
    else:
        integration_all_target = get_integration_all_target(args)

    return {
        'sanity': 'all',
        'units': 'all',
        'integration': integration_all_target,
        'windows-integration': integration_all_target,
        'network-integration': integration_all_target,
    }


def get_integration_all_target(args):  # type: (TestConfig) -> str
    """Return the target to use when all tests should be run."""
    if isinstance(args, IntegrationConfig):
        return args.changed_all_target

    return 'all'
