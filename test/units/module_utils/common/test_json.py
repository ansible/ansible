from __future__ import annotations

import json

from ansible.module_utils import _internal
from ansible.module_utils.common.json import AnsibleJSONEncoder
from ansible.module_utils._internal._json._legacy_encoder import LegacyTargetJSONEncoder


def test_controller_impl_patch() -> None:
    """Ensure that the context-appropriate implementation of `AnsibleJSONEncoder` is patched into the module."""
    if _internal.is_controller:
        assert AnsibleJSONEncoder is not LegacyTargetJSONEncoder
    else:
        assert AnsibleJSONEncoder is LegacyTargetJSONEncoder


def test_mu_bytes() -> None:
    assert json.dumps(b'abc', cls=LegacyTargetJSONEncoder, _decode_bytes=True) == '"abc"'
