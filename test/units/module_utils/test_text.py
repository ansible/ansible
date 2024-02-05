from __future__ import annotations

import codecs

from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text


def test_exports():
    """Ensure legacy attributes are exported."""

    from ansible.module_utils import _text

    assert _text.codecs == codecs
    assert _text.PY3 is True
    assert _text.text_type is str
    assert _text.binary_type is bytes
    assert _text.to_bytes == to_bytes
    assert _text.to_native == to_native
    assert _text.to_text == to_text
