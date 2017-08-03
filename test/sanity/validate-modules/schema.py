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
from ansible.module_utils.six import string_types
list_string_types = list(string_types)

suboption_schema = Schema(
    {
        Required('description'): Any(list_string_types, *string_types),
        'required': bool,
        'choices': list,
        'aliases': Any(list, *string_types),
        'version_added': Any(float, *string_types),
        'default': Any(None, float, int, bool, list, dict, *string_types),
        # Note: Types are strings, not literal bools, such as True or False
        'type': Any(None, "bool")
    },
    extra=PREVENT_EXTRA
)

# This generates list of dicts with keys from string_types and suboption_schema value
# for example in Python 3: {str: suboption_schema}
list_dict_suboption_schema = [{str_type: suboption_schema} for str_type in string_types]

option_schema = Schema(
    {
        Required('description'): Any(list_string_types, *string_types),
        'required': bool,
        'choices': list,
        'aliases': Any(list, *string_types),
        'version_added': Any(float, *string_types),
        'default': Any(None, float, int, bool, list, dict, *string_types),
        'suboptions': Any(None, *list_dict_suboption_schema),
        # Note: Types are strings, not literal bools, such as True or False
        'type': Any(None, "bool")
    },
    extra=PREVENT_EXTRA
)

# This generates list of dicts with keys from string_types and option_schema value
# for example in Python 3: {str: option_schema}
list_dict_option_schema = [{str_type: option_schema} for str_type in string_types]


def return_schema(data):

    return_schema_dict = {
        Required('description'): Any(list, *string_types),
        Required('returned'): Any(*string_types),
        Required('type'): Any('string', 'list', 'boolean', 'dict', 'complex', 'bool', 'float', 'int', 'dictionary', 'str'),
        'version_added': Any(float, *string_types),
        'sample': Any(None, list, dict, int, float, *string_types),
        'example': Any(None, list, dict, int, float, *string_types)
    }
    if isinstance(data, dict):
        if 'type' in data and (data['type'] == 'complex'):
            # This will just check if the schema has a 'contains' value.
            # It won't recursively validate the contents of the 'contains' field
            additional_schema = {
                Required('contains'): Any(dict, list, *string_types)
            }
            return_schema_dict.update(additional_schema)

    return Schema(
        return_schema_dict,
        extra=PREVENT_EXTRA
    )


def doc_schema(module_name):
    if module_name.startswith('_'):
        module_name = module_name[1:]
    return Schema(
        {
            Required('module'): module_name,
            'deprecated': Any(*string_types),
            Required('short_description'): Any(*string_types),
            Required('description'): Any(list_string_types, *string_types),
            Required('version_added'): Any(float, *string_types),
            Required('author'): Any(None, list_string_types, *string_types),
            'notes': Any(None, list_string_types),
            'requirements': list_string_types,
            'todo': Any(None, list_string_types, *string_types),
            'options': Any(None, *list_dict_option_schema),
            'extends_documentation_fragment': Any(list_string_types, *string_types)
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
            Required('metadata_version'): '1.0',
            Required('supported_by'): Any('core', 'community', 'curated')
        }
    )


# Things to add soon
####################
# 1) Recursively validate `type: complex` fields
#    This will improve documentation, though require fair amount of module tidyup

# Possible Future Enhancements
##############################

# 1) Don't allow empty options for choices, aliases, etc
# 2) If type: bool ensure choices isn't set - perhaps use Exclusive
# 3) both version_added should be quoted floats
# 4) Use Recursive Schema: https://github.com/alecthomas/voluptuous/issues/128 though don't allow two layers

#  Tool that takes JSON and generates RETURN skeleton (needs to support complex structures)
