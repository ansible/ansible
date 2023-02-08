# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import errno
import json
import os
import pkgutil
import random
import re

from ansible.module_utils.compat.version import LooseVersion

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.compat.importlib import import_module
from ansible.plugins.loader import ps_module_utils_loader
from ansible.utils.collection_loader import resource_from_fqcr


class PSModuleDepFinder(object):

    def __init__(self):
        # This is also used by validate-modules to get a module's required utils in base and a collection.
        self.ps_modules = dict()
        self.exec_scripts = dict()

        # by defining an explicit dict of cs utils and where they are used, we
        # can potentially save time by not adding the type multiple times if it
        # isn't needed
        self.cs_utils_wrapper = dict()
        self.cs_utils_module = dict()

        self.ps_version = None
        self.os_version = None
        self.become = False

        self._re_cs_module = [
            # Reference C# module_util in another C# util, this must always be the fully qualified name.
            # 'using ansible_collections.{namespace}.{collection}.plugins.module_utils.{name}'
            re.compile(to_bytes(r'(?i)^using\s((Ansible\..+)|'
                                r'(ansible_collections\.\w+\.\w+\.plugins\.module_utils\.[\w\.]+));\s*$')),
        ]

        self._re_cs_in_ps_module = [
            # Reference C# module_util in a PowerShell module
            # '#AnsibleRequires -CSharpUtil Ansible.{name}'
            # '#AnsibleRequires -CSharpUtil ansible_collections.{namespace}.{collection}.plugins.module_utils.{name}'
            # '#AnsibleRequires -CSharpUtil ..module_utils.{name}'
            # Can have '-Optional' at the end to denote the util is optional
            re.compile(to_bytes(r'(?i)^#\s*ansiblerequires\s+-csharputil\s+((Ansible\.[\w\.]+)|'
                                r'(ansible_collections\.\w+\.\w+\.plugins\.module_utils\.[\w\.]+)|'
                                r'(\.[\w\.]+))(?P<optional>\s+-Optional){0,1}')),
        ]

        self._re_ps_module = [
            # Original way of referencing a builtin module_util
            # '#Requires -Module Ansible.ModuleUtils.{name}
            re.compile(to_bytes(r'(?i)^#\s*requires\s+\-module(?:s?)\s*(Ansible\.ModuleUtils\..+)')),
            # New way of referencing a builtin and collection module_util
            # '#AnsibleRequires -PowerShell Ansible.ModuleUtils.{name}'
            # '#AnsibleRequires -PowerShell ansible_collections.{namespace}.{collection}.plugins.module_utils.{name}'
            # '#AnsibleRequires -PowerShell ..module_utils.{name}'
            # Can have '-Optional' at the end to denote the util is optional
            re.compile(to_bytes(r'(?i)^#\s*ansiblerequires\s+-powershell\s+((Ansible\.ModuleUtils\.[\w\.]+)|'
                                r'(ansible_collections\.\w+\.\w+\.plugins\.module_utils\.[\w\.]+)|'
                                r'(\.[\w\.]+))(?P<optional>\s+-Optional){0,1}')),
        ]

        self._re_wrapper = re.compile(to_bytes(r'(?i)^#\s*ansiblerequires\s+-wrapper\s+(\w*)'))
        self._re_ps_version = re.compile(to_bytes(r'(?i)^#requires\s+\-version\s+([0-9]+(\.[0-9]+){0,3})$'))
        self._re_os_version = re.compile(to_bytes(r'(?i)^#ansiblerequires\s+\-osversion\s+([0-9]+(\.[0-9]+){0,3})$'))
        self._re_become = re.compile(to_bytes(r'(?i)^#ansiblerequires\s+\-become$'))

    def scan_module(self, module_data, fqn=None, wrapper=False, powershell=True):
        lines = module_data.split(b'\n')
        module_utils = set()
        if wrapper:
            cs_utils = self.cs_utils_wrapper
        else:
            cs_utils = self.cs_utils_module

        if powershell:
            checks = [
                # PS module contains '#Requires -Module Ansible.ModuleUtils.*'
                # PS module contains '#AnsibleRequires -Powershell Ansible.*' (or collections module_utils ref)
                (self._re_ps_module, self.ps_modules, ".psm1"),
                # PS module contains '#AnsibleRequires -CSharpUtil Ansible.*' (or collections module_utils ref)
                (self._re_cs_in_ps_module, cs_utils, ".cs"),
            ]
        else:
            checks = [
                # CS module contains 'using Ansible.*;' or 'using ansible_collections.ns.coll.plugins.module_utils.*;'
                (self._re_cs_module, cs_utils, ".cs"),
            ]

        for line in lines:
            for check in checks:
                for pattern in check[0]:
                    match = pattern.match(line)
                    if match:
                        # tolerate windows line endings by stripping any remaining
                        # newline chars
                        module_util_name = to_text(match.group(1).rstrip())
                        match_dict = match.groupdict()
                        optional = match_dict.get('optional', None) is not None

                        if module_util_name not in check[1].keys():
                            module_utils.add((module_util_name, check[2], fqn, optional))

                        break

            if powershell:
                ps_version_match = self._re_ps_version.match(line)
                if ps_version_match:
                    self._parse_version_match(ps_version_match, "ps_version")

                os_version_match = self._re_os_version.match(line)
                if os_version_match:
                    self._parse_version_match(os_version_match, "os_version")

                # once become is set, no need to keep on checking recursively
                if not self.become:
                    become_match = self._re_become.match(line)
                    if become_match:
                        self.become = True

            if wrapper:
                wrapper_match = self._re_wrapper.match(line)
                if wrapper_match:
                    self.scan_exec_script(wrapper_match.group(1).rstrip())

        # recursively drill into each Requires to see if there are any more
        # requirements
        for m in set(module_utils):
            self._add_module(*m, wrapper=wrapper)

    def scan_exec_script(self, name):
        # scans lib/ansible/executor/powershell for scripts used in the module
        # exec side. It also scans these scripts for any dependencies
        name = to_text(name)
        if name in self.exec_scripts.keys():
            return

        data = pkgutil.get_data("ansible.executor.powershell", to_native(name + ".ps1"))
        if data is None:
            raise AnsibleError("Could not find executor powershell script "
                               "for '%s'" % name)

        b_data = to_bytes(data)

        # remove comments to reduce the payload size in the exec wrappers
        if C.DEFAULT_DEBUG:
            exec_script = b_data
        else:
            exec_script = _strip_comments(b_data)
        self.exec_scripts[name] = to_bytes(exec_script)
        self.scan_module(b_data, wrapper=True, powershell=True)

    def _add_module(self, name, ext, fqn, optional, wrapper=False):
        m = to_text(name)

        util_fqn = None

        if m.startswith("Ansible."):
            # Builtin util, use plugin loader to get the data
            mu_path = ps_module_utils_loader.find_plugin(m, ext)

            if not mu_path:
                if optional:
                    return

                raise AnsibleError('Could not find imported module support code '
                                   'for \'%s\'' % m)

            module_util_data = to_bytes(_slurp(mu_path))
        else:
            # Collection util, load the package data based on the util import.

            submodules = m.split(".")
            if m.startswith('.'):
                fqn_submodules = fqn.split('.')
                for submodule in submodules:
                    if submodule:
                        break
                    del fqn_submodules[-1]

                submodules = fqn_submodules + [s for s in submodules if s]

            n_package_name = to_native('.'.join(submodules[:-1]), errors='surrogate_or_strict')
            n_resource_name = to_native(submodules[-1] + ext, errors='surrogate_or_strict')

            try:
                module_util = import_module(n_package_name)
                pkg_data = pkgutil.get_data(n_package_name, n_resource_name)
                if pkg_data is None:
                    raise ImportError("No package data found")

                module_util_data = to_bytes(pkg_data, errors='surrogate_or_strict')
                util_fqn = to_text("%s.%s " % (n_package_name, submodules[-1]), errors='surrogate_or_strict')

                # Get the path of the util which is required for coverage collection.
                resource_paths = list(module_util.__path__)
                if len(resource_paths) != 1:
                    # This should never happen with a collection but we are just being defensive about it.
                    raise AnsibleError("Internal error: Referenced module_util package '%s' contains 0 or multiple "
                                       "import locations when we only expect 1." % n_package_name)
                mu_path = os.path.join(resource_paths[0], n_resource_name)
            except (ImportError, OSError) as err:
                if getattr(err, "errno", errno.ENOENT) == errno.ENOENT:
                    if optional:
                        return

                    raise AnsibleError('Could not find collection imported module support code for \'%s\''
                                       % to_native(m))

                else:
                    raise

        util_info = {
            'data': module_util_data,
            'path': to_text(mu_path),
        }
        if ext == ".psm1":
            self.ps_modules[m] = util_info
        else:
            if wrapper:
                self.cs_utils_wrapper[m] = util_info
            else:
                self.cs_utils_module[m] = util_info
        self.scan_module(module_util_data, fqn=util_fqn, wrapper=wrapper, powershell=(ext == ".psm1"))

    def _parse_version_match(self, match, attribute):
        new_version = to_text(match.group(1)).rstrip()

        # PowerShell cannot cast a string of "1" to Version, it must have at
        # least the major.minor for it to be valid so we append 0
        if match.group(2) is None:
            new_version = "%s.0" % new_version

        existing_version = getattr(self, attribute, None)
        if existing_version is None:
            setattr(self, attribute, new_version)
        else:
            # determine which is the latest version and set that
            if LooseVersion(new_version) > LooseVersion(existing_version):
                setattr(self, attribute, new_version)


