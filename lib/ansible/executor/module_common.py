# (c) 2013-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015 Toshio Kuratomi <tkuratomi@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast
import base64
import datetime
import imp
import json
import os
import shlex
import zipfile
import random
import re
from io import BytesIO

from ansible.release import __version__, __author__
from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.plugins.loader import module_utils_loader, ps_module_utils_loader
from ansible.plugins.shell.powershell import async_watchdog, async_wrapper, become_wrapper, leaf_exec, exec_wrapper
# Must import strategy and use write_locks from there
# If we import write_locks directly then we end up binding a
# variable to the object and then it never gets updated.
from ansible.executor import action_write_locks

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


REPLACER = b"#<<INCLUDE_ANSIBLE_MODULE_COMMON>>"
REPLACER_VERSION = b"\"<<ANSIBLE_VERSION>>\""
REPLACER_COMPLEX = b"\"<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>\""
REPLACER_WINDOWS = b"# POWERSHELL_COMMON"
REPLACER_JSONARGS = b"<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>"
REPLACER_SELINUX = b"<<SELINUX_SPECIAL_FILESYSTEMS>>"

# We could end up writing out parameters with unicode characters so we need to
# specify an encoding for the python source file
ENCODING_STRING = u'# -*- coding: utf-8 -*-'
b_ENCODING_STRING = b'# -*- coding: utf-8 -*-'

# module_common is relative to module_utils, so fix the path
_MODULE_UTILS_PATH = os.path.join(os.path.dirname(__file__), '..', 'module_utils')

# ******************************************************************************

