"""
Internal implementation of utilities to support unit testing of Ansible Python modules.
Use `ansible.module_utils.testing` instead of importing this directly.
"""

from __future__ import annotations

import contextlib
import json
import typing as t

from unittest import mock

from ..serialization import get_module_encoder, Direction
from ...module_utils import basic


@contextlib.contextmanager
def patch_module_args(args: str | bytes | dict[str, t.Any] | None, profile: str) -> t.Iterator[None]:
    """Expose the given module args and serialization profile to AnsibleModule instances created within this context."""
    # DTFIX-MERGE: can we eliminate str and bytes inputs here? a dict is really all we should need
    if not isinstance(profile, str):
        raise TypeError()

    if args is None:
        args = dict(ANSIBLE_MODULE_ARGS={})

    if isinstance(args, dict):
        encoder = get_module_encoder(profile, Direction.CONTROLLER_TO_MODULE)
        args = json.dumps(args, cls=encoder)

    if isinstance(args, str):
        args = args.encode()

    if not isinstance(args, bytes):
        raise TypeError()

    with mock.patch.object(basic, '_ANSIBLE_ARGS', args), mock.patch.object(basic, '_ANSIBLE_PROFILE', profile):
        yield
