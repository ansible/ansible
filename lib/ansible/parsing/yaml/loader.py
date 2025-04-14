from __future__ import annotations as _annotations

import typing as _t

from ansible._internal._yaml import _loader


def AnsibleLoader(*args, **kwargs) -> _t.Any:
    """Compatibility factory function; returns an Ansible YAML loader instance."""
    return _loader.AnsibleLoader(*args, **kwargs)
