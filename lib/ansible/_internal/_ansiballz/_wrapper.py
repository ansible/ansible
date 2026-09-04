# shebang placeholder

from __future__ import annotations

# For test-module.py script to tell this is a ANSIBALLZ_WRAPPER
_ANSIBALLZ_WRAPPER = True

# This code is part of Ansible, but is an independent component.
# The code in this particular templatable string, and this templatable string
# only, is BSD licensed.  Modules which end up using this snippet, which is
# dynamically combined together by Ansible still belong to the author of the
# module, and they may assign their own license to the complete work.
#
# Copyright (c), James Cammarata, 2016
# Copyright (c), Toshio Kuratomi, 2016
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import os.path

# Access to the working directory is required by Python when using pipelining, as well as for the coverage module.
# Some platforms, such as macOS, may not allow querying the working directory when using become to drop privileges.
try:
    os.getcwd()
except OSError:
    try:
        os.chdir(os.path.expanduser('~'))
    except OSError:
        os.chdir('/')

import sys
import __main__

# For some distros and python versions we pick up this script in the temporary
# directory.  This leads to problems when the ansible module masks a python
# library that another import needs.  We have not figured out what about the
# specific distros and python versions causes this to behave differently.
#
# Tested distros:
# Fedora23 with python3.4  Works
# Ubuntu15.10 with python2.7  Works
# Ubuntu15.10 with python3.4  Fails without this
# Ubuntu16.04.1 with python3.5  Fails without this
# To test on another platform:
# * use the copy module (since this shadows the stdlib copy module)
# * Turn off pipelining
# * Make sure that the destination file does not exist
# * ansible ubuntu16-test -m copy -a 'src=/etc/motd dest=/var/tmp/m'
# This will traceback in shutil.  Looking at the complete traceback will show
# that shutil is importing copy which finds the ansible module instead of the
# stdlib module
scriptdir = None
try:
    scriptdir = os.path.dirname(os.path.realpath(__main__.__file__))
except (AttributeError, OSError):
    # Some platforms don't set __file__ when reading from stdin
    # OSX raises OSError if using abspath() in a directory we don't have
    # permission to read (realpath calls abspath)
    pass

# Strip cwd from sys.path to avoid potential permissions issues
excludes = {'', '.', scriptdir}
sys.path = [p for p in sys.path if p not in excludes]

import datetime
import io
import tempfile
import zipfile
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from types import ModuleType

# deprecated: description='ResourceReader moved from importlib.abc to importlib.resources.abc in Python 3.13' python_version='3.13'
try:
    from importlib.resources.abc import ResourceReader
except ImportError:
    from importlib.abc import ResourceReader  # type: ignore[attr-defined,no-redef]


class InMemoryZipImporter(MetaPathFinder, Loader):
    """Import modules directly from in-memory zip bytes."""

    def __init__(self, zip_bytes: bytes) -> None:
        self._zipfile = zipfile.ZipFile(io.BytesIO(zip_bytes))
        self._modules: set[str] = set()
        self._packages: set[str] = set()
        self._code_cache: dict[str, bytes] = {}

        for name in self._zipfile.namelist():
            if not name.endswith('.py'):
                continue

            if name.endswith('__init__.py'):
                pkg = name[:-12].replace('/', '.')
                if pkg:
                    self._packages.add(pkg)
                    self._modules.add(pkg)
            else:
                mod = name[:-3].replace('/', '.')
                self._modules.add(mod)

            parts = (pkg if name.endswith('__init__.py') else mod).split('.')
            for i in range(1, len(parts)):
                parent = '.'.join(parts[:i])
                if parent:
                    self._packages.add(parent)

    def find_spec(self, fullname: str, path, target=None) -> ModuleSpec | None:
        if fullname not in self._modules:
            return None

        is_package = fullname in self._packages

        return ModuleSpec(
            name=fullname,
            loader=self,
            origin=f'<ansiballz>/{fullname.replace(".", "/")}{"/__init__.py" if is_package else ".py"}',
            is_package=is_package,
        )

    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        return None

    def exec_module(self, module: ModuleType) -> None:
        fullname = module.__name__
        is_package = fullname in self._packages

        if is_package:
            filepath = fullname.replace('.', '/') + '/__init__.py'
        else:
            filepath = fullname.replace('.', '/') + '.py'

        if filepath not in self._code_cache:
            self._code_cache[filepath] = self._zipfile.read(filepath)

        code_bytes = self._code_cache[filepath]
        module.__file__ = f'<ansiballz>/{filepath}'
        if is_package:
            module.__path__ = [f'<ansiballz>/{fullname.replace(".", "/")}']

        code = compile(code_bytes, module.__file__, 'exec', dont_inherit=True)
        exec(code, module.__dict__)

    def get_resource_reader(self, fullname: str):
        if fullname not in self._packages:
            return None
        return _InMemoryResourceReader(self._zipfile, fullname)

    def get_data(self, path: str) -> bytes:
        if path.startswith('<ansiballz>/'):
            path = path[13:]
        try:
            return self._zipfile.read(path)
        except KeyError as e:
            raise OSError(f'Resource not found: {path}') from e

    def get_source(self, fullname: str) -> str:
        """Get the source code for a module (for inspect.getsource() support)."""
        is_package = fullname in self._packages
        if is_package:
            filepath = fullname.replace('.', '/') + '/__init__.py'
        else:
            filepath = fullname.replace('.', '/') + '.py'

        try:
            code_bytes = self._zipfile.read(filepath)
            return code_bytes.decode('utf-8')
        except KeyError as e:
            raise ImportError(f'Source not found for {fullname!r}') from e


