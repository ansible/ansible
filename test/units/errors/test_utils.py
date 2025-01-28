from __future__ import annotations

import pytest

from ansible.errors import get_chained_message, AnsibleError
from ansible.errors.utils import _create_error_summary
from ansible.module_utils.common.messages import ErrorSummary
from ansible.utils.datatag.tags import AnsibleSourcePosition
from ansible.utils.display import format_message


def raise_exceptions(exceptions: list[BaseException]) -> None:
    if len(exceptions) > 1:
        try:
            raise_exceptions(exceptions[1:])
        except Exception as ex:
            raise exceptions[0] from ex

    raise exceptions[0]


_shared_cause = Exception('shared cause')
_source_pos_x = AnsibleSourcePosition(src='/x')
_source_pos_y = AnsibleSourcePosition(src='/y')


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
            'a: b\n\n'
            'one'
        ),
    ),
    (
        [
            AnsibleError('a', help_text='one'),
            AnsibleError('b', help_text='one'),
        ],
        'a: b',
        (
            'a: b\n\n'
            'one'
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
            'a: b: c\n\n'
            'one'
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
            'a\n\n'
            'one\n\n'
            '<<< caused by >>>\n\n'
            'b\n\n'
            'two'
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
            'b\n\n'
            'one'
        ),
    ),

    # collapsing source position

    (
        [
            AnsibleError('a', obj=_source_pos_x.tag('x'), orig_exc=Exception('ignored')),
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
            AnsibleError('a', obj=_source_pos_x.tag('x'), orig_exc=_shared_cause),
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
            AnsibleError('a', obj=_source_pos_x.tag('x'), orig_exc=Exception('b')),
        ],
        'a: b',
        (
            'a: b\n'
            'Origin: /x'
        ),
    ),
    (
        [
            AnsibleError('a', obj=_source_pos_x.tag('x')),
            AnsibleError('b', obj=_source_pos_x.tag('x')),
        ],
        'a: b',
        (
            'a: b\n'
            'Origin: /x'
        ),
    ),
    (
        [
            AnsibleError('a', obj=_source_pos_x.tag('x')),
            Exception('b'),
            AnsibleError('c', obj=_source_pos_x.tag('x')),
        ],
        'a: b: c',
        (
            'a: b: c\n'
            'Origin: /x'
        ),
    ),
    (
        [
            AnsibleError('a', obj=_source_pos_x.tag('x')),
            AnsibleError('b', obj=_source_pos_y.tag('x')),
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
            AnsibleError('b', obj=_source_pos_y.tag('x')),
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

    error_details = _create_error_summary(error.value).details

    message_chain = get_chained_message(error.value)
    formatted_message = format_message(ErrorSummary(details=error_details))

    assert message_chain == expected_message_chain
    assert formatted_message.strip() == (expected_formatted_message or expected_message_chain)
