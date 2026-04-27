# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Matt Martz <matt@sivel.net>
# Copyright (C) 2015 Rackspace US, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations

import re


REJECTLIST_DIRS = frozenset(('.git', 'test', '.github', '.idea'))
SYS_EXIT_REGEX = re.compile(r'[^#]*sys.exit\s*\(.*')
NO_LOG_REGEX = re.compile(r'(?:pass(?!ive)|secret|token|key)', re.I)

# Everything that should not be used in a dictionary of a return value,
# since it will make user's life harder.
FORBIDDEN_DICTIONARY_KEYS = frozenset([
    'clear',
    'copy',
    'fromkeys',
    'get',
    'items',
    'keys',
    'pop',
    'popitem',
    'setdefault',
    'update',
    'values',
])


REJECTLIST_IMPORTS = {
    'requests': {
        'new_only': True,
        'error': {
            'code': 'use-module-utils-urls',
            'msg': ('requests import found, should use '
                    'ansible.module_utils.urls instead')
        }
    },
    r'boto(?:\.|$)': {
        'new_only': True,
        'error': {
            'code': 'use-boto3',
            'msg': 'boto import found, new modules should use boto3'
        }
    },
}


PLUGINS_WITH_RETURN_VALUES = ('module', )
PLUGINS_WITH_EXAMPLES = ('module', )
PLUGINS_WITH_YAML_EXAMPLES = ('module', )
