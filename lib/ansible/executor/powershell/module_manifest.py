# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import base64
import dataclasses
import errno
import json
import os
import pkgutil
import secrets
import re
import typing as t

from importlib import import_module

from ansible.module_utils.compat.version import LooseVersion

from ansible import constants as C
from ansible.module_utils.common.json import Direction, get_module_encoder
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.plugins.become import BecomeBase
from ansible.plugins.become.runas import BecomeModule as RunasBecomeModule
from ansible.plugins.loader import ps_module_utils_loader


@dataclasses.dataclass(frozen=True)
class _ExecManifest:
    scripts: dict[str, _ScriptInfo] = dataclasses.field(default_factory=dict)
    actions: list[_ManifestAction] = dataclasses.field(default_factory=list)
    signed_hashlist: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True, kw_only=True)
class _ScriptInfo:
    content: dataclasses.InitVar[bytes]
    path: str
    script: str = dataclasses.field(init=False)

    def __post_init__(self, content: bytes) -> None:
        object.__setattr__(self, 'script', base64.b64encode(content).decode())


@dataclasses.dataclass(frozen=True, kw_only=True)
class _ManifestAction:
    name: str
    params: dict[str, object] = dataclasses.field(default_factory=dict)
    secure_params: dict[str, object] = dataclasses.field(default_factory=dict)


