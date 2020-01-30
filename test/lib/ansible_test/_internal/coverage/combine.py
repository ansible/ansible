"""Combine code coverage files."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import re

from ..target import (
    walk_module_targets,
    walk_compile_targets,
    walk_powershell_targets,
)

from ..util import (
    display,
    to_text,
)

from ..util_common import (
    ResultType,
    write_json_test_results,
)

from ..data import (
    data_context,
)

from . import (
    initialize_coverage,
    COVERAGE_OUTPUT_FILE_NAME,
    COVERAGE_GROUPS,
    CoverageConfig,
)


def command_coverage_combine(args):
    """Patch paths in coverage files and merge into a single file.
    :type args: CoverageConfig
    :rtype: list[str]
    """
    paths = _command_coverage_combine_powershell(args) + _command_coverage_combine_python(args)

    for path in paths:
        display.info('Generated combined output: %s' % path, verbosity=1)

    return paths


def _command_coverage_combine_python(args):
    """
    :type args: CoverageConfig
    :rtype: list[str]
    """
    coverage = initialize_coverage(args)

    modules = dict((target.module, target.path) for target in list(walk_module_targets()) if target.path.endswith('.py'))

    coverage_dir = ResultType.COVERAGE.path
    coverage_files = [os.path.join(coverage_dir, f) for f in os.listdir(coverage_dir)
                      if '=coverage.' in f and '=python' in f]

    counter = 0
    sources = _get_coverage_targets(args, walk_compile_targets)
    groups = _build_stub_groups(args, sources, lambda line_count: set())

    if data_context().content.collection:
        collection_search_re = re.compile(r'/%s/' % data_context().content.collection.directory)
        collection_sub_re = re.compile(r'^.*?/%s/' % data_context().content.collection.directory)
    else:
        collection_search_re = None
        collection_sub_re = None

    for coverage_file in coverage_files:
        counter += 1
        display.info('[%4d/%4d] %s' % (counter, len(coverage_files), coverage_file), verbosity=2)

        original = coverage.CoverageData()

        group = get_coverage_group(args, coverage_file)

        if group is None:
            display.warning('Unexpected name for coverage file: %s' % coverage_file)
            continue

        if os.path.getsize(coverage_file) == 0:
            display.warning('Empty coverage file: %s' % coverage_file)
            continue

        try:
            original.read_file(coverage_file)
        except Exception as ex:  # pylint: disable=locally-disabled, broad-except
            display.error(u'%s' % ex)
            continue

        for filename in original.measured_files():
            arcs = set(original.arcs(filename) or [])

            if not arcs:
                # This is most likely due to using an unsupported version of coverage.
                display.warning('No arcs found for "%s" in coverage file: %s' % (filename, coverage_file))
                continue

            filename = _sanitize_filename(filename, modules=modules, collection_search_re=collection_search_re,
                                          collection_sub_re=collection_sub_re)
            if not filename:
                continue

            if group not in groups:
                groups[group] = {}

            arc_data = groups[group]

            if filename not in arc_data:
                arc_data[filename] = set()

            arc_data[filename].update(arcs)

    output_files = []
    invalid_path_count = 0
    invalid_path_chars = 0

    coverage_file = os.path.join(ResultType.COVERAGE.path, COVERAGE_OUTPUT_FILE_NAME)

    for group in sorted(groups):
        arc_data = groups[group]

        updated = coverage.CoverageData()

        for filename in arc_data:
            if not os.path.isfile(filename):
                if collection_search_re and collection_search_re.search(filename) and os.path.basename(filename) == '__init__.py':
                    # the collection loader uses implicit namespace packages, so __init__.py does not need to exist on disk
                    continue

                invalid_path_count += 1
                invalid_path_chars += len(filename)

                if args.verbosity > 1:
                    display.warning('Invalid coverage path: %s' % filename)

                continue

            updated.add_arcs({filename: list(arc_data[filename])})

        if args.all:
            updated.add_arcs(dict((source[0], []) for source in sources))

        if not args.explain:
            output_file = coverage_file + group
            updated.write_file(output_file)
            output_files.append(output_file)

    if invalid_path_count > 0:
        display.warning('Ignored %d characters from %d invalid coverage path(s).' % (invalid_path_chars, invalid_path_count))

    return sorted(output_files)


def _command_coverage_combine_powershell(args):
    """
    :type args: CoverageConfig
    :rtype: list[str]
    """
    coverage_dir = ResultType.COVERAGE.path
    coverage_files = [os.path.join(coverage_dir, f) for f in os.listdir(coverage_dir)
                      if '=coverage.' in f and '=powershell' in f]

    def _default_stub_value(lines):
        val = {}
        for line in range(lines):
            val[line] = 0
        return val

    counter = 0
    sources = _get_coverage_targets(args, walk_powershell_targets)
    groups = _build_stub_groups(args, sources, _default_stub_value)

    for coverage_file in coverage_files:
        counter += 1
        display.info('[%4d/%4d] %s' % (counter, len(coverage_files), coverage_file), verbosity=2)

        group = get_coverage_group(args, coverage_file)

        if group is None:
            display.warning('Unexpected name for coverage file: %s' % coverage_file)
            continue

        if os.path.getsize(coverage_file) == 0:
            display.warning('Empty coverage file: %s' % coverage_file)
            continue

        try:
            with open(coverage_file, 'rb') as original_fd:
                coverage_run = json.loads(to_text(original_fd.read(), errors='replace'))
        except Exception as ex:  # pylint: disable=locally-disabled, broad-except
            display.error(u'%s' % ex)
            continue

        for filename, hit_info in coverage_run.items():
            if group not in groups:
                groups[group] = {}

            coverage_data = groups[group]

            filename = _sanitize_filename(filename)
            if not filename:
                continue

            if filename not in coverage_data:
                coverage_data[filename] = {}

            file_coverage = coverage_data[filename]

            if not isinstance(hit_info, list):
                hit_info = [hit_info]

            for hit_entry in hit_info:
                if not hit_entry:
                    continue

                line_count = file_coverage.get(hit_entry['Line'], 0) + hit_entry['HitCount']
                file_coverage[hit_entry['Line']] = line_count

    output_files = []
    invalid_path_count = 0
    invalid_path_chars = 0

    for group in sorted(groups):
        coverage_data = groups[group]

        for filename in coverage_data:
            if not os.path.isfile(filename):
                invalid_path_count += 1
                invalid_path_chars += len(filename)

                if args.verbosity > 1:
                    display.warning('Invalid coverage path: %s' % filename)

                continue

        if args.all:
            # Add 0 line entries for files not in coverage_data
            for source, source_line_count in sources:
                if source in coverage_data:
                    continue

                coverage_data[source] = _default_stub_value(source_line_count)

        if not args.explain:
            output_file = COVERAGE_OUTPUT_FILE_NAME + group + '-powershell'

            write_json_test_results(ResultType.COVERAGE, output_file, coverage_data)

            output_files.append(os.path.join(ResultType.COVERAGE.path, output_file))

    if invalid_path_count > 0:
        display.warning(
            'Ignored %d characters from %d invalid coverage path(s).' % (invalid_path_chars, invalid_path_count))

    return sorted(output_files)


def _get_coverage_targets(args, walk_func):
    """
    :type args: CoverageConfig
    :type walk_func: Func
    :rtype: list[tuple[str, int]]
    """
    sources = []

    if args.all or args.stub:
        # excludes symlinks of regular files to avoid reporting on the same file multiple times
        # in the future it would be nice to merge any coverage for symlinks into the real files
        for target in walk_func(include_symlinks=False):
            target_path = os.path.abspath(target.path)

            with open(target_path, 'r') as target_fd:
                target_lines = len(target_fd.read().splitlines())

            sources.append((target_path, target_lines))

        sources.sort()

    return sources


def _build_stub_groups(args, sources, default_stub_value):
    """
    :type args: CoverageConfig
    :type sources: List[tuple[str, int]]
    :type default_stub_value: Func[int]
    :rtype: dict
    """
    groups = {}

    if args.stub:
        stub_group = []
        stub_groups = [stub_group]
        stub_line_limit = 500000
        stub_line_count = 0

        for source, source_line_count in sources:
            stub_group.append((source, source_line_count))
            stub_line_count += source_line_count

            if stub_line_count > stub_line_limit:
                stub_line_count = 0
                stub_group = []
                stub_groups.append(stub_group)

        for stub_index, stub_group in enumerate(stub_groups):
            if not stub_group:
                continue

            groups['=stub-%02d' % (stub_index + 1)] = dict((source, default_stub_value(line_count))
                                                           for source, line_count in stub_group)

    return groups


def get_coverage_group(args, coverage_file):
    """
    :type args: CoverageConfig
    :type coverage_file: str
    :rtype: str
    """
    parts = os.path.basename(coverage_file).split('=', 4)

    if len(parts) != 5 or not parts[4].startswith('coverage.'):
        return None

    names = dict(
        command=parts[0],
        target=parts[1],
        environment=parts[2],
        version=parts[3],
    )

    group = ''

    for part in COVERAGE_GROUPS:
        if part in args.group_by:
            group += '=%s' % names[part]

    return group


def _sanitize_filename(filename, modules=None, collection_search_re=None, collection_sub_re=None):
    """
    :type filename: str
    :type modules: dict | None
    :type collection_search_re: Pattern | None
    :type collection_sub_re: Pattern | None
    :rtype: str | None
    """
    ansible_path = os.path.abspath('lib/ansible/') + '/'
    root_path = data_context().content.root + '/'
    integration_temp_path = os.path.sep + os.path.join(ResultType.TMP.relative_path, 'integration') + os.path.sep

    if modules is None:
        modules = {}

    if '/ansible_modlib.zip/ansible/' in filename:
        # Rewrite the module_utils path from the remote host to match the controller. Ansible 2.6 and earlier.
        new_name = re.sub('^.*/ansible_modlib.zip/ansible/', ansible_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif collection_search_re and collection_search_re.search(filename):
        new_name = os.path.abspath(collection_sub_re.sub('', filename))
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search(r'/ansible_[^/]+_payload\.zip/ansible/', filename):
        # Rewrite the module_utils path from the remote host to match the controller. Ansible 2.7 and later.
        new_name = re.sub(r'^.*/ansible_[^/]+_payload\.zip/ansible/', ansible_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif '/ansible_module_' in filename:
        # Rewrite the module path from the remote host to match the controller. Ansible 2.6 and earlier.
        module_name = re.sub('^.*/ansible_module_(?P<module>.*).py$', '\\g<module>', filename)
        if module_name not in modules:
            display.warning('Skipping coverage of unknown module: %s' % module_name)
            return None
        new_name = os.path.abspath(modules[module_name])
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search(r'/ansible_[^/]+_payload(_[^/]+|\.zip)/__main__\.py$', filename):
        # Rewrite the module path from the remote host to match the controller. Ansible 2.7 and later.
        # AnsiballZ versions using zipimporter will match the `.zip` portion of the regex.
        # AnsiballZ versions not using zipimporter will match the `_[^/]+` portion of the regex.
        module_name = re.sub(r'^.*/ansible_(?P<module>[^/]+)_payload(_[^/]+|\.zip)/__main__\.py$',
                             '\\g<module>', filename).rstrip('_')
        if module_name not in modules:
            display.warning('Skipping coverage of unknown module: %s' % module_name)
            return None
        new_name = os.path.abspath(modules[module_name])
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif re.search('^(/.*?)?/root/ansible/', filename):
        # Rewrite the path of code running on a remote host or in a docker container as root.
        new_name = re.sub('^(/.*?)?/root/ansible/', root_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name
    elif integration_temp_path in filename:
        # Rewrite the path of code running from an integration test temporary directory.
        new_name = re.sub(r'^.*' + re.escape(integration_temp_path) + '[^/]+/', root_path, filename)
        display.info('%s -> %s' % (filename, new_name), verbosity=3)
        filename = new_name

    return filename
