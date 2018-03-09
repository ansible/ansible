#!/usr/bin/env python
"""Import the given python module(s) and report error(s) encountered."""

from __future__ import absolute_import, print_function

import contextlib
import imp
import os
import re
import sys
import traceback

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import ansible.module_utils.basic
import ansible.module_utils.common.removed


class ImporterAnsibleModuleException(Exception):
    """Exception thrown during initialization of ImporterAnsibleModule."""
    pass


class ImporterAnsibleModule(object):
    """Replacement for AnsibleModule to support import testing."""
    def __init__(self, *args, **kwargs):
        raise ImporterAnsibleModuleException()


# stop Ansible module execution during AnsibleModule instantiation
ansible.module_utils.basic.AnsibleModule = ImporterAnsibleModule
# no-op for _load_params since it may be called before instantiating AnsibleModule
ansible.module_utils.basic._load_params = lambda *args, **kwargs: {}
# no-op for removed_module since it is called in place of AnsibleModule instantiation
ansible.module_utils.common.removed.removed_module = lambda *args, **kwargs: None


def main():
    """Main program function."""
    base_dir = os.getcwd()
    messages = set()

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        test_python_module(path, base_dir, messages, False)
        test_python_module(path, base_dir, messages, True)

    if messages:
        exit(10)


def test_python_module(path, base_dir, messages, ansible_module):
    if ansible_module:
        # importing modules with __main__ under Python 2.6 exits with status code 1
        if sys.version_info < (2, 7):
            return

        # only run __main__ protected code for Ansible modules
        if not path.startswith('lib/ansible/modules/'):
            return

        # async_wrapper is not an Ansible module
        if path == 'lib/ansible/modules/utilities/logic/async_wrapper.py':
            return

        # run code protected by __name__ conditional
        name = '__main__'
        # show the Ansible module responsible for the exception, even if it was thrown in module_utils
        filter_dir = os.path.join(base_dir, 'lib/ansible/modules')
    else:
        # do not run code protected by __name__ conditional
        name = 'module_import_test'
        # show the Ansible file responsible for the exception, even if it was thrown in 3rd party code
        filter_dir = base_dir

    capture = Capture()
    try:
        with open(path, 'r') as module_fd:
            with capture_output(capture):
                imp.load_module(name, module_fd, os.path.abspath(path), ('.py', 'r', imp.PY_SOURCE))

        capture_report(path, capture, messages)
    except ImporterAnsibleModuleException:
        # module instantiated AnsibleModule without raising an exception
        pass
    except BaseException as ex:  # pylint: disable=locally-disabled, broad-except
        capture_report(path, capture, messages)

        exc_type, _, exc_tb = sys.exc_info()
        message = str(ex)
        results = list(reversed(traceback.extract_tb(exc_tb)))
        source = None
        line = 0
        offset = 0

        for result in results:
            if result[0].startswith(filter_dir):
                source = result[0][len(base_dir) + 1:].replace('test/sanity/import/', '')
                line = result[1] or 0
                break

        if not source:
            # If none of our source files are found in the traceback, report the file we were testing.
            # I haven't been able to come up with a test case that encounters this issue yet.
            source = path
            message += ' (in %s:%d)' % (results[-1][0], results[-1][1] or 0)
        elif isinstance(ex, SyntaxError):
            if ex.filename.endswith(path):  # pylint: disable=locally-disabled, no-member
                # A SyntaxError in the source we're importing will have the correct path, line and offset.
                # However, the traceback will report the path to this importer.py script instead.
                # We'll use the details from the SyntaxError in this case, as it's more accurate.
                source = path
                line = ex.lineno or 0  # pylint: disable=locally-disabled, no-member
                offset = ex.offset or 0  # pylint: disable=locally-disabled, no-member
                message = str(ex)

                # Hack to remove the filename and line number from the message, if present.
                message = message.replace(' (%s, line %d)' % (os.path.basename(path), line), '')

        message = re.sub(r'\n *', ': ', message)
        error = '%s:%d:%d: %s: %s' % (source, line, offset, exc_type.__name__, message)

        report_message(error, messages)


class Capture(object):
    """Captured output and/or exception."""
    def __init__(self):
        self.stdout = StringIO()
        self.stderr = StringIO()


def capture_report(path, capture, messages):
    """Report on captured output.
    :type path: str
    :type capture: Capture
    :type messages: set[str]
    """
    if capture.stdout.getvalue():
        message = '%s:%d:%d: %s: %s' % (path, 0, 0, 'Output', 'Import resulted in output to stdout.')
        report_message(message, messages)

    if capture.stderr.getvalue():
        message = '%s:%d:%d: %s: %s' % (path, 0, 0, 'Output', 'Import resulted in output to stderr.')
        report_message(message, messages)


def report_message(message, messages):
    """Report message if not already reported.
    :type message: str
    :type messages: set[str]
    """
    if message not in messages:
        messages.add(message)
        print(message)


@contextlib.contextmanager
def capture_output(capture):
    """Capture sys.stdout and sys.stderr.
    :type capture: Capture
    """
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    sys.stdout = capture.stdout
    sys.stderr = capture.stderr

    try:
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


if __name__ == '__main__':
    main()