def _slurp(path):
    if not os.path.exists(path):
        raise AnsibleError("imported module support code does not exist at %s"
                           % os.path.abspath(path))
    fd = open(path, 'rb')
    data = fd.read()
    fd.close()
    return data


def _strip_comments(source):
    # Strip comments and blank lines from the wrapper
    buf = []
    start_block = False
    for line in source.splitlines():
        l = line.strip()

        if start_block and l.endswith(b'#>'):
            start_block = False
            continue
        elif start_block:
            continue
        elif l.startswith(b'<#'):
            start_block = True
            continue
        elif not l or l.startswith(b'#'):
            continue

        buf.append(line)
    return b'\n'.join(buf)


def _create_powershell_wrapper(b_module_data, module_path, module_args,
                               environment, async_timeout, become,
                               become_method, become_user, become_password,
                               become_flags, substyle, task_vars, module_fqn):
    # creates the manifest/wrapper used in PowerShell/C# modules to enable
    # things like become and async - this is also called in action/script.py

    # FUTURE: add process_wrapper.ps1 to run module_wrapper in a new process
    # if running under a persistent connection and substyle is C# so we
    # don't have type conflicts
    finder = PSModuleDepFinder()
    if substyle != 'script':
        # don't scan the module for util dependencies and other Ansible related
        # flags if the substyle is 'script' which is set by action/script
        finder.scan_module(b_module_data, fqn=module_fqn, powershell=(substyle == "powershell"))

    module_wrapper = "module_%s_wrapper" % substyle
    exec_manifest = dict(
        module_entry=to_text(base64.b64encode(b_module_data)),
        powershell_modules=dict(),
        csharp_utils=dict(),
        csharp_utils_module=list(),  # csharp_utils only required by a module
        module_args=module_args,
        actions=[module_wrapper],
        environment=environment,
        encoded_output=False,
    )
    finder.scan_exec_script(module_wrapper)

    if async_timeout > 0:
        finder.scan_exec_script('exec_wrapper')
        finder.scan_exec_script('async_watchdog')
        finder.scan_exec_script('async_wrapper')

        exec_manifest["actions"].insert(0, 'async_watchdog')
        exec_manifest["actions"].insert(0, 'async_wrapper')
        exec_manifest["async_jid"] = f'j{random.randint(0, 999999999999)}'
        exec_manifest["async_timeout_sec"] = async_timeout
        exec_manifest["async_startup_timeout"] = C.config.get_config_value("WIN_ASYNC_STARTUP_TIMEOUT", variables=task_vars)

    if become and resource_from_fqcr(become_method) == 'runas':  # runas and namespace.collection.runas
        finder.scan_exec_script('exec_wrapper')
        finder.scan_exec_script('become_wrapper')

        exec_manifest["actions"].insert(0, 'become_wrapper')
        exec_manifest["become_user"] = become_user
        exec_manifest["become_password"] = become_password
        exec_manifest['become_flags'] = become_flags

    exec_manifest['min_ps_version'] = finder.ps_version
    exec_manifest['min_os_version'] = finder.os_version
    if finder.become and 'become_wrapper' not in exec_manifest['actions']:
        finder.scan_exec_script('exec_wrapper')
        finder.scan_exec_script('become_wrapper')

        exec_manifest['actions'].insert(0, 'become_wrapper')
        exec_manifest['become_user'] = 'SYSTEM'
        exec_manifest['become_password'] = None
        exec_manifest['become_flags'] = None

    coverage_manifest = dict(
        module_path=module_path,
        module_util_paths=dict(),
        output=None,
    )
    coverage_output = C.config.get_config_value('COVERAGE_REMOTE_OUTPUT', variables=task_vars)
    if coverage_output and substyle == 'powershell':
        finder.scan_exec_script('coverage_wrapper')
        coverage_manifest['output'] = coverage_output

        coverage_enabled = C.config.get_config_value('COVERAGE_REMOTE_PATHS', variables=task_vars)
        coverage_manifest['path_filter'] = coverage_enabled

    # make sure Ansible.ModuleUtils.AddType is added if any C# utils are used
    if len(finder.cs_utils_wrapper) > 0 or len(finder.cs_utils_module) > 0:
        finder._add_module(b"Ansible.ModuleUtils.AddType", ".psm1", None, False,
                           wrapper=False)

    # exec_wrapper is only required to be part of the payload if using
    # become or async, to save on payload space we check if exec_wrapper has
    # already been added, and remove it manually if it hasn't later
    exec_required = "exec_wrapper" in finder.exec_scripts.keys()
    finder.scan_exec_script("exec_wrapper")
    # must contain an empty newline so it runs the begin/process/end block
    finder.exec_scripts["exec_wrapper"] += b"\n\n"

    exec_wrapper = finder.exec_scripts["exec_wrapper"]
    if not exec_required:
        finder.exec_scripts.pop("exec_wrapper")

    for name, data in finder.exec_scripts.items():
        b64_data = to_text(base64.b64encode(data))
        exec_manifest[name] = b64_data

    for name, data in finder.ps_modules.items():
        b64_data = to_text(base64.b64encode(data['data']))
        exec_manifest['powershell_modules'][name] = b64_data
        coverage_manifest['module_util_paths'][name] = data['path']

    cs_utils = {}
    for cs_util in [finder.cs_utils_wrapper, finder.cs_utils_module]:
        for name, data in cs_util.items():
            cs_utils[name] = data['data']

    for name, data in cs_utils.items():
        b64_data = to_text(base64.b64encode(data))
        exec_manifest['csharp_utils'][name] = b64_data
    exec_manifest['csharp_utils_module'] = list(finder.cs_utils_module.keys())

    # To save on the data we are sending across we only add the coverage info if coverage is being run
    if 'coverage_wrapper' in exec_manifest:
        exec_manifest['coverage'] = coverage_manifest

    b_json = to_bytes(json.dumps(exec_manifest))
    # delimit the payload JSON from the wrapper to keep sensitive contents out of scriptblocks (which can be logged)
    b_data = exec_wrapper + b'\0\0\0\0' + b_json
    return b_data
