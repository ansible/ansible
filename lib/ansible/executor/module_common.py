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
import json
import os
import shlex
import zipfile
import re
import pkgutil
from ast import AST, Import, ImportFrom
from io import BytesIO

from ansible.release import __version__, __author__
from ansible import constants as C
from ansible.errors import AnsibleError, AnsiblePluginRemovedError
from ansible.executor.interpreter_discovery import InterpreterDiscoveryRequiredError
from ansible.executor.powershell import module_manifest as ps_manifest
from ansible.module_utils.common.json import AnsibleJSONEncoder
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.plugins.loader import module_utils_loader
from ansible.utils.collection_loader._collection_finder import _get_collection_metadata, _nested_dict_get

# Must import strategy and use write_locks from there
# If we import write_locks directly then we end up binding a
# variable to the object and then it never gets updated.
from ansible.executor import action_write_locks

from ansible.utils.display import Display
from collections import namedtuple


try:
    import importlib.util
    import importlib.machinery
    imp = None
except ImportError:
    import imp

# if we're on a Python that doesn't have FNFError, redefine it as IOError (since that's what we'll see)
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

display = Display()

ModuleUtilsProcessEntry = namedtuple('ModuleUtilsInfo', ['name_parts', 'is_ambiguous', 'has_redirected_child', 'is_optional'])

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
_ANSIBALLZ_WRAPPER = True # For test-module.py script to tell this is a ANSIBALLZ_WRAPPER
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
def _ansiballz_main():
%(rlimit)s
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

    # Strip cwd from sys.path to avoid potential permissions issues
    excludes = set(('', '.', scriptdir))
    sys.path = [p for p in sys.path if p not in excludes]

    import base64
    import runpy
    import shutil
    import tempfile
    import zipfile

    if sys.version_info < (3,):
        PY3 = False
    else:
        PY3 = True

    ZIPDATA = """%(zipdata)s"""

    # Note: temp_path isn't needed once we switch to zipimport
    def invoke_module(modlib_path, temp_path, json_params):
        # When installed via setuptools (including python setup.py install),
        # ansible may be installed with an easy-install.pth file.  That file
        # may load the system-wide install of ansible rather than the one in
        # the module.  sitecustomize is the only way to override that setting.
        z = zipfile.ZipFile(modlib_path, mode='a')

        # py3: modlib_path will be text, py2: it's bytes.  Need bytes at the end
        sitecustomize = u'import sys\\nsys.path.insert(0,"%%s")\\n' %%  modlib_path
        sitecustomize = sitecustomize.encode('utf-8')
        # Use a ZipInfo to work around zipfile limitation on hosts with
        # clocks set to a pre-1980 year (for instance, Raspberry Pi)
        zinfo = zipfile.ZipInfo()
        zinfo.filename = 'sitecustomize.py'
        zinfo.date_time = ( %(year)i, %(month)i, %(day)i, %(hour)i, %(minute)i, %(second)i)
        z.writestr(zinfo, sitecustomize)
        z.close()

        # Put the zipped up module_utils we got from the controller first in the python path so that we
        # can monkeypatch the right basic
        sys.path.insert(0, modlib_path)

        # Monkeypatch the parameters into basic
        from ansible.module_utils import basic
        basic._ANSIBLE_ARGS = json_params
%(coverage)s
        # Run the module!  By importing it as '__main__', it thinks it is executing as a script
        runpy.run_module(mod_name='%(module_fqn)s', init_globals=None, run_name='__main__', alter_sys=True)

        # Ansible modules must exit themselves
        print('{"msg": "New-style module did not handle its own exit", "failed": true}')
        sys.exit(1)

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

        if command == 'excommunicate':
            print('The excommunicate debug command is deprecated and will be removed in 2.11.  Use execute instead.')
            command = 'execute'

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

            # Set pythonpath to the debug dir
            sys.path.insert(0, basedir)

            # read in the args file which the user may have modified
            with open(args_path, 'rb') as f:
                json_params = f.read()

            # Monkeypatch the parameters into basic
            from ansible.module_utils import basic
            basic._ANSIBLE_ARGS = json_params

            # Run the module!  By importing it as '__main__', it thinks it is executing as a script
            runpy.run_module(mod_name='%(module_fqn)s', init_globals=None, run_name='__main__', alter_sys=True)

            # Ansible modules must exit themselves
            print('{"msg": "New-style module did not handle its own exit", "failed": true}')
            sys.exit(1)

        else:
            print('WARNING: Unknown debug command.  Doing nothing.')
            exitcode = 0

        return exitcode

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
        # Only need to use [ansible_module]_payload_ in the temp_path until we move to zipimport
        # (this helps ansible-test produce coverage stats)
        temp_path = tempfile.mkdtemp(prefix='ansible_%(ansible_module)s_payload_')

        zipped_mod = os.path.join(temp_path, 'ansible_%(ansible_module)s_payload.zip')
        with open(zipped_mod, 'wb') as modlib:
            modlib.write(base64.b64decode(ZIPDATA))

        if len(sys.argv) == 2:
            exitcode = debug(sys.argv[1], zipped_mod, ANSIBALLZ_PARAMS)
        else:
            # Note: temp_path isn't needed once we switch to zipimport
            invoke_module(zipped_mod, temp_path, ANSIBALLZ_PARAMS)
    finally:
        try:
            shutil.rmtree(temp_path)
        except (NameError, OSError):
            # tempdir creation probably failed
            pass
    sys.exit(exitcode)

