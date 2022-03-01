"""Converters for use as the type argument for arparse's add_argument method."""
from __future__ import annotations

import argparse
import typing as t


def key_value_type(value):  # type: (str) -> t.Tuple[str, str]
    """Wrapper around key_value."""
    return key_value(value)


def key_value(value):  # type: (str) -> t.Tuple[str, str]
    """Type parsing and validation for argparse key/value pairs separated by an '=' character."""
    parts = value.split('=')

    if len(parts) != 2:
        raise argparse.ArgumentTypeError('"%s" must be in the format "key=value"' % value)

    return parts[0], parts[1]
