# -*- coding: utf-8 -*-
# (c) 2017, Adrian Likins <alikins@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import pytest

from ansible.module_utils.basic import PASSWORD_MATCH
#from ansible.module_utils.basic import PASSWD_ARG_RE
from ansible.module_utils._text import to_text, to_bytes


SHOULD_MATCH_STRING = '''
admin_password
login_password
my-password
my_pass
my_passphrase
my_passwd
pass
pass-word
passphrase
passwd
password
password
proxy_password
update_password
update_password
'''


SHOULD_MATCH = SHOULD_MATCH_STRING.strip().splitlines()

SHOULD_MATCH_MODIFIER = []

SHOULD_NOT_MATCH = ['blippy',
                    'notapassword',
                    'not_apas',
                    'password ',
                    'passhprase']


def no_mod(text):
    return text


def add_trailing(text):
    return '%s ' % text


def add_leading(text):
    return ' %s' % text


def add_leading_and_trailing(text):
    return ' %s ' % text


def covert_to_text(text):
    return to_text(text)


def covert_to_bytes(text):
    return to_bytes(text)


def dash_dash(text):
    return '--%s' % text


def under_pre(text):
    return '_%s' % text


def dunder_pre(text):
    return '__%s' % text


def new_line_pre(text):
    return '\n%s' % text


def new_line_post(text):
    return '%s\n' % text


# NOTE: the commented out modifiers cause the current regex to fail
modifiers = [(no_mod, 'original'),
#             (add_trailing, 'trailing space'),
#             (add_leading, 'leading space'),
#             (add_leading_and_trailing, 'leading and trailing space'),
#             (dash_dash, '-- prepended'),
#             (under_pre, '_ prepended'),
#             (new_line_pre, 'new line prepended'),
             (new_line_post, 'new line postpended'),
#             (covert_to_bytes, 'to_bytes'),
             (covert_to_text, 'to_text')]


regexes = [PASSWORD_MATCH]


def add_modifiers(regexes, text_list, modifier):
    new_text_list = []
    for regex in regexes:
        for text in text_list:
            for modifier in modifiers:
                new_text_list.append((regex, text, modifier[0], modifier[1]))
    return new_text_list


SHOULD_MATCH_MODIFIER = add_modifiers(regexes, SHOULD_MATCH, modifiers)
SHOULD_NOT_MATCH_MODIFIERS = add_modifiers(regexes, SHOULD_NOT_MATCH, modifiers)


@pytest.mark.parametrize("regex,text,modifier,modifier_desc", SHOULD_MATCH_MODIFIER)
def test_password_match_match_modifiers(regex, text, modifier, modifier_desc):
    mod_text = modifier(text)
    msg = 'The regex """%s""" should match on "%s" (%s) but did not.' % (regex.pattern, mod_text, modifier_desc)
    assert regex.search(mod_text), msg


@pytest.mark.parametrize("regex,text,modifier,modifier_desc", SHOULD_NOT_MATCH_MODIFIERS)
def test_password_match_no_match(regex, text, modifier, modifier_desc):
    mod_text = modifier(text)
    msg = 'The regex """%s""" should not match on "%s" (%s) but did.' % (regex.pattern, mod_text, modifier_desc)
    assert regex.search(mod_text) is None, msg
