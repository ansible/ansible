"""Test target identification, iteration and inclusion/exclusion."""

from __future__ import annotations

import collections
import collections.abc as c
import enum
import os
import re
import itertools
import abc
import typing as t

from .encoding import (
    to_bytes,
    to_text,
)

from .io import (
    read_text_file,
)

from .util import (
    ApplicationError,
    display,
    read_lines_without_comments,
    is_subdir,
)

from .data import (
    data_context,
    content_plugins,
)

MODULE_EXTENSIONS = '.py', '.ps1'


def find_target_completion(target_func: c.Callable[[], c.Iterable[CompletionTarget]], prefix: str, short: bool) -> list[str]:
    """Return a list of targets from the given target function which match the given prefix."""
    try:
        targets = target_func()
        matches = list(walk_completion_targets(targets, prefix, short))
        return matches
    except Exception as ex:  # pylint: disable=locally-disabled, broad-except
        return ['%s' % ex]


def walk_completion_targets(targets: c.Iterable[CompletionTarget], prefix: str, short: bool = False) -> tuple[str, ...]:
    """Return a tuple of targets from the given target iterable which match the given prefix."""
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


def walk_internal_targets[TCompletionTarget: CompletionTarget](
    targets: c.Iterable[TCompletionTarget],
    includes: t.Optional[list[str]] = None,
    excludes: t.Optional[list[str]] = None,
    requires: t.Optional[list[str]] = None,
) -> tuple[TCompletionTarget, ...]:
    """Return a tuple of matching completion targets."""
    targets = tuple(targets)

    include_targets = sorted(filter_targets(targets, includes), key=lambda include_target: include_target.name)

    if requires:
        require_targets = set(filter_targets(targets, requires))
        include_targets = [require_target for require_target in include_targets if require_target in require_targets]

    if excludes:
        list(filter_targets(targets, excludes, include=False))

    internal_targets = set(filter_targets(include_targets, excludes, errors=False, include=False))
    return tuple(sorted(internal_targets, key=lambda sort_target: sort_target.name))


def filter_targets[TCompletionTarget: CompletionTarget](
    targets: c.Iterable[TCompletionTarget],
    patterns: list[str],
    include: bool = True,
    errors: bool = True,
) -> c.Iterable[TCompletionTarget]:
    """Iterate over the given targets and filter them based on the supplied arguments."""
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

        yield target

    if errors:
        if unmatched:
            raise TargetPatternsNotMatched(unmatched)


def walk_module_targets() -> c.Iterable[TestTarget]:
    """Iterate through the module test targets."""
    for target in walk_test_targets(path=data_context().content.module_path, module_path=data_context().content.module_path, extensions=MODULE_EXTENSIONS):
        if not target.module:
            continue

        yield target


def walk_units_targets() -> c.Iterable[TestTarget]:
    """Return an iterable of units targets."""
    return walk_test_targets(path=data_context().content.unit_path, module_path=data_context().content.unit_module_path, extensions=('.py',), prefix='test_')


def walk_compile_targets(include_symlinks: bool = True) -> c.Iterable[TestTarget]:
    """Return an iterable of compile targets."""
    return walk_test_targets(module_path=data_context().content.module_path, extensions=('.py',), extra_dirs=('bin',), include_symlinks=include_symlinks)


def walk_powershell_targets(include_symlinks: bool = True) -> c.Iterable[TestTarget]:
    """Return an iterable of PowerShell targets."""
    return walk_test_targets(module_path=data_context().content.module_path, extensions=('.ps1', '.psm1'), include_symlinks=include_symlinks)


def walk_sanity_targets() -> c.Iterable[TestTarget]:
    """Return an iterable of sanity targets."""
    return walk_test_targets(module_path=data_context().content.module_path, include_symlinks=True, include_symlinked_directories=True)


def walk_posix_integration_targets(include_hidden: bool = False) -> c.Iterable[IntegrationTarget]:
    """Return an iterable of POSIX integration targets."""
    for target in walk_integration_targets():
        if 'posix/' in target.aliases or (include_hidden and 'hidden/posix/' in target.aliases):
            yield target


def walk_network_integration_targets(include_hidden: bool = False) -> c.Iterable[IntegrationTarget]:
    """Return an iterable of network integration targets."""
    for target in walk_integration_targets():
        if 'network/' in target.aliases or (include_hidden and 'hidden/network/' in target.aliases):
            yield target


def walk_windows_integration_targets(include_hidden: bool = False) -> c.Iterable[IntegrationTarget]:
    """Return an iterable of windows integration targets."""
    for target in walk_integration_targets():
        if 'windows/' in target.aliases or (include_hidden and 'hidden/windows/' in target.aliases):
            yield target