class PSModuleDepFinder(object):

    def __init__(self) -> None:
        # This is also used by validate-modules to get a module's required utils in base and a collection.
        self.scripts: dict[str, _ScriptInfo] = {}
        self.signed_hashlist: set[str] = set()

        if builtin_hashlist := _get_powershell_signed_hashlist():
            self.signed_hashlist.add(builtin_hashlist.path)
            self.scripts[builtin_hashlist.path] = builtin_hashlist

        self._util_deps: dict[str, set[str]] = {}

        self.ps_version: str | None = None
        self.os_version: str | None = None
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

        self._re_ps_version = re.compile(to_bytes(r'(?i)^#requires\s+\-version\s+([0-9]+(\.[0-9]+){0,3})$'))
        self._re_os_version = re.compile(to_bytes(r'(?i)^#ansiblerequires\s+\-osversion\s+([0-9]+(\.[0-9]+){0,3})$'))
        self._re_become = re.compile(to_bytes(r'(?i)^#ansiblerequires\s+\-become$'))

    def scan_exec_script(self, name: str) -> None:
        # scans lib/ansible/executor/powershell for scripts used in the module
        # exec side. It also scans these scripts for any dependencies
        if name in self.scripts:
            return

        exec_code = _get_powershell_script(name)
        self.scripts[name] = _ScriptInfo(
            content=exec_code,
            path=name,
        )
        self.scan_module(exec_code, powershell=True)

    def scan_module(
        self,
        module_data: bytes,
        fqn: str | None = None,
        powershell: bool = True,
    ) -> set[str]:
        lines = module_data.split(b'\n')
        module_utils: set[tuple[str, str, bool]] = set()

        if fqn and fqn.startswith("ansible_collections."):
            submodules = fqn.split('.')
            collection_name = '.'.join(submodules[:3])

            collection_hashlist = _get_powershell_signed_hashlist(collection_name)
            if collection_hashlist and collection_hashlist.path not in self.signed_hashlist:
                self.signed_hashlist.add(collection_hashlist.path)
                self.scripts[collection_hashlist.path] = collection_hashlist

        if powershell:
            checks = [
                # PS module contains '#Requires -Module Ansible.ModuleUtils.*'
                # PS module contains '#AnsibleRequires -Powershell Ansible.*' (or collections module_utils ref)
                (self._re_ps_module, ".psm1"),
                # PS module contains '#AnsibleRequires -CSharpUtil Ansible.*' (or collections module_utils ref)
                (self._re_cs_in_ps_module, ".cs"),
            ]
        else:
            checks = [
                # CS module contains 'using Ansible.*;' or 'using ansible_collections.ns.coll.plugins.module_utils.*;'
                (self._re_cs_module, ".cs"),
            ]

        for line in lines:
            for patterns, util_extension in checks:
                for pattern in patterns:
                    match = pattern.match(line)
                    if match:
                        # tolerate windows line endings by stripping any remaining
                        # newline chars
                        module_util_name = to_text(match.group(1).rstrip())
                        match_dict = match.groupdict()
                        optional = match_dict.get('optional', None) is not None
                        module_utils.add((module_util_name, util_extension, optional))
                        break

            if not powershell:
                continue

            if ps_version_match := self._re_ps_version.match(line):
                self._parse_version_match(ps_version_match, "ps_version")

            if os_version_match := self._re_os_version.match(line):
                self._parse_version_match(os_version_match, "os_version")

            # once become is set, no need to keep on checking recursively
            if not self.become and self._re_become.match(line):
                self.become = True

        dependencies: set[str] = set()
        for name, ext, optional in set(module_utils):
            util_name = self._scan_module_util(name, ext, fqn, optional)
            if util_name:
                dependencies.add(util_name)
                util_deps = self._util_deps[util_name]
                dependencies.update(util_deps)

        return dependencies

    def _scan_module_util(
        self,
        name: str,
        ext: str,
        module_fqn: str | None,
        optional: bool,
    ) -> str | None:
        util_name: str
        util_path: str
        util_data: bytes
        util_fqn: str | None = None

        if name.startswith("Ansible."):
            # Builtin util, or the old role module_utils reference.
            util_name = f"{name}{ext}"

            if util_name in self._util_deps:
                return util_name

            util_path = ps_module_utils_loader.find_plugin(name, ext)
            if not util_path or not os.path.exists(util_path):
                if optional:
                    return None

                raise AnsibleError(f"Could not find imported module util '{name}'")

            with open(util_path, 'rb') as mu_file:
                util_data = mu_file.read()

        else:
            # Collection util, load the package data based on the util import.
            submodules = name.split(".")
            if name.startswith('.'):
                fqn_submodules = (module_fqn or "").split('.')
                for submodule in submodules:
                    if submodule:
                        break
                    del fqn_submodules[-1]

                submodules = fqn_submodules + [s for s in submodules if s]

            util_package = '.'.join(submodules[:-1])
            util_resource_name = f"{submodules[-1]}{ext}"
            util_fqn = f"{util_package}.{submodules[-1]}"
            util_name = f"{util_package}.{util_resource_name}"

            if util_name in self._util_deps:
                return util_name

            try:
                module_util = import_module(util_package)
                util_code = pkgutil.get_data(util_package, util_resource_name)
                if util_code is None:
                    raise ImportError("No package data found")
                util_data = util_code

                # Get the path of the util which is required for coverage collection.
                resource_paths = list(module_util.__path__)
                if len(resource_paths) != 1:
                    # This should never happen with a collection but we are just being defensive about it.
                    raise AnsibleError(f"Internal error: Referenced module_util package '{util_package}' contains 0 "
                                       "or multiple import locations when we only expect 1.")

                util_path = os.path.join(resource_paths[0], util_resource_name)
            except (ImportError, OSError) as err:
                if getattr(err, "errno", errno.ENOENT) == errno.ENOENT:
                    if optional:
                        return None

                    raise AnsibleError(f"Could not find collection imported module support code for '{name}'")

                else:
                    raise

        # This is important to be set before scan_module is called to avoid
        # recursive dependencies.
        self.scripts[util_name] = _ScriptInfo(
            content=util_data,
            path=util_path,
        )

        # It is important this is set before calling scan_module to ensure
        # recursive dependencies don't result in an infinite loop.
        dependencies = self._util_deps[util_name] = set()

        util_deps = self.scan_module(util_data, fqn=util_fqn, powershell=(ext == ".psm1"))
        dependencies.update(util_deps)
        for dep in dependencies:
            if dep_list := self._util_deps.get(dep):
                dependencies.update(dep_list)

        if ext == ".cs":
            # Any C# code requires the AddType.psm1 module to load.
            dependencies.add("Ansible.ModuleUtils.AddType.psm1")
            self._scan_module_util("Ansible.ModuleUtils.AddType", ".psm1", None, False)

        return util_name

    def _parse_version_match(self, match: re.Match, attribute: str) -> None:
        new_version = to_text(match.group(1)).rstrip()

        # PowerShell cannot cast a string of "1" to Version, it must have at
        # least the major.minor for it to be valid so we append 0
        if match.group(2) is None:
            new_version = f"{new_version}.0"

        existing_version = getattr(self, attribute, None)
        if existing_version is None:
            setattr(self, attribute, new_version)
        else:
            # determine which is the latest version and set that
            if LooseVersion(new_version) > LooseVersion(existing_version):
                setattr(self, attribute, new_version)


