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
import json
import os
import shlex
import zipfile
from io import BytesIO

# from Ansible
from ansible import __version__
from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.utils.unicode import to_bytes, to_unicode
from ansible.plugins.strategy import action_write_locks

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

REPLACER          = b"#<<INCLUDE_ANSIBLE_MODULE_COMMON>>"
REPLACER_VERSION  = b"\"<<ANSIBLE_VERSION>>\""
REPLACER_COMPLEX  = b"\"<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>\""
REPLACER_WINDOWS  = b"# POWERSHELL_COMMON"
REPLACER_JSONARGS = b"<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>"
REPLACER_SELINUX  = b"<<SELINUX_SPECIAL_FILESYSTEMS>>"

# We could end up writing out parameters with unicode characters so we need to
# specify an encoding for the python source file
ENCODING_STRING = u'# -*- coding: utf-8 -*-'

# we've moved the module_common relative to the snippets, so fix the path
_SNIPPET_PATH = os.path.join(os.path.dirname(__file__), '..', 'module_utils')

# ******************************************************************************

ZIPLOADER_TEMPLATE = u'''%(shebang)s
%(coding)s
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
import sys
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

    p = subprocess.Popen(['%(interpreter)s', module], env=os.environ, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
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
    # remote machine. Run with ANSIBLE_KEEP_REMOTE_FILES=1 envvar and -vvv
    # to save the module file remotely.  Login to the remote machine and use
    # /path/to/module explode to extract the ZIPDATA payload into source
    # files.  Edit the source files to instrument the code or experiment with
    # different values.  Then use /path/to/module execute to run the extracted
    # files you've edited instead of the actual zipped module.

    # Okay to use __file__ here because we're running from a kept file
    basedir = os.path.abspath(os.path.dirname(__file__))
    args_path = os.path.join(basedir, 'args')
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
                f = open(dest_filename, 'w')
                f.write(z.read(filename))
                f.close()

        # write the args file
        f = open(args_path, 'w')
        f.write(json_params)
        f.close()

        print('Module expanded into:')
        print('%%s' %% os.path.join(basedir, 'ansible'))
        exitcode = 0

    elif command == 'execute':
        # Execute the exploded code instead of executing the module from the
        # embedded ZIPDATA.  This allows people to easily run their modified
        # code on the remote machine to see how changes will affect it.
        # This differs slightly from default Ansible execution of Python modules
        # as it passes the arguments to the module via a file instead of stdin.

        pythonpath = os.environ.get('PYTHONPATH')
        if pythonpath:
            os.environ['PYTHONPATH'] = ':'.join((basedir, pythonpath))
        else:
            os.environ['PYTHONPATH'] = basedir

        p = subprocess.Popen(['%(interpreter)s', 'ansible_module_%(ansible_module)s.py', args_path], env=os.environ, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
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

        # stub the
        sys.argv = ['%(ansible_module)s', args_path]
        from ansible_module_%(ansible_module)s import main
        main()
        print('WARNING: Module returned to wrapper instead of exiting')
        sys.exit(1)
    else:
        print('WARNING: Unknown debug command.  Doing nothing.')
        exitcode = 0

    return exitcode

if __name__ == '__main__':
    ZIPLOADER_PARAMS = %(params)s
    if PY3:
        ZIPLOADER_PARAMS = ZIPLOADER_PARAMS.encode('utf-8')
    try:
        temp_path = tempfile.mkdtemp(prefix='ansible_')
        zipped_mod = os.path.join(temp_path, 'ansible_modlib.zip')
        modlib = open(zipped_mod, 'wb')
        modlib.write(base64.b64decode(ZIPDATA))
        modlib.close()
        if len(sys.argv) == 2:
            exitcode = debug(sys.argv[1], zipped_mod, ZIPLOADER_PARAMS)
        else:
            z = zipfile.ZipFile(zipped_mod)
            module = os.path.join(temp_path, 'ansible_module_%(ansible_module)s.py')
            f = open(module, 'wb')
            f.write(z.read('ansible_module_%(ansible_module)s.py'))
            f.close()
            exitcode = invoke_module(module, zipped_mod, ZIPLOADER_PARAMS)
    finally:
        try:
            shutil.rmtree(temp_path)
        except OSError:
            # tempdir creation probably failed
            pass
    sys.exit(exitcode)
'''