if __name__ == '__main__':
    _ansiballz_main()
'''

ANSIBALLZ_COVERAGE_TEMPLATE = '''
        # Access to the working directory is required by coverage.
        # Some platforms, such as macOS, may not allow querying the working directory when using become to drop privileges.
        try:
            os.getcwd()
        except OSError:
            os.chdir('/')

        os.environ['COVERAGE_FILE'] = '%(coverage_output)s'

        import atexit

        try:
            import coverage
        except ImportError:
            print('{"msg": "Could not import `coverage` module.", "failed": true}')
            sys.exit(1)

        cov = coverage.Coverage(config_file='%(coverage_config)s')

        def atexit_coverage():
            cov.stop()
            cov.save()

        atexit.register(atexit_coverage)

        cov.start()
'''

ANSIBALLZ_COVERAGE_CHECK_TEMPLATE = '''
        try:
            if PY3:
                import importlib.util
                if importlib.util.find_spec('coverage') is None:
                    raise ImportError
            else:
                import imp
                imp.find_module('coverage')
        except ImportError:
            print('{"msg": "Could not find `coverage` module.", "failed": true}')
            sys.exit(1)
'''

ANSIBALLZ_RLIMIT_TEMPLATE = '''
    import resource

    existing_soft, existing_hard = resource.getrlimit(resource.RLIMIT_NOFILE)

    # adjust soft limit subject to existing hard limit
    requested_soft = min(existing_hard, %(rlimit_nofile)d)

    if requested_soft != existing_soft:
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (requested_soft, existing_hard))
        except ValueError:
            # some platforms (eg macOS) lie about their hard limit
            pass
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

# dirname(dirname(dirname(site-packages/ansible/executor/module_common.py) == site-packages
# Do this instead of getting site-packages from distutils.sysconfig so we work when we
# haven't been installed
site_packages = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CORE_LIBRARY_PATH_RE = re.compile(r'%s/(?P<path>ansible/modules/.*)\.(py|ps1)$' % site_packages)
COLLECTION_PATH_RE = re.compile(r'/(?P<path>ansible_collections/[^/]+/[^/]+/plugins/modules/.*)\.(py|ps1)$')

# Detect new-style Python modules by looking for required imports:
# import ansible_collections.[my_ns.my_col.plugins.module_utils.my_module_util]
# from ansible_collections.[my_ns.my_col.plugins.module_utils import my_module_util]
# import ansible.module_utils[.basic]
# from ansible.module_utils[ import basic]
# from ansible.module_utils[.basic import AnsibleModule]
# from ..module_utils[ import basic]
# from ..module_utils[.basic import AnsibleModule]
NEW_STYLE_PYTHON_MODULE_RE = re.compile(
    # Relative imports
    br'(?:from +\.{2,} *module_utils.* +import |'
    # Collection absolute imports:
    br'from +ansible_collections\.[^.]+\.[^.]+\.plugins\.module_utils.* +import |'
    br'import +ansible_collections\.[^.]+\.[^.]+\.plugins\.module_utils.*|'
    # Core absolute imports
    br'from +ansible\.module_utils.* +import |'
    br'import +ansible\.module_utils\.)'
)


