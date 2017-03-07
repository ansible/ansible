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

from voluptuous import PREVENT_EXTRA, Any, Required, Schema

option_schema = Schema(
    {
        Required('description'): Any(basestring, [basestring]),
        'required': bool,
        'choices': list,
        'aliases': Any(basestring, list),
        'version_added': Any(basestring, float),
        'default': Any(None, basestring, float, int, bool, list, dict),
        # FIXME: Recursive Schema: https://github.com/alecthomas/voluptuous/issues/128
        'subspec': Any(None, basestring),
    },
    extra=PREVENT_EXTRA
)

doc_schema = Schema(
    {
        Required('module'): basestring,
        'deprecated': basestring,
        Required('short_description'): basestring,
        Required('description'): Any(basestring, [basestring]),
        # FIXME version_added should be a quoted float, legacy marker, NOT an int/float
        Required('version_added'): Any(basestring, float),
        Required('author'): Any(None, basestring, [basestring]),
        'notes': Any(None, [basestring]),
        'requirements': [basestring],
        'todo': Any(None, basestring, [basestring]),
        # Note: Types are strings, not literal bools, such as True or False
        'type': Any(None, "bool"),
        'options': Any(
            None,
            {
                basestring: option_schema
                }
        ),
        'extends_documentation_fragment': Any(basestring, [basestring])
    },
    extra=PREVENT_EXTRA
)

metadata_schema = Schema(
    {
        Required('status'): [Any('stableinterface', 'preview', 'deprecated',
                                 'removed')],
        Required('version'): '1.0',
        Required('supported_by'): Any('core', 'community', 'unmaintained',
                                      'committer')
    }
)