class ModuleDepFinder(ast.NodeVisitor):
    # Caveats:
    # This code currently does not handle:
    # * relative imports from py2.6+ from . import urls
    # * python packages (directories with __init__.py in them)
    IMPORT_PREFIX_SIZE = len('ansible.module_utils.')

    def __init__(self, *args, **kwargs):
        super(ModuleDepFinder, self).__init__(*args, **kwargs)
        self.module_files = set()

    def visit_Import(self, node):
        # import ansible.module_utils.MODLIB[.other]
        for alias in (a for a in node.names if a.name.startswith('ansible.module_utils.')):
            py_mod = alias.name[self.IMPORT_PREFIX_SIZE:].split('.', 1)[0]
            self.module_files.add(py_mod)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module.startswith('ansible.module_utils'):
            where_from = node.module[self.IMPORT_PREFIX_SIZE:]
            # from ansible.module_utils.MODLIB[.other] import foo
            if where_from:
                py_mod = where_from.split('.', 1)[0]
                self.module_files.add(py_mod)
            else:
                # from ansible.module_utils import MODLIB
                for alias in node.names:
                    self.module_files.add(alias.name)
        self.generic_visit(node)


def _strip_comments(source):
    # Strip comments and blank lines from the wrapper
    buf = []
    for line in source.splitlines():
        l = line.strip()
        if not l or l.startswith(u'#'):
            continue
        buf.append(line)
    return u'\n'.join(buf)

# ZIPLOADER_TEMPLATE stripped of comments for smaller over the wire size
STRIPPED_ZIPLOADER_TEMPLATE = _strip_comments(ZIPLOADER_TEMPLATE)

def _slurp(path):
    if not os.path.exists(path):
        raise AnsibleError("imported module support code does not exist at %s" % path)
    fd = open(path, 'rb')
    data = fd.read()
    fd.close()
    return data

def _get_shebang(interpreter, task_vars, args=tuple()):
    """
    Note not stellar API:
       Returns None instead of always returning a shebang line.  Doing it this
       way allows the caller to decide to use the shebang it read from the
       file rather than trust that we reformatted what they already have
       correctly.
    """
    interpreter_config = u'ansible_%s_interpreter' % os.path.basename(interpreter)

    if interpreter_config not in task_vars:
        return (None, interpreter)

    interpreter = task_vars[interpreter_config]
    shebang = u'#!' + interpreter

    if args:
        shebang = shebang + u' ' + u' '.join(args)

    return (shebang, interpreter)

def _get_facility(task_vars):
    facility = C.DEFAULT_SYSLOG_FACILITY
    if 'ansible_syslog_facility' in task_vars:
        facility = task_vars['ansible_syslog_facility']
    return facility

def recursive_finder(data, snippet_names, snippet_data, zf):
    """
    Using ModuleDepFinder, make sure we have all of the module_utils files that
    the module its module_utils files needs.
    """
    tree = ast.parse(data)
    finder = ModuleDepFinder()
    finder.visit(tree)

    new_snippets = set()
    for snippet_name in finder.module_files.difference(snippet_names):
        fname = '%s.py' % snippet_name
        new_snippets.add(snippet_name)
        if snippet_name not in snippet_data:
            snippet_data[snippet_name] = _slurp(os.path.join(_SNIPPET_PATH, fname))
        zf.writestr(os.path.join("ansible/module_utils", fname), snippet_data[snippet_name])
    snippet_names.update(new_snippets)

    for snippet_name in tuple(new_snippets):
        recursive_finder(snippet_data[snippet_name], snippet_names, snippet_data, zf)
        del snippet_data[snippet_name]

