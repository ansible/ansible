"""Classify changes in Ansible code."""

from __future__ import absolute_import, print_function

import collections
import os
import re
import time

from lib.target import (
    walk_module_targets,
    walk_integration_targets,
    walk_units_targets,
    walk_compile_targets,
    walk_sanity_targets,
    load_integration_prefixes,
    analyze_integration_target_dependencies,
)

from lib.util import (
    display,
)

from lib.import_analysis import (
    get_python_module_utils_imports,
)

from lib.csharp_import_analysis import (
    get_csharp_module_utils_imports,
)

from lib.powershell_import_analysis import (
    get_powershell_module_utils_imports,
)

from lib.config import (
    TestConfig,
    IntegrationConfig,
)

from lib.metadata import (
    ChangeDescription,
)

FOCUSED_TARGET = '__focused__'


def categorize_changes(args, paths, verbose_command=None):
    """
    :type args: TestConfig
    :type paths: list[str]
    :type verbose_command: str
    :rtype: ChangeDescription
    """
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

    for command in commands:
        commands[command].discard('none')

        if any(t == 'all' for t in commands[command]):
            commands[command] = set(['all'])

    commands = dict((c, sorted(commands[c])) for c in commands if commands[c])
    focused_commands = dict((c, sorted(focused_commands[c])) for c in focused_commands)

    for command in commands:
        if commands[command] == ['all']:
            commands[command] = []  # changes require testing all targets, do not filter targets

    changes = ChangeDescription()
    changes.command = verbose_command
    changes.changed_paths = sorted(original_paths)
    changes.deleted_paths = sorted(deleted_paths)
    changes.regular_command_targets = commands
    changes.focused_command_targets = focused_commands
    changes.no_integration_paths = sorted(no_integration_paths)

    return changes


