"""
This is testing JSON functionality from module_utils which is only available in a controller context.
Do not add tests here which should pass in a target context.
"""

from __future__ import annotations

import json
import pytest

from ansible.errors import AnsibleRuntimeError
from ansible.module_utils._internal._json._profiles import _tagless


@pytest.mark.parametrize("value", (
    r'"\ud8f3"',
    r'["\ud8f3"]',
    r'[["\ud8f3"]]',
    r'[[{"key": "\ud8f3"}]]',
    r'{"key": "\ud8f3"}',
    r'{"key": ["\ud8f3"]}',
    r'{"key": {"subkey": "\ud8f3"}}',
    r'{"key": {"subkey": ["\ud8f3"]}}',
    r'{"key": [{"subkey": ["\ud8f3"]}]}',
    r'{"\ud8f3": "value"}',
    r'{"key": {"\ud8f3": "subvalue"}}',
    r'{"key": [{"\ud8f3": "subvalue"}]}',
))
def test_invalid_utf8_decoding(value: str) -> None:
    """Verify that strings which cannot be encoded as valid UTF8 result in an error during deserialization."""
    with pytest.raises(AnsibleRuntimeError, match='^Refusing to deserialize an invalid UTF8 string value'):
        json.loads(value, cls=_tagless.Decoder)
