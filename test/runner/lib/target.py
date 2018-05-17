"""Test target identification, iteration and inclusion/exclusion."""

from __future__ import absolute_import, print_function

import collections
import os
import re
import errno
import itertools
import abc
import sys

from lib.util import (
    ApplicationError,
)

MODULE_EXTENSIONS = '.py', '.ps1'


def find_target_completion(target_func, prefix):
    """
    :type target_func: () -> collections.Iterable[CompletionTarget]
    :type prefix: unicode
    :rtype: list[str]
    """
    try:
        targets = target_func()
        if sys.version_info[0] == 2:
            prefix = prefix.encode()
        short = os.environ.get('COMP_TYPE') == '63'  # double tab completion from bash
        matches = walk_completion_targets(targets, prefix, short)
        return matches
    except Exception as ex:  # pylint: disable=locally-disabled, broad-except
        return [str(ex)]


def walk_completion_targets(targets, prefix, short=False):
    """
    :type targets: collections.Iterable[CompletionTarget]
    :type prefix: str
    :type short: bool
    :rtype: tuple[str]
    """
    aliases = set(alias for target in targets for alias in target.aliases)

    if prefix.endswith('/') and prefix in aliases:
        aliases.remove(prefix)

    matches = [alias for alias in aliases if alias.startswith(prefix) and '/' not in alias[len(prefix):-1]]

    if short:
        offset = len(os.path.dirname(prefix))
        if offset:
            offset += 1
            relative_matches = [match[offset:] for match in matches if len(match) > offset]
            if len(relative_matches) > 1:
                matches = relative_matches

    return tuple(sorted(matches))


def walk_internal_targets(targets, includes=None, excludes=None, requires=None):
    """
    :type targets: collections.Iterable[T <= CompletionTarget]
    :type includes: list[str]
    :type excludes: list[str]
    :type requires: list[str]
    :rtype: tuple[T <= CompletionTarget]
    """
    targets = tuple(targets)

    include_targets = sorted(filter_targets(targets, includes, errors=True, directories=False), key=lambda t: t.name)

    if requires:
        require_targets = set(filter_targets(targets, requires, errors=True, directories=False))
        include_targets = [target for target in include_targets if target in require_targets]

    if excludes:
        list(filter_targets(targets, excludes, errors=True, include=False, directories=False))

    internal_targets = set(filter_targets(include_targets, excludes, errors=False, include=False, directories=False))
    return tuple(sorted(internal_targets, key=lambda t: t.name))


def walk_external_targets(targets, includes=None, excludes=None, requires=None):
    """
    :type targets: collections.Iterable[CompletionTarget]
    :type includes: list[str]
    :type excludes: list[str]
    :type requires: list[str]
    :rtype: tuple[CompletionTarget], tuple[CompletionTarget]
    """
    targets = tuple(targets)

    if requires:
        include_targets = list(filter_targets(targets, includes, errors=True, directories=False))
        require_targets = set(filter_targets(targets, requires, errors=True, directories=False))
        includes = [target.name for target in include_targets if target in require_targets]

        if includes:
            include_targets = sorted(filter_targets(targets, includes, errors=True), key=lambda t: t.name)
        else:
            include_targets = []
    else:
        include_targets = sorted(filter_targets(targets, includes, errors=True), key=lambda t: t.name)

    if excludes:
        exclude_targets = sorted(filter_targets(targets, excludes, errors=True), key=lambda t: t.name)
    else:
        exclude_targets = []

    previous = None
    include = []
    for target in include_targets:
        if isinstance(previous, DirectoryTarget) and isinstance(target, DirectoryTarget) \
                and previous.name == target.name:
            previous.modules = tuple(set(previous.modules) | set(target.modules))
        else:
            include.append(target)
            previous = target

    previous = None
    exclude = []
    for target in exclude_targets:
        if isinstance(previous, DirectoryTarget) and isinstance(target, DirectoryTarget) \
                and previous.name == target.name:
            previous.modules = tuple(set(previous.modules) | set(target.modules))
        else:
            exclude.append(target)
            previous = target

    return tuple(include), tuple(exclude)


