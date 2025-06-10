from __future__ import annotations

import dataclasses
import json

import typing as t

from ansible.module_utils._internal._ansiballz import _extensions
from ansible.module_utils._internal._ansiballz._extensions import _pydevd, _coverage
from ansible.constants import config

_T = t.TypeVar('_T')


class ExtensionManager:
    """AnsiballZ extension manager."""

    def __init__(
        self,
        debugger: _pydevd.Options | None = None,
        coverage: _coverage.Options | None = None,
    ) -> None:
        options = dict(
            _pydevd=debugger,
            _coverage=coverage,
        )

        self._debugger = debugger
        self._coverage = coverage
        self._extension_names = tuple(name for name, option in options.items() if option)
        self._module_names = tuple(f'{_extensions.__name__}.{name}' for name in self._extension_names)

        self.source_mapping: dict[str, str] = {}

    @property
    def debugger_enabled(self) -> bool:
        """Returns True if the debugger extension is enabled, otherwise False."""
        return bool(self._debugger)

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

        if self._debugger:
            extension_options['_pydevd'] = dataclasses.replace(
                self._debugger,
                source_mapping=self._get_source_mapping(),
            )

        if self._coverage:
            extension_options['_coverage'] = self._coverage

        extensions = {extension: dataclasses.asdict(options) for extension, options in extension_options.items()}

        return extensions

    def _get_source_mapping(self) -> dict[str, str]:
        """Get the source mapping, adjusting the source root as needed."""
        if self._debugger.source_mapping:
            source_mapping = {self._translate_path(key): value for key, value in self.source_mapping.items()}
        else:
            source_mapping = self.source_mapping

        return source_mapping

    def _translate_path(self, path: str) -> str:
        """Translate a local path to a foreign path."""
        for replace, match in self._debugger.source_mapping.items():
            if path.startswith(match):
                return replace + path[len(match) :]

        return path

    @classmethod
    def create(cls, task_vars: dict[str, object]) -> t.Self:
        """Create an instance using the provided task vars."""
        return cls(
            debugger=cls._get_options('_ANSIBALLZ_DEBUGGER_CONFIG', _pydevd.Options, task_vars),
            coverage=cls._get_options('_ANSIBALLZ_COVERAGE_CONFIG', _coverage.Options, task_vars),
        )

    @classmethod
    def _get_options(cls, name: str, config_type: type[_T], task_vars: dict[str, object]) -> _T | None:
        """Parse configuration from the named environment variable as the specified type, or None if not configured."""
        if (value := config.get_config_value(name, variables=task_vars)) is None:
            return None

        data = json.loads(value) if isinstance(value, str) else value
        options = config_type(**data)

        return options
