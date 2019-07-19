# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

try:
    from html import escape as html_escape
except ImportError:
    # Python-3.2 or later
    import cgi

    def html_escape(text, quote=True):
        return cgi.escape(text, quote)

from jinja2.runtime import Undefined

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types


_ITALIC = re.compile(r"I\(([^)]+)\)")
_BOLD = re.compile(r"B\(([^)]+)\)")
_MODULE = re.compile(r"M\(([^)]+)\)")
_URL = re.compile(r"U\(([^)]+)\)")
_LINK = re.compile(r"L\(([^)]+), *([^)]+)\)")
_CONST = re.compile(r"C\(([^)]+)\)")
_RULER = re.compile(r"HORIZONTALLINE")


def html_ify(text):
    ''' convert symbols like I(this is in italics) to valid HTML '''

    if not isinstance(text, string_types):
        text = to_text(text)

    t = html_escape(text)
    t = _ITALIC.sub(r"<em>\1</em>", t)
    t = _BOLD.sub(r"<b>\1</b>", t)
    t = _MODULE.sub(r"<span class='module'>\1</span>", t)
    t = _URL.sub(r"<a href='\1'>\1</a>", t)
    t = _LINK.sub(r"<a href='\2'>\1</a>", t)
    t = _CONST.sub(r"<code>\1</code>", t)
    t = _RULER.sub(r"<hr/>", t)

    return t.strip()


def documented_type(text):
    ''' Convert any python type to a type for documentation '''

    if isinstance(text, Undefined):
        return '-'
    if text == 'str':
        return 'string'
    if text == 'bool':
        return 'boolean'
    if text == 'int':
        return 'integer'
    if text == 'dict':
        return 'dictionary'
    return text


# The max filter was added in Jinja2-2.10.  Until we can require that version, use this
def do_max(seq):
    return max(seq)


def rst_ify(text):
    ''' convert symbols like I(this is in italics) to valid restructured text '''

    try:
        t = _ITALIC.sub(r"*\1*", text)
        t = _BOLD.sub(r"**\1**", t)
        t = _MODULE.sub(r":ref:`\1 <\1_module>`", t)
        t = _LINK.sub(r"`\1 <\2>`_", t)
        t = _URL.sub(r"\1", t)
        t = _CONST.sub(r"``\1``", t)
        t = _RULER.sub(r"------------", t)
    except Exception as e:
        raise AnsibleError("Could not process (%s) : %s" % (text, e))

    return t


def rst_fmt(text, fmt):
    ''' helper for Jinja2 to do format strings '''

    return fmt % (text)


def rst_xline(width, char="="):
    ''' return a restructured text line of a given length '''

    return char * width