def filter_targets(targets, patterns, include=True, directories=True, errors=True):
    """
    :type targets: collections.Iterable[CompletionTarget]
    :type patterns: list[str]
    :type include: bool
    :type directories: bool
    :type errors: bool
    :rtype: collections.Iterable[CompletionTarget]
    """
    unmatched = set(patterns or ())
    compiled_patterns = dict((p, re.compile('^%s$' % p)) for p in patterns) if patterns else None

    for target in targets:
        matched_directories = set()
        match = False

        if patterns:
            for alias in target.aliases:
                for pattern in patterns:
                    if compiled_patterns[pattern].match(alias):
                        match = True

                        try:
                            unmatched.remove(pattern)
                        except KeyError:
                            pass

                        if alias.endswith('/'):
                            if target.base_path and len(target.base_path) > len(alias):
                                matched_directories.add(target.base_path)
                            else:
                                matched_directories.add(alias)
        elif include:
            match = True
            if not target.base_path:
                matched_directories.add('.')
            for alias in target.aliases:
                if alias.endswith('/'):
                    if target.base_path and len(target.base_path) > len(alias):
                        matched_directories.add(target.base_path)
                    else:
                        matched_directories.add(alias)

        if match != include:
            continue

        if directories and matched_directories:
            yield DirectoryTarget(sorted(matched_directories, key=len)[0], target.modules)
        else:
            yield target

    if errors:
        if unmatched:
            raise TargetPatternsNotMatched(unmatched)


def walk_module_targets():
    """
    :rtype: collections.Iterable[TestTarget]
    """
    path = 'lib/ansible/modules'

    for target in walk_test_targets(path, path + '/', extensions=MODULE_EXTENSIONS):
        if not target.module:
            continue

        yield target


def walk_units_targets():
    """
    :rtype: collections.Iterable[TestTarget]
    """
    return walk_test_targets(path='test/units', module_path='test/units/modules/', extensions=('.py',), prefix='test_')


def walk_compile_targets():
    """
    :rtype: collections.Iterable[TestTarget]
    """
    return walk_test_targets(module_path='lib/ansible/modules/', extensions=('.py',), extra_dirs=('bin',))


def walk_sanity_targets():
    """
    :rtype: collections.Iterable[TestTarget]
    """
    return walk_test_targets(module_path='lib/ansible/modules/')


def walk_posix_integration_targets(include_hidden=False):
    """
    :type include_hidden: bool
    :rtype: collections.Iterable[IntegrationTarget]
    """
    for target in walk_integration_targets():
        if 'posix/' in target.aliases or (include_hidden and 'hidden/posix/' in target.aliases):
            yield target


def walk_network_integration_targets(include_hidden=False):
    """
    :type include_hidden: bool
    :rtype: collections.Iterable[IntegrationTarget]
    """
    for target in walk_integration_targets():
        if 'network/' in target.aliases or (include_hidden and 'hidden/network/' in target.aliases):
            yield target


def walk_windows_integration_targets(include_hidden=False):
    """
    :type include_hidden: bool
    :rtype: collections.Iterable[IntegrationTarget]
    """
    for target in walk_integration_targets():
        if 'windows/' in target.aliases or (include_hidden and 'hidden/windows/' in target.aliases):
            yield target


def walk_integration_targets():
    """
    :rtype: collections.Iterable[IntegrationTarget]
    """
    path = 'test/integration/targets'
    modules = frozenset(t.module for t in walk_module_targets())
    paths = sorted(os.path.join(path, p) for p in os.listdir(path))
    prefixes = load_integration_prefixes()

    for path in paths:
        if os.path.isdir(path):
            yield IntegrationTarget(path, modules, prefixes)


def load_integration_prefixes():
    """
    :rtype: dict[str, str]
    """
    path = 'test/integration'
    names = sorted(f for f in os.listdir(path) if os.path.splitext(f)[0] == 'target-prefixes')
    prefixes = {}

    for name in names:
        prefix = os.path.splitext(name)[1][1:]
        with open(os.path.join(path, name), 'r') as prefix_fd:
            prefixes.update(dict((k, prefix) for k in prefix_fd.read().splitlines()))

    return prefixes


