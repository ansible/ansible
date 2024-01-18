# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from functools import partial

from urllib.parse import unquote_plus


class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            'urldecode': partial(unquote_plus),
        }
