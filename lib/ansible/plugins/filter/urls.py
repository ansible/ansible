# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six.moves.urllib.parse import unquote_plus
from ansible.module_utils._text import to_bytes, to_text


def urldecode(string):
    return to_text(unquote_plus(to_bytes(string, errors='surrogate_then_strict')))


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            'urldecode': urldecode,
        }
