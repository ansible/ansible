# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# deprecated: description="deprecate unsafe_proxy module" core_version="2.23"
# DTFIX5: add full unit test coverage
from __future__ import annotations

from collections.abc import Mapping, Set

from ansible.module_utils._internal import _no_six
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.module_utils.common.collections import is_sequence
from ansible._internal._datatag._tags import TrustedAsTemplate

__all__ = ['AnsibleUnsafe', 'wrap_var']


class AnsibleUnsafe:
    def __new__(cls, value):
        return TrustedAsTemplate.untag(value)


class AnsibleUnsafeBytes(bytes):
    def __new__(cls, value):
        return TrustedAsTemplate.untag(value)


class AnsibleUnsafeText(str):
    def __new__(cls, value):
        return TrustedAsTemplate.untag(value)


class NativeJinjaUnsafeText(str):
    def __new__(cls, value):
        return TrustedAsTemplate.untag(value)


def _wrap_dict(v):
    return dict((wrap_var(k), wrap_var(item)) for k, item in v.items())


def _wrap_sequence(v):
    """Wraps a sequence with unsafe, not meant for strings, primarily
    ``tuple`` and ``list``
    """
    v_type = type(v)
    return v_type(wrap_var(item) for item in v)


def _wrap_set(v):
    return set(wrap_var(item) for item in v)


def wrap_var(v):
    # maintain backward compat by recursively *un* marking TrustedAsTemplate
    if v is None or isinstance(v, AnsibleUnsafe):
        return v

    if isinstance(v, Mapping):
        v = _wrap_dict(v)
    elif isinstance(v, Set):
        v = _wrap_set(v)
    elif is_sequence(v):
        v = _wrap_sequence(v)
    elif isinstance(v, bytes):
        v = AnsibleUnsafeBytes(v)
    elif isinstance(v, str):
        v = AnsibleUnsafeText(v)

    return v


def to_unsafe_bytes(*args, **kwargs):
    return wrap_var(to_bytes(*args, **kwargs))


def to_unsafe_text(*args, **kwargs):
    return wrap_var(to_text(*args, **kwargs))


def __getattr__(importable_name):
    return _no_six.deprecate(importable_name, __name__, "binary_type", "text_type")
