import json
import pytest

from ansible.modules.files.json_patch import JSONPatcher, PathError

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


sample_json = json.dumps([
    {"foo": {"one": 1, "two": 2, "three": 3}, "enabled": True},
    {"bar": {"one": 1, "two": 2, "three": 3}, "enabled": False},
    {"baz": [{"foo": "apples", "bar": "oranges"},
             {"foo": "grapes", "bar": "oranges"},
             {"foo": "bananas", "bar": "potatoes"}],
     "enabled": False}])


# OPERATION: ADD
def test_op_add_foo_four():
    """Should add a `four` member to the first object."""
    patches = [
        {"op": "add", "path": "/0/foo/four", "value": 4}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[0]['foo']['four'] == 4


def test_op_add_object_list():
    """Should add a new first object to the 'baz' list."""
    patches = [
        {"op": "add", "path": "/2/baz/0", "value": {"foo": "kiwis", "bar": "strawberries"}}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[2]['baz'][0] == patches[0]['value']


def test_op_add_object_end_of_list():
    """should add a new last object to the 'baz' list."""
    patches = [
        {"op": "add", "path": "/2/baz/-", "value": {"foo": "raspberries", "bar": "blueberries"}}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[2]['baz'][-1] == patches[0]['value']


def test_op_add_replace_existing_value():
    """Should find an existing property and replace its value."""
    patches = [
        {"op": "add", "path": "/1/bar/three", "value": 10}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[1]['bar']['three'] == 10


def test_op_add_ignore_existing_value():
    """Should ignore an existing property with the same value."""
    patches = [
        {"op": "add", "path": "/1/bar/one", "value": 1}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is False
    assert tested is None
    assert jp.obj[1]['bar']['one'] == 1


# OPERATION: REMOVE
def test_op_remove_foo_three():
    """Should remove the 'three' member from the first object."""
    patches = [
        {"op": "remove", "path": "/0/foo/three"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert 'three' not in jp.obj[0]['foo']


def test_op_remove_baz_list_member():
    """Should remove the last fruit item from the 'baz' list."""
    patches = [
        {"op": "remove", "path": "/2/baz/2"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    for obj in jp.obj[2]['baz']:
        assert obj['foo'] != 'bananas'
        assert obj['bar'] != 'potatoes'


def test_op_remove_fail_on_nonexistent_path():
    """Should raise an exception if referencing a non-existent tree to remove."""
    patches = [
        {"op": "remove", "path": "/0/qux/one"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    with pytest.raises(PathError):
        jp.patch()


def test_op_remove_unchanged_on_nonexistent_member():
    """Should not raise an exception if referencing a non-existent leaf to remove."""
    patches = [
        {"op": "remove", "path": "/0/foo/four"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is False
    assert tested is None


# OPERATION: REPLACE
def test_op_replace_foo_three():
    """Should replace the value for the 'three' member in 'foo'."""
    patches = [
        {"op": "replace", "path": "/0/foo/three", "value": "booyah"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[0]['foo']['three'] == 'booyah'


def test_op_replace_fail_on_nonexistent_path_or_member():
    """Should raise an exception if any part of the referenced path does not exist (RFC 6902)."""
    patches = [
        {"op": "replace", "path": "/0/foo/four", "value": 4}
    ]
    jp = JSONPatcher(sample_json, *patches)
    with pytest.raises(PathError):
        jp.patch()


# OPERATION: MOVE
def test_op_move_foo_three_bar_four():
    """Should move the 'three' property from 'foo' to 'bar'."""
    patches = [
        {"op": "move", "from": "/0/foo/three", "path": "/1/bar/four"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[0]['foo'].get('three', 'DUMMY VALUE') == 'DUMMY VALUE'
    assert jp.obj[1]['bar']['four'] == 3


def test_op_move_baz_list_foo():
    """Should move the 'baz' list of fruits to 'foo' object."""
    patches = [
        {"op": "move", "from": "/2/baz", "path": "/0/foo/fruits"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[2].get('baz', 'DUMMY VALUE') == 'DUMMY VALUE'
    assert len(jp.obj[0]['foo']['fruits']) == 3


def test_op_move_unchanged_on_nonexistent():
    """Should not raise an exception if moving a non-existent object member."""
    patches = [
        {"op": "move", "from": "/0/foo/four", "path": "/1/bar/four"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is False
    assert tested is None


def test_op_move_foo_object_end_of_list():
    """Should move the 'three' member in 'foo' to the end of the 'baz' list."""
    patches = [
        {"op": "move", "from": "/0/foo/three", "path": "/2/baz/-"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[0]['foo'].get('three', 'DUMMY VALUE') == 'DUMMY VALUE'
    assert jp.obj[2]['baz'][-1] == 3


# OPERATION: COPY
def test_op_copy_foo_three_bar_four():
    """Should copy the 'three' member in 'foo' to the 'bar' object."""
    patches = [
        {"op": "copy", "from": "/0/foo/three", "path": "/1/bar/four"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert jp.obj[0]['foo']['three'] == 3
    assert jp.obj[1]['bar']['four'] == 3


def test_op_copy_baz_list_bar():
    """Should copy the 'baz' list of fruits to 'foo' object."""
    patches = [
        {"op": "copy", "from": "/2/baz", "path": "/0/foo/fruits"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is None
    assert len(jp.obj[2]['baz']) == 3
    assert len(jp.obj[0]['foo']['fruits']) == 3


def test_op_copy_fail_on_nonexistent_member():
    """Should raise an exception when copying a non-existent member."""
    patches = [
        {"op": "copy", "from": "/1/bar/four", "path": "/0/foo/fruits"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    with pytest.raises(PathError):
        jp.patch()


# OPERATION: TEST
def test_op_test_string_equal():
    """Should return True that two strings are equal."""
    patches = [
        {"op": "test", "path": "/2/baz/0/foo", "value": "apples"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is None
    assert tested is True


def test_op_test_string_unequal():
    """Should return False that two strings are unequal."""
    patches = [
        {"op": "test", "path": "/2/baz/0/foo", "value": "bananas"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is None
    assert tested is False


def test_op_test_number_equal():
    """Should return True that two numbers are equal."""
    patches = [
        {"op": "test", "path": "/0/foo/one", "value": 1}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is None
    assert tested is True


def test_op_test_number_unequal():
    """Should return False that two numbers are unequal."""
    patches = [
        {"op": "test", "path": "/0/foo/one", "value": "bananas"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is None
    assert tested is False


def test_op_test_list_equal():
    """Should return True that two lists are equal."""
    patches = [
        {"op": "add", "path": "/0/foo/compare", "value": [1, 2, 3]},
        {"op": "test", "path": "/0/foo/compare", "value": [1, 2, 3]}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is True
    assert tested is True


def test_op_test_wildcard():
    """Should find an element in the 'baz' list with the matching value."""
    patches = [
        {"op": "test", "path": "/2/baz/*/foo", "value": "grapes"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is None
    assert tested is True


def test_op_test_wildcard_not_found():
    """Should return False on not finding an element with the given value."""
    patches = [
        {"op": "test", "path": "/2/baz/*/bar", "value": "rocks"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is None
    assert tested is False


def test_op_test_multiple_tests():
    """Should return False if at least one test returns False."""
    patches = [
        {"op": "test", "path": "/0/foo/one", "value": 2},
        {"op": "test", "path": "/1/bar/one", "value": 1}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is None
    assert tested is False


def test_op_test_nonexistent_member():
    """Should return False even if path does not exist."""
    patches = [
        {"op": "test", "path": "/10/20/foo", "value": "bar"}
    ]
    jp = JSONPatcher(sample_json, *patches)
    changed, tested = jp.patch()
    assert changed is None
    assert tested is False