def _find_snippet_imports(module_name, module_data, module_path, module_args, task_vars, module_compression):
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
    # we're using module replacer or ziploader to format the module itself.
    if REPLACER in module_data:
        # Do REPLACER before from ansible.module_utils because we need make sure
        # we substitute "from ansible.module_utils basic" for REPLACER
        module_style = 'new'
        module_substyle = 'python'
        module_data = module_data.replace(REPLACER, b'from ansible.module_utils.basic import *')
    elif b'from ansible.module_utils.' in module_data:
        module_style = 'new'
        module_substyle = 'python'
    elif REPLACER_WINDOWS in module_data:
        module_style = 'new'
        module_substyle = 'powershell'
    elif REPLACER_JSONARGS in module_data:
        module_style = 'new'
        module_substyle = 'jsonargs'
    elif b'WANT_JSON' in module_data:
        module_substyle = module_style = 'non_native_want_json'

    shebang = None
    # Neither old-style nor non_native_want_json modules should be modified
    # except for the shebang line (Done by modify_module)
    if module_style in ('old', 'non_native_want_json'):
        return module_data, module_style, shebang

    output = BytesIO()
    snippet_names = set()

    if module_substyle == 'python':
        # ziploader for new-style python classes
        constants = dict(
                SELINUX_SPECIAL_FS=C.DEFAULT_SELINUX_SPECIAL_FS,
                SYSLOG_FACILITY=_get_facility(task_vars),
                )
        params = dict(ANSIBLE_MODULE_ARGS=module_args,
                ANSIBLE_MODULE_CONSTANTS=constants,
                )
        #python_repred_args = to_bytes(repr(module_args_json))
        #python_repred_constants = to_bytes(repr(json.dumps(constants)), errors='strict')
        python_repred_params = to_bytes(repr(json.dumps(params)), errors='strict')

        try:
            compression_method = getattr(zipfile, module_compression)
        except AttributeError:
            display.warning(u'Bad module compression string specified: %s.  Using ZIP_STORED (no compression)' % module_compression)
            compression_method = zipfile.ZIP_STORED

        lookup_path = os.path.join(C.DEFAULT_LOCAL_TMP, 'ziploader_cache')
        cached_module_filename = os.path.join(lookup_path, "%s-%s" % (module_name, module_compression))

        zipdata = None
        # Optimization -- don't lock if the module has already been cached
        if os.path.exists(cached_module_filename):
            zipdata = open(cached_module_filename, 'rb').read()
            # Fool the check later... I think we should just remove the check
            snippet_names.add('basic')
        else:
            with action_write_locks[module_name]:
                # Check that no other process has created this while we were
                # waiting for the lock
                if not os.path.exists(cached_module_filename):
                    # Create the module zip data
                    zipoutput = BytesIO()
                    zf = zipfile.ZipFile(zipoutput, mode='w', compression=compression_method)
                    zf.writestr('ansible/__init__.py', b''.join((b"__version__ = '", to_bytes(__version__), b"'\n")))
                    zf.writestr('ansible/module_utils/__init__.py', b'')

                    zf.writestr('ansible_module_%s.py' % module_name, module_data)

                    snippet_data = dict()
                    recursive_finder(module_data, snippet_names, snippet_data, zf)
                    zf.close()
                    zipdata = base64.b64encode(zipoutput.getvalue())

                    # Write the assembled module to a temp file (write to temp
                    # so that no one looking for the file reads a partially
                    # written file)
                    if not os.path.exists(lookup_path):
                        # Note -- if we have a global function to setup, that would
                        # be a better place to run this
                        os.mkdir(lookup_path)
                    with open(cached_module_filename + '-part', 'w') as f:
                        f.write(zipdata)

                    # Rename the file into its final position in the cache so
                    # future users of this module can read it off the
                    # filesystem instead of constructing from scratch.
                    os.rename(cached_module_filename + '-part', cached_module_filename)

            if zipdata is None:
                # Another process wrote the file while we were waiting for
                # the write lock.  Go ahead and read the data from disk
                # instead of re-creating it.
                try:
                    zipdata = open(cached_module_filename, 'rb').read()
                except IOError:
                    raise AnsibleError('A different worker process failed to create module file.  Look at traceback for that process for debugging information.')
                # Fool the check later... I think we should just remove the check
                snippet_names.add('basic')
        shebang, interpreter = _get_shebang(u'/usr/bin/python', task_vars)
        if shebang is None:
            shebang = u'#!/usr/bin/python'
        output.write(to_bytes(STRIPPED_ZIPLOADER_TEMPLATE % dict(
            zipdata=zipdata,
            ansible_module=module_name,
            #args=python_repred_args,
            #constants=python_repred_constants,
            params=python_repred_params,
            shebang=shebang,
            interpreter=interpreter,
            coding=ENCODING_STRING,
            )))
        module_data = output.getvalue()

        # Sanity check from 1.x days.  Maybe too strict.  Some custom python
        # modules that use ziploader may implement their own helpers and not
        # need basic.py.  All the constants that we substituted into basic.py
        # for module_replacer are now available in other, better ways.
        if 'basic' not in snippet_names:
            raise AnsibleError("missing required import in %s: Did not import ansible.module_utils.basic for boilerplate helper code" % module_path)

    elif module_substyle == 'powershell':
        # Module replacer for jsonargs and windows
        lines = module_data.split(b'\n')
        for line in lines:
            if REPLACER_WINDOWS in line:
                ps_data = _slurp(os.path.join(_SNIPPET_PATH, "powershell.ps1"))
                output.write(ps_data)
                snippet_names.add(b'powershell')
                continue
            output.write(line + b'\n')
        module_data = output.getvalue()

        module_args_json = to_bytes(json.dumps(module_args))
        module_data = module_data.replace(REPLACER_JSONARGS, module_args_json)

        # Sanity check from 1.x days.  This is currently useless as we only
        # get here if we are going to substitute powershell.ps1 into the
        # module anyway.  Leaving it for when/if we add other powershell
        # module_utils files.
        if b'powershell' not in snippet_names:
            raise AnsibleError("missing required import in %s: # POWERSHELL_COMMON" % module_path)

    elif module_substyle == 'jsonargs':
        module_args_json = to_bytes(json.dumps(module_args))

        # these strings could be included in a third-party module but
        # officially they were included in the 'basic' snippet for new-style
        # python modules (which has been replaced with something else in
        # ziploader) If we remove them from jsonargs-style module replacer
        # then we can remove them everywhere.
        python_repred_args = to_bytes(repr(module_args_json))
        module_data = module_data.replace(REPLACER_VERSION, to_bytes(repr(__version__)))
        module_data = module_data.replace(REPLACER_COMPLEX, python_repred_args)
        module_data = module_data.replace(REPLACER_SELINUX, to_bytes(','.join(C.DEFAULT_SELINUX_SPECIAL_FS)))

        # The main event -- substitute the JSON args string into the module
        module_data = module_data.replace(REPLACER_JSONARGS, module_args_json)

        facility = b'syslog.' + to_bytes(_get_facility(task_vars), errors='strict')
        module_data = module_data.replace(b'syslog.LOG_USER', facility)

    return (module_data, module_style, shebang)

