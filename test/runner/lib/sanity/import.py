"""Sanity test for proper import exception handling."""
from __future__ import absolute_import, print_function

import os

from lib.sanity import (
    SanityMultipleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
)

from lib.util import (
    SubprocessError,
    run_command,
    intercept_command,
    remove_tree,
    display,
    find_python,
    read_lines_without_comments,
    parse_to_list_of_dict,
    make_dirs,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.executor import (
    generate_pip_install,
)

from lib.config import (
    SanityConfig,
)


class ImportTest(SanityMultipleVersion):
    """Sanity test for proper import exception handling."""
    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        skip_file = 'test/sanity/import/skip.txt'
        skip_paths = read_lines_without_comments(skip_file, remove_blank_lines=True)
        skip_paths_set = set(skip_paths)

        paths = sorted(
            i.path
            for i in targets.include
            if os.path.splitext(i.path)[1] == '.py' and
            (i.path.startswith('lib/ansible/modules/') or i.path.startswith('lib/ansible/module_utils/')) and
            i.path not in skip_paths_set
        )

        if not paths:
            return SanitySkipped(self.name, python_version=python_version)

        env = ansible_environment(args, color=False)

        # create a clean virtual environment to minimize the available imports beyond the python standard library
        virtual_environment_path = os.path.abspath('test/runner/.tox/minimal-py%s' % python_version.replace('.', ''))
        virtual_environment_bin = os.path.join(virtual_environment_path, 'bin')

        remove_tree(virtual_environment_path)

        python = find_python(python_version)

        cmd = [python, '-m', 'virtualenv', virtual_environment_path, '--python', python, '--no-setuptools', '--no-wheel']

        if not args.coverage:
            cmd.append('--no-pip')

        run_command(args, cmd, capture=True)

        # add the importer to our virtual environment so it can be accessed through the coverage injector
        importer_path = os.path.join(virtual_environment_bin, 'importer.py')
        if not args.explain:
            os.symlink(os.path.abspath('test/sanity/import/importer.py'), importer_path)

        # create a minimal python library
        python_path = os.path.abspath('test/runner/.tox/import/lib')
        ansible_path = os.path.join(python_path, 'ansible')
        ansible_init = os.path.join(ansible_path, '__init__.py')
        ansible_link = os.path.join(ansible_path, 'module_utils')

        if not args.explain:
            make_dirs(ansible_path)

            with open(ansible_init, 'w'):
                pass

            if not os.path.exists(ansible_link):
                os.symlink('../../../../../../lib/ansible/module_utils', ansible_link)

        # activate the virtual environment
        env['PATH'] = '%s:%s' % (virtual_environment_bin, env['PATH'])
        env['PYTHONPATH'] = python_path

        # make sure coverage is available in the virtual environment if needed
        if args.coverage:
            run_command(args, generate_pip_install(['pip'], 'sanity.import', packages=['setuptools']), env=env)
            run_command(args, generate_pip_install(['pip'], 'sanity.import', packages=['coverage']), env=env)
            run_command(args, ['pip', 'uninstall', '--disable-pip-version-check', '-y', 'setuptools'], env=env)
            run_command(args, ['pip', 'uninstall', '--disable-pip-version-check', '-y', 'pip'], env=env)

        cmd = ['importer.py']

        data = '\n'.join(paths)

        display.info(data, verbosity=4)

        results = []

        try:
            stdout, stderr = intercept_command(args, cmd, data=data, target_name=self.name, env=env, capture=True, python_version=python_version,
                                               path=env['PATH'])

            if stdout or stderr:
                raise SubprocessError(cmd, stdout=stdout, stderr=stderr)
        except SubprocessError as ex:
            if ex.status != 10 or ex.stderr or not ex.stdout:
                raise

            pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'

            results = parse_to_list_of_dict(pattern, ex.stdout)

            results = [SanityMessage(
                message=r['message'],
                path=r['path'],
                line=int(r['line']),
                column=int(r['column']),
            ) for r in results]

            results = [result for result in results if result.path not in skip_paths_set]

        if results:
            return SanityFailure(self.name, messages=results, python_version=python_version)

        return SanitySuccess(self.name, python_version=python_version)