def walk_integration_targets() -> c.Iterable[IntegrationTarget]:
    """Return an iterable of integration targets."""
    path = data_context().content.integration_targets_path
    modules = frozenset(target.module for target in walk_module_targets())
    paths = data_context().content.walk_files(path)
    prefixes = load_integration_prefixes()
    targets_path_tuple = tuple(path.split(os.path.sep))

    entry_dirs = (
        'defaults',
        'files',
        'handlers',
        'meta',
        'tasks',
        'templates',
        'vars',
    )

    entry_files = (
        'main.yml',
        'main.yaml',
    )

    entry_points = []

    for entry_dir in entry_dirs:
        for entry_file in entry_files:
            entry_points.append(os.path.join(os.path.sep, entry_dir, entry_file))

    # any directory with at least one file is a target
    path_tuples = set(tuple(os.path.dirname(p).split(os.path.sep))
                      for p in paths)

    # also detect targets which are ansible roles, looking for standard entry points
    path_tuples.update(tuple(os.path.dirname(os.path.dirname(p)).split(os.path.sep))
                       for p in paths if any(p.endswith(entry_point) for entry_point in entry_points))

    # remove the top-level directory if it was included
    if targets_path_tuple in path_tuples:
        path_tuples.remove(targets_path_tuple)

    previous_path_tuple = None
    paths = []

    for path_tuple in sorted(path_tuples):
        if previous_path_tuple and previous_path_tuple == path_tuple[:len(previous_path_tuple)]:
            # ignore nested directories
            continue

        previous_path_tuple = path_tuple
        paths.append(os.path.sep.join(path_tuple))

    for path in paths:
        yield IntegrationTarget(to_text(path), modules, prefixes)


def load_integration_prefixes() -> dict[str, str]:
    """Load and return the integration test prefixes."""
    path = data_context().content.integration_path
    file_paths = sorted(f for f in data_context().content.get_files(path) if os.path.splitext(os.path.basename(f))[0] == 'target-prefixes')
    prefixes = {}

    for file_path in file_paths:
        prefix = os.path.splitext(file_path)[1][1:]
        prefixes.update(dict((k, prefix) for k in read_text_file(file_path).splitlines()))

    return prefixes


def walk_test_targets(
    path: t.Optional[str] = None,
    module_path: t.Optional[str] = None,
    extensions: t.Optional[tuple[str, ...]] = None,
    prefix: t.Optional[str] = None,
    extra_dirs: t.Optional[tuple[str, ...]] = None,
    include_symlinks: bool = False,
    include_symlinked_directories: bool = False,
) -> c.Iterable[TestTarget]:
    """Iterate over available test targets."""
    if path:
        file_paths = data_context().content.walk_files(path, include_symlinked_directories=include_symlinked_directories)
    else:
        file_paths = data_context().content.all_files(include_symlinked_directories=include_symlinked_directories)

    for file_path in file_paths:
        name, ext = os.path.splitext(os.path.basename(file_path))

        if extensions and ext not in extensions:
            continue

        if prefix and not name.startswith(prefix):
            continue

        symlink = os.path.islink(to_bytes(file_path.rstrip(os.path.sep)))

        if symlink and not include_symlinks:
            continue

        yield TestTarget(to_text(file_path), module_path, prefix, path, symlink)

    file_paths = []

    if extra_dirs:
        for extra_dir in extra_dirs:
            for file_path in data_context().content.get_files(extra_dir):
                file_paths.append(file_path)

    for file_path in file_paths:
        symlink = os.path.islink(to_bytes(file_path.rstrip(os.path.sep)))

        if symlink and not include_symlinks:
            continue

        yield TestTarget(file_path, module_path, prefix, path, symlink)


