# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import PY3, iteritems, string_types
from ansible.module_utils.six.moves.urllib.parse import quote, quote_plus, unquote_plus
from ansible.module_utils._text import to_bytes, to_text

try:
    from jinja2.filters import do_urlencode
    HAS_URLENCODE = True
except ImportError:
    HAS_URLENCODE = False


def unicode_urldecode(string):
    if PY3:
        return unquote_plus(string)
    return to_text(unquote_plus(to_bytes(string)))


def do_urldecode(string):
    return unicode_urldecode(string)


# NOTE: We implement urlencode when Jinja2 is older than v2.7
def unicode_urlencode(string, for_qs=False):
    safe = b'' if for_qs else b'/'
    if for_qs:
        quote_func = quote_plus
    else:
        quote_func = quote
    if PY3:
        return quote_func(string, safe)
    return to_text(quote_func(to_bytes(string), safe))


def do_urlencode(value):
    itemiter = None
    if isinstance(value, dict):
        itemiter = iteritems(value)
    elif not isinstance(value, string_types):
        try:
            itemiter = iter(value)
        except TypeError:
            pass
    if itemiter is None:
        return unicode_urlencode(value)
    return u'&'.join(unicode_urlencode(k) + '=' +
                     unicode_urlencode(v, for_qs=True)
                     for k, v in itemiter)


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        filters = {
            'urldecode': do_urldecode,
        }

        if not HAS_URLENCODE:
            filters['urlencode'] = do_urlencode

        return filters