class ModuleDepFinder(ast.NodeVisitor):
    def __init__(self, module_fqn, tree, is_pkg_init=False, *args, **kwargs):
        """
        Walk the ast tree for the python module.
        :arg module_fqn: The fully qualified name to reach this module in dotted notation.
            example: ansible.module_utils.basic
        :arg is_pkg_init: Inform the finder it's looking at a package init (eg __init__.py) to allow
            relative import expansion to use the proper package level without having imported it locally first.

        Save submodule[.submoduleN][.identifier] into self.submodules
        when they are from ansible.module_utils or ansible_collections packages

        self.submodules will end up with tuples like:
          - ('ansible', 'module_utils', 'basic',)
          - ('ansible', 'module_utils', 'urls', 'fetch_url')
          - ('ansible', 'module_utils', 'database', 'postgres')
          - ('ansible', 'module_utils', 'database', 'postgres', 'quote')
          - ('ansible', 'module_utils', 'database', 'postgres', 'quote')
          - ('ansible_collections', 'my_ns', 'my_col', 'plugins', 'module_utils', 'foo')

        It's up to calling code to determine whether the final element of the
        tuple are module names or something else (function, class, or variable names)
        .. seealso:: :python3:class:`ast.NodeVisitor`
        """
        super(ModuleDepFinder, self).__init__(*args, **kwargs)
        self._tree = tree  # squirrel this away so we can compare node parents to it
        self.submodules = set()
        self.optional_imports = set()
        self.module_fqn = module_fqn
        self.is_pkg_init = is_pkg_init

        self._visit_map = {
            Import: self.visit_Import,
            ImportFrom: self.visit_ImportFrom,
        }

        self.visit(tree)

    def generic_visit(self, node):
        """Overridden ``generic_visit`` that makes some assumptions about our
        use case, and improves performance by calling visitors directly instead
        of calling ``visit`` to offload calling visitors.
        """
        generic_visit = self.generic_visit
        visit_map = self._visit_map
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, (Import, ImportFrom)):
                        item.parent = node
                        visit_map[item.__class__](item)
                    elif isinstance(item, AST):
                        generic_visit(item)

    visit = generic_visit

    def visit_Import(self, node):
        """
        Handle import ansible.module_utils.MODLIB[.MODLIBn] [as asname]

        We save these as interesting submodules when the imported library is in ansible.module_utils
        or ansible.collections
        """
        for alias in node.names:
            if (alias.name.startswith('ansible.module_utils.') or
                    alias.name.startswith('ansible_collections.')):
                py_mod = tuple(alias.name.split('.'))
                self.submodules.add(py_mod)
                # if the import's parent is the root document, it's a required import, otherwise it's optional
                if node.parent != self._tree:
                    self.optional_imports.add(py_mod)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Handle from ansible.module_utils.MODLIB import [.MODLIBn] [as asname]

        Also has to handle relative imports

        We save these as interesting submodules when the imported library is in ansible.module_utils
        or ansible.collections
        """

        # FIXME: These should all get skipped:
        # from ansible.executor import module_common
        # from ...executor import module_common
        # from ... import executor (Currently it gives a non-helpful error)
        if node.level > 0:
            # if we're in a package init, we have to add one to the node level (and make it none if 0 to preserve the right slicing behavior)
            level_slice_offset = -node.level + 1 or None if self.is_pkg_init else -node.level
            if self.module_fqn:
                parts = tuple(self.module_fqn.split('.'))
                if node.module:
                    # relative import: from .module import x
                    node_module = '.'.join(parts[:level_slice_offset] + (node.module,))
                else:
                    # relative import: from . import x
                    node_module = '.'.join(parts[:level_slice_offset])
            else:
                # fall back to an absolute import
                node_module = node.module
        else:
            # absolute import: from module import x
            node_module = node.module

        # Specialcase: six is a special case because of its
        # import logic
        py_mod = None
        if node.names[0].name == '_six':
            self.submodules.add(('_six',))
        elif node_module.startswith('ansible.module_utils'):
            # from ansible.module_utils.MODULE1[.MODULEn] import IDENTIFIER [as asname]
            # from ansible.module_utils.MODULE1[.MODULEn] import MODULEn+1 [as asname]
            # from ansible.module_utils.MODULE1[.MODULEn] import MODULEn+1 [,IDENTIFIER] [as asname]
            # from ansible.module_utils import MODULE1 [,MODULEn] [as asname]
            py_mod = tuple(node_module.split('.'))

        elif node_module.startswith('ansible_collections.'):
            if node_module.endswith('plugins.module_utils') or '.plugins.module_utils.' in node_module:
                # from ansible_collections.ns.coll.plugins.module_utils import MODULE [as aname] [,MODULE2] [as aname]
                # from ansible_collections.ns.coll.plugins.module_utils.MODULE import IDENTIFIER [as aname]
                # FIXME: Unhandled cornercase (needs to be ignored):
                # from ansible_collections.ns.coll.plugins.[!module_utils].[FOO].plugins.module_utils import IDENTIFIER
                py_mod = tuple(node_module.split('.'))
            else:
                # Not from module_utils so ignore.  for instance:
                # from ansible_collections.ns.coll.plugins.lookup import IDENTIFIER
                pass

        if py_mod:
            for alias in node.names:
                self.submodules.add(py_mod + (alias.name,))
                # if the import's parent is the root document, it's a required import, otherwise it's optional
                if node.parent != self._tree:
                    self.optional_imports.add(py_mod + (alias.name,))

        self.generic_visit(node)


def _slurp(path):
    if not os.path.exists(path):
        raise AnsibleError("imported module support code does not exist at %s" % os.path.abspath(path))
    with open(path, 'rb') as fd:
        data = fd.read()
    return data


def _get_shebang(interpreter, task_vars, templar, args=tuple()):
    """
    Note not stellar API:
       Returns None instead of always returning a shebang line.  Doing it this
       way allows the caller to decide to use the shebang it read from the
       file rather than trust that we reformatted what they already have
       correctly.
    """
    interpreter_name = os.path.basename(interpreter).strip()

    # FUTURE: add logical equivalence for python3 in the case of py3-only modules

    # check for first-class interpreter config
    interpreter_config_key = "INTERPRETER_%s" % interpreter_name.upper()

    if C.config.get_configuration_definitions().get(interpreter_config_key):
        # a config def exists for this interpreter type; consult config for the value
        interpreter_out = C.config.get_config_value(interpreter_config_key, variables=task_vars)
        discovered_interpreter_config = u'discovered_interpreter_%s' % interpreter_name

        interpreter_out = templar.template(interpreter_out.strip())

        facts_from_task_vars = task_vars.get('ansible_facts', {})

        # handle interpreter discovery if requested
        if interpreter_out in ['auto', 'auto_legacy', 'auto_silent', 'auto_legacy_silent']:
            if discovered_interpreter_config not in facts_from_task_vars:
                # interpreter discovery is desired, but has not been run for this host
                raise InterpreterDiscoveryRequiredError("interpreter discovery needed",
                                                        interpreter_name=interpreter_name,
                                                        discovery_mode=interpreter_out)
            else:
                interpreter_out = facts_from_task_vars[discovered_interpreter_config]
    else:
        # a config def does not exist for this interpreter type; consult vars for a possible direct override
        interpreter_config = u'ansible_%s_interpreter' % interpreter_name

        if interpreter_config not in task_vars:
            return None, interpreter

        interpreter_out = templar.template(task_vars[interpreter_config].strip())

    shebang = u'#!' + interpreter_out

    if args:
        shebang = shebang + u' ' + u' '.join(args)

    return shebang, interpreter_out


class ModuleUtilLocatorBase:
    def __init__(self, fq_name_parts, is_ambiguous=False, child_is_redirected=False, is_optional=False):
        self._is_ambiguous = is_ambiguous
        # a child package redirection could cause intermediate package levels to be missing, eg
        # from ansible.module_utils.x.y.z import foo; if x.y.z.foo is redirected, we may not have packages on disk for
        # the intermediate packages x.y.z, so we'll need to supply empty packages for those
        self._child_is_redirected = child_is_redirected
        self._is_optional = is_optional
        self.found = False
        self.redirected = False
        self.fq_name_parts = fq_name_parts
        self.source_code = ''
        self.output_path = ''
        self.is_package = False
        self._collection_name = None
        # for ambiguous imports, we should only test for things more than one level below module_utils
        # this lets us detect erroneous imports and redirections earlier
        if is_ambiguous and len(self._get_module_utils_remainder_parts(fq_name_parts)) > 1:
            self.candidate_names = [fq_name_parts, fq_name_parts[:-1]]
        else:
            self.candidate_names = [fq_name_parts]

    @property
    def candidate_names_joined(self):
        return ['.'.join(n) for n in self.candidate_names]

    def _handle_redirect(self, name_parts):
        module_utils_relative_parts = self._get_module_utils_remainder_parts(name_parts)

        # only allow redirects from below module_utils- if above that, bail out (eg, parent package names)
        if not module_utils_relative_parts:
            return False

        try:
            collection_metadata = _get_collection_metadata(self._collection_name)
        except ValueError as ve:  # collection not found or some other error related to collection load
            if self._is_optional:
                return False
            raise AnsibleError('error processing module_util {0} loading redirected collection {1}: {2}'
                               .format('.'.join(name_parts), self._collection_name, to_native(ve)))

        routing_entry = _nested_dict_get(collection_metadata, ['plugin_routing', 'module_utils', '.'.join(module_utils_relative_parts)])
        if not routing_entry:
            return False
        # FIXME: add deprecation warning support

        dep_or_ts = routing_entry.get('tombstone')
        removed = dep_or_ts is not None
        if not removed:
            dep_or_ts = routing_entry.get('deprecation')

        if dep_or_ts:
            removal_date = dep_or_ts.get('removal_date')
            removal_version = dep_or_ts.get('removal_version')
            warning_text = dep_or_ts.get('warning_text')

            msg = 'module_util {0} has been removed'.format('.'.join(name_parts))
            if warning_text:
                msg += ' ({0})'.format(warning_text)
            else:
                msg += '.'

            display.deprecated(msg, removal_version, removed, removal_date, self._collection_name)
        if 'redirect' in routing_entry:
            self.redirected = True
            source_pkg = '.'.join(name_parts)
            self.is_package = True  # treat all redirects as packages
            redirect_target_pkg = routing_entry['redirect']

            # expand FQCN redirects
            if not redirect_target_pkg.startswith('ansible_collections'):
                split_fqcn = redirect_target_pkg.split('.')
                if len(split_fqcn) < 3:
                    raise Exception('invalid redirect for {0}: {1}'.format(source_pkg, redirect_target_pkg))
                # assume it's an FQCN, expand it
                redirect_target_pkg = 'ansible_collections.{0}.{1}.plugins.module_utils.{2}'.format(
                    split_fqcn[0],  # ns
                    split_fqcn[1],  # coll
                    '.'.join(split_fqcn[2:])  # sub-module_utils remainder
                )
            display.vvv('redirecting module_util {0} to {1}'.format(source_pkg, redirect_target_pkg))
            self.source_code = self._generate_redirect_shim_source(source_pkg, redirect_target_pkg)
            return True
        return False

    def _get_module_utils_remainder_parts(self, name_parts):
        # subclasses should override to return the name parts after module_utils
        return []

    def _get_module_utils_remainder(self, name_parts):
        # return the remainder parts as a package string
        return '.'.join(self._get_module_utils_remainder_parts(name_parts))

    def _find_module(self, name_parts):
        return False

    def _locate(self, redirect_first=True):
        for candidate_name_parts in self.candidate_names:
            if redirect_first and self._handle_redirect(candidate_name_parts):
                break

            if self._find_module(candidate_name_parts):
                break

            if not redirect_first and self._handle_redirect(candidate_name_parts):
                break

        else:  # didn't find what we were looking for- last chance for packages whose parents were redirected
            if self._child_is_redirected:  # make fake packages
                self.is_package = True
                self.source_code = ''
            else:  # nope, just bail
                return

        if self.is_package:
            path_parts = candidate_name_parts + ('__init__',)
        else:
            path_parts = candidate_name_parts
        self.found = True
        self.output_path = os.path.join(*path_parts) + '.py'
        self.fq_name_parts = candidate_name_parts

    def _generate_redirect_shim_source(self, fq_source_module, fq_target_module):
        return """