def analyze_integration_target_dependencies(integration_targets: list[IntegrationTarget]) -> dict[str, set[str]]:
    """Analyze the given list of integration test targets and return a dictionary expressing target names and the target names which depend on them."""
    real_target_root = os.path.realpath(data_context().content.integration_targets_path) + '/'

    role_targets = [target for target in integration_targets if target.type == 'role']
    hidden_role_target_names = set(target.name for target in role_targets if 'hidden/' in target.aliases)

    dependencies: collections.defaultdict[str, set[str]] = collections.defaultdict(set)

    # handle setup dependencies
    for target in integration_targets:
        for setup_target_name in target.setup_always + target.setup_once:
            dependencies[setup_target_name].add(target.name)

    # handle target dependencies
    for target in integration_targets:
        for need_target in target.needs_target:
            dependencies[need_target].add(target.name)

    # handle symlink dependencies between targets
    # this use case is supported, but discouraged
    for target in integration_targets:
        for path in data_context().content.walk_files(target.path):
            if not os.path.islink(to_bytes(path.rstrip(os.path.sep))):
                continue

            real_link_path = os.path.realpath(path)

            if not real_link_path.startswith(real_target_root):
                continue

            link_target = real_link_path[len(real_target_root):].split('/')[0]

            if link_target == target.name:
                continue

            dependencies[link_target].add(target.name)

    # intentionally primitive analysis of role meta to avoid a dependency on pyyaml
    # script based targets are scanned as they may execute a playbook with role dependencies
    for target in integration_targets:
        meta_dir = os.path.join(target.path, 'meta')

        if not os.path.isdir(meta_dir):
            continue

        meta_paths = data_context().content.get_files(meta_dir)

        for meta_path in meta_paths:
            if os.path.exists(meta_path):
                # try and decode the file as a utf-8 string, skip if it contains invalid chars (binary file)
                try:
                    meta_lines = read_text_file(meta_path).splitlines()
                except UnicodeDecodeError:
                    continue

                for meta_line in meta_lines:
                    if re.search(r'^ *#.*$', meta_line):
                        continue

                    if not meta_line.strip():
                        continue

                    for hidden_target_name in hidden_role_target_names:
                        if hidden_target_name in meta_line:
                            dependencies[hidden_target_name].add(target.name)

    while True:
        changes = 0

        for dummy, dependent_target_names in dependencies.items():
            for dependent_target_name in list(dependent_target_names):
                new_target_names = dependencies.get(dependent_target_name)

                if new_target_names:
                    for new_target_name in new_target_names:
                        if new_target_name not in dependent_target_names:
                            dependent_target_names.add(new_target_name)
                            changes += 1

        if not changes:
            break

    for target_name in sorted(dependencies):
        consumers = dependencies[target_name]

        if not consumers:
            continue

        display.info('%s:' % target_name, verbosity=4)

        for consumer in sorted(consumers):
            display.info('  %s' % consumer, verbosity=4)

    return dependencies


class CompletionTarget(metaclass=abc.ABCMeta):
    """Command-line argument completion target base class."""

    def __init__(self) -> None:
        self.name = ''
        self.path = ''
        self.base_path: t.Optional[str] = None
        self.modules: tuple[str, ...] = tuple()
        self.aliases: tuple[str, ...] = tuple()

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


class TestTarget(CompletionTarget):
    """Generic test target."""

    def __init__(
        self,
        path: str,
        module_path: t.Optional[str],
        module_prefix: t.Optional[str],
        base_path: str,
        symlink: t.Optional[bool] = None,
    ) -> None:
        super().__init__()

        if symlink is None:
            symlink = os.path.islink(to_bytes(path.rstrip(os.path.sep)))

        self.name = path
        self.path = path
        self.base_path = base_path + '/' if base_path else None
        self.symlink = symlink

        name, ext = os.path.splitext(os.path.basename(self.path))

        if module_path and is_subdir(path, module_path) and name != '__init__' and ext in MODULE_EXTENSIONS:
            self.module = name[len(module_prefix or ''):].lstrip('_')
            self.modules = (self.module,)
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


class IntegrationTargetType(enum.Enum):
    """Type of integration test target."""

    CONTROLLER = enum.auto()
    TARGET = enum.auto()
    UNKNOWN = enum.auto()
    CONFLICT = enum.auto()


def extract_plugin_references(name: str, aliases: list[str]) -> list[tuple[str, str]]:
    """Return a list of plugin references found in the given integration test target name and aliases."""
    plugins = content_plugins()
    found: list[tuple[str, str]] = []

    for alias in [name] + aliases:
        plugin_type = 'modules'
        plugin_name = alias

        if plugin_name in plugins.get(plugin_type, {}):
            found.append((plugin_type, plugin_name))

        parts = alias.split('_')

        for type_length in (1, 2):
            if len(parts) > type_length:
                plugin_type = '_'.join(parts[:type_length])
                plugin_name = '_'.join(parts[type_length:])

                if plugin_name in plugins.get(plugin_type, {}):
                    found.append((plugin_type, plugin_name))

    return found


