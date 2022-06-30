# Copyright Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import locale


LOCALE_INITIALIZED = False
LOCALE_INITIALIZATION_ERR = None
LOCALE = None


def _parse_localename(localename):

    """ Parses the locale code for localename and returns the
        result as tuple (language code, encoding).

        The localename is normalized and passed through the locale
        alias engine. A ValueError is raised in case the locale name
        cannot be parsed.

        The language code corresponds to RFC 1766.  code and encoding
        can be None in case the values cannot be determined or are
        unknown to this implementation.

    """
    code = locale.normalize(localename)
    if '@' in code:
        # Deal with locale modifiers
        code, modifier = code.split('@', 1)
        if modifier == 'euro' and '.' not in code:
            # Assume Latin-9 for @euro locales. This is bogus,
            # since some systems may use other encodings for these
            # locales. Also, we ignore other modifiers.
            return code, 'iso-8859-15'

    if '.' in code:
        return tuple(code.split('.')[:2])
    elif code == 'C':
        return None, None
    elif code == 'UTF-8':
        # On macOS "LC_CTYPE=UTF-8" is a valid locale setting
        # for getting UTF-8 handling for text.
        return None, 'UTF-8'
    raise ValueError('unknown locale: %s' % localename)


def initialize_locale():
    """Set the locale to the users default setting
    and set ``_LOCALE_INITIALIZED`` to indicate whether
    ``get_text_width`` may run into trouble
    """
    global LOCALE, LOCALE_INITIALIZED, LOCALE_INITIALIZATION_ERR
    if LOCALE_INITIALIZED is False:
        try:
            LOCALE = _parse_localename(
                locale.setlocale(locale.LC_ALL, '')
            )
        except locale.Error as e:
            LOCALE_INITIALIZATION_ERR = e
        else:
            LOCALE_INITIALIZED = True
            return LOCALE
    return LOCALE
