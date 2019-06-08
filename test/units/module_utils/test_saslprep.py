# -*- coding: utf-8 -*-
import pytest

from ansible.module_utils.saslprep import saslprep

VALID = [
    (u'', u''),
    (u'a', u'a'),
    (u'й', u'й'),
    (u'\u30DE\u30C8\u30EA\u30C3\u30AF\u30B9', u'\u30DE\u30C8\u30EA\u30C3\u30AF\u30B9'),
    (u'The\u00ADM\u00AAtr\u2168', u'TheMatrIX'),
    (u"I\u00ADX", u"IX"),
    (u"user", u"user"),
    (u"USER", u"USER"),
    (u"\u00AA", u"a"),
    (u"\u2168", u"IX"),
]

INVALID = [
    (None, TypeError),
    (b'', TypeError),
    (u'\u0007', ValueError),
    (u'\u0627\u0031', ValueError),
]


@pytest.mark.parametrize("source,target", VALID)
def test_saslprep_conversions(source, target):
    assert saslprep(source) == target


@pytest.mark.parametrize("value,exception", INVALID)
def test_saslprep_exceptions(value, exception):
    with pytest.raises(exception) as ex:
        saslprep(value)