class PathMapper(object):
    """Map file paths to test commands and targets."""
    def __init__(self, args):
        """
        :type args: TestConfig
        """
        self.args = args
        self.integration_all_target = get_integration_all_target(self.args)

        self.integration_targets = list(walk_integration_targets())
        self.module_targets = list(walk_module_targets())
        self.compile_targets = list(walk_compile_targets())
        self.units_targets = list(walk_units_targets())
        self.sanity_targets = list(walk_sanity_targets())
        self.powershell_targets = [t for t in self.sanity_targets if os.path.splitext(t.path)[1] == '.ps1']
        self.csharp_targets = [t for t in self.sanity_targets if os.path.splitext(t.path)[1] == '.cs']

        self.units_modules = set(t.module for t in self.units_targets if t.module)
        self.units_paths = set(a for t in self.units_targets for a in t.aliases)
        self.sanity_paths = set(t.path for t in self.sanity_targets)

        self.module_names_by_path = dict((t.path, t.module) for t in self.module_targets)
        self.integration_targets_by_name = dict((t.name, t) for t in self.integration_targets)
        self.integration_targets_by_alias = dict((a, t) for t in self.integration_targets for a in t.aliases)

        self.posix_integration_by_module = dict((m, t.name) for t in self.integration_targets
                                                if 'posix/' in t.aliases for m in t.modules)
        self.windows_integration_by_module = dict((m, t.name) for t in self.integration_targets
                                                  if 'windows/' in t.aliases for m in t.modules)
        self.network_integration_by_module = dict((m, t.name) for t in self.integration_targets
                                                  if 'network/' in t.aliases for m in t.modules)

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

    def get_dependent_paths(self, path):
        """
        :type path: str
        :rtype: list[str]
        """
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

    def get_dependent_paths_non_recursive(self, path):
        """
        :type path: str
        :rtype: list[str]
        """
        paths = self.get_dependent_paths_internal(path)
        paths += [t.path + '/' for t in self.paths_to_dependent_targets.get(path, set())]
        paths = sorted(set(paths))

        return paths

    def get_dependent_paths_internal(self, path):
        """
        :type path: str
        :rtype: list[str]
        """
        ext = os.path.splitext(os.path.split(path)[1])[1]

        if path.startswith('lib/ansible/module_utils/'):
            if ext == '.py':
                return self.get_python_module_utils_usage(path)

            if ext == '.psm1':
                return self.get_powershell_module_utils_usage(path)

            if ext == '.cs':
                return self.get_csharp_module_utils_usage(path)

        if path.startswith('test/integration/targets/'):
            return self.get_integration_target_usage(path)

        return []

    def get_python_module_utils_usage(self, path):
        """
        :type path: str
        :rtype: list[str]
        """
        if path == 'lib/ansible/module_utils/__init__.py':
            return []

        if not self.python_module_utils_imports:
            display.info('Analyzing python module_utils imports...')
            before = time.time()
            self.python_module_utils_imports = get_python_module_utils_imports(self.compile_targets)
            after = time.time()
            display.info('Processed %d python module_utils in %d second(s).' % (len(self.python_module_utils_imports), after - before))

        name = os.path.splitext(path)[0].replace('/', '.')[4:]

        if name.endswith('.__init__'):
            name = name[:-9]

        return sorted(self.python_module_utils_imports[name])

    def get_powershell_module_utils_usage(self, path):
        """
        :type path: str
        :rtype: list[str]
        """
        if not self.powershell_module_utils_imports:
            display.info('Analyzing powershell module_utils imports...')
            before = time.time()
            self.powershell_module_utils_imports = get_powershell_module_utils_imports(self.powershell_targets)
            after = time.time()
            display.info('Processed %d powershell module_utils in %d second(s).' % (len(self.powershell_module_utils_imports), after - before))

        name = os.path.splitext(os.path.basename(path))[0]

        return sorted(self.powershell_module_utils_imports[name])

    def get_csharp_module_utils_usage(self, path):
        """
        :type path: str
        :rtype: list[str]
        """
        if not self.csharp_module_utils_imports:
            display.info('Analyzing C# module_utils imports...')
            before = time.time()
            self.csharp_module_utils_imports = get_csharp_module_utils_imports(self.powershell_targets, self.csharp_targets)
            after = time.time()
            display.info('Processed %d C# module_utils in %d second(s).' % (len(self.csharp_module_utils_imports), after - before))

        name = os.path.splitext(os.path.basename(path))[0]

        return sorted(self.csharp_module_utils_imports[name])

    def get_integration_target_usage(self, path):
        """
        :type path: str
        :rtype: list[str]
        """
        target_name = path.split('/')[3]
        dependents = [os.path.join('test/integration/targets/%s/' % target) for target in sorted(self.integration_dependencies.get(target_name, set()))]

        return dependents

    def classify(self, path):
        """
        :type path: str
        :rtype: dict[str, str] | None
        """
        result = self._classify(path)

        # run all tests when no result given
        if result is None:
            return None

        # run sanity on path unless result specified otherwise
        if path in self.sanity_paths and 'sanity' not in result:
            result['sanity'] = path

        return result

    def _classify(self, path):
        """
        :type path: str
        :rtype: dict[str, str] | None
        """
        dirname = os.path.dirname(path)
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)

        minimal = {}

        if path.startswith('.github/'):
            return minimal

        if path.startswith('bin/'):
            return all_tests(self.args)  # broad impact, run all tests

        if path.startswith('contrib/'):
            return {
                'units': 'test/units/contrib/'
            }

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

        if path.startswith('lib/ansible/modules/'):
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

        if path.startswith('lib/ansible/module_utils/'):
            if ext == '.cs':
                return minimal  # already expanded using get_dependent_paths

            if ext == '.psm1':
                return minimal  # already expanded using get_dependent_paths

            if ext == '.py':
                return minimal  # already expanded using get_dependent_paths

        if path.startswith('lib/ansible/plugins/action/'):
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

        if path.startswith('lib/ansible/plugins/connection/'):
            if name == '__init__':
                return {
                    'integration': self.integration_all_target,
                    'windows-integration': self.integration_all_target,
                    'network-integration': self.integration_all_target,
                    'units': 'test/units/plugins/connection/',
                }

            units_path = 'test/units/plugins/connection/test_%s.py' % name

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

        if path.startswith('lib/ansible/plugins/inventory/'):
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
            units_path = 'test/units/plugins/inventory/test_%s.py' % name

            if units_path not in self.units_paths:
                units_path = None

            return {
                'integration': target.name if target and 'posix/' in target.aliases else posix_integration_fallback,
                'windows-integration': target.name if target and 'windows/' in target.aliases else None,
                'network-integration': target.name if target and 'network/' in target.aliases else None,
                'units': units_path,
                FOCUSED_TARGET: target is not None,
            }

        if (path.startswith('lib/ansible/plugins/terminal/') or
                path.startswith('lib/ansible/plugins/cliconf/') or
                path.startswith('lib/ansible/plugins/netconf/')):
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

        if path.startswith('lib/ansible/plugins/doc_fragments/'):
            return {
                'sanity': 'all',
            }

        if path.startswith('lib/ansible/'):
            return all_tests(self.args)  # broad impact, run all tests

        if path.startswith('packaging/'):
            if path.startswith('packaging/requirements/'):
                if name.startswith('requirements-') and ext == '.txt':
                    component = name.split('-', 1)[1]

                    candidates = (
                        'cloud/%s/' % component,
                    )

                    for candidate in candidates:
                        if candidate in self.integration_targets_by_alias:
                            return {
                                'integration': candidate,
                            }

                return all_tests(self.args)  # broad impact, run all tests

            return minimal

        if path.startswith('test/cache/'):
            return minimal

        if path.startswith('test/results/'):
            return minimal

        if path.startswith('test/legacy/'):
            return minimal

        if path.startswith('test/env/'):
            return minimal

        if path.startswith('test/integration/roles/'):
            return minimal

        if path.startswith('test/integration/targets/'):
            if not os.path.exists(path):
                return minimal

            target = self.integration_targets_by_name[path.split('/')[3]]

            if 'hidden/' in target.aliases:
                if target.type == 'role':
                    return minimal  # already expanded using get_dependent_paths

                return {
                    'integration': self.integration_all_target,
                    'windows-integration': self.integration_all_target,
                    'network-integration': self.integration_all_target,
                }

            return {
                'integration': target.name if 'posix/' in target.aliases else None,
                'windows-integration': target.name if 'windows/' in target.aliases else None,
                'network-integration': target.name if 'network/' in target.aliases else None,
                FOCUSED_TARGET: True,
            }

        if path.startswith('test/integration/'):
            if dirname == 'test/integration':
                if self.prefixes.get(name) == 'network' and ext == '.yaml':
                    return minimal  # network integration test playbooks are not used by ansible-test

                if filename == 'network-all.yaml':
                    return minimal  # network integration test playbook not used by ansible-test

                if filename == 'platform_agnostic.yaml':
                    return minimal  # network integration test playbook not used by ansible-test

                if filename.startswith('inventory.') and filename.endswith('.template'):
                    return minimal  # ansible-test does not use these inventory templates

                if filename == 'inventory':
                    return {
                        'integration': self.integration_all_target,
                    }

                for command in (
                        'integration',
                        'windows-integration',
                        'network-integration',
                ):
                    if name == command and ext == '.cfg':
                        return {
                            command: self.integration_all_target,
                        }

                if name.startswith('cloud-config-'):
                    cloud_target = 'cloud/%s/' % name.split('-')[2].split('.')[0]

                    if cloud_target in self.integration_targets_by_alias:
                        return {
                            'integration': cloud_target,
                        }

            return {
                'integration': self.integration_all_target,
                'windows-integration': self.integration_all_target,
                'network-integration': self.integration_all_target,
            }

        if path.startswith('test/sanity/'):
            return {
                'sanity': 'all',  # test infrastructure, run all sanity checks
            }

        if path.startswith('test/units/'):
            if path in self.units_paths:
                return {
                    'units': path,
                }

            if path.startswith('test/units/compat/'):
                return {
                    'units': 'test/units/',
                }

            # changes to files which are not unit tests should trigger tests from the nearest parent directory

            test_path = os.path.dirname(path)

            while test_path:
                if test_path + '/' in self.units_paths:
                    return {
                        'units': test_path + '/',
                    }

                test_path = os.path.dirname(test_path)

        if path.startswith('test/runner/completion/'):
            if path == 'test/runner/completion/docker.txt':
                return all_tests(self.args, force=True)  # force all tests due to risk of breaking changes in new test environment

        if path.startswith('test/runner/lib/cloud/'):
            cloud_target = 'cloud/%s/' % name

            if cloud_target in self.integration_targets_by_alias:
                return {
                    'integration': cloud_target,
                }

            return all_tests(self.args)  # test infrastructure, run all tests

        if path.startswith('test/runner/lib/sanity/'):
            return {
                'sanity': 'all',  # test infrastructure, run all sanity checks
            }

        if path.startswith('test/runner/requirements/'):
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

            if name.startswith('integration.cloud.'):
                cloud_target = 'cloud/%s/' % name.split('.')[2]

                if cloud_target in self.integration_targets_by_alias:
                    return {
                        'integration': cloud_target,
                    }

        if path.startswith('test/runner/'):
            return all_tests(self.args)  # test infrastructure, run all tests

        if path.startswith('test/utils/shippable/tools/'):
            return minimal  # not used by tests

        if path.startswith('test/utils/shippable/'):
            if dirname == 'test/utils/shippable':
                test_map = {
                    'cloud.sh': 'integration:cloud/',
                    'freebsd.sh': 'integration:all',
                    'linux.sh': 'integration:all',
                    'network.sh': 'network-integration:all',
                    'osx.sh': 'integration:all',
                    'rhel.sh': 'integration:all',
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

        if path == 'test/README.md':
            return minimal

        if path.startswith('ticket_stubs/'):
            return minimal

        if '/' not in path:
            if path in (
                    '.gitattributes',
                    '.gitignore',
                    '.gitmodules',
                    '.mailmap',
                    'tox.ini',  # obsolete
                    'COPYING',
                    'VERSION',
                    'Makefile',
            ):
                return minimal

            if path in (
                    'shippable.yml',
                    '.coveragerc',
            ):
                return all_tests(self.args)  # test infrastructure, run all tests

            if path == 'setup.py':
                return all_tests(self.args)  # broad impact, run all tests

            if path == '.yamllint':
                return {
                    'sanity': 'all',
                }

            if ext in ('.md', '.rst', '.txt', '.xml', '.in'):
                return minimal

        return None  # unknown, will result in fall-back to run all tests


def all_tests(args, force=False):
    """
    :type args: TestConfig
    :type force: bool
    :rtype: dict[str, str]
    """
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


def get_integration_all_target(args):
    """
    :type args: TestConfig
    :rtype: str
    """
    if isinstance(args, IntegrationConfig):
        return args.changed_all_target

    return 'all'