class _InMemoryResourceReader(ResourceReader):
    def __init__(self, zipfile: zipfile.ZipFile, package: str):
        self._zipfile = zipfile
        self._package = package
        self._package_path = package.replace('.', '/')

    def open_resource(self, resource: str):
        path = f'{self._package_path}/{resource}'
        try:
            data = self._zipfile.read(path)
            return io.BytesIO(data)
        except KeyError as e:
            raise FileNotFoundError(f'Resource not found: {resource}') from e

    def resource_path(self, resource: str):
        """Get the file system path to a resource.

        Since resources are in memory, this raises FileNotFoundError to signal
        that importlib.resources.as_file() should extract the resource.
        """
        raise FileNotFoundError(f'Resource {resource} is in memory')

    def is_resource(self, name: str) -> bool:
        if '/' in name:
            return False
        path = f'{self._package_path}/{name}'
        try:
            info = self._zipfile.getinfo(path)
            return not info.is_dir()
        except KeyError:
            return False

    def contents(self):
        prefix = self._package_path + '/'
        seen = set()
        for name in self._zipfile.namelist():
            if name.startswith(prefix):
                relative = name[len(prefix) :]
                if '/' in relative:
                    continue
                if not self.is_resource(relative):
                    continue
                if relative not in seen:
                    seen.add(relative)
                    yield relative


def extract_zip(zip_bytes: bytes, dest_dir: str | None = None) -> str:
    """Extract zip file to a directory, creating a tempdir if dest_dir is not provided."""
    if dest_dir is None:
        dest_dir = tempfile.mkdtemp()

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for filename in z.namelist():
            if filename.startswith('/'):
                raise Exception('Something wrong with this module zip file: should not contain absolute paths')

            dest_filename = os.path.join(dest_dir, filename)
            if dest_filename.endswith(os.path.sep) and not os.path.exists(dest_filename):
                os.makedirs(dest_filename)
            else:
                directory = os.path.dirname(dest_filename)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(dest_filename, 'wb') as writer:
                    writer.write(z.read(filename))

    return dest_dir


def invoke_module(zip_bytes: bytes, encoded_params: bytes) -> None:
    importer = InMemoryZipImporter(zip_bytes)
    sys.meta_path.insert(0, importer)

    __main__.ANSIBLE_MODULE_PARAMS = encoded_params.decode('utf-8')
    __main__._ansiballz_zip_data = zip_bytes

    main_code = importer._zipfile.read('__main__.py')
    exec(compile(main_code, '<ansiballz>/__main__.py', 'exec'))


def probe_imports(zip_bytes: bytes, module_names: list[str]) -> int:
    """Probe if modules can be imported from the zip. Returns 0 on success, 1 on failure."""
    try:
        importer = InMemoryZipImporter(zip_bytes)
        sys.meta_path.insert(0, importer)

        for module_name in module_names:
            __import__(module_name)

        return 0
    except Exception:
        return 1