def categorize_integration_test(name: str, aliases: list[str], force_target: bool) -> tuple[IntegrationTargetType, IntegrationTargetType]:
    """Return the integration test target types (used and actual) based on the given target name and aliases."""
    context_controller = f'context/{IntegrationTargetType.CONTROLLER.name.lower()}' in aliases
    context_target = f'context/{IntegrationTargetType.TARGET.name.lower()}' in aliases or force_target
    actual_type = None
    strict_mode = data_context().content.is_ansible

    if context_controller and context_target:
        target_type = IntegrationTargetType.CONFLICT
    elif context_controller and not context_target:
        target_type = IntegrationTargetType.CONTROLLER
    elif context_target and not context_controller:
        target_type = IntegrationTargetType.TARGET
    else:
        target_types = {IntegrationTargetType.TARGET if plugin_type in ('modules', 'module_utils') else IntegrationTargetType.CONTROLLER
                        for plugin_type, plugin_name in extract_plugin_references(name, aliases)}

        if len(target_types) == 1:
            target_type = target_types.pop()
        elif not target_types:
            actual_type = IntegrationTargetType.UNKNOWN
            target_type = actual_type if strict_mode else IntegrationTargetType.TARGET
        else:
            target_type = IntegrationTargetType.CONFLICT

    return target_type, actual_type or target_type


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

    def __init__(self, path: str, modules: frozenset[str], prefixes: dict[str, str]) -> None:
        super().__init__()

        self.relative_path = os.path.relpath(path, data_context().content.integration_targets_path)
        self.name = self.relative_path.replace(os.path.sep, '.')
        self.path = path

        # script_path and type

        file_paths = data_context().content.get_files(path)
        runme_path = os.path.join(path, 'runme.sh')

        if runme_path in file_paths:
            self.type = 'script'
            self.script_path = runme_path
        else:
            self.type = 'role'  # ansible will consider these empty roles, so ansible-test should as well
            self.script_path = None

        # static_aliases

        aliases_path = os.path.join(path, 'aliases')

        if aliases_path in file_paths:
            static_aliases = tuple(read_lines_without_comments(aliases_path, remove_blank_lines=True))
        else:
            static_aliases = tuple()

        # non-group aliases which need to be extracted before group mangling occurs

        self.env_set: dict[str, str] = {
            match.group('key'): match.group('value') for match in (
                re.match(r'env/set/(?P<key>[^/]+)/(?P<value>.*)', alias) for alias in static_aliases
            ) if match
        }

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

        if data_context().content.is_ansible and (self.name == 'ansible-test' or self.name.startswith('ansible-test-')):
            groups.append('ansible-test')

        if not self.modules:
            groups.append('non_module')

        if 'destructive' not in groups:
            groups.append('non_destructive')

        if 'needs/httptester' in groups:
            groups.append('cloud/httptester')  # backwards compatibility for when it was not a cloud plugin

        for prefix, group in prefixes.items():
            if not self.name.startswith(f'{prefix}_'):
                continue

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

        targets_relative_path = data_context().content.integration_targets_path

        # Collect skip entries before group expansion to avoid registering more specific skip entries as less specific versions.
        self.skips = tuple(g for g in groups if g.startswith('skip/'))

        # Collect file paths before group expansion to avoid including the directories.
        # Ignore references to test targets, as those must be defined using `needs/target/*` or other target references.
        self.needs_file = tuple(sorted(set('/'.join(g.split('/')[2:]) for g in groups if
                                           g.startswith('needs/file/') and not g.startswith('needs/file/%s/' % targets_relative_path))))

        # network platform
        networks = [g.split('/')[1] for g in groups if g.startswith('network/')]
        self.network_platform = networks[0] if networks else None

        for group in itertools.islice(groups, 0, len(groups)):
            if '/' in group:
                parts = group.split('/')
                for i in range(1, len(parts)):
                    groups.append('/'.join(parts[:i]))

        if not any(g in self.non_posix for g in groups):
            groups.append('posix')

        # target type

        # targets which are non-posix test against the target, even if they also support posix
        force_target = any(group in self.non_posix for group in groups)

        target_type, actual_type = categorize_integration_test(self.name, list(static_aliases), force_target)

        groups.extend(['context/', f'context/{target_type.name.lower()}'])

        if target_type != actual_type:
            # allow users to query for the actual type
            groups.extend(['context/', f'context/{actual_type.name.lower()}'])

        self.target_type = target_type
        self.actual_type = actual_type

        # aliases

        aliases = [self.name] + \
                  ['%s/' % g for g in groups] + \
                  ['%s/%s' % (g, self.name) for g in groups if g not in self.categories]

        if 'hidden/' in aliases:
            aliases = ['hidden/'] + ['hidden/%s' % a for a in aliases if not a.startswith('hidden/')]

        self.aliases = tuple(sorted(set(aliases)))

        # configuration

        self.retry_never = 'retry/never/' in self.aliases

        self.setup_once = tuple(sorted(set(g.split('/')[2] for g in groups if g.startswith('setup/once/'))))
        self.setup_always = tuple(sorted(set(g.split('/')[2] for g in groups if g.startswith('setup/always/'))))
        self.needs_target = tuple(sorted(set(g.split('/')[2] for g in groups if g.startswith('needs/target/'))))


class TargetPatternsNotMatched(ApplicationError):
    """One or more targets were not matched when a match was required."""

    def __init__(self, patterns: set[str]) -> None:
        self.patterns = sorted(patterns)

        if len(patterns) > 1:
            message = 'Target patterns not matched:\n%s' % '\n'.join(self.patterns)
        else:
            message = 'Target pattern not matched: %s' % self.patterns[0]

        super().__init__(message)
