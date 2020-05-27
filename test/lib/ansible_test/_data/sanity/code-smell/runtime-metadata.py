#!/usr/bin/env python
"""Schema validation of ansible-base's ansible_builtin_runtime.yml and collection's meta/runtime.yml"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import sys
import yaml

from voluptuous import Any, MultipleInvalid, PREVENT_EXTRA
from voluptuous import Required, Schema
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import string_types


def main():
    """Validate runtime"""
    ansible_builtin_runtime = 'lib/ansible/config/ansible_builtin_runtime.yml'
    collection_legacy_file = 'meta/routing.yml'
    collection_runtime_file = 'meta/runtime.yml'
    path = ''

    # Check if the correct routing files can be found

    if os.path.isfile(ansible_builtin_runtime):
        # We are in side an ansible-base checkout, so validate ansible_builtin_runtime
        path = ansible_builtin_runtime
    elif os.path.isfile(collection_runtime_file):
        # We are in a collection, so validate meta/routing.yml
        path = collection_runtime_file

    if os.path.isfile(collection_legacy_file):
        # Collection contains old name, renamed in #67684
        print('%s:%d:%d: %s' % (collection_legacy_file, 0, 0, ("Should be called '%s'" % collection_runtime_file)))

    if not path:
        # In a collection, though no meta/routing
        sys.exit(0)

    try:
        with open(path, 'r') as f_path:
            routing = yaml.safe_load(f_path)
    except yaml.error.MarkedYAMLError as ex:
        print('%s:%d:%d: YAML load failed: %s' % (path, ex.context_mark.line +
                                                  1, ex.context_mark.column + 1, re.sub(r'\s+', ' ', str(ex))))
        sys.exit()
    except Exception as ex:  # pylint: disable=broad-except
        print('%s:%d:%d: YAML load failed: %s' %
              (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        sys.exit()

    # Updates to schema MUST also be reflected in the documentation
    # ~https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html

    # plugin_routing schema

    deprecation_schema = Any(Schema(
        {
            Required('removal_date'): Any(*string_types),
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
            ('deprecation'): Any(deprecation_schema),
            ('redirect'): Any(*string_types),
        }, extra=PREVENT_EXTRA)
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


if __name__ == '__main__':
    main()