import sys
import {1} as mod

sys.modules['{0}'] = mod
""".format(fq_source_module, fq_target_module)

        # FIXME: add __repr__ impl


class LegacyModuleUtilLocator(ModuleUtilLocatorBase):
    def __init__(self, fq_name_parts, is_ambiguous=False, mu_paths=None, child_is_redirected=False):
        super(LegacyModuleUtilLocator, self).__init__(fq_name_parts, is_ambiguous, child_is_redirected)

        if fq_name_parts[0:2] != ('ansible', 'module_utils'):
            raise Exception('this class can only locate from ansible.module_utils, got {0}'.format(fq_name_parts))

        if fq_name_parts[2] == 'six':
            # FIXME: handle the ansible.module_utils.six._six case with a redirect or an internal _six attr on six itself?
            # six creates its submodules at runtime; convert all these to just 'ansible.module_utils.six'
            fq_name_parts = ('ansible', 'module_utils', 'six')
            self.candidate_names = [fq_name_parts]

        self._mu_paths = mu_paths
        self._collection_name = 'ansible.builtin'  # legacy module utils always look in ansible.builtin for redirects
        self._locate(redirect_first=False)  # let local stuff override redirects for legacy

    def _get_module_utils_remainder_parts(self, name_parts):
        return name_parts[2:]  # eg, foo.bar for ansible.module_utils.foo.bar

    def _find_module(self, name_parts):
        rel_name_parts = self._get_module_utils_remainder_parts(name_parts)

        # no redirection; try to find the module
        if len(rel_name_parts) == 1:  # direct child of module_utils, just search the top-level dirs we were given
            paths = self._mu_paths
        else:  # a nested submodule of module_utils, extend the paths given with the intermediate package names
            paths = [os.path.join(p, *rel_name_parts[:-1]) for p in
                     self._mu_paths]  # extend the MU paths with the relative bit

        if imp is None:  # python3 find module
            # find_spec needs the full module name
            self._info = info = importlib.machinery.PathFinder.find_spec('.'.join(name_parts), paths)
            if info is not None and os.path.splitext(info.origin)[1] in importlib.machinery.SOURCE_SUFFIXES:
                self.is_package = info.origin.endswith('/__init__.py')
                path = info.origin
            else:
                return False
            self.source_code = _slurp(path)
        else:  # python2 find module
            try:
                # imp just wants the leaf module/package name being searched for
                info = imp.find_module(name_parts[-1], paths)
            except ImportError:
                return False

            if info[2][2] == imp.PY_SOURCE:
                fd = info[0]
            elif info[2][2] == imp.PKG_DIRECTORY:
                self.is_package = True
                fd = open(os.path.join(info[1], '__init__.py'))
            else:
                return False

            try:
                self.source_code = fd.read()
            finally:
                fd.close()

        return True


class CollectionModuleUtilLocator(ModuleUtilLocatorBase):
    def __init__(self, fq_name_parts, is_ambiguous=False, child_is_redirected=False, is_optional=False):
        super(CollectionModuleUtilLocator, self).__init__(fq_name_parts, is_ambiguous, child_is_redirected, is_optional)

        if fq_name_parts[0] != 'ansible_collections':
            raise Exception('CollectionModuleUtilLocator can only locate from ansible_collections, got {0}'.format(fq_name_parts))
        elif len(fq_name_parts) >= 6 and fq_name_parts[3:5] != ('plugins', 'module_utils'):
            raise Exception('CollectionModuleUtilLocator can only locate below ansible_collections.(ns).(coll).plugins.module_utils, got {0}'
                            .format(fq_name_parts))

        self._collection_name = '.'.join(fq_name_parts[1:3])

        self._locate()

    def _find_module(self, name_parts):
        # synthesize empty inits for packages down through module_utils- we don't want to allow those to be shipped over, but the
        # package hierarchy needs to exist
        if len(name_parts) < 6:
            self.source_code = ''
            self.is_package = True
            return True

        # NB: we can't use pkgutil.get_data safely here, since we don't want to import/execute package/module code on
        # the controller while analyzing/assembling the module, so we'll have to manually import the collection's
        # Python package to locate it (import root collection, reassemble resource path beneath, fetch source)

        collection_pkg_name = '.'.join(name_parts[0:3])
        resource_base_path = os.path.join(*name_parts[3:])

        src = None
        # look for package_dir first, then module
        try:
            src = pkgutil.get_data(collection_pkg_name, to_native(os.path.join(resource_base_path, '__init__.py')))
        except ImportError:
            pass

        # TODO: we might want to synthesize fake inits for py3-style packages, for now they're required beneath module_utils

        if src is not None:  # empty string is OK
            self.is_package = True
        else:
            try:
                src = pkgutil.get_data(collection_pkg_name, to_native(resource_base_path + '.py'))
            except ImportError:
                pass

        if src is None:  # empty string is OK
            return False

        self.source_code = src
        return True

    def _get_module_utils_remainder_parts(self, name_parts):
        return name_parts[5:]  # eg, foo.bar for ansible_collections.ns.coll.plugins.module_utils.foo.bar


def recursive_finder(name, module_fqn, module_data, zf):
    """
    Using ModuleDepFinder, make sure we have all of the module_utils files that
    the module and its module_utils files needs. (no longer actually recursive)
    :arg name: Name of the python module we're examining
    :arg module_fqn: Fully qualified name of the python module we're scanning
    :arg module_data: string Python code of the module we're scanning
    :arg zf: An open :python:class:`zipfile.ZipFile` object that holds the Ansible module payload
        which we're assembling
    """

    # py_module_cache maps python module names to a tuple of the code in the module
    # and the pathname to the module.
    # Here we pre-load it with modules which we create without bothering to
    # read from actual files (In some cases, these need to differ from what ansible
    # ships because they're namespace packages in the module)
    # FIXME: do we actually want ns pkg behavior for these? Seems like they should just be forced to emptyish pkg stubs
    py_module_cache = {
        ('ansible',): (
            b'from pkgutil import extend_path\n'
            b'__path__=extend_path(__path__,__name__)\n'
            b'__version__="' + to_bytes(__version__) +
            b'"\n__author__="' + to_bytes(__author__) + b'"\n',
            'ansible/__init__.py'),
        ('ansible', 'module_utils'): (
            b'from pkgutil import extend_path\n'
            b'__path__=extend_path(__path__,__name__)\n',
            'ansible/module_utils/__init__.py')}

    module_utils_paths = [p for p in module_utils_loader._get_paths(subdirs=False) if os.path.isdir(p)]
    module_utils_paths.append(_MODULE_UTILS_PATH)

    # Parse the module code and find the imports of ansible.module_utils
    try:
        tree = compile(module_data, '<unknown>', 'exec', ast.PyCF_ONLY_AST)
    except (SyntaxError, IndentationError) as e:
        raise AnsibleError("Unable to import %s due to %s" % (name, e.msg))

    finder = ModuleDepFinder(module_fqn, tree)

    # the format of this set is a tuple of the module name and whether or not the import is ambiguous as a module name
    # or an attribute of a module (eg from x.y import z <-- is z a module or an attribute of x.y?)
    modules_to_process = [ModuleUtilsProcessEntry(m, True, False, is_optional=m in finder.optional_imports) for m in finder.submodules]

    # HACK: basic is currently always required since module global init is currently tied up with AnsiballZ arg input
    modules_to_process.append(ModuleUtilsProcessEntry(('ansible', 'module_utils', 'basic'), False, False, is_optional=False))

    # we'll be adding new modules inline as we discover them, so just keep going til we've processed them all
    while modules_to_process:
        modules_to_process.sort()  # not strictly necessary, but nice to process things in predictable and repeatable order
        py_module_name, is_ambiguous, child_is_redirected, is_optional = modules_to_process.pop(0)

        if py_module_name in py_module_cache:
            # this is normal; we'll often see the same module imported many times, but we only need to process it once
            continue

        if py_module_name[0:2] == ('ansible', 'module_utils'):
            module_info = LegacyModuleUtilLocator(py_module_name, is_ambiguous=is_ambiguous,
                                                  mu_paths=module_utils_paths, child_is_redirected=child_is_redirected)
        elif py_module_name[0] == 'ansible_collections':
            module_info = CollectionModuleUtilLocator(py_module_name, is_ambiguous=is_ambiguous,
                                                      child_is_redirected=child_is_redirected, is_optional=is_optional)
        else:
            # FIXME: dot-joined result
            display.warning('ModuleDepFinder improperly found a non-module_utils import %s'
                            % [py_module_name])
            continue

        # Could not find the module.  Construct a helpful error message.
        if not module_info.found:
            if is_optional:
                # this was a best-effort optional import that we couldn't find, oh well, move along...
                continue
            # FIXME: use dot-joined candidate names
            msg = 'Could not find imported module support code for {0}.  Looked for ({1})'.format(module_fqn, module_info.candidate_names_joined)
            raise AnsibleError(msg)

        # check the cache one more time with the module we actually found, since the name could be different than the input
        # eg, imported name vs module
        if module_info.fq_name_parts in py_module_cache:
            continue

        # compile the source, process all relevant imported modules
        try:
            tree = compile(module_info.source_code, '<unknown>', 'exec', ast.PyCF_ONLY_AST)
        except (SyntaxError, IndentationError) as e:
            raise AnsibleError("Unable to import %s due to %s" % (module_info.fq_name_parts, e.msg))

        finder = ModuleDepFinder('.'.join(module_info.fq_name_parts), tree, module_info.is_package)
        modules_to_process.extend(ModuleUtilsProcessEntry(m, True, False, is_optional=m in finder.optional_imports)
                                  for m in finder.submodules if m not in py_module_cache)

        # we've processed this item, add it to the output list
        py_module_cache[module_info.fq_name_parts] = (module_info.source_code, module_info.output_path)

        # ensure we process all ancestor package inits
        accumulated_pkg_name = []
        for pkg in module_info.fq_name_parts[:-1]:
            accumulated_pkg_name.append(pkg)  # we're accumulating this across iterations
            normalized_name = tuple(accumulated_pkg_name)  # extra machinations to get a hashable type (list is not)
            if normalized_name not in py_module_cache:
                modules_to_process.append(ModuleUtilsProcessEntry(normalized_name, False, module_info.redirected, is_optional=is_optional))

    for py_module_name in py_module_cache:
        py_module_file_name = py_module_cache[py_module_name][1]

        zf.writestr(py_module_file_name, py_module_cache[py_module_name][0])
        mu_file = to_text(py_module_file_name, errors='surrogate_or_strict')
        display.vvvvv("Including module_utils file %s" % mu_file)


def _is_binary(b_module_data):
    textchars = bytearray(set([7, 8, 9, 10, 12, 13, 27]) | set(range(0x20, 0x100)) - set([0x7f]))
    start = b_module_data[:1024]
    return bool(start.translate(None, textchars))


def _get_ansible_module_fqn(module_path):
    """
    Get the fully qualified name for an ansible module based on its pathname

    remote_module_fqn is the fully qualified name.  Like ansible.modules.system.ping
    Or ansible_collections.Namespace.Collection_name.plugins.modules.ping
    .. warning:: This function is for ansible modules only.  It won't work for other things
        (non-module plugins, etc)
    """
    remote_module_fqn = None

    # Is this a core module?
    match = CORE_LIBRARY_PATH_RE.search(module_path)
    if not match:
        # Is this a module in a collection?
        match = COLLECTION_PATH_RE.search(module_path)

    # We can tell the FQN for core modules and collection modules
    if match:
        path = match.group('path')
        if '.' in path:
            # FQNs must be valid as python identifiers.  This sanity check has failed.
            # we could check other things as well
            raise ValueError('Module name (or path) was not a valid python identifier')

        remote_module_fqn = '.'.join(path.split('/'))
    else:
        # Currently we do not handle modules in roles so we can end up here for that reason
        raise ValueError("Unable to determine module's fully qualified name")

    return remote_module_fqn


def _add_module_to_zip(zf, remote_module_fqn, b_module_data):
    """Add a module from ansible or from an ansible collection into the module zip"""
    module_path_parts = remote_module_fqn.split('.')

    # Write the module
    module_path = '/'.join(module_path_parts) + '.py'
    zf.writestr(module_path, b_module_data)

    # Write the __init__.py's necessary to get there
    if module_path_parts[0] == 'ansible':
        # The ansible namespace is setup as part of the module_utils setup...
        start = 2
        existing_paths = frozenset()
    else:
        # ... but ansible_collections and other toplevels are not
        start = 1
        existing_paths = frozenset(zf.namelist())

    for idx in range(start, len(module_path_parts)):
        package_path = '/'.join(module_path_parts[:idx]) + '/__init__.py'
        # If a collections module uses module_utils from a collection then most packages will have already been added by recursive_finder.
        if package_path in existing_paths:
            continue
        # Note: We don't want to include more than one ansible module in a payload at this time
        # so no need to fill the __init__.py with namespace code
        zf.writestr(package_path, b'')


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
    elif NEW_STYLE_PYTHON_MODULE_RE.search(b_module_data):
        module_style = 'new'
        module_substyle = 'python'
    elif REPLACER_WINDOWS in b_module_data:
        module_style = 'new'
        module_substyle = 'powershell'
        b_module_data = b_module_data.replace(REPLACER_WINDOWS, b'#Requires -Module Ansible.ModuleUtils.Legacy')
    elif re.search(b'#Requires -Module', b_module_data, re.IGNORECASE) \
            or re.search(b'#Requires -Version', b_module_data, re.IGNORECASE)\
            or re.search(b'#AnsibleRequires -OSVersion', b_module_data, re.IGNORECASE) \
            or re.search(b'#AnsibleRequires -Powershell', b_module_data, re.IGNORECASE) \
            or re.search(b'#AnsibleRequires -CSharpUtil', b_module_data, re.IGNORECASE):
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

    try:
        remote_module_fqn = _get_ansible_module_fqn(module_path)
    except ValueError:
        # Modules in roles currently are not found by the fqn heuristic so we
        # fallback to this.  This means that relative imports inside a module from
        # a role may fail.  Absolute imports should be used for future-proofness.
        # People should start writing collections instead of modules in roles so we
        # may never fix this
        display.debug('ANSIBALLZ: Could not determine module FQN')
        remote_module_fqn = 'ansible.modules.%s' % module_name

    if module_substyle == 'python':
        params = dict(ANSIBLE_MODULE_ARGS=module_args,)
        try:
            python_repred_params = repr(json.dumps(params, cls=AnsibleJSONEncoder, vault_to_text=True))
        except TypeError as e:
            raise AnsibleError("Unable to pass options to module, they must be JSON serializable: %s" % to_native(e))

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
            with open(cached_module_filename, 'rb') as module_data:
                zipdata = module_data.read()
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

                    # walk the module imports, looking for module_utils to send- they'll be added to the zipfile
                    recursive_finder(module_name, remote_module_fqn, b_module_data, zf)

                    display.debug('ANSIBALLZ: Writing module into payload')
                    _add_module_to_zip(zf, remote_module_fqn, b_module_data)

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
                    with open(cached_module_filename, 'rb') as f:
                        zipdata = f.read()
                except IOError:
                    raise AnsibleError('A different worker process failed to create module file. '
                                       'Look at traceback for that process for debugging information.')
        zipdata = to_text(zipdata, errors='surrogate_or_strict')

        shebang, interpreter = _get_shebang(u'/usr/bin/python', task_vars, templar)
        if shebang is None:
            shebang = u'#!/usr/bin/python'

        # FUTURE: the module cache entry should be invalidated if we got this value from a host-dependent source
        rlimit_nofile = C.config.get_config_value('PYTHON_MODULE_RLIMIT_NOFILE', variables=task_vars)

        if not isinstance(rlimit_nofile, int):
            rlimit_nofile = int(templar.template(rlimit_nofile))

        if rlimit_nofile:
            rlimit = ANSIBALLZ_RLIMIT_TEMPLATE % dict(
                rlimit_nofile=rlimit_nofile,
            )
        else:
            rlimit = ''

        coverage_config = os.environ.get('_ANSIBLE_COVERAGE_CONFIG')

        if coverage_config:
            coverage_output = os.environ['_ANSIBLE_COVERAGE_OUTPUT']

            if coverage_output:
                # Enable code coverage analysis of the module.
                # This feature is for internal testing and may change without notice.
                coverage = ANSIBALLZ_COVERAGE_TEMPLATE % dict(
                    coverage_config=coverage_config,
                    coverage_output=coverage_output,
                )
            else:
                # Verify coverage is available without importing it.
                # This will detect when a module would fail with coverage enabled with minimal overhead.
                coverage = ANSIBALLZ_COVERAGE_CHECK_TEMPLATE
        else:
            coverage = ''

        now = datetime.datetime.utcnow()
        output.write(to_bytes(ACTIVE_ANSIBALLZ_TEMPLATE % dict(
            zipdata=zipdata,
            ansible_module=module_name,
            module_fqn=remote_module_fqn,
            params=python_repred_params,
            shebang=shebang,
            coding=ENCODING_STRING,
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            second=now.second,
            coverage=coverage,
            rlimit=rlimit,
        )))
        b_module_data = output.getvalue()

    elif module_substyle == 'powershell':
        # Powershell/winrm don't actually make use of shebang so we can
        # safely set this here.  If we let the fallback code handle this
        # it can fail in the presence of the UTF8 BOM commonly added by
        # Windows text editors
        shebang = u'#!powershell'
        # create the common exec wrapper payload and set that as the module_data
        # bytes
        b_module_data = ps_manifest._create_powershell_wrapper(
            b_module_data, module_path, module_args, environment,
            async_timeout, become, become_method, become_user, become_password,
            become_flags, module_substyle, task_vars, remote_module_fqn
        )

    elif module_substyle == 'jsonargs':
        module_args_json = to_bytes(json.dumps(module_args, cls=AnsibleJSONEncoder, vault_to_text=True))

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


def get_action_args_with_defaults(action, args, defaults, templar, redirected_names=None):
    group_collection_map = {
        'acme': ['community.crypto'],
        'aws': ['amazon.aws', 'community.aws'],
        'azure': ['azure.azcollection'],
        'cpm': ['wti.remote'],
        'docker': ['community.general', 'community.docker'],
        'gcp': ['google.cloud'],
        'k8s': ['community.kubernetes', 'community.general', 'community.kubevirt', 'community.okd', 'kubernetes.core'],
        'os': ['openstack.cloud'],
        'ovirt': ['ovirt.ovirt', 'community.general'],
        'vmware': ['community.vmware'],
        'testgroup': ['testns.testcoll', 'testns.othercoll', 'testns.boguscoll']
    }

    if not redirected_names:
        redirected_names = [action]

    tmp_args = {}
    module_defaults = {}

    # Merge latest defaults into dict, since they are a list of dicts
    if isinstance(defaults, list):
        for default in defaults:
            module_defaults.update(default)

    # if I actually have defaults, template and merge
    if module_defaults:
        module_defaults = templar.template(module_defaults)

        # deal with configured group defaults first
        for default in module_defaults:
            if not default.startswith('group/'):
                continue

            group_name = default.split('group/')[-1]

            for collection_name in group_collection_map.get(group_name, []):
                try:
                    action_group = _get_collection_metadata(collection_name).get('action_groups', {})
                except ValueError:
                    # The collection may not be installed
                    continue

                if any(name for name in redirected_names if name in action_group):
                    tmp_args.update((module_defaults.get('group/%s' % group_name) or {}).copy())

        # handle specific action defaults
        for action in redirected_names:
            if action in module_defaults:
                tmp_args.update(module_defaults[action].copy())

    # direct args override all
    tmp_args.update(args)

    return tmp_args
