from __future__ import annotations

from ansible._internal._ansiballz._builder import ExtensionManager
from ansible.module_utils._internal._ansiballz._extensions import _pydevd


def test_debugger_source_mapping() -> None:
    """Synthetic coverage for builder source mapping."""
    debug_options = _pydevd.Options(source_mapping={
        "ide/path.py": "controller/path.py",
        "ide/something.py": "controller/not_match.py",
    })

    manager = ExtensionManager(debug_options)
    manager.source_mapping.update({
        "controller/path.py": "zip/path.py",
        "controller/other.py": "not_match.py",
    })

    extensions = manager.get_extensions()

    assert extensions['_pydevd']['source_mapping'] == {'controller/other.py': 'not_match.py', 'ide/path.py': 'zip/path.py'}
