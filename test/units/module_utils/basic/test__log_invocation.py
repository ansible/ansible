# -*- coding: utf-8 -*-
# (c) 2016, James Cammarata <jimi@sngx.net>
# (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest


ARGS = dict(foo=False, bar=[1, 2, 3], bam="bam", baz=u'baz')
ARGUMENT_SPEC = dict(
    foo=dict(default=True, type='bool'),
    bar=dict(default=[], type='list'),
    bam=dict(default="bam"),
    baz=dict(default=u"baz"),
    password=dict(default=True),
    no_log=dict(default="you shouldn't see me", no_log=True),
)


@pytest.mark.parametrize('am, stdin', [(ARGUMENT_SPEC, ARGS)], indirect=['am', 'stdin'])
def test_module_utils_basic__log_invocation(am, mocker):

    am.log = mocker.MagicMock()
    am._log_invocation()

    # Message is generated from a dict so it will be in an unknown order.
    # have to check this manually rather than with assert_called_with()
    args = am.log.call_args[0]
    assert len(args) == 1
    message = args[0]

    assert len(message) == \
        len('Invoked with bam=bam bar=[1, 2, 3] foo=False baz=baz no_log=NOT_LOGGING_PARAMETER password=NOT_LOGGING_PASSWORD')

    assert message.startswith('Invoked with ')
    assert ' bam=bam' in message
    assert ' bar=[1, 2, 3]' in message
    assert ' foo=False' in message
    assert ' baz=baz' in message
    assert ' no_log=NOT_LOGGING_PARAMETER' in message
    assert ' password=NOT_LOGGING_PASSWORD' in message

    kwargs = am.log.call_args[1]
    assert kwargs == \
        dict(log_args={
            'foo': 'False',
            'bar': '[1, 2, 3]',
            'bam': 'bam',
            'baz': 'baz',
            'password': 'NOT_LOGGING_PASSWORD',
            'no_log': 'NOT_LOGGING_PARAMETER',
        })
