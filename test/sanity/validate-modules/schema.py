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

from voluptuous import ALLOW_EXTRA, Any, Required, Schema

option_schema = Schema(
    {
        Required('description'): Any(basestring, [basestring]),
        'required': bool,
        'choices': list,
        'aliases': list,
        'version_added': Any(basestring, float)
    },
    extra=ALLOW_EXTRA
)

doc_schema = Schema(
    {
        Required('module'): basestring,
        'short_description': basestring,
        'description': Any(basestring, [basestring]),
        'version_added': Any(basestring, float),
        'author': Any(None, basestring, [basestring]),
        'notes': Any(None, [basestring]),
        'requirements': [basestring],
        'options': Any(None, dict),
        'extends_documentation_fragment': Any(basestring, [basestring])
    },
    extra=ALLOW_EXTRA
)
