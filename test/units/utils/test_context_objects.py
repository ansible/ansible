# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import argparse

import pytest

from ansible.module_utils.common.collections import ImmutableDict
from ansible.utils import context_objects as co


MAKE_IMMUTABLE_DATA = (
    ("くらとみ", "くらとみ"),
    (42, 42),
    ({"café": "くらとみ"}, ImmutableDict({"café": "くらとみ"})),
    ([1, "café", "くらとみ"], (1, "café", "くらとみ")),
    (set((1, "café", "くらとみ")), frozenset((1, "café", "くらとみ"))),
    ({"café": [1, set("ñ")]}, ImmutableDict({"café": (1, frozenset("ñ"))})),
    (
        [set((1, 2)), {"くらとみ": 3}],
        (frozenset((1, 2)), ImmutableDict({"くらとみ": 3})),
    ),
)


@pytest.mark.parametrize("data, expected", MAKE_IMMUTABLE_DATA)
def test_make_immutable(data, expected):
    assert co._make_immutable(data) == expected


def test_cliargs_from_dict():
    old_dict = {
        "tags": ["production", "webservers"],
        "check_mode": True,
        "start_at_task": "Start with くらとみ",
    }
    expected = frozenset(
        (
            ("tags", ("production", "webservers")),
            ("check_mode", True),
            ("start_at_task", "Start with くらとみ"),
        )
    )

    assert frozenset(co.CLIArgs(old_dict).items()) == expected


def test_cliargs():
    class FakeOptions:
        pass

    options = FakeOptions()
    options.tags = ["production", "webservers"]
    options.check_mode = True
    options.start_at_task = "Start with くらとみ"

    expected = frozenset(
        (
            ("tags", ("production", "webservers")),
            ("check_mode", True),
            ("start_at_task", "Start with くらとみ"),
        )
    )

    assert frozenset(co.CLIArgs.from_options(options).items()) == expected


def test_cliargs_argparse():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "integers",
        metavar="N",
        type=int,
        nargs="+",
        help="an integer for the accumulator",
    )
    parser.add_argument(
        "--sum",
        dest="accumulate",
        action="store_const",
        const=sum,
        default=max,
        help="sum the integers (default: find the max)",
    )
    args = parser.parse_args(["--sum", "1", "2"])

    expected = frozenset((("accumulate", sum), ("integers", (1, 2))))

    assert frozenset(co.CLIArgs.from_options(args).items()) == expected
