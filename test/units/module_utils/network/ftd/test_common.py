from ansible.module_utils.network.ftd.common import equal_objects


# simple objects

def test_equal_objects_return_false_with_different_length():
    assert not equal_objects(
        {'foo': 1},
        {'foo': 1, 'bar': 2}
    )


def test_equal_objects_return_false_with_different_fields():
    assert not equal_objects(
        {'foo': 1},
        {'bar': 1}
    )


def test_equal_objects_return_false_with_different_value_types():
    assert not equal_objects(
        {'foo': 1},
        {'foo': '1'}
    )


def test_equal_objects_return_false_with_different_values():
    assert not equal_objects(
        {'foo': 1},
        {'foo': 2}
    )


def test_equal_objects_return_false_with_different_nested_values():
    assert not equal_objects(
        {'foo': {'bar': 1}},
        {'foo': {'bar': 2}}
    )


def test_equal_objects_return_false_with_different_list_length():
    assert not equal_objects(
        {'foo': []},
        {'foo': ['bar']}
    )


def test_equal_objects_return_true_with_equal_objects():
    assert equal_objects(
        {'foo': 1, 'bar': 2},
        {'bar': 2, 'foo': 1}
    )


def test_equal_objects_return_true_with_equal_nested_dicts():
    assert equal_objects(
        {'foo': {'bar': 1, 'buz': 2}},
        {'foo': {'buz': 2, 'bar': 1}}
    )


def test_equal_objects_return_true_with_equal_lists():
    assert equal_objects(
        {'foo': ['bar']},
        {'foo': ['bar']}
    )


def test_equal_objects_return_true_with_ignored_fields():
    assert equal_objects(
        {'foo': 1, 'version': '123', 'id': '123123'},
        {'foo': 1}
    )


# objects with object references

def test_equal_objects_return_true_with_different_ref_ids():
    assert not equal_objects(
        {'foo': {'id': '1', 'type': 'network', 'ignored_field': 'foo'}},
        {'foo': {'id': '2', 'type': 'network', 'ignored_field': 'bar'}}
    )


def test_equal_objects_return_true_with_different_ref_types():
    assert not equal_objects(
        {'foo': {'id': '1', 'type': 'network', 'ignored_field': 'foo'}},
        {'foo': {'id': '1', 'type': 'accessRule', 'ignored_field': 'bar'}}
    )


def test_equal_objects_return_true_with_same_object_refs():
    assert equal_objects(
        {'foo': {'id': '1', 'type': 'network', 'ignored_field': 'foo'}},
        {'foo': {'id': '1', 'type': 'network', 'ignored_field': 'bar'}}
    )


# objects with array of object references

def test_equal_objects_return_false_with_different_array_length():
    assert not equal_objects(
        {'foo': [
            {'id': '1', 'type': 'network', 'ignored_field': 'foo'}
        ]},
        {'foo': []}
    )


def test_equal_objects_return_false_with_different_array_order():
    assert not equal_objects(
        {'foo': [
            {'id': '1', 'type': 'network', 'ignored_field': 'foo'},
            {'id': '2', 'type': 'network', 'ignored_field': 'bar'}
        ]},
        {'foo': [
            {'id': '2', 'type': 'network', 'ignored_field': 'foo'},
            {'id': '1', 'type': 'network', 'ignored_field': 'bar'}
        ]}
    )


def test_equal_objects_return_true_with_equal_ref_arrays():
    assert equal_objects(
        {'foo': [
            {'id': '1', 'type': 'network', 'ignored_field': 'foo'}
        ]},
        {'foo': [
            {'id': '1', 'type': 'network', 'ignored_field': 'bar'}
        ]}
    )
