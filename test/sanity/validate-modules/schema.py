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

suboption_schema = Schema(
    {
        Required('description'): Any(basestring, [basestring]),
        'required': bool,
        'choices': list,
        'aliases': Any(basestring, list),
        'version_added': Any(basestring, float),
        'default': Any(None, basestring, float, int, bool, list, dict),
        # Note: Types are strings, not literal bools, such as True or False
        'type': Any(None, "bool")
    },
    extra=PREVENT_EXTRA
)

option_schema = Schema(
    {
        Required('description'): Any(basestring, [basestring]),
        'required': bool,
        'choices': list,
        'aliases': Any(basestring, list),
        'version_added': Any(basestring, float),
        'default': Any(None, basestring, float, int, bool, list, dict),
        'suboptions': Any(None, {basestring: suboption_schema,}),
        # Note: Types are strings, not literal bools, such as True or False
        'type': Any(None, "bool")
    },
    extra=PREVENT_EXTRA
)

def doc_schema(module_name):
    if module_name.startswith('_'):
        module_name = module_name[1:]
    return Schema(
        {
            Required('module'): module_name,
            'deprecated': basestring,
            Required('short_description'): basestring,
            Required('description'): Any(basestring, [basestring]),
            Required('version_added'): Any(basestring, float),
            Required('author'): Any(None, basestring, [basestring]),
            'notes': Any(None, [basestring]),
            'requirements': [basestring],
            'todo': Any(None, basestring, [basestring]),
            'options': Any(None, {basestring: option_schema}),
            'extends_documentation_fragment': Any(basestring, [basestring])
        },
        extra=PREVENT_EXTRA
    )

def metadata_schema(deprecated):
    valid_status = Any('stableinterface', 'preview', 'deprecated', 'removed')
    if deprecated:
        valid_status = Any('deprecated')

    return Schema(
        {
            Required('status'): [valid_status],
            Required('version'): '1.0',
            Required('supported_by'): Any('core', 'community', 'unmaintained',
                                          'committer')
        }
    )



# Things to add soon
####################
# 1) Validate RETURN, including `contains` if `type: complex`
#    This will improve documentation, though require fair amount of module tidyup

# Possible Future Enhancements
##############################

# 1) Don't allow empty options for choices, aliases, etc
# 2) If type: bool ensure choices isn't set - perhaps use Exclusive
# 3) both version_added should be quoted floats
# 4) Use Recursive Schema: https://github.com/alecthomas/voluptuous/issues/128 though don't allow two layers

#  Tool that takes JSON and generates RETURN skeleton (needs to support complex structures)