ANSIBALLZ_TEMPLATE = u'''%(shebang)s
%(coding)s
ANSIBALLZ_WRAPPER = True # For test-module script to tell this is a ANSIBALLZ_WRAPPER
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
if scriptdir is not None:
    sys.path = [p for p in sys.path if p != scriptdir]

import base64
import shutil
import zipfile
import tempfile
import subprocess

if sys.version_info < (3,):
    bytes = str
    PY3 = False
else:
    unicode = str
    PY3 = True
try:
    # Python-2.6+
    from io import BytesIO as IOStream
except ImportError:
    # Python < 2.6
    from StringIO import StringIO as IOStream

ZIPDATA = """%(zipdata)s"""

def invoke_module(module, modlib_path, json_params):
    pythonpath = os.environ.get('PYTHONPATH')
    if pythonpath:
        os.environ['PYTHONPATH'] = ':'.join((modlib_path, pythonpath))
    else:
        os.environ['PYTHONPATH'] = modlib_path

    p = subprocess.Popen([%(interpreter)s, module], env=os.environ, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    (stdout, stderr) = p.communicate(json_params)

    if not isinstance(stderr, (bytes, unicode)):
        stderr = stderr.read()
    if not isinstance(stdout, (bytes, unicode)):
        stdout = stdout.read()
    if PY3:
        sys.stderr.buffer.write(stderr)
        sys.stdout.buffer.write(stdout)
    else:
        sys.stderr.write(stderr)
        sys.stdout.write(stdout)
    return p.returncode

def debug(command, zipped_mod, json_params):
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
    #   ControlPath=/home/badger/.ansible/cp/ansible-ssh-%%h-%%p-%%r -tt rhel7 '/bin/sh -c '"'"'LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
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
    script_path = os.path.join(basedir, 'ansible_module_%(ansible_module)s.py')

    if command == 'explode':
        # transform the ZIPDATA into an exploded directory of code and then
        # print the path to the code.  This is an easy way for people to look
        # at the code on the remote machine for debugging it in that
        # environment
        z = zipfile.ZipFile(zipped_mod)
        for filename in z.namelist():
            if filename.startswith('/'):
                raise Exception('Something wrong with this module zip file: should not contain absolute paths')

            dest_filename = os.path.join(basedir, filename)
            if dest_filename.endswith(os.path.sep) and not os.path.exists(dest_filename):
                os.makedirs(dest_filename)
            else:
                directory = os.path.dirname(dest_filename)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                f = open(dest_filename, 'wb')
                f.write(z.read(filename))
                f.close()

        # write the args file
        f = open(args_path, 'wb')
        f.write(json_params)
        f.close()

        print('Module expanded into:')
        print('%%s' %% basedir)
        exitcode = 0

    elif command == 'execute':
        # Execute the exploded code instead of executing the module from the
        # embedded ZIPDATA.  This allows people to easily run their modified
        # code on the remote machine to see how changes will affect it.
        # This differs slightly from default Ansible execution of Python modules
        # as it passes the arguments to the module via a file instead of stdin.

        # Set pythonpath to the debug dir
        pythonpath = os.environ.get('PYTHONPATH')
        if pythonpath:
            os.environ['PYTHONPATH'] = ':'.join((basedir, pythonpath))
        else:
            os.environ['PYTHONPATH'] = basedir

        p = subprocess.Popen([%(interpreter)s, script_path, args_path],
                env=os.environ, shell=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        (stdout, stderr) = p.communicate()

        if not isinstance(stderr, (bytes, unicode)):
            stderr = stderr.read()
        if not isinstance(stdout, (bytes, unicode)):
            stdout = stdout.read()
        if PY3:
            sys.stderr.buffer.write(stderr)
            sys.stdout.buffer.write(stdout)
        else:
            sys.stderr.write(stderr)
            sys.stdout.write(stdout)
        return p.returncode

    elif command == 'excommunicate':
        # This attempts to run the module in-process (by importing a main
        # function and then calling it).  It is not the way ansible generally
        # invokes the module so it won't work in every case.  It is here to
        # aid certain debuggers which work better when the code doesn't change
        # from one process to another but there may be problems that occur
        # when using this that are only artifacts of how we're invoking here,
        # not actual bugs (as they don't affect the real way that we invoke
        # ansible modules)

        # stub the args and python path
        sys.argv = ['%(ansible_module)s', args_path]
        sys.path.insert(0, basedir)

        from ansible_module_%(ansible_module)s import main
        main()
        print('WARNING: Module returned to wrapper instead of exiting')
        sys.exit(1)
    else:
        print('WARNING: Unknown debug command.  Doing nothing.')
        exitcode = 0

    return exitcode

if __name__ == '__main__':
    #
    # See comments in the debug() method for information on debugging
    #

    ANSIBALLZ_PARAMS = %(params)s
    if PY3:
        ANSIBALLZ_PARAMS = ANSIBALLZ_PARAMS.encode('utf-8')
    try:
        # There's a race condition with the controller removing the
        # remote_tmpdir and this module executing under async.  So we cannot
        # store this in remote_tmpdir (use system tempdir instead)
        temp_path = tempfile.mkdtemp(prefix='ansible_')

        zipped_mod = os.path.join(temp_path, 'ansible_modlib.zip')
        modlib = open(zipped_mod, 'wb')
        modlib.write(base64.b64decode(ZIPDATA))
        modlib.close()

        if len(sys.argv) == 2:
            exitcode = debug(sys.argv[1], zipped_mod, ANSIBALLZ_PARAMS)
        else:
            z = zipfile.ZipFile(zipped_mod, mode='r')
            module = os.path.join(temp_path, 'ansible_module_%(ansible_module)s.py')
            f = open(module, 'wb')
            f.write(z.read('ansible_module_%(ansible_module)s.py'))
            f.close()

            # When installed via setuptools (including python setup.py install),
            # ansible may be installed with an easy-install.pth file.  That file
            # may load the system-wide install of ansible rather than the one in
            # the module.  sitecustomize is the only way to override that setting.
            z = zipfile.ZipFile(zipped_mod, mode='a')

            # py3: zipped_mod will be text, py2: it's bytes.  Need bytes at the end
            sitecustomize = u'import sys\\nsys.path.insert(0,"%%s")\\n' %%  zipped_mod
            sitecustomize = sitecustomize.encode('utf-8')
            # Use a ZipInfo to work around zipfile limitation on hosts with
            # clocks set to a pre-1980 year (for instance, Raspberry Pi)
            zinfo = zipfile.ZipInfo()
            zinfo.filename = 'sitecustomize.py'
            zinfo.date_time = ( %(year)i, %(month)i, %(day)i, %(hour)i, %(minute)i, %(second)i)
            z.writestr(zinfo, sitecustomize)
            z.close()

            exitcode = invoke_module(module, zipped_mod, ANSIBALLZ_PARAMS)
    finally:
        try:
            shutil.rmtree(temp_path)
        except (NameError, OSError):
            # tempdir creation probably failed
            pass
    sys.exit(exitcode)
'''


