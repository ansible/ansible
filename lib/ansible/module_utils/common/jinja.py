# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
"""Lightweight Jinja template detection helpers which do not require a Jinja environment."""

from __future__ import annotations

JINJA2_OVERRIDE = '#jinja2:'

BLOCK_START_STRING = '{%'
BLOCK_END_STRING = '%}'
VARIABLE_START_STRING = '{{'
VARIABLE_END_STRING = '}}'
COMMENT_START_STRING = '{#'
COMMENT_END_STRING = '#}'


def _starts_and_ends_with_jinja_delimiters(value):
    """Returns True if the given value starts and ends with Jinja variable, block or comment delimiters."""
    for marker in (BLOCK_START_STRING, VARIABLE_START_STRING, COMMENT_START_STRING):
        if value.startswith(marker):
            break
    else:
        return False

    for marker in (BLOCK_END_STRING, VARIABLE_END_STRING, COMMENT_END_STRING):
        if value.endswith(marker):
            return True

    return False


def is_possibly_all_template(value):
    """
    A lightweight check to determine if the given string looks like it contains *only* a template, even if that template is invalid.
    Returns `True` if the given string starts with a Jinja overrides header or if it starts and ends with Jinja template delimiters.
    """
    return value.startswith(JINJA2_OVERRIDE) or _starts_and_ends_with_jinja_delimiters(value)
