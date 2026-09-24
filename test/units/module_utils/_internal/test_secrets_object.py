from __future__ import annotations

import collections
import types

import pytest

from ansible.module_utils._internal import _secrets, _secrets_object
from ansible.module_utils._internal._datatag import AnsibleSingletonTagBase, AnsibleTagHelper
from ansible.module_utils._internal._secrets_object import mask_object


@pytest.fixture
def masker(monkeypatch):
    """A private masker installed as the singleton mask_object uses, so registrations do not leak into other tests."""
    private = _secrets.SecretMasker()
    monkeypatch.setattr(_secrets_object, '_secret_masker', private)
    return private


def test_mask_object_empty_registry_returns_input_identity(masker):
    value = {"a": ["b", {"c": 1}]}
    assert mask_object(value) is value


def test_mask_object_masks_strings_keys_and_nested_containers(masker):
    masker.register_secret_text("hunter2secret")
    value = {"a": "x hunter2secret y", "b": ["hunter2secret", ["ok", "hunter2secret"], {"hunter2secret": "hunter2secret"}]}

    assert mask_object(value) == {"a": "x $REDACTED$ y", "b": ["$REDACTED$", ["ok", "$REDACTED$"], {"$REDACTED$": "$REDACTED$"}]}


def test_mask_object_does_not_mutate_input_and_shares_unchanged_subtrees(masker):
    masker.register_secret_text("hunter2secret")
    untouched = {"c": ["d", 1]}
    value = {"a": "hunter2secret", "b": untouched, "l": ["ok"]}

    masked = mask_object(value)

    assert masked is not value
    assert value == {"a": "hunter2secret", "b": untouched, "l": ["ok"]}
    assert masked["b"] is untouched
    assert masked["l"] is value["l"]


def test_mask_object_unchanged_is_same_as_input(masker):
    masker.register_secret_text("hunter2secret")
    value = {"a": ["b", {"c": [1, 2]}]}
    assert mask_object(value) is value


def test_mask_object_preserves_key_order_with_masked_key_in_place(masker):
    masker.register_secret_text("hunter2secret")
    masked = mask_object({"first": 1, "hunter2secret": 2, "last": 3})
    assert list(masked) == ["first", "$REDACTED$", "last"]


def test_mask_object_colliding_masked_keys_are_suffixed_deterministically(masker):
    masker.register_secret_texts(["secretone1", "secrettwo2"])
    value = {"secretone1": "a", "secrettwo2": "b", "$REDACTED$": "c", "$REDACTED$ (2)": "d"}

    assert mask_object(value) == {"$REDACTED$": "a", "$REDACTED$ (2)": "b", "$REDACTED$ (3)": "c", "$REDACTED$ (2) (2)": "d"}


def test_mask_object_collision_suffix_uses_custom_placeholder(masker):
    masker.register_secret_texts(["secretone1", "secrettwo2"])
    assert mask_object({"secretone1": 1, "secrettwo2": 2}, mask_placeholder="<x>") == {"<x>": 1, "<x> (2)": 2}


def test_mask_object_numbers_are_masked_by_their_string_form(masker):
    masker.register_secret_text("1234567")
    assert mask_object([1234567, 22345678, 1234567.5, 123, True, None]) == ["$REDACTED$", 22345678, "$REDACTED$.5", 123, True, None]


def test_mask_object_numeric_keys_are_masked(masker):
    masker.register_secret_text("1234567")
    assert mask_object({1234567: "v", 7: "w"}) == {"$REDACTED$": "v", 7: "w"}


def test_mask_object_bool_is_never_treated_as_a_secret(masker):
    masker.register_secret_text("True")
    value = [True, False]
    assert mask_object(value) is value


def test_mask_object_changed_containers_are_rebuilt_as_native_types(masker):
    masker.register_secret_text("hunter2secret")
    unchanged = ("ok",)
    masked = mask_object({"t": ("hunter2secret",), "s": {"hunter2secret", "ok"}, "f": frozenset({"hunter2secret"}), "u": unchanged})

    assert masked == {"t": ["$REDACTED$"], "s": {"$REDACTED$", "ok"}, "f": {"$REDACTED$"}, "u": ("ok",)}
    assert [type(masked[key]) for key in ("t", "s", "f")] == [list, set, set]
    assert masked["u"] is unchanged


def test_mask_object_converts_other_container_implementations(masker):
    masker.register_secret_text("hunter2secret")
    value = {
        "m": types.MappingProxyType({"hunter2secret": collections.deque(["ok", "hunter2secret"]), "s": collections.OrderedDict(k="hunter2secret")}),
        "r": range(3),
    }

    masked = mask_object(value)

    assert masked == {"m": {"$REDACTED$": ["ok", "$REDACTED$"], "s": {"k": "$REDACTED$"}}, "r": range(3)}
    assert [type(masked["m"]), type(masked["m"]["$REDACTED$"]), type(masked["m"]["s"])] == [dict, list, dict]
    assert masked["r"] is value["r"]


def test_mask_object_unknown_types_are_returned_as_is(masker):
    masker.register_secret_text("hunter2secret")
    sentinel = object()
    value = [sentinel, b"hunter2secret"]
    assert mask_object(value) is value


