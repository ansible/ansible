"""Code coverage utilities."""

from __future__ import absolute_import, print_function

import os
import re

from lib.target import (
    walk_module_targets,
)

from lib.util import (
    display,
    ApplicationError,
    EnvironmentConfig,
    run_command,
)

from lib.executor import (
    Delegate,
    install_command_requirements,
)

COVERAGE_DIR = 'test/results/coverage'
COVERAGE_FILE = os.path.join(COVERAGE_DIR, 'coverage')


def command_coverage_combine(args):
    """Patch paths in coverage files and merge into a single file.
    :type args: CoverageConfig
    """
    coverage = initialize_coverage(args)

    modules = dict((t.module, t.path) for t in list(walk_module_targets()))

    coverage_files = [os.path.join(COVERAGE_DIR, f) for f in os.listdir(COVERAGE_DIR)
                      if f.startswith('coverage') and f != 'coverage']

    arc_data = {}

    ansible_path = os.path.abspath('lib/ansible/') + '/'
    root_path = os.getcwd() + '/'

    counter = 0

    for coverage_file in coverage_files:
        counter += 1
        display.info('[%4d/%4d] %s' % (counter, len(coverage_files), coverage_file), verbosity=2)

        original = coverage.CoverageData()

        if os.path.getsize(coverage_file) == 0:
            display.warning('Empty coverage file: %s' % coverage_file)
            continue

        try:
            original.read_file(coverage_file)
        except Exception as ex:  # pylint: disable=locally-disabled, broad-except
            display.error(str(ex))
            continue

        for filename in original.measured_files():
            arcs = set(original.arcs(filename))

            if '/ansible_modlib.zip/ansible/' in filename:
                new_name = re.sub('^.*/ansible_modlib.zip/ansible/', ansible_path, filename)
                display.info('%s -> %s' % (filename, new_name), verbosity=3)
                filename = new_name
            elif '/ansible_module_' in filename:
                module = re.sub('^.*/ansible_module_(?P<module>.*).py$', '\\g<module>', filename)
                new_name = os.path.abspath(modules[module])
                display.info('%s -> %s' % (filename, new_name), verbosity=3)
                filename = new_name
            elif filename.startswith('/root/ansible/'):
                new_name = re.sub('^/.*?/ansible/', root_path, filename)
                display.info('%s -> %s' % (filename, new_name), verbosity=3)
                filename = new_name

            if filename not in arc_data:
                arc_data[filename] = set()

            arc_data[filename].update(arcs)

    updated = coverage.CoverageData()

    for filename in arc_data:
        if not os.path.isfile(filename):
            display.warning('Invalid coverage path: %s' % filename)
            continue

        updated.add_arcs({filename: list(arc_data[filename])})

    if not args.explain:
        updated.write_file(COVERAGE_FILE)


def command_coverage_report(args):
    """
    :type args: CoverageConfig
    """
    command_coverage_combine(args)
    run_command(args, ['coverage', 'report'])


def command_coverage_html(args):
    """
    :type args: CoverageConfig
    """
    command_coverage_combine(args)
    run_command(args, ['coverage', 'html', '-d', 'test/results/reports/coverage'])


def command_coverage_xml(args):
    """
    :type args: CoverageConfig
    """
    command_coverage_combine(args)
    run_command(args, ['coverage', 'xml', '-o', 'test/results/reports/coverage.xml'])


def command_coverage_erase(args):
    """
    :type args: CoverageConfig
    """
    initialize_coverage(args)

    for name in os.listdir(COVERAGE_DIR):
        if not name.startswith('coverage'):
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


class CoverageConfig(EnvironmentConfig):
    """Configuration for the coverage command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CoverageConfig, self).__init__(args, 'coverage')
