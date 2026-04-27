"""Support fixtures for testing Ansible modules."""

from __future__ import annotations

from ansible.module_utils._internal import _traceback
from ansible.module_utils.common import warnings

import pytest


class ModuleEnvMocker:
    """
    A Swiss Army Knife mock fixture for target-side environments (e.g., modules, module_utils).

    Using this fixture automatically applies a number of default patches, and offers tests a one-stop
    fixture to configure a number of others.

    Default behaviors:
    * Warnings and deprecations are cleared.
    * Traceback collection is disabled.
    """

    def __init__(self, mp: pytest.MonkeyPatch):
        self._mp = mp
        self.reset_warnings()
        self.reset_deprecations()
        self.set_traceback_config()

    def set_traceback_config(self, value: list[_traceback.TracebackEvent] | None = None) -> None:
        """Accepts a list of TracebackEvent values to enable."""
        self._mp.setattr(_traceback, '_module_tracebacks_enabled_events', value or [])

    def reset_warnings(self) -> None:
        """Clears accumulated target-side warnings."""
        self._mp.setattr(warnings, '_global_warnings', {})

    def reset_deprecations(self) -> None:
        """Clears accumulated target-side deprecation warnings."""
        self._mp.setattr(warnings, '_global_deprecations', {})


@pytest.fixture
def module_env_mocker(monkeypatch: pytest.MonkeyPatch) -> ModuleEnvMocker:
    """Provides a ModuleEnvMocker instance that allows configurable simulation of an Ansible Python module runtime environment."""
    return ModuleEnvMocker(monkeypatch)