def _strip_comments(source):
    # Strip comments and blank lines from the wrapper
    buf = []
    for line in source.splitlines():
        l = line.strip()
        if not l or l.startswith(u'#'):
            continue
        buf.append(line)
    return u'\n'.join(buf)


if C.DEFAULT_KEEP_REMOTE_FILES:
    # Keep comments when KEEP_REMOTE_FILES is set.  That way users will see
    # the comments with some nice usage instructions
    ACTIVE_ANSIBALLZ_TEMPLATE = ANSIBALLZ_TEMPLATE
else:
    # ANSIBALLZ_TEMPLATE stripped of comments for smaller over the wire size
    ACTIVE_ANSIBALLZ_TEMPLATE = _strip_comments(ANSIBALLZ_TEMPLATE)


class ModuleDepFinder(ast.NodeVisitor):
    # Caveats:
    # This code currently does not handle:
    # * relative imports from py2.6+ from . import urls
    IMPORT_PREFIX_SIZE = len('ansible.module_utils.')

    def __init__(self, *args, **kwargs):
        """
        Walk the ast tree for the python module.

        Save submodule[.submoduleN][.identifier] into self.submodules

        self.submodules will end up with tuples like:
          - ('basic',)
          - ('urls', 'fetch_url')
          - ('database', 'postgres')
          - ('database', 'postgres', 'quote')

        It's up to calling code to determine whether the final element of the
        dotted strings are module names or something else (function, class, or
        variable names)
        """
        super(ModuleDepFinder, self).__init__(*args, **kwargs)
        self.submodules = set()

    def visit_Import(self, node):
        # import ansible.module_utils.MODLIB[.MODLIBn] [as asname]
        for alias in (a for a in node.names if a.name.startswith('ansible.module_utils.')):
            py_mod = alias.name[self.IMPORT_PREFIX_SIZE:]
            py_mod = tuple(py_mod.split('.'))
            self.submodules.add(py_mod)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # Specialcase: six is a special case because of its
        # import logic
        if node.names[0].name == '_six':
            self.submodules.add(('_six',))
        elif node.module.startswith('ansible.module_utils'):
            where_from = node.module[self.IMPORT_PREFIX_SIZE:]
            if where_from:
                # from ansible.module_utils.MODULE1[.MODULEn] import IDENTIFIER [as asname]
                # from ansible.module_utils.MODULE1[.MODULEn] import MODULEn+1 [as asname]
                # from ansible.module_utils.MODULE1[.MODULEn] import MODULEn+1 [,IDENTIFIER] [as asname]
                py_mod = tuple(where_from.split('.'))
                for alias in node.names:
                    self.submodules.add(py_mod + (alias.name,))
            else:
                # from ansible.module_utils import MODLIB [,MODLIB2] [as asname]
                for alias in node.names:
                    self.submodules.add((alias.name,))
        self.generic_visit(node)


def _slurp(path):
    if not os.path.exists(path):
        raise AnsibleError("imported module support code does not exist at %s" % os.path.abspath(path))
    fd = open(path, 'rb')
    data = fd.read()
    fd.close()
    return data


def _get_shebang(interpreter, task_vars, templar, args=tuple()):
    """
    Note not stellar API:
       Returns None instead of always returning a shebang line.  Doing it this
       way allows the caller to decide to use the shebang it read from the
       file rather than trust that we reformatted what they already have
       correctly.
    """
    interpreter_config = u'ansible_%s_interpreter' % os.path.basename(interpreter).strip()

    if interpreter_config not in task_vars:
        return (None, interpreter)

    interpreter = templar.template(task_vars[interpreter_config].strip())
    shebang = u'#!' + interpreter

    if args:
        shebang = shebang + u' ' + u' '.join(args)

    return (shebang, interpreter)


