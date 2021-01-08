# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import sys

from ansible import constants as C

ANSIBLE_COLOR = True
if C.ANSIBLE_NOCOLOR:
    ANSIBLE_COLOR = False
elif not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
    ANSIBLE_COLOR = False
else:
    try:
        import curses
        curses.setupterm()
        if curses.tigetnum('colors') < 0:
            ANSIBLE_COLOR = False
    except ImportError:
        # curses library was not found
        pass
    except curses.error:
        # curses returns an error (e.g. could not find terminal)
        ANSIBLE_COLOR = False

if C.ANSIBLE_FORCE_COLOR:
    ANSIBLE_COLOR = True

# --- begin "pretty"
#
# pretty - A miniature library that provides a Python print and stdout
# wrapper that makes colored terminal text easier to use (e.g. without
# having to mess around with ANSI escape sequences). This code is public
# domain - there is no license except that you must leave this header.
#
# Copyright (C) 2008 Brian Nez <thedude at bri1 dot com>


def parsecolor(color):
    """SGR parameter string for the specified color name."""
    matches = re.match(r"color(?P<color>[0-9]+)"
                       r"|(?P<rgb>rgb(?P<red>[0-5])(?P<green>[0-5])(?P<blue>[0-5]))"
                       r"|gray(?P<gray>[0-9]+)", color)
    if not matches:
        return C.COLOR_CODES[color]
    if matches.group('color'):
        return u'38;5;%d' % int(matches.group('color'))
    if matches.group('rgb'):
        return u'38;5;%d' % (16 + 36 * int(matches.group('red')) +
                             6 * int(matches.group('green')) +
                             int(matches.group('blue')))
    if matches.group('gray'):
        return u'38;5;%d' % (232 + int(matches.group('gray')))


def stringc(text, color, wrap_nonvisible_chars=False):
    """String in color."""

    if ANSIBLE_COLOR:
        color_code = parsecolor(color)
        fmt = u"\033[%sm%s\033[0m"
        if wrap_nonvisible_chars:
            # This option is provided for use in cases when the
            # formatting of a command line prompt is needed, such as
            # `ansible-console`. As said in `readline` sources:
            # readline/display.c:321
            # /* Current implementation:
            #         \001 (^A) start non-visible characters
            #         \002 (^B) end non-visible characters
            #    all characters except \001 and \002 (following a \001) are copied to
            #    the returned string; all characters except those between \001 and
            #    \002 are assumed to be `visible'. */
            fmt = u"\001\033[%sm\002%s\001\033[0m\002"
        return u"\n".join([fmt % (color_code, t) for t in text.split(u'\n')])
    else:
        return text


def colorize(lead, num, color):
    """ Print 'lead' = 'num' in 'color' """
    s = u"%s=%-4s" % (lead, str(num))
    if num != 0 and ANSIBLE_COLOR and color is not None:
        s = stringc(s, color)
    return s


def hostcolor(host, stats, color=True):
    if ANSIBLE_COLOR and color:
        if stats['failures'] != 0 or stats['unreachable'] != 0:
            return u"%-37s" % stringc(host, C.COLOR_ERROR)
        elif stats['changed'] != 0:
            return u"%-37s" % stringc(host, C.COLOR_CHANGED)
        else:
            return u"%-37s" % stringc(host, C.COLOR_OK)
    return u"%-26s" % host
