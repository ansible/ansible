#!/usr/bin/env python
"""Import the given python module(s) and report error(s) encountered."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def main():
    """
    Main program function used to isolate globals from imported code.
    Changes to globals in imported modules on Python 2.x will overwrite our own globals.
    """
    import ansible
    import contextlib
    import datetime
    import json
    import os
    import re
    import runpy
    import subprocess
    import sys
    import traceback
    import types
    import warnings

    ansible_path = os.path.dirname(os.path.dirname(ansible.__file__))
    temp_path = os.environ['SANITY_TEMP_PATH'] + os.path.sep
    external_python = os.environ.get('SANITY_EXTERNAL_PYTHON') or sys.executable
    collection_full_name = os.environ.get('SANITY_COLLECTION_FULL_NAME')
    collection_root = os.environ.get('ANSIBLE_COLLECTIONS_PATH')

    try:
        # noinspection PyCompatibility
        from importlib import import_module
    except ImportError:
        def import_module(name):
            __import__(name)
            return sys.modules[name]

    try:
        # noinspection PyCompatibility
        from StringIO import StringIO
    except ImportError:
        from io import StringIO

    if collection_full_name:
        # allow importing code from collections when testing a collection
        from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native, text_type
        from ansible.utils.collection_loader._collection_finder import _AnsibleCollectionFinder
        from ansible.utils.collection_loader import _collection_finder

        yaml_to_json_path = os.path.join(os.path.dirname(__file__), 'yaml_to_json.py')
        yaml_to_dict_cache = {}

        # unique ISO date marker matching the one present in yaml_to_json.py
        iso_date_marker = 'isodate:f23983df-f3df-453c-9904-bcd08af468cc:'
        iso_date_re = re.compile('^%s([0-9]{4})-([0-9]{2})-([0-9]{2})$' % iso_date_marker)

        def parse_value(value):
            """Custom value parser for JSON deserialization that recognizes our internal ISO date format."""
            if isinstance(value, text_type):
                match = iso_date_re.search(value)

                if match:
                    value = datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

            return value

        def object_hook(data):
            """Object hook for custom ISO date deserialization from JSON."""
            return dict((key, parse_value(value)) for key, value in data.items())

        def yaml_to_dict(yaml, content_id):
            """
            Return a Python dict version of the provided YAML.
            Conversion is done in a subprocess since the current Python interpreter does not have access to PyYAML.
            """
            if content_id in yaml_to_dict_cache:
                return yaml_to_dict_cache[content_id]

            try:
                cmd = [external_python, yaml_to_json_path]
                proc = subprocess.Popen([to_bytes(c) for c in cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout_bytes, stderr_bytes = proc.communicate(to_bytes(yaml))

                if proc.returncode != 0:
                    raise Exception('command %s failed with return code %d: %s' % ([to_native(c) for c in cmd], proc.returncode, to_native(stderr_bytes)))

                data = yaml_to_dict_cache[content_id] = json.loads(to_text(stdout_bytes), object_hook=object_hook)

                return data
            except Exception as ex:
                raise Exception('internal importer error - failed to parse yaml: %s' % to_native(ex))

        _collection_finder._meta_yml_to_dict = yaml_to_dict  # pylint: disable=protected-access

        collection_loader = _AnsibleCollectionFinder(paths=[collection_root])
        collection_loader._install()  # pylint: disable=protected-access
    else:
        # do not support collection loading when not testing a collection
        collection_loader = None

    # remove all modules under the ansible package
    list(map(sys.modules.pop, [m for m in sys.modules if m.partition('.')[0] == ansible.__name__]))

    # pre-load an empty ansible package to prevent unwanted code in __init__.py from loading
    # this more accurately reflects the environment that AnsiballZ runs modules under
    # it also avoids issues with imports in the ansible package that are not allowed
    ansible_module = types.ModuleType(ansible.__name__)
    ansible_module.__file__ = ansible.__file__
    ansible_module.__path__ = ansible.__path__
    ansible_module.__package__ = ansible.__package__

    sys.modules[ansible.__name__] = ansible_module

    class ImporterAnsibleModuleException(Exception):
        """Exception thrown during initialization of ImporterAnsibleModule."""

    class ImporterAnsibleModule:
        """Replacement for AnsibleModule to support import testing."""
        def __init__(self, *args, **kwargs):
            raise ImporterAnsibleModuleException()

    class ImportBlacklist:
        """Blacklist inappropriate imports."""
        def __init__(self, path, name):
            self.path = path
            self.name = name
            self.loaded_modules = set()

        def find_module(self, fullname, path=None):
            """Return self if the given fullname is blacklisted, otherwise return None.
            :param fullname: str
            :param path: str
            :return: ImportBlacklist | None
            """
            if fullname in self.loaded_modules:
                return None  # ignore modules that are already being loaded

            if is_name_in_namepace(fullname, ['ansible']):
                if fullname in ('ansible.module_utils.basic', 'ansible.module_utils.common.removed'):
                    return self  # intercept loading so we can modify the result

                if is_name_in_namepace(fullname, ['ansible.module_utils', self.name]):
                    return None  # module_utils and module under test are always allowed

                if any(os.path.exists(candidate_path) for candidate_path in convert_ansible_name_to_absolute_paths(fullname)):
                    return self  # blacklist ansible files that exist

                return None  # ansible file does not exist, do not blacklist

            if is_name_in_namepace(fullname, ['ansible_collections']):
                if not collection_loader:
                    return self  # blacklist collections when we are not testing a collection

                if is_name_in_namepace(fullname, ['ansible_collections...plugins.module_utils', self.name]):
                    return None  # module_utils and module under test are always allowed

                if collection_loader.find_module(fullname, path):
                    return self  # blacklist collection files that exist

                return None  # collection file does not exist, do not blacklist

            # not a namespace we care about
            return None

        def load_module(self, fullname):
            """Raise an ImportError.
            :type fullname: str
            """
            if fullname == 'ansible.module_utils.basic':
                module = self.__load_module(fullname)

                # stop Ansible module execution during AnsibleModule instantiation
                module.AnsibleModule = ImporterAnsibleModule
                # no-op for _load_params since it may be called before instantiating AnsibleModule
                module._load_params = lambda *args, **kwargs: {}  # pylint: disable=protected-access

                return module

            if fullname == 'ansible.module_utils.common.removed':
                module = self.__load_module(fullname)

                # no-op for removed_module since it is called in place of AnsibleModule instantiation
                module.removed_module = lambda *args, **kwargs: None

                return module

            raise ImportError('import of "%s" is not allowed in this context' % fullname)

        def __load_module(self, fullname):
            """Load the requested module while avoiding infinite recursion.
            :type fullname: str
            :rtype: module
            """
            self.loaded_modules.add(fullname)
            return import_module(fullname)

    def run():
        """Main program function."""
        base_dir = os.getcwd()
        messages = set()

        for path in sys.argv[1:] or sys.stdin.read().splitlines():
            name = convert_relative_path_to_name(path)
            test_python_module(path, name, base_dir, messages)

        if messages:
            sys.exit(10)

    def test_python_module(path, name, base_dir, messages):
        """Test the given python module by importing it.
        :type path: str
        :type name: str
        :type base_dir: str
        :type messages: set[str]
        """
        if name in sys.modules:
            return  # cannot be tested because it has already been loaded

        is_ansible_module = (path.startswith('lib/ansible/modules/') or path.startswith('plugins/modules/')) and os.path.basename(path) != '__init__.py'
        run_main = is_ansible_module

        if path == 'lib/ansible/modules/async_wrapper.py':
            # async_wrapper is a non-standard Ansible module (does not use AnsibleModule) so we cannot test the main function
            run_main = False

        capture_normal = Capture()
        capture_main = Capture()

        try:
            with monitor_sys_modules(path, messages):
                with blacklist_imports(path, name, messages):
                    with capture_output(capture_normal):
                        import_module(name)

            if run_main:
                with monitor_sys_modules(path, messages):
                    with blacklist_imports(path, name, messages):
                        with capture_output(capture_main):
                            runpy.run_module(name, run_name='__main__', alter_sys=True)
        except ImporterAnsibleModuleException:
            # module instantiated AnsibleModule without raising an exception
            pass
        except BaseException as ex:  # pylint: disable=locally-disabled, broad-except
            # intentionally catch all exceptions, including calls to sys.exit
            exc_type, _exc, exc_tb = sys.exc_info()
            message = str(ex)
            results = list(reversed(traceback.extract_tb(exc_tb)))
            line = 0
            offset = 0
            full_path = os.path.join(base_dir, path)
            base_path = base_dir + os.path.sep
            source = None

            # avoid line wraps in messages
            message = re.sub(r'\n *', ': ', message)

            for result in results:
                if result[0] == full_path:
                    # save the line number for the file under test
                    line = result[1] or 0

                if not source and result[0].startswith(base_path) and not result[0].startswith(temp_path):
                    # save the first path and line number in the traceback which is in our source tree
                    source = (os.path.relpath(result[0], base_path), result[1] or 0, 0)

            if isinstance(ex, SyntaxError):
                # SyntaxError has better information than the traceback
                if ex.filename == full_path:  # pylint: disable=locally-disabled, no-member
                    # syntax error was reported in the file under test
                    line = ex.lineno or 0  # pylint: disable=locally-disabled, no-member
                    offset = ex.offset or 0  # pylint: disable=locally-disabled, no-member
                elif ex.filename.startswith(base_path) and not ex.filename.startswith(temp_path):  # pylint: disable=locally-disabled, no-member
                    # syntax error was reported in our source tree
                    source = (os.path.relpath(ex.filename, base_path), ex.lineno or 0, ex.offset or 0)  # pylint: disable=locally-disabled, no-member

                # remove the filename and line number from the message
                # either it was extracted above, or it's not really useful information
                message = re.sub(r' \(.*?, line [0-9]+\)$', '', message)

            if source and source[0] != path:
                message += ' (at %s:%d:%d)' % (source[0], source[1], source[2])

            report_message(path, line, offset, 'traceback', '%s: %s' % (exc_type.__name__, message), messages)
        finally:
            capture_report(path, capture_normal, messages)
            capture_report(path, capture_main, messages)

    def is_name_in_namepace(name, namespaces):
        """Returns True if the given name is one of the given namespaces, otherwise returns False."""
        name_parts = name.split('.')

        for namespace in namespaces:
            namespace_parts = namespace.split('.')
            length = min(len(name_parts), len(namespace_parts))

            truncated_name = name_parts[0:length]
            truncated_namespace = namespace_parts[0:length]

            # empty parts in the namespace are treated as wildcards
            # to simplify the comparison, use those empty parts to indicate the positions in the name to be empty as well
            for idx, part in enumerate(truncated_namespace):
                if not part:
                    truncated_name[idx] = part

            # example: name=ansible, allowed_name=ansible.module_utils
            # example: name=ansible.module_utils.system.ping, allowed_name=ansible.module_utils
            if truncated_name == truncated_namespace:
                return True

        return False

    def check_sys_modules(path, before, messages):
        """Check for unwanted changes to sys.modules.
        :type path: str
        :type before: dict[str, module]
        :type messages: set[str]
        """
        after = sys.modules
        removed = set(before.keys()) - set(after.keys())
        changed = set(key for key, value in before.items() if key in after and value != after[key])

        # additions are checked by our custom PEP 302 loader, so we don't need to check them again here

        for module in sorted(removed):
            report_message(path, 0, 0, 'unload', 'unloading of "%s" in sys.modules is not supported' % module, messages)

        for module in sorted(changed):
            report_message(path, 0, 0, 'reload', 'reloading of "%s" in sys.modules is not supported' % module, messages)

    def convert_ansible_name_to_absolute_paths(name):
        """Calculate the module path from the given name.
        :type name: str
        :rtype: list[str]
        """
        return [
            os.path.join(ansible_path, name.replace('.', os.path.sep)),
            os.path.join(ansible_path, name.replace('.', os.path.sep)) + '.py',
        ]

    def convert_relative_path_to_name(path):
        """Calculate the module name from the given path.
        :type path: str
        :rtype: str
        """
        if path.endswith('/__init__.py'):
            clean_path = os.path.dirname(path)
        else:
            clean_path = path

        clean_path = os.path.splitext(clean_path)[0]

        name = clean_path.replace(os.path.sep, '.')

        if collection_loader:
            # when testing collections the relative paths (and names) being tested are within the collection under test
            name = 'ansible_collections.%s.%s' % (collection_full_name, name)
        else:
            # when testing ansible all files being imported reside under the lib directory
            name = name[len('lib/'):]

        return name

    class Capture:
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
            first = capture.stdout.getvalue().strip().splitlines()[0].strip()
            report_message(path, 0, 0, 'stdout', first, messages)

        if capture.stderr.getvalue():
            first = capture.stderr.getvalue().strip().splitlines()[0].strip()
            report_message(path, 0, 0, 'stderr', first, messages)

    def report_message(path, line, column, code, message, messages):
        """Report message if not already reported.
        :type path: str
        :type line: int
        :type column: int
        :type code: str
        :type message: str
        :type messages: set[str]
        """
        message = '%s:%d:%d: %s: %s' % (path, line, column, code, message)

        if message not in messages:
            messages.add(message)
            print(message)

    @contextlib.contextmanager
    def blacklist_imports(path, name, messages):
        """Blacklist imports.
        :type path: str
        :type name: str
        :type messages: set[str]
        """
        blacklist = ImportBlacklist(path, name)

        sys.meta_path.insert(0, blacklist)
        sys.path_importer_cache.clear()

        try:
            yield
        finally:
            if sys.meta_path[0] != blacklist:
                report_message(path, 0, 0, 'metapath', 'changes to sys.meta_path[0] are not permitted', messages)

            while blacklist in sys.meta_path:
                sys.meta_path.remove(blacklist)

            sys.path_importer_cache.clear()

    @contextlib.contextmanager
    def monitor_sys_modules(path, messages):
        """Monitor sys.modules for unwanted changes, reverting any additions made to our own namespaces."""
        snapshot = sys.modules.copy()

        try:
            yield
        finally:
            check_sys_modules(path, snapshot, messages)

            for key in set(sys.modules.keys()) - set(snapshot.keys()):
                if is_name_in_namepace(key, ('ansible', 'ansible_collections')):
                    del sys.modules[key]  # only unload our own code since we know it's native Python

    @contextlib.contextmanager
    def capture_output(capture):
        """Capture sys.stdout and sys.stderr.
        :type capture: Capture
        """
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        sys.stdout = capture.stdout
        sys.stderr = capture.stderr

        # clear all warnings registries to make all warnings available
        for module in sys.modules.values():
            try:
                module.__warningregistry__.clear()
            except AttributeError:
                pass

        with warnings.catch_warnings():
            warnings.simplefilter('error')

            try:
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

    run()


if __name__ == '__main__':
    main()
