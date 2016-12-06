"""Classify changes in Ansible code."""

from __future__ import absolute_import, print_function

import os

from lib.target import (
    walk_module_targets,
    walk_integration_targets,
    walk_units_targets,
    walk_compile_targets,
    walk_sanity_targets,
)

from lib.util import (
    display,
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
        self.units_paths = set(t.path for t in self.units_targets)
        self.sanity_paths = set(t.path for t in self.sanity_targets)

        self.module_names_by_path = dict((t.path, t.module) for t in self.module_targets)
        self.integration_targets_by_name = dict((t.name, t) for t in self.integration_targets)

        self.posix_integration_by_module = dict((m, t.name) for t in self.integration_targets
                                                if 'posix/' in t.aliases for m in t.modules)
        self.windows_integration_by_module = dict((m, t.name) for t in self.integration_targets
                                                  if 'windows/' in t.aliases for m in t.modules)
        self.network_integration_by_module = dict((m, t.name) for t in self.integration_targets
                                                  if 'network/' in t.aliases for m in t.modules)

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

        if path.startswith('docs-api/'):
            return minimal

        if path.startswith('docsite/'):
            return minimal

        if path.startswith('examples/'):
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
                return {
                    'integration': 'all',
                    'network-integration': 'all',
                    'units': 'all',
                }

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

            return {
                'units': os.path.dirname(path),
            }

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