def walk_test_targets(path=None, module_path=None, extensions=None, prefix=None, extra_dirs=None):
    """
    :type path: str | None
    :type module_path: str | None
    :type extensions: tuple[str] | None
    :type prefix: str | None
    :type extra_dirs: tuple[str] | None
    :rtype: collections.Iterable[TestTarget]
    """
    for root, _, file_names in os.walk(path or '.', topdown=False):
        if root.endswith('/__pycache__'):
            continue

        if '/.tox/' in root:
            continue

        if path is None:
            root = root[2:]

        if root.startswith('.') and root != '.github':
            continue

        for file_name in file_names:
            name, ext = os.path.splitext(os.path.basename(file_name))

            if name.startswith('.'):
                continue

            if extensions and ext not in extensions:
                continue

            if prefix and not name.startswith(prefix):
                continue

            file_path = os.path.join(root, file_name)

            if os.path.islink(file_path):
                # special case to allow a symlink of ansible_release.py -> ../release.py
                if file_path != 'lib/ansible/module_utils/ansible_release.py':
                    continue

            yield TestTarget(file_path, module_path, prefix, path)

    if extra_dirs:
        for extra_dir in extra_dirs:
            file_names = os.listdir(extra_dir)

            for file_name in file_names:
                file_path = os.path.join(extra_dir, file_name)

                if os.path.isfile(file_path) and not os.path.islink(file_path):
                    yield TestTarget(file_path, module_path, prefix, path)


def analyze_integration_target_dependencies(integration_targets):
    """
    :type integration_targets: list[IntegrationTarget]
    :rtype: dict[str,set[str]]
    """
    hidden_role_target_names = set(t.name for t in integration_targets if t.type == 'role' and 'hidden/' in t.aliases)
    normal_role_targets = [t for t in integration_targets if t.type == 'role' and 'hidden/' not in t.aliases]
    dependencies = collections.defaultdict(set)

    # handle setup dependencies
    for target in integration_targets:
        for setup_target_name in target.setup_always + target.setup_once:
            dependencies[setup_target_name].add(target.name)

    # intentionally primitive analysis of role meta to avoid a dependency on pyyaml
    for role_target in normal_role_targets:
        meta_dir = os.path.join(role_target.path, 'meta')

        if not os.path.isdir(meta_dir):
            continue

        meta_paths = sorted([os.path.join(meta_dir, name) for name in os.listdir(meta_dir)])

        for meta_path in meta_paths:
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as meta_fd:
                    meta_lines = meta_fd.read().splitlines()

                for meta_line in meta_lines:
                    if re.search(r'^ *#.*$', meta_line):
                        continue

                    if not meta_line.strip():
                        continue

                    for hidden_target_name in hidden_role_target_names:
                        if hidden_target_name in meta_line:
                            dependencies[hidden_target_name].add(role_target.name)

    return dependencies


class CompletionTarget(object):
    """Command-line argument completion target base class."""
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.name = None
        self.path = None
        self.base_path = None
        self.modules = tuple()
        self.aliases = tuple()

    def __eq__(self, other):
        if isinstance(other, CompletionTarget):
            return self.__repr__() == other.__repr__()

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.name.__lt__(other.name)

    def __gt__(self, other):
        return self.name.__gt__(other.name)

    def __hash__(self):
        return hash(self.__repr__())

    def __repr__(self):
        if self.modules:
            return '%s (%s)' % (self.name, ', '.join(self.modules))

        return self.name


class DirectoryTarget(CompletionTarget):
    """Directory target."""
    def __init__(self, path, modules):
        """
        :type path: str
        :type modules: tuple[str]
        """
        super(DirectoryTarget, self).__init__()

        self.name = path
        self.path = path
        self.modules = modules


class TestTarget(CompletionTarget):
    """Generic test target."""
    def __init__(self, path, module_path, module_prefix, base_path):
        """
        :type path: str
        :type module_path: str | None
        :type module_prefix: str | None
        :type base_path: str
        """
        super(TestTarget, self).__init__()

        self.name = path
        self.path = path
        self.base_path = base_path + '/' if base_path else None

        name, ext = os.path.splitext(os.path.basename(self.path))

        if module_path and path.startswith(module_path) and name != '__init__' and ext in MODULE_EXTENSIONS:
            self.module = name[len(module_prefix or ''):].lstrip('_')
            self.modules = self.module,
        else:
            self.module = None
            self.modules = tuple()

        aliases = [self.path, self.module]
        parts = self.path.split('/')

        for i in range(1, len(parts)):
            alias = '%s/' % '/'.join(parts[:i])
            aliases.append(alias)

        aliases = [a for a in aliases if a]

        self.aliases = tuple(sorted(aliases))


