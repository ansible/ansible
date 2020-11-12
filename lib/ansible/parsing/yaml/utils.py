# Copyright (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import text_type


def convert_yaml_objects_to_native(obj):
    """The PyYAML C extension rejects subclasses of str, so we need to ensure objects
    that we pass are native types.

    This function recurses an object and ensures we cast any of the types from
    ``ansible.parsing.yaml.objects`` into their native types, effectively cleansing
    the data before we hand it over to the Emitter internals

    This function doesn't directly check for the types from ``ansible.parsing.yaml.objects``
    but instead checks for the types those objects inherit from, to offer more flexibility.
    """
    if isinstance(obj, dict):
        return dict((convert_yaml_objects_to_native(k), convert_yaml_objects_to_native(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return [convert_yaml_objects_to_native(v) for v in obj]
    elif isinstance(obj, text_type):
        return text_type(obj)
    else:
        return obj