def _bootstrap_powershell_script(
    name: str,
    parameters: dict[str, t.Any] | None = None,
    *,
    has_input: bool = False,
) -> tuple[str, bytes]:
    """Build bootstrap wrapper for specified script.

    Builds the bootstrap wrapper and input needed to run the specified executor
    PowerShell script specified.

    :param name: The name of the PowerShell script to run.
    :param parameters: The parameters to pass to the script.
    :param has_input: The script will be provided with input data.
    :return: The bootstrap wrapper and input to provide to it.
    """
    exec_manifest = _ExecManifest()

    script = _get_powershell_script(name)
    exec_manifest.scripts[name] = _ScriptInfo(
        content=script,
        path=name,
    )

    exec_manifest.actions.append(
        _ManifestAction(
            name=name,
            params=parameters or {},
        )
    )

    if hashlist := _get_powershell_signed_hashlist():
        exec_manifest.signed_hashlist.append(hashlist.path)
        exec_manifest.scripts[hashlist.path] = hashlist

    bootstrap_wrapper = _get_powershell_script("bootstrap_wrapper.ps1")
    bootstrap_input = _get_bootstrap_input(exec_manifest)
    if has_input:
        bootstrap_input += b"\n\0\0\0\0\n"

    return bootstrap_wrapper.decode(), bootstrap_input


def _get_powershell_script(
    name: str,
) -> bytes:
    """Get the requested PowerShell script.

    Gets the script stored in the ansible.executore.powershell package.

    :param name: The name of the PowerShell script to retrieve.
    :return: The contents of the requested PowerShell script as a byte string.
    """
    package_name = 'ansible.executor.powershell'

    code = pkgutil.get_data(package_name, name)
    if code is None:
        raise AnsibleFileNotFound(f"Could not find powershell script '{package_name}.{name}'")

    try:
        sig_data = pkgutil.get_data(package_name, f"{name}.authenticode")
    except FileNotFoundError:
        sig_data = None

    if sig_data:
        code = code + b"\r\n" + b"\r\n".join(sig_data.splitlines()) + b"\r\n"

    return code


def _create_powershell_wrapper(
    *,
    name: str,
    module_data: bytes,
    module_path: str,
    module_args: dict[t.Any, t.Any],
    environment: dict[str, str],
    async_timeout: int,
    become_plugin: BecomeBase | None,
    substyle: t.Literal["powershell", "script"],
    task_vars: dict[str, t.Any],
    profile: str,
) -> bytes:
    """Creates module or script wrapper for PowerShell.

    Creates the input data to provide to bootstrap_wrapper.ps1 when running a
    PowerShell module or script.

    :param name: The fully qualified name of the module or script filename (without extension).
    :param module_data: The data of the module or script.
    :param module_path: The path of the module or script.
    :param module_args: The arguments to pass to the module or script.
    :param environment: The environment variables to set when running the module or script.
    :param async_timeout: The timeout to use for async execution or 0 for no async.
    :param become_plugin: The become plugin to use for privilege escalation or None for no become.
    :param substyle: The substyle of the module or script to run [powershell or script].
    :param task_vars: The task variables used on the task.

    :return: The input data for bootstrap_wrapper.ps1 as a byte string.
    """

    actions: list[_ManifestAction] = []
    finder = PSModuleDepFinder()
    finder.scan_exec_script('module_wrapper.ps1')

    ext = os.path.splitext(module_path)[1]
    name_with_ext = f"{name}{ext}"
    finder.scripts[name_with_ext] = _ScriptInfo(
        content=module_data,
        path=module_path,
    )

    module_params: dict[str, t.Any] = {
        'Script': name_with_ext,
        'Environment': environment,
    }
    if substyle != 'script':
        module_deps = finder.scan_module(
            module_data,
            fqn=name,
            powershell=True,
        )
        cs_deps = []
        ps_deps = []
        for dep in module_deps:
            if dep.endswith('.cs'):
                cs_deps.append(dep)
            else:
                ps_deps.append(dep)

        module_params |= {
            'Variables': [
                {
                    'Name': 'complex_args',
                    'Value': _prepare_module_args(module_args, profile),
                    'Scope': 'Global',
                },
            ],
            'CSharpModules': cs_deps,
            'PowerShellModules': ps_deps,
            'ForModule': True,
        }

    if become_plugin or finder.become:
        become_script = 'become_wrapper.ps1'
        become_params: dict[str, t.Any] = {
            'BecomeUser': 'SYSTEM',
        }
        become_secure_params: dict[str, t.Any] = {}

        if become_plugin:
            if not isinstance(become_plugin, RunasBecomeModule):
                msg = f"Become plugin {become_plugin.name} is not supported by the Windows exec wrapper. Make sure to set the become method to runas."
                raise AnsibleError(msg)

            become_script, become_params, become_secure_params = become_plugin._build_powershell_wrapper_action()

        finder.scan_exec_script('exec_wrapper.ps1')
        finder.scan_exec_script(become_script)
        actions.append(
            _ManifestAction(
                name=become_script,
                params=become_params,
                secure_params=become_secure_params,
            )
        )

    if async_timeout > 0:
        finder.scan_exec_script('bootstrap_wrapper.ps1')
        finder.scan_exec_script('exec_wrapper.ps1')

        async_dir = environment.get('ANSIBLE_ASYNC_DIR', None)
        if not async_dir:
            raise AnsibleError("The environment variable 'ANSIBLE_ASYNC_DIR' is not set.")

        finder.scan_exec_script('async_wrapper.ps1')
        actions.append(
            _ManifestAction(
                name='async_wrapper.ps1',
                params={
                    'AsyncDir': async_dir,
                    'AsyncJid': f'j{secrets.randbelow(999999999999)}',
                    'StartupTimeout': C.config.get_config_value("WIN_ASYNC_STARTUP_TIMEOUT", variables=task_vars),
                },
            )
        )

        finder.scan_exec_script('async_watchdog.ps1')
        actions.append(
            _ManifestAction(
                name='async_watchdog.ps1',
                params={
                    'Timeout': async_timeout,
                },
            )
        )

    coverage_output = C.config.get_config_value('COVERAGE_REMOTE_OUTPUT', variables=task_vars)
    if coverage_output and substyle == 'powershell':
        path_filter = C.config.get_config_value('COVERAGE_REMOTE_PATHS', variables=task_vars)

        finder.scan_exec_script('coverage_wrapper.ps1')
        actions.append(
            _ManifestAction(
                name='coverage_wrapper.ps1',
                params={
                    'ModuleName': name_with_ext,
                    'OutputPath': coverage_output,
                    'PathFilter': path_filter,
                },
            )
        )

    actions.append(
        _ManifestAction(
            name='module_wrapper.ps1',
            params=module_params,
        ),
    )

    temp_path: str | None = None
    for temp_key in ['_ansible_tmpdir', '_ansible_remote_tmp']:
        if temp_value := module_args.get(temp_key, None):
            temp_path = temp_value
            break

    exec_manifest = _ExecManifest(
        scripts=finder.scripts,
        actions=actions,
        signed_hashlist=list(finder.signed_hashlist),
    )

    return _get_bootstrap_input(
        exec_manifest,
        min_os_version=finder.os_version,
        min_ps_version=finder.ps_version,
        temp_path=temp_path,
    )


