from __future__ import annotations

import pytest

from ansible._internal._errors import _error_factory

from ansible.errors import AnsibleError
from ansible._internal import _display_utils
from ansible._internal._datatag._tags import Origin
from ansible._internal._errors._error_utils import format_exception_message
from ansible.module_utils._internal import _messages
from units.mock.error_helper import raise_exceptions


_shared_cause = Exception('shared cause')
_origin_x = Origin(path='/x')
_origin_y = Origin(path='/y')


@pytest.mark.parametrize("exceptions, expected_message_chain, expected_formatted_message", (
    ([AnsibleError('a')], 'a', None),
    ([AnsibleError('a'), AnsibleError('b')], 'a: b', None),
    ([AnsibleError('a: b'), AnsibleError('b')], 'a: b', None),
    ([Exception('a')], 'a', None),
    ([Exception('a'), Exception('b')], 'a: b', None),
    ([Exception('a: b'), Exception('b')], 'a: b', None),
    ([AnsibleError('a'), Exception('b')], 'a: b', None),
    ([AnsibleError('a: b'), Exception('b')], 'a: b', None),
    ([Exception('a'), AnsibleError('b')], 'a: b', None),
    ([Exception('a: b'), AnsibleError('b')], 'a: b', None),
    ([AnsibleError('a'), AnsibleError('b'), Exception('c'), Exception('d')], 'a: b: c: d', None),
    ([AnsibleError('a: b: c: d'), AnsibleError('b'), Exception('c: d'), Exception('d')], 'a: b: c: d', None),

    # collapsing help_text

    (
        [
            AnsibleError('a', help_text='one'),
            Exception('b'),
        ],
        'a: b',
        (
            'a: b one'
        ),
    ),
    (
        [
            AnsibleError('a', help_text='one'),
            AnsibleError('b', help_text='one'),
        ],
        'a: b',
        (
            'a: b one'
        ),
    ),
    (
        [
            AnsibleError('a', help_text='one'),
            Exception('b'),
            AnsibleError('c', help_text='one'),
        ],
        'a: b: c',
        (
            'a: b: c one'
        ),
    ),
    (
        [
            AnsibleError('a', help_text='one'),
            AnsibleError('b', help_text='two'),
        ],
        'a: b',
        (
            'a: b\n\n'
            'a one\n\n'
            '<<< caused by >>>\n\n'
            'b two'
        ),
    ),
    (
        [
            AnsibleError('a'),
            AnsibleError('b', help_text='one'),
        ],
        'a: b',
        (
            'a: b\n\n'
            'a\n\n'
            '<<< caused by >>>\n\n'
            'b one'
        ),
    ),

    # collapsing origin

    (
        [
            AnsibleError('a', obj=_origin_x.tag('x'), orig_exc=Exception('ignored')),
            Exception('b'),
        ],
        'a: b',
        (
            'a: b\n'
            'Origin: /x'
        ),
    ),
    (
        [
            AnsibleError('a', obj=_origin_x.tag('x'), orig_exc=_shared_cause),
            _shared_cause,
        ],
        'a: shared cause',
        (
            'a: shared cause\n'
            'Origin: /x'
        ),
    ),
    (
        [
            # same as above, but exercises the old `orig_exc` path that displays a warning
            AnsibleError('a', obj=_origin_x.tag('x'), orig_exc=Exception('b')),
        ],
        'a: b',
        (
            'a: b\n'
            'Origin: /x'
        ),
    ),
    (
        [
            AnsibleError('a', obj=_origin_x.tag('x')),
            AnsibleError('b', obj=_origin_x.tag('x')),
        ],
        'a: b',
        (
            'a: b\n'
            'Origin: /x'
        ),
    ),
    (
        [
            AnsibleError('a', obj=_origin_x.tag('x')),
            Exception('b'),
            AnsibleError('c', obj=_origin_x.tag('x')),
        ],
        'a: b: c',
        (
            'a: b: c\n'
            'Origin: /x'
        ),
    ),
    (
        [
            AnsibleError('a', obj=_origin_x.tag('x')),
            AnsibleError('b', obj=_origin_y.tag('x')),
        ],
        'a: b',
        (
            'a: b\n\n'
            'a\n'
            'Origin: /x\n\n'
            '<<< caused by >>>\n\n'
            'b\n'
            'Origin: /y'
        ),
    ),
    (
        [
            AnsibleError('a'),
            AnsibleError('b', obj=_origin_y.tag('x')),
        ],
        'a: b',
        (
            'a: b\n\n'
            'a\n\n'
            '<<< caused by >>>\n\n'
            'b\n'
            'Origin: /y'
        ),
    ),
), ids=str)
def test_error_messages(exceptions: list[BaseException], expected_message_chain: str, expected_formatted_message: str | None) -> None:
    with pytest.raises(Exception) as error:
        raise_exceptions(exceptions)

    event = _error_factory.ControllerEventFactory.from_exception(error.value, False)

    message_chain = format_exception_message(error.value)
    formatted_message = _display_utils.format_message(_messages.ErrorSummary(event=event), False)

    assert message_chain == expected_message_chain
    assert formatted_message.strip() == (expected_formatted_message or expected_message_chain)
