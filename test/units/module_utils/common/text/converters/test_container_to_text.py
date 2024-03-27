# -*- coding: utf-8 -*-
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import pytest

from ansible.module_utils.common.text.converters import container_to_text


DEFAULT_ENCODING = "utf-8"
DEFAULT_ERR_HANDLER = "surrogate_or_strict"


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ({1: 1}, {1: 1}),
        ([1, 2], [1, 2]),
        ((1, 2), (1, 2)),
        (1, 1),
        (1.1, 1.1),
        (b"str", "str"),
        ("str", "str"),
        ([b"str"], ["str"]),
        ((b"str"), ("str")),
        ({b"str": b"str"}, {"str": "str"}),
    ],
)
@pytest.mark.parametrize(
    "encoding",
    [
        "utf-8",
        "latin1",
        "shift-jis",
        "big5",
        "koi8_r",
    ],
)
@pytest.mark.parametrize(
    "errors",
    [
        "strict",
        "surrogate_or_strict",
        "surrogate_then_replace",
    ],
)
def test_container_to_text_different_types(test_input, expected, encoding, errors):
    """Test for passing objects to container_to_text()."""
    assert container_to_text(test_input, encoding=encoding, errors=errors) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ({1: 1}, {1: 1}),
        ([1, 2], [1, 2]),
        ((1, 2), (1, 2)),
        (1, 1),
        (1.1, 1.1),
        (True, True),
        (None, None),
        ("str", "str"),
        ("くらとみ".encode(DEFAULT_ENCODING), "くらとみ"),
        ("café".encode(DEFAULT_ENCODING), "café"),
        ("str".encode(DEFAULT_ENCODING), "str"),
        (["str".encode(DEFAULT_ENCODING)], ["str"]),
        (("str".encode(DEFAULT_ENCODING)), ("str")),
        ({b"str": b"str"}, {"str": "str"}),
    ],
)
def test_container_to_text_default_encoding_and_err(test_input, expected):
    """
    Test for passing objects to container_to_text(). Default encoding and errors
    """
    assert (
        container_to_text(
            test_input, encoding=DEFAULT_ENCODING, errors=DEFAULT_ERR_HANDLER
        )
        == expected
    )


@pytest.mark.parametrize(
    "test_input,encoding,expected",
    [
        ("й".encode("utf-8"), "latin1", "Ð¹"),
        ("café".encode("utf-8"), "shift_jis", "cafﾃｩ"),
    ],
)
@pytest.mark.parametrize(
    "errors",
    [
        "strict",
        "surrogate_or_strict",
        "surrogate_then_replace",
    ],
)
def test_container_to_text_incomp_encod_chars(test_input, encoding, errors, expected):
    """
    Test for passing incompatible characters and encodings container_to_text().
    """
    assert container_to_text(test_input, encoding=encoding, errors=errors) == expected
