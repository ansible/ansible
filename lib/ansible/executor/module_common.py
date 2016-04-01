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
ENCODING_STRING = b'# -*- coding: utf-8 -*-'

# we've moved the module_common relative to the snippets, so fix the path
_SNIPPET_PATH = os.path.join(os.path.dirname(__file__), '..', 'module_utils')

# ******************************************************************************

ZIPLOADER_DATA = u'''%(shebang)s
# -*- coding: utf-8 -*-'
import os
import sys
import base64
import tempfile

ZIPDATA = """%(zipdata)s"""
os.environ['ANSIBLE_MODULE_ARGS'] = %(args)s
os.environ['ANSIBLE_MODULE_CONSTANTS'] = %(constants)s

try:
    temp_fd, temp_path = tempfile.mkstemp(prefix='ansible_')
    os.write(temp_fd, base64.b64decode(ZIPDATA))
    sys.path.insert(0, temp_path)
    from ansible.module_exec.%(ansible_module)s.__main__ import main
    main()
finally:
    try:
        os.close(temp_fd)
        os.remove(temp_path)
    except NameError:
        # mkstemp failed
        pass
'''

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
        return None

    interpreter = task_vars[interpreter_config]
    shebang = u'#!' + interpreter

    if args:
        shebang = shebang + u' ' + u' '.join(args)

    return shebang

def _get_facility(task_vars):
    facility = C.DEFAULT_SYSLOG_FACILITY
    if 'ansible_syslog_facility' in task_vars:
        facility = task_vars['ansible_syslog_facility']
    return facility

def _find_snippet_imports(module_name, module_data, module_path, module_args, task_vars, module_compression):
    """
    Given the source of the module, convert it to a Jinja2 template to insert
    module code and return whether it's a new or old style module.
    """

    module_substyle = module_style = 'old'
    # Do REPLACER before from ansible.module_utils because we need make sure
    # we substitute "from ansible.module_utils basic" for REPLACER
    if REPLACER in module_data:
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

    module_args_json = to_bytes(json.dumps(module_args))

    output = BytesIO()
    lines = module_data.split(b'\n')

    snippet_names = set()

    if module_substyle == 'python':
        # ziploader for new-style python classes
        python_repred_args = to_bytes(repr(module_args_json))
        constants = dict(
                SELINUX_SPECIAL_FS=C.DEFAULT_SELINUX_SPECIAL_FS,
                SYSLOG_FACILITY=_get_facility(task_vars),
                )
        python_repred_constants = to_bytes(repr(json.dumps(constants)), errors='strict')

        try:
            compression_method = getattr(zipfile, module_compression)
        except AttributeError:
            display.warning(u'Bad module compression string specified: %s.  Using ZIP_STORED (no compression)' % module_compression)
            compression_method = zipfile.ZIP_STORED
        zipoutput = BytesIO()
        zf = zipfile.ZipFile(zipoutput, mode='w', compression=compression_method)
        zf.writestr('ansible/__init__.py', b''.join((b"__version__ = '", to_bytes(__version__), b"'\n")))
        zf.writestr('ansible/module_utils/__init__.py', b'')
        zf.writestr('ansible/module_exec/__init__.py', b'')

        zf.writestr('ansible/module_exec/%s/__init__.py' % module_name, b"")
        final_data = []

        for line in lines:
            if line.startswith(b'from ansible.module_utils.'):
                tokens=line.split(b".")
                snippet_name = tokens[2].split()[0]
                snippet_names.add(snippet_name)
                fname = to_unicode(snippet_name + b".py")
                zf.writestr(os.path.join("ansible/module_utils", fname), _slurp(os.path.join(_SNIPPET_PATH, fname)))
                final_data.append(line)
            else:
                final_data.append(line)

        zf.writestr('ansible/module_exec/%s/__main__.py' % module_name, b"\n".join(final_data))
        zf.close()
        shebang = _get_shebang(u'/usr/bin/python', task_vars) or u'#!/usr/bin/python'
        output.write(to_bytes(ZIPLOADER_DATA % dict(
            zipdata=base64.b64encode(zipoutput.getvalue()),
            ansible_module=module_name,
            args=python_repred_args,
            constants=python_repred_constants,
            shebang=shebang,
            )))
        module_data = output.getvalue()

        # Sanity check from 1.x days.  Maybe too strict.  Some custom python
        # modules that use ziploader may implement their own helpers and not
        # need basic.py.  All the constants that we substituted into basic.py
        # for module_replacer are now available in other, better ways.
        if b'basic' not in snippet_names:
            raise AnsibleError("missing required import in %s: Did not import ansible.module_utils.basic for boilerplate helper code" % module_path)

    elif module_substyle == 'powershell':
        # Module replacer for jsonargs and windows
        for line in lines:
            if REPLACER_WINDOWS in line:
                ps_data = _slurp(os.path.join(_SNIPPET_PATH, "powershell.ps1"))
                output.write(ps_data)
                snippet_names.add(b'powershell')
        module_data = output.getvalue()
        module_data = module_data.replace(REPLACER_JSONARGS, module_args_json)

        # Sanity check from 1.x days.  This is currently useless as we only
        # get here if we are going to substitute powershell.ps1 into the
        # module anyway.  Leaving it for when/if we add other powershell
        # module_utils files.
        if b'powershell' not in snippet_names:
            raise AnsibleError("missing required import in %s: # POWERSHELL_COMMON" % module_path)

    elif module_substyle == 'jsonargs':
        # these strings could be included in a third-party module but
        # officially they were included in the 'basic' snippet for new-style
        # python modules (which has been replaced with something else in
        # ziploader) If we remove them from jsonargs-style module replacer
        # then we can remove them everywhere.
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
    ### TODO: Optimization ideas if this code is actually a source of slowness:
    # * Fix comment stripping: Currently doesn't preserve shebangs and encoding info (but we unconditionally add encoding info)
    # * Use pyminifier if installed
    # * comment stripping/pyminifier needs to have config setting to turn it
    #   off for debugging purposes (goes along with keep remote but should be
    #   separate otherwise users wouldn't be able to get info on what the
    #   minifier output)
    # * Only split into lines and recombine into strings once
    # * Cache the modified module?  If only the args are different and we do
    #   that as the last step we could cache all the work up to that point.

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

            new_shebang = to_bytes(_get_shebang(interpreter, task_vars, args[1:]), errors='strict', nonstring='passthru')
            if new_shebang:
                lines[0] = shebang = new_shebang

            if os.path.basename(interpreter).startswith(b'python'):
                lines.insert(1, ENCODING_STRING)
        else:
            # No shebang, assume a binary module?
            pass

        module_data = b"\n".join(lines)
    else:
        shebang = to_bytes(shebang, errors='strict')

    return (module_data, module_style, shebang)
