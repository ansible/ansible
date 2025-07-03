"""Actions for argparse."""

from __future__ import annotations

import argparse
import enum
import typing as t


class EnumAction(argparse.Action):
    """Parse an enum using the lowercase enum names."""

    def __init__(self, **kwargs: t.Any) -> None:
        self.enum_type: t.Type[enum.Enum] = kwargs.pop('type', None)
        kwargs.setdefault('choices', tuple(e.name.lower() for e in self.enum_type))
        super().__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        value = self.enum_type[values.upper()]
        setattr(namespace, self.dest, value)
