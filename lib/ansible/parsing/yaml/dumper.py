from __future__ import annotations as _annotations

import typing as _t

from ansible._internal._yaml import _dumper


def AnsibleDumper(*args, **kwargs) -> _t.Any:
    """Compatibility factory function; returns an Ansible YAML dumper instance."""
    return _dumper.AnsibleDumper(*args, **kwargs)
