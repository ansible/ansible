"""
Utilities to support unit testing of Ansible Python modules.
Not supported for use cases other than testing.
"""

from __future__ import annotations as _annotations

import contextlib as _contextlib
import json as _json
import typing as _t

from unittest import mock as _mock

from . import serialization as _serialization
from . import basic as _basic


@_contextlib.contextmanager
def patch_module_args(args: dict[str, _t.Any] | None) -> _t.Iterator[None]:
    """
    Expose the given module args to AnsibleModule instances created within this context.
    The module args dict must include a top-level `ANSIBLE_MODULE_ARGS` key.
    """
    if not isinstance(args, (dict, type(None))):
        raise TypeError("The `args` arg must be a dict or None.")

    profile = 'legacy'  # this should be configurable in the future, once the profile feature is more fully baked

    if args is None:
        args = dict(ANSIBLE_MODULE_ARGS={})

    encoder = _serialization.get_module_encoder(profile, _serialization.Direction.CONTROLLER_TO_MODULE)
    args = _json.dumps(args, cls=encoder).encode()

    with _mock.patch.object(_basic, '_ANSIBLE_ARGS', args), _mock.patch.object(_basic, '_ANSIBLE_PROFILE', profile):
        yield