def recursive_finder(name, data, py_module_names, py_module_cache, zf):
    """
    Using ModuleDepFinder, make sure we have all of the module_utils files that
    the module its module_utils files needs.
    """
    # Parse the module and find the imports of ansible.module_utils
    tree = ast.parse(data)
    finder = ModuleDepFinder()
    finder.visit(tree)

    #
    # Determine what imports that we've found are modules (vs class, function.
    # variable names) for packages
    #

    normalized_modules = set()
    # Loop through the imports that we've found to normalize them
    # Exclude paths that match with paths we've already processed
    # (Have to exclude them a second time once the paths are processed)

    module_utils_paths = [p for p in module_utils_loader._get_paths(subdirs=False) if os.path.isdir(p)]
    module_utils_paths.append(_MODULE_UTILS_PATH)
    for py_module_name in finder.submodules.difference(py_module_names):
        module_info = None

        if py_module_name[0] == 'six':
            # Special case the python six library because it messes up the
            # import process in an incompatible way
            module_info = imp.find_module('six', module_utils_paths)
            py_module_name = ('six',)
            idx = 0
        elif py_module_name[0] == '_six':
            # Special case the python six library because it messes up the
            # import process in an incompatible way
            module_info = imp.find_module('_six', [os.path.join(p, 'six') for p in module_utils_paths])
            py_module_name = ('six', '_six')
            idx = 0
        else:
            # Check whether either the last or the second to last identifier is
            # a module name
            for idx in (1, 2):
                if len(py_module_name) < idx:
                    break
                try:
                    module_info = imp.find_module(py_module_name[-idx],
                                                  [os.path.join(p, *py_module_name[:-idx]) for p in module_utils_paths])
                    break
                except ImportError:
                    continue

        # Could not find the module.  Construct a helpful error message.
        if module_info is None:
            msg = ['Could not find imported module support code for %s.  Looked for' % (name,)]
            if idx == 2:
                msg.append('either %s.py or %s.py' % (py_module_name[-1], py_module_name[-2]))
            else:
                msg.append(py_module_name[-1])
            raise AnsibleError(' '.join(msg))

        # Found a byte compiled file rather than source.  We cannot send byte
        # compiled over the wire as the python version might be different.
        # imp.find_module seems to prefer to return source packages so we just
        # error out if imp.find_module returns byte compiled files (This is
        # fragile as it depends on undocumented imp.find_module behaviour)
        if module_info[2][2] not in (imp.PY_SOURCE, imp.PKG_DIRECTORY):
            msg = ['Could not find python source for imported module support code for %s.  Looked for' % name]
            if idx == 2:
                msg.append('either %s.py or %s.py' % (py_module_name[-1], py_module_name[-2]))
            else:
                msg.append(py_module_name[-1])
            raise AnsibleError(' '.join(msg))

        if idx == 2:
            # We've determined that the last portion was an identifier and
            # thus, not part of the module name
            py_module_name = py_module_name[:-1]

        # If not already processed then we've got work to do
        if py_module_name not in py_module_names:
            # If not in the cache, then read the file into the cache
            # We already have a file handle for the module open so it makes
            # sense to read it now
            if py_module_name not in py_module_cache:
                if module_info[2][2] == imp.PKG_DIRECTORY:
                    # Read the __init__.py instead of the module file as this is
                    # a python package
                    normalized_name = py_module_name + ('__init__',)
                    normalized_path = os.path.join(os.path.join(module_info[1], '__init__.py'))
                    normalized_data = _slurp(normalized_path)
                else:
                    normalized_name = py_module_name
                    normalized_path = module_info[1]
                    normalized_data = module_info[0].read()
                    module_info[0].close()

                py_module_cache[normalized_name] = (normalized_data, normalized_path)
                normalized_modules.add(normalized_name)

            # Make sure that all the packages that this module is a part of
            # are also added
            for i in range(1, len(py_module_name)):
                py_pkg_name = py_module_name[:-i] + ('__init__',)
                if py_pkg_name not in py_module_names:
                    pkg_dir_info = imp.find_module(py_pkg_name[-1],
                                                   [os.path.join(p, *py_pkg_name[:-1]) for p in module_utils_paths])
                    normalized_modules.add(py_pkg_name)
                    py_module_cache[py_pkg_name] = (_slurp(pkg_dir_info[1]), pkg_dir_info[1])

    #
    # iterate through all of the ansible.module_utils* imports that we haven't
    # already checked for new imports
    #

    # set of modules that we haven't added to the zipfile
    unprocessed_py_module_names = normalized_modules.difference(py_module_names)

    for py_module_name in unprocessed_py_module_names:
        py_module_path = os.path.join(*py_module_name)
        py_module_file_name = '%s.py' % py_module_path

        zf.writestr(os.path.join("ansible/module_utils",
                    py_module_file_name), py_module_cache[py_module_name][0])
        display.vvvvv("Using module_utils file %s" % py_module_cache[py_module_name][1])

    # Add the names of the files we're scheduling to examine in the loop to
    # py_module_names so that we don't re-examine them in the next pass
    # through recursive_finder()
    py_module_names.update(unprocessed_py_module_names)

    for py_module_file in unprocessed_py_module_names:
        recursive_finder(py_module_file, py_module_cache[py_module_file][0], py_module_names, py_module_cache, zf)
        # Save memory; the file won't have to be read again for this ansible module.
        del py_module_cache[py_module_file]


