# Copyright Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import locale


LOCALE_INITIALIZED = False
LOCALE_INITIALIZATION_ERR = None
LOCALE = None


def initialize_locale():
    """Set the locale to the users default setting
    and set ``_LOCALE_INITIALIZED`` to indicate whether
    ``get_text_width`` may run into trouble
    """
    global LOCALE, LOCALE_INITIALIZED, LOCALE_INITIALIZATION_ERR
    if LOCALE_INITIALIZED is False:
        try:
            locale.setlocale(locale.LC_ALL, '')
            LOCALE = locale.getpreferredencoding(False)
        except locale.Error as e:
            LOCALE_INITIALIZATION_ERR = e
        else:
            LOCALE_INITIALIZED = True
            return LOCALE
    return LOCALE
