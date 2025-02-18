from __future__ import annotations

import copy
import pickle

import pytest
import jinja2
import jinja2.utils

from ansible._internal._templating._jinja_common import MarkerError, Marker


# NB: this module is named with a trailing underscore to work around a PyCharm/pydevd bug:
#  https://youtrack.jetbrains.com/issue/PY-70408/Debugger-skips-all-breakpoints-in-a-single-test-file


def get_dunder_methods_to_intercept() -> list[str]:
    """
    Return a list of dunder methods on Jinja's StrictUndefined that should be overridden by Ansible's Marker.
    When new methods are added in future Python/Jinja versions, they need to be added to Marker or the ignore_names list below.
    """
    dunder_names = set(name for name in dir(jinja2.StrictUndefined) if name.startswith('__') and name.endswith('__'))

    strict_undefined_intercepted_method_names = set(
        name for name in dir(jinja2.StrictUndefined)
        if getattr(jinja2.StrictUndefined, name) is jinja2.StrictUndefined._fail_with_undefined_error and name != '_fail_with_undefined_error'
    )

    # Some attributes/methods are necessary for core Python interactions and must not be intercepted, thus they are excluded from this test.
    ignore_names = {
        '__class__',
        '__dir__',
        '__doc__',
        '__firstlineno__',
        '__getattr__',  # tested separately since it is intercepted with a custom method
        '__getattribute__',
        '__getitem__',  # tested separately since it is intercepted with a custom method
        '__getstate__',
        '__init__',
        '__init_subclass__',
        '__module__',
        '__new__',
        '__reduce__',
        '__reduce_ex__',
        '__setattr__',  # tested separately since it is intercepted with a custom method
        '__slots__',  # tested separately since it's not a method
        '__sizeof__',
        '__static_attributes__',
        '__subclasshook__',
    }

    # Some methods not intercepted by Jinja's StrictUndefined should be intercepted by Marker.
    additional_method_names = {
        '__aiter__',
        '__delattr__',
        '__format__',
        '__repr__',
        '__setitem__',
    }

    assert not strict_undefined_intercepted_method_names - dunder_names  # ensure Jinja intercepted methods have not been overlooked
    assert not ignore_names & additional_method_names  # ensure no overap between ignore_names and additional_method_names

    return sorted(dunder_names - ignore_names | additional_method_names)


def test_jinja_undefined_shape():
    """
    Assert that the internal shape of Jinja's StrictUndefined matches Marker's expectations.
    If this test fails, it likely means Jinja has changed something about the internals of Undefined in a way we'll need to address.
    """
    assert jinja2.StrictUndefined in Marker.__bases__  # ensure we're directly inheriting the base we're validating

    required_attrs = (
        '_undefined_message',
        '_undefined_name',
        '_fail_with_undefined_error',
    )

    assert all(hasattr(jinja2.StrictUndefined, a) for a in required_attrs)

    assert isinstance(jinja2.StrictUndefined.__slots__, tuple)  # we don't actually care what's slotted, just that the attr exists (or has been patched back on)


@pytest.mark.parametrize("name", get_dunder_methods_to_intercept())
def test_marker_methods(marker: Marker, name: str) -> None:
    """Verify all expected dunder methods on Marker raise a MarkerError."""
    method = getattr(marker, name)

    with pytest.raises(MarkerError) as err:
        method()

    assert err.value.source is marker


def test_getattr_attribute_error(marker: Marker) -> None:
    """Verify unknown dunder attributes on Marker raise an AttributeError."""
    with pytest.raises(AttributeError) as err:
        getattr(marker, '__does_not_exist__')

    assert err.value.obj is marker
    assert err.value.name == '__does_not_exist__'


def test_getattr_propagation(marker: Marker) -> None:
    """Verify unknown non-dunder attributes on Marker return self."""
    assert marker.does_not_exist is marker


def test_getitem_propagation(marker: Marker) -> None:
    """Verify items return self."""
    assert marker['does_not_exist'] is marker


def test_setattr(marker: Marker) -> None:
    """Verify setattr raises MarkerError."""
    with pytest.raises(MarkerError) as err:
        marker.something = True

    assert err.value.source is marker


def test_setitem(marker: Marker) -> None:
    """Verify setitem raises MarkerError."""
    with pytest.raises(MarkerError) as err:
        marker['something'] = True

    assert err.value.source is marker


def test_slots(marker: Marker) -> None:
    """Verify all Marker instances are slotted."""
    assert isinstance(marker.__slots__, tuple)
    assert not hasattr(marker, '__dict__')


def marker_attrs(marker: Marker) -> list[str]:
    """Returns a list of internal attributes for a Marker type (using known prefixes)."""
    return [name for name in dir(marker) if name.startswith('_undefined_') or name.startswith('_marker_')]


def test_copy(marker: Marker) -> None:
    """Verify copying an Marker works."""
    copied = copy.copy(marker)

    assert copied is not marker

    for attribute_name in marker_attrs(marker):
        assert getattr(copied, attribute_name) is getattr(marker, attribute_name), attribute_name


def test_deepcopy(marker: Marker) -> None:
    """Verify deep copying an Marker works."""
    copied = copy.deepcopy(marker)

    assert copied is not marker

    for attribute_name in marker_attrs(marker):
        copied_value = getattr(copied, attribute_name)
        marker_value = getattr(marker, attribute_name)

        if attribute_name == '_undefined_exception':
            # The `_undefined_exception` attribute is a type, so the identity remains unchanged.
            assert copied_value is marker_value, attribute_name
        elif attribute_name == '_undefined_obj' and marker_value is jinja2.utils.missing:
            # The `_undefined_obj` attribute defaults to the `jinja2.utils.missing`, a singleton of `jinja2.utils.MissingType`.
            assert copied_value is marker_value, attribute_name
        elif type(marker_value) in (str, type(None)):
            # Values of type `str` or `None` should be equal.
            assert copied_value == marker_value, attribute_name
        else:
            # All other types should be actual copies.
            assert copied_value is not marker_value, attribute_name


def test_pickle(marker: Marker) -> None:
    """Verify pickling a Marker works."""
    pickled = pickle.loads(pickle.dumps(marker))

    assert pickled is not marker

    for attribute_name in marker_attrs(marker):
        pickled_value = getattr(pickled, attribute_name)
        marker_value = getattr(marker, attribute_name)

        if attribute_name == '_marker_captured_exception':
            # The `_marker_captured_exception` attribute is an `Exception` instance, which doesn't support equality comparisons, compare as a `str` instead.
            pickled_value = str(pickled_value)
            marker_value = str(marker_value)

        assert pickled_value == marker_value, attribute_name