class IntegrationTarget(CompletionTarget):
    """Integration test target."""
    non_posix = frozenset((
        'network',
        'windows',
    ))

    categories = frozenset(non_posix | frozenset((
        'posix',
        'module',
        'needs',
        'skip',
    )))

    def __init__(self, path, modules, prefixes):
        """
        :type path: str
        :type modules: frozenset[str]
        :type prefixes: dict[str, str]
        """
        super(IntegrationTarget, self).__init__()

        self.name = os.path.basename(path)
        self.path = path

        # script_path and type

        contents = sorted(os.listdir(path))

        runme_files = tuple(c for c in contents if os.path.splitext(c)[0] == 'runme')
        test_files = tuple(c for c in contents if os.path.splitext(c)[0] == 'test')

        self.script_path = None

        if runme_files:
            self.type = 'script'
            self.script_path = os.path.join(path, runme_files[0])
        elif test_files:
            self.type = 'special'
        elif os.path.isdir(os.path.join(path, 'tasks')) or os.path.isdir(os.path.join(path, 'defaults')):
            self.type = 'role'
        else:
            self.type = 'unknown'

        # static_aliases

        try:
            with open(os.path.join(path, 'aliases'), 'r') as aliases_file:
                static_aliases = tuple(aliases_file.read().splitlines())
        except IOError as ex:
            if ex.errno != errno.ENOENT:
                raise
            static_aliases = tuple()

        # modules

        if self.name in modules:
            module_name = self.name
        elif self.name.startswith('win_') and self.name[4:] in modules:
            module_name = self.name[4:]
        else:
            module_name = None

        self.modules = tuple(sorted(a for a in static_aliases + tuple([module_name]) if a in modules))

        # groups

        groups = [self.type]
        groups += [a for a in static_aliases if a not in modules]
        groups += ['module/%s' % m for m in self.modules]

        if not self.modules:
            groups.append('non_module')

        if 'destructive' not in groups:
            groups.append('non_destructive')

        if '_' in self.name:
            prefix = self.name[:self.name.find('_')]
        else:
            prefix = None

        if prefix in prefixes:
            group = prefixes[prefix]

            if group != prefix:
                group = '%s/%s' % (group, prefix)

            groups.append(group)

        if self.name.startswith('win_'):
            groups.append('windows')

        if self.name.startswith('connection_'):
            groups.append('connection')

        if self.name.startswith('setup_') or self.name.startswith('prepare_'):
            groups.append('hidden')

        if self.type not in ('script', 'role'):
            groups.append('hidden')

        for group in itertools.islice(groups, 0, len(groups)):
            if '/' in group:
                parts = group.split('/')
                for i in range(1, len(parts)):
                    groups.append('/'.join(parts[:i]))

        if not any(g in self.non_posix for g in groups):
            groups.append('posix')

        # aliases

        aliases = [self.name] + \
                  ['%s/' % g for g in groups] + \
                  ['%s/%s' % (g, self.name) for g in groups if g not in self.categories]

        if 'hidden/' in aliases:
            aliases = ['hidden/'] + ['hidden/%s' % a for a in aliases if not a.startswith('hidden/')]

        self.aliases = tuple(sorted(set(aliases)))

        # configuration

        self.setup_once = tuple(sorted(set(g.split('/')[2] for g in groups if g.startswith('setup/once/'))))
        self.setup_always = tuple(sorted(set(g.split('/')[2] for g in groups if g.startswith('setup/always/'))))


class TargetPatternsNotMatched(ApplicationError):
    """One or more targets were not matched when a match was required."""
    def __init__(self, patterns):
        """
        :type patterns: set[str]
        """
        self.patterns = sorted(patterns)

        if len(patterns) > 1:
            message = 'Target patterns not matched:\n%s' % '\n'.join(self.patterns)
        else:
            message = 'Target pattern not matched: %s' % self.patterns[0]

        super(TargetPatternsNotMatched, self).__init__(message)
