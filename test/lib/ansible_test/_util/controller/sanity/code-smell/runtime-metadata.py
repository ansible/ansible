"""Schema validation of ansible-core's ansible_builtin_runtime.yml and collection's meta/runtime.yml"""
from __future__ import annotations

import datetime
import os
import re
import sys

from functools import partial

import yaml

from voluptuous import All, Any, MultipleInvalid, PREVENT_EXTRA
from voluptuous import Required, Schema, Invalid
from voluptuous.humanize import humanize_error

from ansible.module_utils.compat.version import StrictVersion, LooseVersion
from ansible.module_utils.six import string_types
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.version import SemanticVersion


def fqcr(value):
    """Validate a FQCR."""
    if not isinstance(value, string_types):
        raise Invalid('Must be a string that is a FQCR')
    if not AnsibleCollectionRef.is_valid_fqcr(value):
        raise Invalid('Must be a FQCR')
    return value


def isodate(value, check_deprecation_date=False, is_tombstone=False):
    """Validate a datetime.date or ISO 8601 date string."""
    # datetime.date objects come from YAML dates, these are ok
    if isinstance(value, datetime.date):
        removal_date = value
    else:
        # make sure we have a string
        msg = 'Expected ISO 8601 date string (YYYY-MM-DD), or YAML date'
        if not isinstance(value, string_types):
            raise Invalid(msg)
        # From Python 3.7 in, there is datetime.date.fromisoformat(). For older versions,
        # we have to do things manually.
        if not re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2}$', value):
            raise Invalid(msg)
        try:
            removal_date = datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise Invalid(msg)
    # Make sure date is correct
    today = datetime.date.today()
    if is_tombstone:
        # For a tombstone, the removal date must be in the past
        if today < removal_date:
            raise Invalid(
                'The tombstone removal_date (%s) must not be after today (%s)' % (removal_date, today))
    else:
        # For a deprecation, the removal date must be in the future. Only test this if
        # check_deprecation_date is truish, to avoid checks to suddenly start to fail.
        if check_deprecation_date and today > removal_date:
            raise Invalid(
                'The deprecation removal_date (%s) must be after today (%s)' % (removal_date, today))
    return value


def removal_version(value, is_ansible, current_version=None, is_tombstone=False):
    """Validate a removal version string."""
    msg = (
        'Removal version must be a string' if is_ansible else
        'Removal version must be a semantic version (https://semver.org/)'
    )
    if not isinstance(value, string_types):
        raise Invalid(msg)
    try:
        if is_ansible:
            version = StrictVersion()
            version.parse(value)
            version = LooseVersion(value)  # We're storing Ansible's version as a LooseVersion
        else:
            version = SemanticVersion()
            version.parse(value)
            if version.major != 0 and (version.minor != 0 or version.patch != 0):
                raise Invalid('removal_version (%r) must be a major release, not a minor or patch release '
                              '(see specification at https://semver.org/)' % (value, ))
        if current_version is not None:
            if is_tombstone:
                # For a tombstone, the removal version must not be in the future
                if version > current_version:
                    raise Invalid('The tombstone removal_version (%r) must not be after the '
                                  'current version (%s)' % (value, current_version))
            else:
                # For a deprecation, the removal version must be in the future
                if version <= current_version:
                    raise Invalid('The deprecation removal_version (%r) must be after the '
                                  'current version (%s)' % (value, current_version))
    except ValueError:
        raise Invalid(msg)
    return value


def any_value(value):
    """Accepts anything."""
    return value


def get_ansible_version():
    """Return current ansible-core version"""
    from ansible.release import __version__

    return LooseVersion('.'.join(__version__.split('.')[:3]))


def get_collection_version():
    """Return current collection version, or None if it is not available"""
    import importlib.util

    collection_detail_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tools', 'collection_detail.py')
    collection_detail_spec = importlib.util.spec_from_file_location('collection_detail', collection_detail_path)
    collection_detail = importlib.util.module_from_spec(collection_detail_spec)
    sys.modules['collection_detail'] = collection_detail
    collection_detail_spec.loader.exec_module(collection_detail)

    # noinspection PyBroadException
    try:
        result = collection_detail.read_manifest_json('.') or collection_detail.read_galaxy_yml('.')
        return SemanticVersion(result['version'])
    except Exception:  # pylint: disable=broad-except
        # We do not care why it fails, in case we cannot get the version
        # just return None to indicate "we don't know".
        return None