def test_mask_object_preserves_datatag_tags_on_replaced_values(masker):
    class _ProbeTag(AnsibleSingletonTagBase):
        pass

    masker.register_secret_texts(["hunter2secret", "1234567"])
    tag = _ProbeTag()
    value = tag.tag(
        {
            "k": tag.tag("hunter2secret"),
            "l": tag.tag(["hunter2secret"]),
            "n": tag.tag(1234567),
            "t": tag.tag(("hunter2secret",)),  # converted to a list
            "s": tag.tag({"hunter2secret"}),  # rebuilt as a new set
            "same": tag.tag(["ok"]),  # unchanged, returned as-is
        }
    )

    masked = mask_object(value)

    assert masked == {"k": "$REDACTED$", "l": ["$REDACTED$"], "n": "$REDACTED$", "t": ["$REDACTED$"], "s": {"$REDACTED$"}, "same": ["ok"]}
    assert all(_ProbeTag.is_tagged_on(item) for item in (masked, *masked.values()))
    assert AnsibleTagHelper.tags(masked["k"]) == AnsibleTagHelper.tags(value["k"])
    assert masked["same"] is value["same"]


def test_mask_object_lines_keys_rebuilds_lines_from_masked_text(masker):
    input_result = {
        "stdout": "before line1\nline2 after\nlast",
        "stdout_lines": ["before line1", "line2 after", "last"],
    }
    expected = {
        "stdout": "before $REDACTED$ after\nlast",
        "stdout_lines": ["before $REDACTED$ after", "last"],
    }
    masker.register_secret_text("line1\nline2")

    actual = mask_object(input_result, lines_keys={"stdout": "stdout_lines"})
    assert actual == expected


def test_mask_object_lines_keys_applies_at_any_depth_and_key_order(masker):
    input_item = {
        "stdout_lines": ["a line1", "line2"],
        "rc": 0,
        "stdout": "a line1\nline2",
    }
    input_result = {
        "results": [input_item],
        "nested": {"registered": input_item},
    }
    expected_item = {
        "stdout_lines": ["a $REDACTED$"],
        "rc": 0,
        "stdout": "a $REDACTED$",
    }
    expected_result = {
        "results": [expected_item],
        "nested": {"registered": expected_item},
    }
    masker.register_secret_text("line1\nline2")

    actual = mask_object(input_result, lines_keys={"stdout": "stdout_lines"})
    assert actual == expected_result


def test_mask_object_lines_keys_finds_masked_key_names(masker):
    input_result = {
        "changed": True,
        "stdout": "a line1\nline2",
        "stdout_lines": ["a line1", "line2"],
    }
    expected_result = {
        "changed": True,
        "$REDACTED$": "a $REDACTED$",
        "$REDACTED$_lines": ["a $REDACTED$"],
    }
    masker.register_secret_texts(["stdout", "line1\nline2"])

    actual = mask_object(input_result, lines_keys={"stdout": "stdout_lines"})
    assert actual == expected_result


@pytest.mark.parametrize(
    "value, expected",
    (
        pytest.param(
            {"stdout": "a hunter2secret", "stdout_lines": ["custom", "hunter2secret"]},
            {"stdout": "a $REDACTED$", "stdout_lines": ["custom", "$REDACTED$"]},
            id="lines-not-a-split-of-the-original-text",
        ),
        pytest.param(
            {"stdout": "Not a secret", "stdout_lines": ["custom", "hunter2secret"]},
            {"stdout": "Not a secret", "stdout_lines": ["custom", "$REDACTED$"]},
            id="original-not-masked",
        ),
        pytest.param(
            {"stdout": ["a hunter2secret"], "stdout_lines": {"a": ["hunter2secret"]}},
            {"stdout": ["a $REDACTED$"], "stdout_lines": {"a": ["$REDACTED$"]}},
            id="lines-is-not-a-string",
        ),
        pytest.param(
            {"stdout": "a hunter2secret"},
            {"stdout": "a $REDACTED$"},
            id="no-lines",
        ),
        pytest.param(
            {"stdout_lines": ["a hunter2secret"]},
            {"stdout_lines": ["a $REDACTED$"]},
            id="no-text",
        ),
    ),
)
def test_mask_object_lines_keys_leaves_other_shapes_as_normal_masked_value(masker, value, expected):
    """Tests that the stdout_lines value is masked like a normal masked value if not in the expected auto lines format."""
    masker.register_secret_text("hunter2secret")

    actual = mask_object(value, lines_keys={"stdout": "stdout_lines"})
    assert actual == expected


def test_mask_object_masking_failure_does_not_leak_value(masker, monkeypatch):
    masker.register_secret_text("hunter2secret")

    def boom(*args, **kwargs):
        raise ValueError("hunter2secret")

    monkeypatch.setattr(masker, "mask_string", boom)

    with pytest.raises(_secrets.AnsibleSecretMaskError) as exc:
        mask_object(["hunter2secret"])

    assert "hunter2secret" not in str(exc.value)
    assert exc.value.__cause__ is None