# ******************************************************************************

def modify_module(module_name, module_path, module_args, task_vars=dict(), module_compression='ZIP_STORED'):
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

    All modules are required to import at least basic, though there will also
    be other snippets.

    For powershell, there's equivalent conventions like this:

    # POWERSHELL_COMMON

    which results in the inclusion of the common code from powershell.ps1

    """
    with open(module_path, 'rb') as f:

        # read in the module source
        module_data = f.read()

    (module_data, module_style, shebang) = _find_snippet_imports(module_name, module_data, module_path, module_args, task_vars, module_compression)

    if shebang is None:
        lines = module_data.split(b"\n", 1)
        if lines[0].startswith(b"#!"):
            shebang = lines[0].strip()
            args = shlex.split(str(shebang[2:]))
            interpreter = args[0]
            interpreter = to_bytes(interpreter)

            new_shebang = to_bytes(_get_shebang(interpreter, task_vars, args[1:])[0], errors='strict', nonstring='passthru')
            if new_shebang:
                lines[0] = shebang = new_shebang

            if os.path.basename(interpreter).startswith(b'python'):
                lines.insert(1, to_bytes(ENCODING_STRING))
        else:
            # No shebang, assume a binary module?
            pass

        module_data = b"\n".join(lines)
    else:
        shebang = to_bytes(shebang, errors='strict')

    return (module_data, module_style, shebang)