def _is_binary(b_module_data):
    textchars = bytearray(set([7, 8, 9, 10, 12, 13, 27]) | set(range(0x20, 0x100)) - set([0x7f]))
    start = b_module_data[:1024]
    return bool(start.translate(None, textchars))


def _find_module_utils(module_name, b_module_data, module_path, module_args, task_vars, templar, module_compression, async_timeout, become,
                       become_method, become_user, become_password, become_flags, environment):
    """
    Given the source of the module, convert it to a Jinja2 template to insert
    module code and return whether it's a new or old style module.
    """
    module_substyle = module_style = 'old'

    # module_style is something important to calling code (ActionBase).  It
    # determines how arguments are formatted (json vs k=v) and whether
    # a separate arguments file needs to be sent over the wire.
    # module_substyle is extra information that's useful internally.  It tells
    # us what we have to look to substitute in the module files and whether
    # we're using module replacer or ansiballz to format the module itself.
    if _is_binary(b_module_data):
        module_substyle = module_style = 'binary'
    elif REPLACER in b_module_data:
        # Do REPLACER before from ansible.module_utils because we need make sure
        # we substitute "from ansible.module_utils basic" for REPLACER
        module_style = 'new'
        module_substyle = 'python'
        b_module_data = b_module_data.replace(REPLACER, b'from ansible.module_utils.basic import *')
    elif b'from ansible.module_utils.' in b_module_data:
        module_style = 'new'
        module_substyle = 'python'
    elif REPLACER_WINDOWS in b_module_data:
        module_style = 'new'
        module_substyle = 'powershell'
        b_module_data = b_module_data.replace(REPLACER_WINDOWS, b'#Requires -Module Ansible.ModuleUtils.Legacy')
    elif re.search(b'#Requires -Module', b_module_data, re.IGNORECASE) \
            or re.search(b'#Requires -Version', b_module_data, re.IGNORECASE)\
            or re.search(b'#AnsibleRequires -OSVersion', b_module_data, re.IGNORECASE):
        module_style = 'new'
        module_substyle = 'powershell'
    elif REPLACER_JSONARGS in b_module_data:
        module_style = 'new'
        module_substyle = 'jsonargs'
    elif b'WANT_JSON' in b_module_data:
        module_substyle = module_style = 'non_native_want_json'

    shebang = None
    # Neither old-style, non_native_want_json nor binary modules should be modified
    # except for the shebang line (Done by modify_module)
    if module_style in ('old', 'non_native_want_json', 'binary'):
        return b_module_data, module_style, shebang

    output = BytesIO()
    py_module_names = set()

    if module_substyle == 'python':
        params = dict(ANSIBLE_MODULE_ARGS=module_args,)
        python_repred_params = repr(json.dumps(params))

        try:
            compression_method = getattr(zipfile, module_compression)
        except AttributeError:
            display.warning(u'Bad module compression string specified: %s.  Using ZIP_STORED (no compression)' % module_compression)
            compression_method = zipfile.ZIP_STORED

        lookup_path = os.path.join(C.DEFAULT_LOCAL_TMP, 'ansiballz_cache')
        cached_module_filename = os.path.join(lookup_path, "%s-%s" % (module_name, module_compression))

        zipdata = None
        # Optimization -- don't lock if the module has already been cached
        if os.path.exists(cached_module_filename):
            display.debug('ANSIBALLZ: using cached module: %s' % cached_module_filename)
            zipdata = open(cached_module_filename, 'rb').read()
        else:
            if module_name in action_write_locks.action_write_locks:
                display.debug('ANSIBALLZ: Using lock for %s' % module_name)
                lock = action_write_locks.action_write_locks[module_name]
            else:
                # If the action plugin directly invokes the module (instead of
                # going through a strategy) then we don't have a cross-process
                # Lock specifically for this module.  Use the "unexpected
                # module" lock instead
                display.debug('ANSIBALLZ: Using generic lock for %s' % module_name)
                lock = action_write_locks.action_write_locks[None]

            display.debug('ANSIBALLZ: Acquiring lock')
            with lock:
                display.debug('ANSIBALLZ: Lock acquired: %s' % id(lock))
                # Check that no other process has created this while we were
                # waiting for the lock
                if not os.path.exists(cached_module_filename):
                    display.debug('ANSIBALLZ: Creating module')
                    # Create the module zip data
                    zipoutput = BytesIO()
                    zf = zipfile.ZipFile(zipoutput, mode='w', compression=compression_method)
                    # Note: If we need to import from release.py first,
                    # remember to catch all exceptions: https://github.com/ansible/ansible/issues/16523
                    zf.writestr('ansible/__init__.py',
                                b'from pkgutil import extend_path\n__path__=extend_path(__path__,__name__)\n__version__="' +
                                to_bytes(__version__) + b'"\n__author__="' +
                                to_bytes(__author__) + b'"\n')
                    zf.writestr('ansible/module_utils/__init__.py', b'from pkgutil import extend_path\n__path__=extend_path(__path__,__name__)\n')

                    zf.writestr('ansible_module_%s.py' % module_name, b_module_data)

                    py_module_cache = {('__init__',): (b'', '[builtin]')}
                    recursive_finder(module_name, b_module_data, py_module_names, py_module_cache, zf)
                    zf.close()
                    zipdata = base64.b64encode(zipoutput.getvalue())

                    # Write the assembled module to a temp file (write to temp
                    # so that no one looking for the file reads a partially
                    # written file)
                    if not os.path.exists(lookup_path):
                        # Note -- if we have a global function to setup, that would
                        # be a better place to run this
                        os.makedirs(lookup_path)
                    display.debug('ANSIBALLZ: Writing module')
                    with open(cached_module_filename + '-part', 'wb') as f:
                        f.write(zipdata)

                    # Rename the file into its final position in the cache so
                    # future users of this module can read it off the
                    # filesystem instead of constructing from scratch.
                    display.debug('ANSIBALLZ: Renaming module')
                    os.rename(cached_module_filename + '-part', cached_module_filename)
                    display.debug('ANSIBALLZ: Done creating module')

            if zipdata is None:
                display.debug('ANSIBALLZ: Reading module after lock')
                # Another process wrote the file while we were waiting for
                # the write lock.  Go ahead and read the data from disk
                # instead of re-creating it.
                try:
                    zipdata = open(cached_module_filename, 'rb').read()
                except IOError:
                    raise AnsibleError('A different worker process failed to create module file. '
                                       'Look at traceback for that process for debugging information.')
        zipdata = to_text(zipdata, errors='surrogate_or_strict')

        shebang, interpreter = _get_shebang(u'/usr/bin/python', task_vars, templar)
        if shebang is None:
            shebang = u'#!/usr/bin/python'

        # Enclose the parts of the interpreter in quotes because we're
        # substituting it into the template as a Python string
        interpreter_parts = interpreter.split(u' ')
        interpreter = u"'{0}'".format(u"', '".join(interpreter_parts))

        now = datetime.datetime.utcnow()
        output.write(to_bytes(ACTIVE_ANSIBALLZ_TEMPLATE % dict(
            zipdata=zipdata,
            ansible_module=module_name,
            params=python_repred_params,
            shebang=shebang,
            interpreter=interpreter,
            coding=ENCODING_STRING,
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            second=now.second,
        )))
        b_module_data = output.getvalue()

    elif module_substyle == 'powershell':
        # Powershell/winrm don't actually make use of shebang so we can
        # safely set this here.  If we let the fallback code handle this
        # it can fail in the presence of the UTF8 BOM commonly added by
        # Windows text editors
        shebang = u'#!powershell'

        exec_manifest = dict(
            module_entry=to_text(base64.b64encode(b_module_data)),
            powershell_modules=dict(),
            module_args=module_args,
            actions=['exec'],
            environment=environment
        )

        exec_manifest['exec'] = to_text(base64.b64encode(to_bytes(leaf_exec)))

        if async_timeout > 0:
            exec_manifest["actions"].insert(0, 'async_watchdog')
            exec_manifest["async_watchdog"] = to_text(base64.b64encode(to_bytes(async_watchdog)))
            exec_manifest["actions"].insert(0, 'async_wrapper')
            exec_manifest["async_wrapper"] = to_text(base64.b64encode(to_bytes(async_wrapper)))
            exec_manifest["async_jid"] = str(random.randint(0, 999999999999))
            exec_manifest["async_timeout_sec"] = async_timeout

        if become and become_method == 'runas':
            exec_manifest["actions"].insert(0, 'become')
            exec_manifest["become_user"] = become_user
            exec_manifest["become_password"] = become_password
            exec_manifest['become_flags'] = become_flags
            exec_manifest["become"] = to_text(base64.b64encode(to_bytes(become_wrapper)))

        lines = b_module_data.split(b'\n')
        module_names = set()
        become_required = False
        min_os_version = None
        min_ps_version = None

        requires_module_list = re.compile(to_bytes(r'(?i)^#\s*requires\s+\-module(?:s?)\s*(Ansible\.ModuleUtils\..+)'))
        requires_ps_version = re.compile(to_bytes(r'(?i)^#requires\s+\-version\s+([0-9]+(\.[0-9]+){0,3})$'))
        requires_os_version = re.compile(to_bytes(r'(?i)^#ansiblerequires\s+\-osversion\s+([0-9]+(\.[0-9]+){0,3})$'))
        requires_become = re.compile(to_bytes(r'(?i)^#ansiblerequires\s+\-become$'))

        for line in lines:
            module_util_line_match = requires_module_list.match(line)
            if module_util_line_match:
                module_names.add(module_util_line_match.group(1))

            requires_ps_version_match = requires_ps_version.match(line)
            if requires_ps_version_match:
                min_ps_version = to_text(requires_ps_version_match.group(1))
                # Powershell cannot cast a string of "1" to version, it must
                # have at least the major.minor for it to work so we append 0
                if requires_ps_version_match.group(2) is None:
                    min_ps_version = "%s.0" % min_ps_version

            requires_os_version_match = requires_os_version.match(line)
            if requires_os_version_match:
                min_os_version = to_text(requires_os_version_match.group(1))
                if requires_os_version_match.group(2) is None:
                    min_os_version = "%s.0" % min_os_version

            requires_become_match = requires_become.match(line)
            if requires_become_match:
                become_required = True

        for m in set(module_names):
            m = to_text(m).rstrip()  # tolerate windows line endings
            mu_path = ps_module_utils_loader.find_plugin(m, ".psm1")
            if not mu_path:
                raise AnsibleError('Could not find imported module support code for \'%s\'.' % m)
            exec_manifest["powershell_modules"][m] = to_text(
                base64.b64encode(
                    to_bytes(
                        _slurp(mu_path)
                    )
                )
            )

        exec_manifest['min_ps_version'] = min_ps_version
        exec_manifest['min_os_version'] = min_os_version
        if become_required and 'become' not in exec_manifest["actions"]:
            exec_manifest["actions"].insert(0, 'become')
            exec_manifest["become_user"] = "SYSTEM"
            exec_manifest["become_password"] = None
            exec_manifest['become_flags'] = None
            exec_manifest["become"] = to_text(base64.b64encode(to_bytes(become_wrapper)))

        # FUTURE: smuggle this back as a dict instead of serializing here; the connection plugin may need to modify it
        module_json = json.dumps(exec_manifest)

        b_module_data = exec_wrapper.replace(b"$json_raw = ''", b"$json_raw = @'\r\n%s\r\n'@" % to_bytes(module_json))

    elif module_substyle == 'jsonargs':
        module_args_json = to_bytes(json.dumps(module_args))

        # these strings could be included in a third-party module but
        # officially they were included in the 'basic' snippet for new-style
        # python modules (which has been replaced with something else in
        # ansiballz) If we remove them from jsonargs-style module replacer
        # then we can remove them everywhere.
        python_repred_args = to_bytes(repr(module_args_json))
        b_module_data = b_module_data.replace(REPLACER_VERSION, to_bytes(repr(__version__)))
        b_module_data = b_module_data.replace(REPLACER_COMPLEX, python_repred_args)
        b_module_data = b_module_data.replace(REPLACER_SELINUX, to_bytes(','.join(C.DEFAULT_SELINUX_SPECIAL_FS)))

        # The main event -- substitute the JSON args string into the module
        b_module_data = b_module_data.replace(REPLACER_JSONARGS, module_args_json)

        facility = b'syslog.' + to_bytes(task_vars.get('ansible_syslog_facility', C.DEFAULT_SYSLOG_FACILITY), errors='surrogate_or_strict')
        b_module_data = b_module_data.replace(b'syslog.LOG_USER', facility)

    return (b_module_data, module_style, shebang)