def debug(command: str, zip_bytes: bytes, encoded_params: bytes) -> None:
    # The code here normally doesn't run.  It's only used for debugging on the
    # remote machine.
    #
    # The subcommands in this function make it easier to debug ansiballz
    # modules.  Here's the basic steps:
    #
    # Run ansible with the environment variable: ANSIBLE_KEEP_REMOTE_FILES=1 and -vvv
    # to save the module file remotely::
    #   $ ANSIBLE_KEEP_REMOTE_FILES=1 ansible host1 -m ping -a 'data=october' -vvv
    #
    # Part of the verbose output will tell you where on the remote machine the
    # module was written to::
    #   [...]
    #   <host1> SSH: EXEC ssh -C -q -o ControlMaster=auto -o ControlPersist=60s -o KbdInteractiveAuthentication=no -o
    #   PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey -o PasswordAuthentication=no -o ConnectTimeout=10 -o
    #   ControlPath=/home/badger/.ansible/cp/ansible-ssh-%h-%p-%r -tt rhel7 '/bin/sh -c '"'"'LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
    #   LC_MESSAGES=en_US.UTF-8 /usr/bin/python /home/badger/.ansible/tmp/ansible-tmp-1461173013.93-9076457629738/ping'"'"''
    #   [...]
    #
    # Login to the remote machine and run the module file via from the previous
    # step with the explode subcommand to extract the module payload into
    # source files::
    #   $ ssh host1
    #   $ /usr/bin/python /home/badger/.ansible/tmp/ansible-tmp-1461173013.93-9076457629738/ping explode
    #   Module expanded into:
    #   /home/badger/.ansible/tmp/ansible-tmp-1461173408.08-279692652635227/ansible
    #
    # You can now edit the source files to instrument the code or experiment with
    # different parameter values.  When you're ready to run the code you've modified
    # (instead of the code from the actual zipped module), use the execute subcommand like this::
    #   $ /usr/bin/python /home/badger/.ansible/tmp/ansible-tmp-1461173013.93-9076457629738/ping execute

    # Okay to use __file__ here because we're running from a kept file
    basedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'debug_dir')
    args_path = os.path.join(basedir, 'args')

    if command == 'explode':
        extract_zip(zip_bytes, basedir)

        with open(args_path, 'wb') as writer:
            writer.write(encoded_params)

        print('Module expanded into:')
        print(basedir)

    elif command == 'execute':
        # Execute the exploded code instead of executing the module from the
        # embedded zip.  This allows people to easily run their modified
        # code on the remote machine to see how changes will affect it.

        # Set pythonpath to the debug dir
        sys.path.insert(0, basedir)

        # read in the args file which the user may have modified
        with open(args_path, 'rb') as reader:
            encoded_params = reader.read()

        # Make params available
        __main__.ANSIBLE_MODULE_PARAMS = encoded_params.decode('utf-8')

        # Import and execute __main__.py from the exploded directory
        import importlib.util

        spec = importlib.util.spec_from_file_location('__main__', os.path.join(basedir, '__main__.py'))
        if spec and spec.loader:
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
        else:
            raise Exception('Could not load __main__.py from debug directory')

    else:
        print(f'FATAL: Unknown debug command {command!r}.  Doing nothing.')


def _ansiballz_main(
    zip_data: bytes,
    ansible_module: str,
    module_fqn: str,
    params: str,
    profile: str,
    date_time: datetime.datetime,
    extensions: dict[str, dict[str, object]],
    rlimit_nofile: int,
    wrapper_source: str = '',
) -> None:
    if rlimit_nofile:
        import resource

        existing_soft, existing_hard = resource.getrlimit(resource.RLIMIT_NOFILE)

        # adjust soft limit subject to existing hard limit
        requested_soft = min(existing_hard, rlimit_nofile)

        if requested_soft != existing_soft:
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, (requested_soft, existing_hard))
            except ValueError:
                # some platforms (eg macOS) lie about their hard limit
                pass

    #
    # See comments in the debug() method for information on debugging
    #

    encoded_params = params.encode()

    # Store wrapper source on __main__ for probe and respawn
    __main__._ansiballz_wrapper_source = wrapper_source

    # Check for debug and probe commands
    if len(sys.argv) >= 2:
        if sys.argv[1] == 'probe' and len(sys.argv) == 3:
            module_names = sys.argv[2].split(',')
            sys.exit(probe_imports(zip_data, module_names))
        elif len(sys.argv) == 2:
            debug(sys.argv[1], zip_data, encoded_params)
        else:
            invoke_module(zip_data, encoded_params)
    else:
        invoke_module(zip_data, encoded_params)
