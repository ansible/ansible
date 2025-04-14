from __future__ import annotations

from ansible._internal._datatag._tags import VaultedValue
from ansible.module_utils._internal._datatag import AnsibleTagHelper


def test_vaulted_value_non_propagation_untagged_dst() -> None:
    vv = VaultedValue(ciphertext='')

    src_value = vv.tag('hello src')
    dst_value = 'hello dst'

    result = AnsibleTagHelper.tag_copy(src_value, dst_value)

    assert result is dst_value


def test_vaulted_value_non_propagation_tagged_dst() -> None:
    vv = VaultedValue(ciphertext='')
    vv_dst = VaultedValue(ciphertext='dst')

    src_value = vv.tag('hello src')
    dst_value = vv_dst.tag('hello dst')

    result = AnsibleTagHelper.tag_copy(src_value, dst_value)

    assert vv != vv_dst
    assert AnsibleTagHelper.tags(result) == {vv_dst}


def test_vaulted_value_propagation_untagged_dst() -> None:
    vv = VaultedValue(ciphertext='')

    src_value = vv.tag('hello')
    dst_value = 'hello'

    result = AnsibleTagHelper.tag_copy(src_value, dst_value)

    assert AnsibleTagHelper.tags(result) == {vv}


def test_vaulted_value_propagation_tagged_dst() -> None:
    vv = VaultedValue(ciphertext='')
    vv_dst = VaultedValue(ciphertext='dst')

    src_value = vv.tag('hello')
    dst_value = vv_dst.tag('hello')

    result = AnsibleTagHelper.tag_copy(src_value, dst_value)

    assert vv != vv_dst
    assert AnsibleTagHelper.tags(result) == {vv}