def modify_module(module_name, module_path, module_args, templar, task_vars=None, module_compression='ZIP_STORED', async_timeout=0, become=False,
                  become_method=None, become_user=None, become_password=None, become_flags=None, environment=None):
    """
    Used to insert chunks of code into modules before transfer rather than
    doing regular python imports.  This allows for more efficient transfer in
    a non-bootstrapping scenario by not moving extra files over the wire and
    also takes care of embedding arguments in the transferred modules.

    This version is done in such a way that local imports can still be
    used in the module code, so IDEs don't have to be aware of what is going on.

    Example:

    from ansible.module_utils.basic import *

       ... will result in the insertion of basic.py into the module
       from the module_utils/ directory in the source tree.

    For powershell, this code effectively no-ops, as the exec wrapper requires access to a number of
    properties not available here.

    """
    task_vars = {} if task_vars is None else task_vars
    environment = {} if environment is None else environment

    with open(module_path, 'rb') as f:

        # read in the module source
        b_module_data = f.read()

    (b_module_data, module_style, shebang) = _find_module_utils(module_name, b_module_data, module_path, module_args, task_vars, templar, module_compression,
                                                                async_timeout=async_timeout, become=become, become_method=become_method,
                                                                become_user=become_user, become_password=become_password, become_flags=become_flags,
                                                                environment=environment)

    if module_style == 'binary':
        return (b_module_data, module_style, to_text(shebang, nonstring='passthru'))
    elif shebang is None:
        b_lines = b_module_data.split(b"\n", 1)
        if b_lines[0].startswith(b"#!"):
            b_shebang = b_lines[0].strip()
            # shlex.split on python-2.6 needs bytes.  On python-3.x it needs text
            args = shlex.split(to_native(b_shebang[2:], errors='surrogate_or_strict'))

            # _get_shebang() takes text strings
            args = [to_text(a, errors='surrogate_or_strict') for a in args]
            interpreter = args[0]
            b_new_shebang = to_bytes(_get_shebang(interpreter, task_vars, templar, args[1:])[0],
                                     errors='surrogate_or_strict', nonstring='passthru')

            if b_new_shebang:
                b_lines[0] = b_shebang = b_new_shebang

            if os.path.basename(interpreter).startswith(u'python'):
                b_lines.insert(1, b_ENCODING_STRING)

            shebang = to_text(b_shebang, nonstring='passthru', errors='surrogate_or_strict')
        else:
            # No shebang, assume a binary module?
            pass

        b_module_data = b"\n".join(b_lines)

    return (b_module_data, module_style, shebang)