def _get_bootstrap_input(
    manifest: _ExecManifest,
    min_os_version: str | None = None,
    min_ps_version: str | None = None,
    temp_path: str | None = None,
) -> bytes:
    """Gets the input for bootstrap_wrapper.ps1

    Gets the input needed to send to bootstrap_wrapper.ps1 to run code through
    exec_wrapper.ps1.

    :param manifest: The exec wrapper manifest of scripts and actions to run.
    :param min_os_version: The minimum OS version required to run the scripts.
    :param min_ps_version: The minimum PowerShell version required to run the scripts.
    :param temp_path: The temporary path to use for the scripts if needed.
    :return: The input for bootstrap_wrapper.ps1 as a byte string.
    """
    bootstrap_manifest = {
        'name': 'exec_wrapper',
        'script': _get_powershell_script("exec_wrapper.ps1").decode(),
        'params': {
            'MinOSVersion': min_os_version,
            'MinPSVersion': min_ps_version,
            'TempPath': temp_path,
        },
    }

    bootstrap_input = json.dumps(bootstrap_manifest, ensure_ascii=True)
    exec_input = json.dumps(dataclasses.asdict(manifest))
    return f"{bootstrap_input}\n\0\0\0\0\n{exec_input}".encode()


def _prepare_module_args(module_args: dict[str, t.Any], profile: str) -> dict[str, t.Any]:
    """
    Serialize the module args with the specified profile and deserialize them with the Python built-in JSON decoder.
    This is used to facilitate serializing module args with a different encoder (profile) than is used for the manifest.
    """
    encoder = get_module_encoder(profile, Direction.CONTROLLER_TO_MODULE)

    return json.loads(json.dumps(module_args, cls=encoder))


def _get_powershell_signed_hashlist(
    collection: str | None = None,
) -> _ScriptInfo | None:
    """Gets the signed hashlist script stored in either the Ansible package or for
    the collection specified.

    :param collection: The collection namespace to get the signed hashlist for or None for the builtin.
    :return: The _ScriptInfo payload of the signed hashlist script if found, None if not.
    """
    resource = 'ansible.config' if collection is None else f"{collection}.meta"
    signature_file = 'powershell_signatures.psd1'

    try:
        sig_data = pkgutil.get_data(resource, signature_file)
    except FileNotFoundError:
        sig_data = None

    if sig_data:
        resource_path = f"{resource}.{signature_file}"
        return _ScriptInfo(content=sig_data, path=resource_path)

    return None
