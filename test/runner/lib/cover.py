"""Code coverage utilities."""

from __future__ import absolute_import, print_function

import os
import re

from lib.target import (
    walk_module_targets,
    walk_compile_targets,
)

from lib.util import (
    display,
    ApplicationError,
    run_command,
    common_environment,
)

from lib.config import (
    CoverageConfig,
    CoverageReportConfig,
)

from lib.executor import (
    Delegate,
    install_command_requirements,
)

COVERAGE_DIR = 'test/results/coverage'
COVERAGE_FILE = os.path.join(COVERAGE_DIR, 'coverage')
COVERAGE_GROUPS = ('command', 'target', 'environment', 'version')


def command_coverage_combine(args):
    """Patch paths in coverage files and merge into a single file.
    :type args: CoverageConfig
    :rtype: list[str]
    """
    coverage = initialize_coverage(args)

    modules = dict((t.module, t.path) for t in list(walk_module_targets()))

    coverage_files = [os.path.join(COVERAGE_DIR, f) for f in os.listdir(COVERAGE_DIR) if '=coverage.' in f]

    ansible_path = os.path.abspath('lib/ansible/') + '/'
    root_path = os.getcwd() + '/'

    counter = 0
    groups = {}

    if args.all or args.stub:
        sources = sorted(os.path.abspath(target.path) for target in walk_compile_targets())
    else:
        sources = []

    if args.stub:
        groups['=stub'] = dict((source, set()) for source in sources)

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
            display.error(str(ex))
            continue

        for filename in original.measured_files():
            arcs = set(original.arcs(filename) or [])

            if not arcs:
                # This is most likely due to using an unsupported version of coverage.
                display.warning('No arcs found for "%s" in coverage file: %s' % (filename, coverage_file))
                continue

            if '/ansible_modlib.zip/ansible/' in filename:
                new_name = re.sub('^.*/ansible_modlib.zip/ansible/', ansible_path, filename)
                display.info('%s -> %s' % (filename, new_name), verbosity=3)
                filename = new_name
            elif '/ansible_module_' in filename:
                module = re.sub('^.*/ansible_module_(?P<module>.*).py$', '\\g<module>', filename)
                if module not in modules:
                    display.warning('Skipping coverage of unknown module: %s' % module)
                    continue
                new_name = os.path.abspath(modules[module])
                display.info('%s -> %s' % (filename, new_name), verbosity=3)
                filename = new_name
            elif re.search('^(/.*?)?/root/ansible/', filename):
                new_name = re.sub('^(/.*?)?/root/ansible/', root_path, filename)
                display.info('%s -> %s' % (filename, new_name), verbosity=3)
                filename = new_name

            if group not in groups:
                groups[group] = {}

            arc_data = groups[group]

            if filename not in arc_data:
                arc_data[filename] = set()

            arc_data[filename].update(arcs)

    output_files = []

    for group in sorted(groups):
        arc_data = groups[group]

        updated = coverage.CoverageData()

        for filename in arc_data:
            if not os.path.isfile(filename):
                display.warning('Invalid coverage path: %s' % filename)
                continue

            updated.add_arcs({filename: list(arc_data[filename])})

        if args.all:
            updated.add_arcs(dict((source, []) for source in sources))

        if not args.explain:
            output_file = COVERAGE_FILE + group
            updated.write_file(output_file)
            output_files.append(output_file)

    return sorted(output_files)


def command_coverage_report(args):
    """
    :type args: CoverageReportConfig
    """
    output_files = command_coverage_combine(args)

    for output_file in output_files:
        if args.group_by or args.stub:
            display.info('>>> Coverage Group: %s' % ' '.join(os.path.basename(output_file).split('=')[1:]))

        options = []

        if args.show_missing:
            options.append('--show-missing')

        env = common_environment()
        env.update(dict(COVERAGE_FILE=output_file))
        run_command(args, env=env, cmd=['coverage', 'report'] + options)


def command_coverage_html(args):
    """
    :type args: CoverageConfig
    """
    output_files = command_coverage_combine(args)

    for output_file in output_files:
        dir_name = 'test/results/reports/%s' % os.path.basename(output_file)
        env = common_environment()
        env.update(dict(COVERAGE_FILE=output_file))
        run_command(args, env=env, cmd=['coverage', 'html', '-d', dir_name])


def command_coverage_xml(args):
    """
    :type args: CoverageConfig
    """
    output_files = command_coverage_combine(args)

    for output_file in output_files:
        xml_name = 'test/results/reports/%s.xml' % os.path.basename(output_file)
        env = common_environment()
        env.update(dict(COVERAGE_FILE=output_file))
        run_command(args, env=env, cmd=['coverage', 'xml', '-o', xml_name])


def command_coverage_erase(args):
    """
    :type args: CoverageConfig
    """
    initialize_coverage(args)

    for name in os.listdir(COVERAGE_DIR):
        if not name.startswith('coverage') and '=coverage.' not in name:
            continue

        path = os.path.join(COVERAGE_DIR, name)

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

    group = ''

    for part in COVERAGE_GROUPS:
        if part in args.group_by:
            group += '=%s' % names[part]

    return group
