#!/usr/bin/env python
"""Schema validation of ansible-base's ansible_builtin_runtime.yml and collection's meta/runtime.yml"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import os
import re
import sys
import yaml

from voluptuous import Any, MultipleInvalid, PREVENT_EXTRA
from voluptuous import Required, Schema, Invalid
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import string_types


def isodate(value):
    """Validate a datetime.date or ISO 8601 date string."""
    # datetime.date objects come from YAML dates, these are ok
    if isinstance(value, datetime.date):
        return value
    # make sure we have a string
    msg = 'Expected ISO 8601 date string (YYYY-MM-DD), or YAML date'
    if not isinstance(value, string_types):
        raise Invalid(msg)
    try:
        datetime.datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise Invalid(msg)
    return value


def validate_metadata_file(path):
    """Validate explicit runtime metadata file"""
    try:
        with open(path, 'r') as f_path:
            routing = yaml.safe_load(f_path)
    except yaml.error.MarkedYAMLError as ex:
        print('%s:%d:%d: YAML load failed: %s' % (path, ex.context_mark.line +
                                                  1, ex.context_mark.column + 1, re.sub(r'\s+', ' ', str(ex))))
        return
    except Exception as ex:  # pylint: disable=broad-except
        print('%s:%d:%d: YAML load failed: %s' %
              (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        return

    # Updates to schema MUST also be reflected in the documentation
    # ~https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html

    # plugin_routing schema

    deprecation_tombstoning_schema = Any(Schema(
        {
            Required('removal_date'): Any(isodate),
            'warning_text': Any(*string_types),
        },
        extra=PREVENT_EXTRA
    ), Schema(
        {
            Required('removal_version'): Any(*string_types),
            'warning_text': Any(*string_types),
        },
        extra=PREVENT_EXTRA
    ))

    plugin_routing_schema = Any(
        Schema({
            ('deprecation'): Any(deprecation_tombstoning_schema),
            ('tombstone'): Any(deprecation_tombstoning_schema),
            ('redirect'): Any(*string_types),
        }, extra=PREVENT_EXTRA),
    )

    list_dict_plugin_routing_schema = [{str_type: plugin_routing_schema}
                                       for str_type in string_types]

    plugin_schema = Schema({
        ('action'): Any(None, *list_dict_plugin_routing_schema),
        ('become'): Any(None, *list_dict_plugin_routing_schema),
        ('cache'): Any(None, *list_dict_plugin_routing_schema),
        ('callback'): Any(None, *list_dict_plugin_routing_schema),
        ('cliconf'): Any(None, *list_dict_plugin_routing_schema),
        ('connection'): Any(None, *list_dict_plugin_routing_schema),
        ('doc_fragments'): Any(None, *list_dict_plugin_routing_schema),
        ('filter'): Any(None, *list_dict_plugin_routing_schema),
        ('httpapi'): Any(None, *list_dict_plugin_routing_schema),
        ('inventory'): Any(None, *list_dict_plugin_routing_schema),
        ('lookup'): Any(None, *list_dict_plugin_routing_schema),
        ('module_utils'): Any(None, *list_dict_plugin_routing_schema),
        ('modules'): Any(None, *list_dict_plugin_routing_schema),
        ('netconf'): Any(None, *list_dict_plugin_routing_schema),
        ('shell'): Any(None, *list_dict_plugin_routing_schema),
        ('strategy'): Any(None, *list_dict_plugin_routing_schema),
        ('terminal'): Any(None, *list_dict_plugin_routing_schema),
        ('test'): Any(None, *list_dict_plugin_routing_schema),
        ('vars'): Any(None, *list_dict_plugin_routing_schema),
    }, extra=PREVENT_EXTRA)

    # import_redirection schema

    import_redirection_schema = Any(
        Schema({
            ('redirect'): Any(*string_types),
            # import_redirect doesn't currently support deprecation
        }, extra=PREVENT_EXTRA)
    )

    list_dict_import_redirection_schema = [{str_type: import_redirection_schema}
                                           for str_type in string_types]

    # top level schema

    schema = Schema({
        # All of these are optional
        ('plugin_routing'): Any(plugin_schema),
        ('import_redirection'): Any(None, *list_dict_import_redirection_schema),
        # requires_ansible: In the future we should validate this with SpecifierSet
        ('requires_ansible'): Any(*string_types),
        ('action_groups'): dict,
    }, extra=PREVENT_EXTRA)

    # Ensure schema is valid

    try:
        schema(routing)
    except MultipleInvalid as ex:
        for error in ex.errors:
            # No way to get line/column numbers
            print('%s:%d:%d: %s' % (path, 0, 0, humanize_error(routing, error)))


def main():
    """Validate runtime metadata"""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    collection_legacy_file = 'meta/routing.yml'
    collection_runtime_file = 'meta/runtime.yml'

    for path in paths:
        if path == collection_legacy_file:
            print('%s:%d:%d: %s' % (path, 0, 0, ("Should be called '%s'" % collection_runtime_file)))
            continue

        validate_metadata_file(path)


if __name__ == '__main__':
    main()
