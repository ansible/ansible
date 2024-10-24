#!/usr/bin/env python
"""Validates the required keys (namespace, name, version, readme, authors) for the collection galaxy.yml metadata file"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
import sys
import yaml

from voluptuous import All, Any, MultipleInvalid
from voluptuous import Required, Schema, Optional
from voluptuous.humanize import humanize_error

from ansible.module_utils.six import string_types


def validate_galaxy_metadata_file(path):
    """Validate explicit galaxy.yml metadata file"""
    try:
        with open(path, "r") as f_path:
            routing = yaml.safe_load(f_path)
    except yaml.error.MarkedYAMLError as ex:
        print(
            "%s:%d:%d: YAML load failed: %s"
            % (
                path,
                ex.context_mark.line + 1,
                ex.context_mark.column + 1,
                re.sub(r"\s+", " ", str(ex)),
            )
        )
        return
    except Exception as ex:  # pylint: disable=broad-except
        print(
            "%s:%d:%d: YAML load failed: %s"
            % (path, 0, 0, re.sub(r"\s+", " ", str(ex)))
        )
        return

    schema = Schema(
        {
            Required("namespace"): Any(*string_types),
            Required("name"): Any(*string_types),
            Required("version"): Any(*string_types),
            Required("readme"): Any(*string_types),
            Required("authors"): Any(list),
            Optional("description"): Any(*string_types),
            Optional("license"): Any(list),
            Optional("license_file"): Any(*string_types),
            Optional("tags"): Any(list),
            Optional("dependencies"): Any(dict),
            Optional("repository"): Any(*string_types),
            Optional("documentation"): Any(*string_types),
            Optional("homepage"): Any(*string_types),
            Optional("issues"): Any(*string_types),
            Optional("build_ignore"): Any(list),
        },
        required=True,
    )

    # Ensure schema is valid

    try:
        schema(routing)
    except MultipleInvalid as ex:
        for error in ex.errors:
            # No way to get line/column numbers
            print("%s:%d:%d: %s" % (path, 0, 0, humanize_error(routing, error)))


def main():
    """Validate galaxy.yml metadata"""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    collection_galaxy_file = "galaxy.yml"

    for path in paths:
        if path == collection_galaxy_file:
            validate_galaxy_metadata_file(path)


if __name__ == "__main__":
    main()
