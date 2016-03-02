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

# from python and deps
from io import BytesIO
import json
import os
import shlex

# from Ansible
from ansible import __version__
from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.utils.unicode import to_bytes, to_unicode

REPLACER          = b"#<<INCLUDE_ANSIBLE_MODULE_COMMON>>"
REPLACER_ARGS     = b"\"<<INCLUDE_ANSIBLE_MODULE_ARGS>>\""
REPLACER_COMPLEX  = b"\"<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>\""
REPLACER_WINDOWS  = b"# POWERSHELL_COMMON"
REPLACER_WINARGS  = b"<<INCLUDE_ANSIBLE_MODULE_WINDOWS_ARGS>>"
REPLACER_JSONARGS = b"<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>"
REPLACER_VERSION  = b"\"<<ANSIBLE_VERSION>>\""
REPLACER_SELINUX  = b"<<SELINUX_SPECIAL_FILESYSTEMS>>"

# We could end up writing out parameters with unicode characters so we need to
# specify an encoding for the python source file
ENCODING_STRING = b'# -*- coding: utf-8 -*-'

# we've moved the module_common relative to the snippets, so fix the path
_SNIPPET_PATH = os.path.join(os.path.dirname(__file__), '..', 'module_utils')

# ******************************************************************************

def _slurp(path):
    if not os.path.exists(path):
        raise AnsibleError("imported module support code does not exist at %s" % path)
    fd = open(path, 'rb')
    data = fd.read()
    fd.close()
    return data

def _find_snippet_imports(module_data, module_path, strip_comments):
    """
    Given the source of the module, convert it to a Jinja2 template to insert
    module code and return whether it's a new or old style module.
    """

    module_style = 'old'
    if REPLACER in module_data:
        module_style = 'new'
    elif REPLACER_WINDOWS in module_data:
        module_style = 'new'
    elif REPLACER_JSONARGS in module_data:
        module_style = 'new'
    elif b'from ansible.module_utils.' in module_data:
        module_style = 'new'
    elif b'WANT_JSON' in module_data:
        module_style = 'non_native_want_json'

    output = BytesIO()
    lines = module_data.split(b'\n')
    snippet_names = []

    for line in lines:

        if REPLACER in line:
            output.write(_slurp(os.path.join(_SNIPPET_PATH, "basic.py")))
            snippet_names.append(b'basic')
        if REPLACER_WINDOWS in line:
            ps_data = _slurp(os.path.join(_SNIPPET_PATH, "powershell.ps1"))
            output.write(ps_data)
            snippet_names.append(b'powershell')
        elif line.startswith(b'from ansible.module_utils.'):
            tokens=line.split(b".")
            import_error = False
            if len(tokens) != 3:
                import_error = True
            if b" import *" not in line:
                import_error = True
            if import_error:
                raise AnsibleError("error importing module in %s, expecting format like 'from ansible.module_utils.<lib name> import *'" % module_path)
            snippet_name = tokens[2].split()[0]
            snippet_names.append(snippet_name)
            output.write(_slurp(os.path.join(_SNIPPET_PATH, to_unicode(snippet_name) + ".py")))
        else:
            if strip_comments and line.startswith(b"#") or line == b'':
                pass
            output.write(line)
            output.write(b"\n")

    if not module_path.endswith(".ps1"):
        # Unixy modules
        if len(snippet_names) > 0 and not b'basic' in snippet_names:
            raise AnsibleError("missing required import in %s: from ansible.module_utils.basic import *" % module_path)
    else:
        # Windows modules
        if len(snippet_names) > 0 and not b'powershell' in snippet_names:
            raise AnsibleError("missing required import in %s: # POWERSHELL_COMMON" % module_path)

    return (output.getvalue(), module_style)

# ******************************************************************************

def modify_module(module_path, module_args, task_vars=dict(), strip_comments=False):
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

    (module_data, module_style) = _find_snippet_imports(module_data, module_path, strip_comments)

    module_args_json = to_bytes(json.dumps(module_args))
    python_repred_args = to_bytes(repr(module_args_json))

    # these strings should be part of the 'basic' snippet which is required to be included
    module_data = module_data.replace(REPLACER_VERSION, to_bytes(repr(__version__)))
    module_data = module_data.replace(REPLACER_COMPLEX, python_repred_args)
    module_data = module_data.replace(REPLACER_WINARGS, module_args_json)
    module_data = module_data.replace(REPLACER_JSONARGS, module_args_json)
    module_data = module_data.replace(REPLACER_SELINUX, to_bytes(','.join(C.DEFAULT_SELINUX_SPECIAL_FS)))

    if module_style == 'new':
        facility = C.DEFAULT_SYSLOG_FACILITY
        if 'ansible_syslog_facility' in task_vars:
            facility = task_vars['ansible_syslog_facility']
        module_data = module_data.replace(b'syslog.LOG_USER', to_bytes("syslog.%s" % facility))

    lines = module_data.split(b"\n", 1)
    shebang = None
    if lines[0].startswith(b"#!"):
        shebang = lines[0].strip()
        args = shlex.split(str(shebang[2:]))
        interpreter = args[0]
        interpreter_config = 'ansible_%s_interpreter' % os.path.basename(interpreter)
        interpreter = to_bytes(interpreter)

        if interpreter_config in task_vars:
            interpreter = to_bytes(task_vars[interpreter_config], errors='strict')
            lines[0] = shebang = b"#!{0} {1}".format(interpreter, b" ".join(args[1:]))

        if os.path.basename(interpreter).startswith(b'python'):
            lines.insert(1, ENCODING_STRING)
    else:
        # No shebang, assume a binary module?
        pass

    module_data = b"\n".join(lines)

    return (module_data, module_style, shebang)
