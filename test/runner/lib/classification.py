"""Classify changes in Ansible code."""

from __future__ import absolute_import, print_function

import os
import time

from lib.target import (
    walk_module_targets,
    walk_integration_targets,
    walk_units_targets,
    walk_compile_targets,
    walk_sanity_targets,
    load_integration_prefixes,
)

from lib.util import (
    display,
)

from lib.import_analysis import (
    get_python_module_utils_imports,
)


def categorize_changes(paths, verbose_command=None):
    """
    :type paths: list[str]
    :type verbose_command: str
    :rtype paths: dict[str, list[str]]
    """
    mapper = PathMapper()

    commands = {
        'sanity': set(),
        'compile': set(),
        'units': set(),
        'integration': set(),
        'windows-integration': set(),
        'network-integration': set(),
    }

    additional_paths = set()

    for path in paths:
        dependent_paths = mapper.get_dependent_paths(path)

        if not dependent_paths:
            continue

        display.info('Expanded "%s" to %d dependent file(s):' % (path, len(dependent_paths)), verbosity=1)

        for dependent_path in dependent_paths:
            display.info(dependent_path, verbosity=1)
            additional_paths.add(dependent_path)

    additional_paths -= set(paths)  # don't count changed paths as additional paths

    if additional_paths:
        display.info('Expanded %d changed file(s) into %d additional dependent file(s).' % (len(paths), len(additional_paths)))
        paths = sorted(set(paths) | additional_paths)

    display.info('Mapping %d changed file(s) to tests.' % len(paths))

    for path in paths:
        tests = mapper.classify(path)

        if tests is None:
            display.info('%s -> all' % path, verbosity=1)
            tests = all_tests()  # not categorized, run all tests
            display.warning('Path not categorized: %s' % path)
        else:
            tests = dict((key, value) for key, value in tests.items() if value)

            if verbose_command:
                result = '%s: %s' % (verbose_command, tests.get(verbose_command) or 'none')

                # identify targeted integration tests (those which only target a single integration command)
                if 'integration' in verbose_command and tests.get(verbose_command):
                    if not any('integration' in command for command in tests.keys() if command != verbose_command):
                        result += ' (targeted)'
            else:
                result = '%s' % tests

            display.info('%s -> %s' % (path, result), verbosity=1)

        for command, target in tests.items():
            commands[command].add(target)

    for command in commands:
        if any(t == 'all' for t in commands[command]):
            commands[command] = set(['all'])

    commands = dict((c, sorted(commands[c])) for c in commands.keys() if commands[c])

    return commands


