from __future__ import annotations

import typing as t

import pytest

from ansible.errors import AnsibleError
from ansible.module_utils.common._utils import get_all_subclasses
from ansible.module_utils._internal import _messages
from ansible._internal._templating._jinja_common import Marker, TruncationMarker, CapturedExceptionMarker, VaultExceptionMarker
from ansible._internal._templating._engine import TemplateEngine, TemplateOptions
from ansible._internal._templating._utils import TemplateContext


@pytest.fixture
def template_context() -> t.Iterator[TemplateContext]:
    """A fixture that provides a TemplateContext for the duration of a test."""
    with TemplateContext(template_value=None, templar=TemplateEngine(), options=TemplateOptions.DEFAULT, stop_on_template=False) as ctx:
        yield ctx


def get_concrete_marker_types() -> list[type[Marker]]:
    """Return a sorted list of Marker and its derived types."""
    return sorted(get_all_subclasses(Marker, include_abstract=False, consider_self=True), key=lambda au: au.__name__)


@pytest.fixture(params=get_concrete_marker_types())
def marker(request, template_context: TemplateContext) -> t.Iterator[Marker]:
    """
    A multiplying parameterized fixture that will yield an instance of each Marker-derived type.
    Depends on the template_context fixture, since these types can only be created under templating.
    """
    request_type = request.param

    if issubclass(request_type, TruncationMarker):
        yield request_type()
    elif issubclass(request_type, VaultExceptionMarker):
        yield VaultExceptionMarker(ciphertext='a ciphertext', event=_messages.Event(msg='a msg'))
    elif issubclass(request_type, CapturedExceptionMarker):
        try:
            try:
                raise Exception('bang')
            except Exception as ex:
                defer = ex

            raise AnsibleError('big bang') from defer  # pylint: disable=used-before-assignment  # false positive
        except Exception as ex2:
            yield request_type(ex2)
    else:
        yield request_type(hint="a hint", obj="obj", name="name")
