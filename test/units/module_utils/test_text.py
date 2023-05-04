from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import codecs

from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.six import PY3, text_type, binary_type


def test_exports():
    """Ensure legacy attributes are exported."""

    from ansible.module_utils import _text

    assert _text.codecs == codecs
    assert _text.PY3 == PY3
    assert _text.text_type == text_type
    assert _text.binary_type == binary_type
    assert _text.to_bytes == to_bytes
    assert _text.to_native == to_native
    assert _text.to_text == to_text