def validate_metadata_file(path, is_ansible, check_deprecation_dates=False):
    """Validate explicit runtime metadata file"""
    try:
        with open(path, 'r', encoding='utf-8') as f_path:
            routing = yaml.safe_load(f_path)
    except yaml.error.MarkedYAMLError as ex:
        print('%s:%d:%d: YAML load failed: %s' % (path, ex.context_mark.line +
                                                  1, ex.context_mark.column + 1, re.sub(r'\s+', ' ', str(ex))))
        return
    except Exception as ex:  # pylint: disable=broad-except
        print('%s:%d:%d: YAML load failed: %s' %
              (path, 0, 0, re.sub(r'\s+', ' ', str(ex))))
        return

    if is_ansible:
        current_version = get_ansible_version()
    else:
        current_version = get_collection_version()

    # Updates to schema MUST also be reflected in the documentation
    # ~https://docs.ansible.com/ansible-core/devel/dev_guide/developing_collections.html

    # plugin_routing schema

    avoid_additional_data = Schema(
        Any(
            {
                Required('removal_version'): any_value,
                'warning_text': any_value,
            },
            {
                Required('removal_date'): any_value,
                'warning_text': any_value,
            }
        ),
        extra=PREVENT_EXTRA
    )

    deprecation_schema = All(
        # The first schema validates the input, and the second makes sure no extra keys are specified
        Schema(
            {
                'removal_version': partial(removal_version, is_ansible=is_ansible,
                                           current_version=current_version),
                'removal_date': partial(isodate, check_deprecation_date=check_deprecation_dates),
                'warning_text': Any(*string_types),
            }
        ),
        avoid_additional_data
    )

    tombstoning_schema = All(
        # The first schema validates the input, and the second makes sure no extra keys are specified
        Schema(
            {
                'removal_version': partial(removal_version, is_ansible=is_ansible,
                                           current_version=current_version, is_tombstone=True),
                'removal_date': partial(isodate, is_tombstone=True),
                'warning_text': Any(*string_types),
            }
        ),
        avoid_additional_data
    )

    plugins_routing_common_schema = Schema({
        ('deprecation'): Any(deprecation_schema),
        ('tombstone'): Any(tombstoning_schema),
        ('redirect'): fqcr,
    }, extra=PREVENT_EXTRA)

    plugin_routing_schema = Any(plugins_routing_common_schema)

    # Adjusted schema for modules only
    plugin_routing_schema_modules = Any(
        plugins_routing_common_schema.extend({
            ('action_plugin'): fqcr}
        )
    )

    # Adjusted schema for module_utils
    plugin_routing_schema_mu = Any(
        plugins_routing_common_schema.extend({
            ('redirect'): Any(*string_types)}
        ),
    )

    list_dict_plugin_routing_schema = [{str_type: plugin_routing_schema}
                                       for str_type in string_types]

    list_dict_plugin_routing_schema_mu = [{str_type: plugin_routing_schema_mu}
                                          for str_type in string_types]

    list_dict_plugin_routing_schema_modules = [{str_type: plugin_routing_schema_modules}
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
        ('module_utils'): Any(None, *list_dict_plugin_routing_schema_mu),
        ('modules'): Any(None, *list_dict_plugin_routing_schema_modules),
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
    """Main entry point."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    collection_legacy_file = 'meta/routing.yml'
    collection_runtime_file = 'meta/runtime.yml'

    # This is currently disabled, because if it is enabled this test can start failing
    # at a random date. For this to be properly activated, we (a) need to be able to return
    # codes for this test, and (b) make this error optional.
    check_deprecation_dates = False

    for path in paths:
        if path == collection_legacy_file:
            print('%s:%d:%d: %s' % (path, 0, 0, ("Should be called '%s'" % collection_runtime_file)))
            continue

        validate_metadata_file(
            path,
            is_ansible=path not in (collection_legacy_file, collection_runtime_file),
            check_deprecation_dates=check_deprecation_dates)


if __name__ == '__main__':
    main()
