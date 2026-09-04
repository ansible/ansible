from __future__ import annotations

import dataclasses
import json

import typing as t

from ansible.module_utils._internal._ansiballz import _extensions
from ansible.module_utils._internal._ansiballz._extensions import _debugpy, _pydevd, _coverage
from ansible.constants import config


class ExtensionManager:
    """AnsiballZ extension manager."""

    def __init__(
        self,
        pydevd: _pydevd.Options | None = None,
        debugpy: _debugpy.Options | None = None,
        coverage: _coverage.Options | None = None,
    ) -> None:
        options = dict(
            _pydevd=pydevd,
            _debugpy=debugpy,
            _coverage=coverage,
        )

        self._pydevd = pydevd
        self._debugpy = debugpy
        self._coverage = coverage
        self._extension_names = tuple(name for name, option in options.items() if option)
        self._module_names = tuple(f'{_extensions.__name__}.{name}' for name in self._extension_names)

        self.source_mapping: dict[str, str] = {}

    @property
    def debugger_enabled(self) -> bool:
        """Returns True if the debugger extension is enabled, otherwise False."""
        return bool(self._pydevd or self._debugpy)

    @property
    def extension_names(self) -> tuple[str, ...]:
        """Names of extensions to include in the AnsiballZ payload."""
        return self._extension_names

    @property
    def module_names(self) -> tuple[str, ...]:
        """Python module names of extensions to include in the AnsiballZ payload."""
        return self._module_names

    def get_extensions(self) -> dict[str, dict[str, object]]:
        """Return the configured extensions and their options."""
        extension_options: dict[str, t.Any] = {}

        if self._debugpy:
            extension_options['_debugpy'] = dataclasses.replace(
                self._debugpy,
                source_mapping=self._get_source_mapping(self._debugpy.source_mapping),
            )

        if self._pydevd:
            extension_options['_pydevd'] = dataclasses.replace(
                self._pydevd,
                source_mapping=self._get_source_mapping(self._pydevd.source_mapping),
            )

        if self._coverage:
            extension_options['_coverage'] = self._coverage

        extensions = {extension: dataclasses.asdict(options) for extension, options in extension_options.items()}

        return extensions

    def _get_source_mapping(self, debugger_mapping: dict[str, str]) -> dict[str, str]:
        """Get the source mapping, adjusting the source root as needed."""
        if debugger_mapping:
            source_mapping = {self._translate_path(key, debugger_mapping): value for key, value in self.source_mapping.items()}
        else:
            source_mapping = self.source_mapping

        return source_mapping

    @staticmethod
    def _translate_path(path: str, debugger_mapping: dict[str, str]) -> str:
        """Translate a local path to a foreign path."""
        for replace, match in debugger_mapping.items():
            if path.startswith(match):
                return replace + path[len(match) :]

        return path

    @classmethod
    def create(cls, task_vars: dict[str, object]) -> t.Self:
        """Create an instance using the provided task vars."""
        return cls(
            pydevd=cls._get_options('_ANSIBALLZ_PYDEVD_CONFIG', _pydevd.Options, task_vars),
            debugpy=cls._get_options('_ANSIBALLZ_DEBUGPY_CONFIG', _debugpy.Options, task_vars),
            coverage=cls._get_options('_ANSIBALLZ_COVERAGE_CONFIG', _coverage.Options, task_vars),
        )

    @classmethod
    def _get_options[T](cls, name: str, config_type: type[T], task_vars: dict[str, object]) -> T | None:
        """Parse configuration from the named environment variable as the specified type, or None if not configured."""
        if (value := config.get_config_value(name, variables=task_vars)) is None:
            return None

        data = json.loads(value) if isinstance(value, str) else value
        options = config_type(**data)

        return options


def generate_main_py(
    module_fqn: str,
    profile: str,
    extensions: dict[str, dict[str, object]],
) -> bytes:
    """Generate __main__.py entry point for the ansiballz zip.

    This creates a standard Python entry point that replaces the need for
    _loader.run_module() by providing a __main__.py that sets up the module
    environment and executes the module.
    """
    extension_init_lines = []
    for ext_name, ext_config in extensions.items():
        extension_init_lines.append(f'extensions[{ext_name!r}] = {ext_config!r}')
    extension_init_code = '\n'.join(extension_init_lines) if extension_init_lines else ''

    module_parts = module_fqn.split('.')
    module_name = module_parts[-1]
    package_name = '.'.join(module_parts[:-1]) if len(module_parts) > 1 else ''

    if package_name:
        import_statement = f'from {package_name} import {module_name}'
    else:
        import_statement = f'import {module_name}'

    if extension_init_code:
        extension_setup = f'''# Set up extensions
extensions = {{}}
{extension_init_code}
'''
    else:
        extension_setup = '''# Set up extensions (none configured)
extensions = {}
'''

    code = f'''# __main__.py - Ansiballz entry point
# This file is generated by Ansible and should not be modified.

from __future__ import annotations

import sys
import json
import __main__

# Get params from the wrapper's global scope
# The wrapper sets this before executing __main__.py
params_json = __main__.ANSIBLE_MODULE_PARAMS

# Set module metadata for respawn support
__main__._module_fqn = {module_fqn!r}
__main__._modlib_path = __main__.__file__

# Decode parameters
params = json.loads(params_json)

{extension_setup}
# Initialize module_utils with args
from ansible.module_utils._internal._ansiballz import _loader

try:
    _loader.setup_module_environment(
        json_params=params_json.encode('utf-8'),
        profile={profile!r},
        extensions=extensions,
    )

    # Import and execute the module
    {import_statement}

    if __name__ == '__main__':
        if hasattr({module_name}, 'main'):
            {module_name}.main()
        else:
            raise AttributeError(f"Module '{module_fqn}' has no main() function")

    # An Ansible module must print its own results and exit. If execution reaches this point, that did not happen.
    raise RuntimeError('New-style module did not handle its own exit.')
except SystemExit:
    raise
except Exception as e:
    # Handle exception and format as JSON for controller
    _loader._handle_exception(e, {profile!r})
'''.lstrip()

    return code.encode('utf-8')