class PathMapper(object):
    """Map file paths to test commands and targets."""
    def __init__(self):
        self.integration_targets = list(walk_integration_targets())
        self.module_targets = list(walk_module_targets())
        self.compile_targets = list(walk_compile_targets())
        self.units_targets = list(walk_units_targets())
        self.sanity_targets = list(walk_sanity_targets())

        self.compile_paths = set(t.path for t in self.compile_targets)
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

        self.python_module_utils_imports = {}  # populated on first use to reduce overhead when not needed

    def get_dependent_paths(self, path):
        """
        :type path: str
        :rtype: list[str]
        """
        ext = os.path.splitext(os.path.split(path)[1])[1]

        if path.startswith('lib/ansible/module_utils/'):
            if ext == '.py':
                return self.get_python_module_utils_usage(path)

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

    def classify(self, path):
        """
        :type path: str
        :rtype: dict[str, str] | None
        """
        result = self._classify(path)

        # run all tests when no result given
        if result is None:
            return None

        # compile path if eligible
        if path in self.compile_paths:
            result['compile'] = path

        # run sanity on path unless result specified otherwise
        if path in self.sanity_paths and 'sanity' not in result:
            result['sanity'] = path

        return result

    def _classify(self, path):
        """
        :type path: str
        :rtype: dict[str, str] | None
        """
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)

        minimal = {}

        if path.startswith('.github/'):
            return minimal

        if path.startswith('bin/'):
            return minimal

        if path.startswith('contrib/'):
            return {
                'units': 'test/units/contrib/'
            }

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

        if path.startswith('lib/ansible/modules/'):
            module = self.module_names_by_path.get(path)

            if module:
                return {
                    'units': module if module in self.units_modules else None,
                    'integration': self.posix_integration_by_module.get(module) if ext == '.py' else None,
                    'windows-integration': self.windows_integration_by_module.get(module) if ext == '.ps1' else None,
                    'network-integration': self.network_integration_by_module.get(module),
                }

            return minimal

        if path.startswith('lib/ansible/module_utils/'):
            if ext == '.ps1':
                return {
                    'windows-integration': 'all',
                }

            if ext == '.py':
                return minimal  # already expanded using get_dependent_paths

        if path.startswith('lib/ansible/plugins/connection/'):
            if name == '__init__':
                return {
                    'integration': 'all',
                    'windows-integration': 'all',
                    'network-integration': 'all',
                    'units': 'test/units/plugins/connection/',
                }

            units_path = 'test/units/plugins/connection/test_%s.py' % name

            if units_path not in self.units_paths:
                units_path = None

            integration_name = 'connection_%s' % name

            if integration_name not in self.integration_targets_by_name:
                integration_name = None

            # entire integration test commands depend on these connection plugins

            if name == 'winrm':
                return {
                    'windows-integration': 'all',
                    'units': units_path,
                }

            if name == 'local':
                return {
                    'integration': 'all',
                    'network-integration': 'all',
                    'units': units_path,
                }

            if name == 'network_cli':
                return {
                    'network-integration': 'all',
                    'units': units_path,
                }

            # other connection plugins have isolated integration and unit tests

            return {
                'integration': integration_name,
                'units': units_path,
            }

        if path.startswith('lib/ansible/plugins/terminal/'):
            if ext == '.py':
                if name in self.prefixes and self.prefixes[name] == 'network':
                    network_target = 'network/%s/' % name

                    if network_target in self.integration_targets_by_alias:
                        return {
                            'network-integration': network_target,
                            'units': 'all',
                        }

                    display.warning('Integration tests for "%s" not found.' % network_target)

                    return {
                        'units': 'all',
                    }

                return {
                    'network-integration': 'all',
                    'units': 'all',
                }

        if path.startswith('lib/ansible/utils/module_docs_fragments/'):
            return {
                'sanity': 'all',
            }

        if path.startswith('lib/ansible/'):
            return all_tests()  # broad impact, run all tests

        if path.startswith('packaging/'):
            return minimal

        if path.startswith('test/compile/'):
            return {
                'compile': 'all',
            }

        if path.startswith('test/results/'):
            return minimal

        if path.startswith('test/integration/roles/'):
            return minimal

        if path.startswith('test/integration/targets/'):
            if not os.path.exists(path):
                return minimal

            target = self.integration_targets_by_name[path.split('/')[3]]

            if 'hidden/' in target.aliases:
                return {
                    'integration': 'all',
                    'windows-integration': 'all',
                    'network-integration': 'all',
                }

            return {
                'integration': target.name if 'posix/' in target.aliases else None,
                'windows-integration': target.name if 'windows/' in target.aliases else None,
                'network-integration': target.name if 'network/' in target.aliases else None,
            }

        if path.startswith('test/integration/'):
            return {
                'integration': 'all',
                'windows-integration': 'all',
                'network-integration': 'all',
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

            # changes to files which are not unit tests should trigger tests from the nearest parent directory

            test_path = os.path.dirname(path)

            while test_path:
                if test_path + '/' in self.units_paths:
                    return {
                        'units': test_path + '/',
                    }

                test_path = os.path.dirname(test_path)

        if path.startswith('test/runner/'):
            return all_tests()  # test infrastructure, run all tests

        if path.startswith('test/utils/shippable/'):
            return all_tests()  # test infrastructure, run all tests

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
                    'setup.py',
            ):
                return minimal

            if path in (
                    'shippable.yml',
                    '.coveragerc',
            ):
                return all_tests()  # test infrastructure, run all tests

            if path == '.yamllint':
                return {
                    'sanity': 'all',
                }

            if ext in ('.md', '.rst', '.txt', '.xml', '.in'):
                return minimal

        return None  # unknown, will result in fall-back to run all tests


def all_tests():
    """
    :rtype: dict[str, str]
    """
    return {
        'sanity': 'all',
        'compile': 'all',
        'units': 'all',
        'integration': 'all',
        'windows-integration': 'all',
        'network-integration': 'all',
    }
