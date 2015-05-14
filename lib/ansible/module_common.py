# (c) 2013-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# from python and deps
from cStringIO import StringIO
import inspect
import os
import shlex

# from Ansible
from ansible import errors
from ansible import utils
from ansible import constants as C
from ansible import __version__

REPLACER = "#<<INCLUDE_ANSIBLE_MODULE_COMMON>>"
REPLACER_ARGS = "\"<<INCLUDE_ANSIBLE_MODULE_ARGS>>\""
REPLACER_COMPLEX = "\"<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>\""
REPLACER_WINDOWS = "# POWERSHELL_COMMON"
REPLACER_VERSION = "\"<<ANSIBLE_VERSION>>\""
REPLACER_SELINUX = "<<SELINUX_SPECIAL_FILESYSTEMS>>"


class ModuleReplacer(object):

    """
    The Replacer is used to insert chunks of code into modules before
    transfer.  Rather than doing classical python imports, this allows for more
    efficient transfer in a no-bootstrapping scenario by not moving extra files
    over the wire, and also takes care of embedding arguments in the transferred
    modules.

    This version is done in such a way that local imports can still be
    used in the module code, so IDEs don't have to be aware of what is going on.

    Example:

    from ansible.module_utils.basic import *

       ... will result in the insertion basic.py into the module

    from the module_utils/ directory in the source tree.

    All modules are required to import at least basic, though there will also
    be other snippets.

    # POWERSHELL_COMMON

    Also results in the inclusion of the common code in powershell.ps1

    """

    # ******************************************************************************

    def __init__(self, strip_comments=False):
        this_file = inspect.getfile(inspect.currentframe())
        self.snippet_path = os.path.join(os.path.dirname(this_file), 'module_utils')
        self.strip_comments = strip_comments # TODO: implement

    # ******************************************************************************


    def slurp(self, path):
        if not os.path.exists(path):
            raise errors.AnsibleError("imported module support code does not exist at %s" % path)
        fd = open(path)
        data = fd.read()
        fd.close()
        return data

    def _find_snippet_imports(self, module_data, module_path):
        """
        Given the source of the module, convert it to a Jinja2 template to insert
        module code and return whether it's a new or old style module.
        """

        module_style = 'old'
        if REPLACER in module_data:
            module_style = 'new'
        elif 'from ansible.module_utils.' in module_data:
            module_style = 'new'
        elif 'WANT_JSON' in module_data:
            module_style = 'non_native_want_json'

        output = StringIO()
        lines = module_data.split('\n')
        snippet_names = []

        for line in lines:

            if REPLACER in line:
                output.write(self.slurp(os.path.join(self.snippet_path, "basic.py")))
                snippet_names.append('basic')
            if REPLACER_WINDOWS in line:
                ps_data = self.slurp(os.path.join(self.snippet_path, "powershell.ps1"))
                output.write(ps_data)
                snippet_names.append('powershell')
            elif line.startswith('from ansible.module_utils.'):
                tokens=line.split(".")
                import_error = False
                if len(tokens) != 3:
                    import_error = True
                if " import *" not in line:
                    import_error = True
                if import_error:
                    raise errors.AnsibleError("error importing module in %s, expecting format like 'from ansible.module_utils.basic import *'" % module_path)
                snippet_name = tokens[2].split()[0]
                snippet_names.append(snippet_name)
                output.write(self.slurp(os.path.join(self.snippet_path, snippet_name + ".py")))

            else:
                if self.strip_comments and line.startswith("#") or line == '':
                    pass
                output.write(line)
                output.write("\n")

        if not module_path.endswith(".ps1"):
            # Unixy modules
            if len(snippet_names) > 0 and not 'basic' in snippet_names:
                raise errors.AnsibleError("missing required import in %s: from ansible.module_utils.basic import *" % module_path) 
        else:
            # Windows modules
            if len(snippet_names) > 0 and not 'powershell' in snippet_names:
                raise errors.AnsibleError("missing required import in %s: # POWERSHELL_COMMON" % module_path) 

        return (output.getvalue(), module_style)

    # ******************************************************************************

    def modify_module(self, module_path, complex_args, module_args, inject):

        with open(module_path) as f:

            # read in the module source
            module_data = f.read()

            (module_data, module_style) = self._find_snippet_imports(module_data, module_path)

            complex_args_json = utils.jsonify(complex_args)
            # We force conversion of module_args to str because module_common calls shlex.split,
            # a standard library function that incorrectly handles Unicode input before Python 2.7.3.
            # Note: it would be better to do all this conversion at the border
            # (when the data is originally parsed into data structures) but
            # it's currently coming from too many sources to make that
            # effective.
            try:
                encoded_args = repr(module_args.encode('utf-8'))
            except UnicodeDecodeError:
                encoded_args = repr(module_args)
            try:
                encoded_complex = repr(complex_args_json.encode('utf-8'))
            except UnicodeDecodeError:
                encoded_complex = repr(complex_args_json.encode('utf-8'))

            # these strings should be part of the 'basic' snippet which is required to be included
            module_data = module_data.replace(REPLACER_VERSION, repr(__version__))
            module_data = module_data.replace(REPLACER_SELINUX, ','.join(C.DEFAULT_SELINUX_SPECIAL_FS))
            module_data = module_data.replace(REPLACER_ARGS, encoded_args)
            module_data = module_data.replace(REPLACER_COMPLEX, encoded_complex)

            if module_style == 'new':
                facility = C.DEFAULT_SYSLOG_FACILITY
                if 'ansible_syslog_facility' in inject:
                    facility = inject['ansible_syslog_facility']
                module_data = module_data.replace('syslog.LOG_USER', "syslog.%s" % facility)

            lines = module_data.split("\n")
            shebang = None
            if lines[0].startswith("#!"):
                shebang = lines[0].strip()
                args = shlex.split(str(shebang[2:]))
                interpreter = args[0]
                interpreter_config = 'ansible_%s_interpreter' % os.path.basename(interpreter)

                if interpreter_config in inject:
                    lines[0] = shebang = "#!%s %s" % (inject[interpreter_config], " ".join(args[1:]))
                    module_data = "\n".join(lines)

            return (module_data, module_style, shebang)

