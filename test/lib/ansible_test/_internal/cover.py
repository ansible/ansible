"""Code coverage utilities."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import re
import time

from xml.etree.ElementTree import (
    Comment,
    Element,
    SubElement,
    tostring,
)

from xml.dom import (
    minidom,
)

from . import types as t

from .target import (
    walk_module_targets,
    walk_compile_targets,
    walk_powershell_targets,
)

from .util import (
    display,
    ApplicationError,
    common_environment,
    ANSIBLE_TEST_DATA_ROOT,
    to_text,
    make_dirs,
)

from .util_common import (
    intercept_command,
    ResultType,
    write_json_file,
    write_text_test_results,
    write_json_test_results,
)

from .config import (
    CoverageConfig,
    CoverageReportConfig,
)

from .env import (
    get_ansible_version,
)

from .executor import (
    Delegate,
    install_command_requirements,
)

from .data import (
    data_context,
)

COVERAGE_GROUPS = ('command', 'target', 'environment', 'version')
COVERAGE_CONFIG_PATH = os.path.join(ANSIBLE_TEST_DATA_ROOT, 'coveragerc')
COVERAGE_OUTPUT_FILE_NAME = 'coverage'


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

            filename = _sanitise_filename(filename, modules=modules, collection_search_re=collection_search_re,
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

    if args.export:
        coverage_file = os.path.join(args.export, '')
        suffix = '=coverage.combined'
    else:
        coverage_file = os.path.join(ResultType.COVERAGE.path, COVERAGE_OUTPUT_FILE_NAME)
        suffix = ''

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
            output_file = coverage_file + group + suffix
            updated.write_file(output_file)
            output_files.append(output_file)

    if invalid_path_count > 0:
        display.warning('Ignored %d characters from %d invalid coverage path(s).' % (invalid_path_chars, invalid_path_count))

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


def _sanitise_filename(filename, modules=None, collection_search_re=None, collection_sub_re=None):
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


def command_coverage_report(args):
    """
    :type args: CoverageReportConfig
    """
    output_files = command_coverage_combine(args)

    for output_file in output_files:
        if args.group_by or args.stub:
            display.info('>>> Coverage Group: %s' % ' '.join(os.path.basename(output_file).split('=')[1:]))

        if output_file.endswith('-powershell'):
            display.info(_generate_powershell_output_report(args, output_file))
        else:
            options = []

            if args.show_missing:
                options.append('--show-missing')

            if args.include:
                options.extend(['--include', args.include])

            if args.omit:
                options.extend(['--omit', args.omit])

            run_coverage(args, output_file, 'report', options)


def command_coverage_html(args):
    """
    :type args: CoverageConfig
    """
    output_files = command_coverage_combine(args)

    for output_file in output_files:
        if output_file.endswith('-powershell'):
            # coverage.py does not support non-Python files so we just skip the local html report.
            display.info("Skipping output file %s in html generation" % output_file, verbosity=3)
            continue

        dir_name = os.path.join(ResultType.REPORTS.path, os.path.basename(output_file))
        make_dirs(dir_name)
        run_coverage(args, output_file, 'html', ['-i', '-d', dir_name])

        display.info('HTML report generated: file:///%s' % os.path.join(dir_name, 'index.html'))


def command_coverage_xml(args):
    """
    :type args: CoverageConfig
    """
    output_files = command_coverage_combine(args)

    for output_file in output_files:
        xml_name = '%s.xml' % os.path.basename(output_file)
        if output_file.endswith('-powershell'):
            report = _generage_powershell_xml(output_file)

            rough_string = tostring(report, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty = reparsed.toprettyxml(indent='    ')

            write_text_test_results(ResultType.REPORTS, xml_name, pretty)
        else:
            xml_path = os.path.join(ResultType.REPORTS.path, xml_name)
            make_dirs(ResultType.REPORTS.path)
            run_coverage(args, output_file, 'xml', ['-i', '-o', xml_path])


def command_coverage_erase(args):
    """
    :type args: CoverageConfig
    """
    initialize_coverage(args)

    coverage_dir = ResultType.COVERAGE.path

    for name in os.listdir(coverage_dir):
        if not name.startswith('coverage') and '=coverage.' not in name:
            continue

        path = os.path.join(coverage_dir, name)

        if not args.explain:
            os.remove(path)


def initialize_coverage(args):
    """
    :type args: CoverageConfig
    :rtype: coverage
    """
    if args.delegate:
        raise Delegate()

    if args.requirements:
        install_command_requirements(args)

    try:
        import coverage
    except ImportError:
        coverage = None

    if not coverage:
        raise ApplicationError('You must install the "coverage" python module to use this command.')

    return coverage


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

    export_names = dict(
        version=parts[3],
    )

    group = ''

    for part in COVERAGE_GROUPS:
        if part in args.group_by:
            group += '=%s' % names[part]
        elif args.export:
            group += '=%s' % export_names.get(part, 'various')

    if args.export:
        group = group.lstrip('=')

    return group


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

            filename = _sanitise_filename(filename)
            if not filename:
                continue

            if isinstance(hit_info, dict) and not hit_info.get('Line'):
                # Input data was previously aggregated and thus uses the standard ansible-test output format for PowerShell coverage.
                # This format differs from the more verbose format of raw coverage data from the remote Windows hosts.
                hit_info = dict((int(key), value) for key, value in hit_info.items())

                coverage_data[filename] = hit_info
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
            if args.export:
                output_file = os.path.join(args.export, group + '=coverage.combined')
                write_json_file(output_file, coverage_data)
                output_files.append(output_file)
                continue

            output_file = COVERAGE_OUTPUT_FILE_NAME + group + '-powershell'

            write_json_test_results(ResultType.COVERAGE, output_file, coverage_data)

            output_files.append(os.path.join(ResultType.COVERAGE.path, output_file))

    if invalid_path_count > 0:
        display.warning(
            'Ignored %d characters from %d invalid coverage path(s).' % (invalid_path_chars, invalid_path_count))

    return sorted(output_files)


def _generage_powershell_xml(coverage_file):
    """
    :type coverage_file: str
    :rtype: Element
    """
    with open(coverage_file, 'rb') as coverage_fd:
        coverage_info = json.loads(to_text(coverage_fd.read()))

    content_root = data_context().content.root
    is_ansible = data_context().content.is_ansible

    packages = {}
    for path, results in coverage_info.items():
        filename = os.path.splitext(os.path.basename(path))[0]

        if filename.startswith('Ansible.ModuleUtils'):
            package = 'ansible.module_utils'
        elif is_ansible:
            package = 'ansible.modules'
        else:
            rel_path = path[len(content_root) + 1:]
            plugin_type = "modules" if rel_path.startswith("plugins/modules") else "module_utils"
            package = 'ansible_collections.%splugins.%s' % (data_context().content.collection.prefix, plugin_type)

        if package not in packages:
            packages[package] = {}

        packages[package][path] = results

    elem_coverage = Element('coverage')
    elem_coverage.append(
        Comment(' Generated by ansible-test from the Ansible project: https://www.ansible.com/ '))
    elem_coverage.append(
        Comment(' Based on https://raw.githubusercontent.com/cobertura/web/master/htdocs/xml/coverage-04.dtd '))

    elem_sources = SubElement(elem_coverage, 'sources')

    elem_source = SubElement(elem_sources, 'source')
    elem_source.text = data_context().content.root

    elem_packages = SubElement(elem_coverage, 'packages')

    total_lines_hit = 0
    total_line_count = 0

    for package_name, package_data in packages.items():
        lines_hit, line_count = _add_cobertura_package(elem_packages, package_name, package_data)

        total_lines_hit += lines_hit
        total_line_count += line_count

    elem_coverage.attrib.update({
        'branch-rate': '0',
        'branches-covered': '0',
        'branches-valid': '0',
        'complexity': '0',
        'line-rate': str(round(total_lines_hit / total_line_count, 4)) if total_line_count else "0",
        'lines-covered': str(total_line_count),
        'lines-valid': str(total_lines_hit),
        'timestamp': str(int(time.time())),
        'version': get_ansible_version(),
    })

    return elem_coverage


def _add_cobertura_package(packages, package_name, package_data):
    """
    :type packages: SubElement
    :type package_name: str
    :type package_data: Dict[str, Dict[str, int]]
    :rtype: Tuple[int, int]
    """
    elem_package = SubElement(packages, 'package')
    elem_classes = SubElement(elem_package, 'classes')

    total_lines_hit = 0
    total_line_count = 0

    for path, results in package_data.items():
        lines_hit = len([True for hits in results.values() if hits])
        line_count = len(results)

        total_lines_hit += lines_hit
        total_line_count += line_count

        elem_class = SubElement(elem_classes, 'class')

        class_name = os.path.splitext(os.path.basename(path))[0]
        if class_name.startswith("Ansible.ModuleUtils"):
            class_name = class_name[20:]

        content_root = data_context().content.root
        filename = path
        if filename.startswith(content_root):
            filename = filename[len(content_root) + 1:]

        elem_class.attrib.update({
            'branch-rate': '0',
            'complexity': '0',
            'filename': filename,
            'line-rate': str(round(lines_hit / line_count, 4)) if line_count else "0",
            'name': class_name,
        })

        SubElement(elem_class, 'methods')

        elem_lines = SubElement(elem_class, 'lines')

        for number, hits in results.items():
            elem_line = SubElement(elem_lines, 'line')
            elem_line.attrib.update(
                hits=str(hits),
                number=str(number),
            )

    elem_package.attrib.update({
        'branch-rate': '0',
        'complexity': '0',
        'line-rate': str(round(total_lines_hit / total_line_count, 4)) if total_line_count else "0",
        'name': package_name,
    })

    return total_lines_hit, total_line_count


def _generate_powershell_output_report(args, coverage_file):
    """
    :type args: CoverageReportConfig
    :type coverage_file: str
    :rtype: str
    """
    with open(coverage_file, 'rb') as coverage_fd:
        coverage_info = json.loads(to_text(coverage_fd.read()))

    root_path = data_context().content.root + '/'

    name_padding = 7
    cover_padding = 8

    file_report = []
    total_stmts = 0
    total_miss = 0

    for filename in sorted(coverage_info.keys()):
        hit_info = coverage_info[filename]

        if filename.startswith(root_path):
            filename = filename[len(root_path):]

        if args.omit and filename in args.omit:
            continue
        if args.include and filename not in args.include:
            continue

        stmts = len(hit_info)
        miss = len([c for c in hit_info.values() if c == 0])

        name_padding = max(name_padding, len(filename) + 3)

        total_stmts += stmts
        total_miss += miss

        cover = "{0}%".format(int((stmts - miss) / stmts * 100))

        missing = []
        current_missing = None
        sorted_lines = sorted([int(x) for x in hit_info.keys()])
        for idx, line in enumerate(sorted_lines):
            hit = hit_info[str(line)]
            if hit == 0 and current_missing is None:
                current_missing = line
            elif hit != 0 and current_missing is not None:
                end_line = sorted_lines[idx - 1]
                if current_missing == end_line:
                    missing.append(str(current_missing))
                else:
                    missing.append('%s-%s' % (current_missing, end_line))
                current_missing = None

        if current_missing is not None:
            end_line = sorted_lines[-1]
            if current_missing == end_line:
                missing.append(str(current_missing))
            else:
                missing.append('%s-%s' % (current_missing, end_line))

        file_report.append({'name': filename, 'stmts': stmts, 'miss': miss, 'cover': cover, 'missing': missing})

    if total_stmts == 0:
        return ''

    total_percent = '{0}%'.format(int((total_stmts - total_miss) / total_stmts * 100))
    stmts_padding = max(8, len(str(total_stmts)))
    miss_padding = max(7, len(str(total_miss)))

    line_length = name_padding + stmts_padding + miss_padding + cover_padding

    header = 'Name'.ljust(name_padding) + 'Stmts'.rjust(stmts_padding) + 'Miss'.rjust(miss_padding) + \
             'Cover'.rjust(cover_padding)

    if args.show_missing:
        header += 'Lines Missing'.rjust(16)
        line_length += 16

    line_break = '-' * line_length
    lines = ['%s%s%s%s%s' % (f['name'].ljust(name_padding), str(f['stmts']).rjust(stmts_padding),
                             str(f['miss']).rjust(miss_padding), f['cover'].rjust(cover_padding),
                             '   ' + ', '.join(f['missing']) if args.show_missing else '')
             for f in file_report]
    totals = 'TOTAL'.ljust(name_padding) + str(total_stmts).rjust(stmts_padding) + \
             str(total_miss).rjust(miss_padding) + total_percent.rjust(cover_padding)

    report = '{0}\n{1}\n{2}\n{1}\n{3}'.format(header, line_break, "\n".join(lines), totals)
    return report


def run_coverage(args, output_file, command, cmd):  # type: (CoverageConfig, str, str, t.List[str]) -> None
    """Run the coverage cli tool with the specified options."""
    env = common_environment()
    env.update(dict(COVERAGE_FILE=output_file))

    cmd = ['python', '-m', 'coverage.__main__', command, '--rcfile', COVERAGE_CONFIG_PATH] + cmd

    intercept_command(args, target_name='coverage', env=env, cmd=cmd, disable_coverage=True)
