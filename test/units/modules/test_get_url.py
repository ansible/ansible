# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import pytest

from ansible.modules.get_url import parse_digest_lines

FILENAME = "sample.txt"


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        pytest.param(
            [
                "2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25 sample.txt",
            ],
            [("2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25", FILENAME)],
            id="single-line-digest-single-space",
        ),
        pytest.param(
            [
                "2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25         sample.txt",
            ],
            [("2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25", FILENAME)],
            id="single-line-digest-multiple-spaces",
        ),
        pytest.param(
            [
                "2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25         .sample.txt",
            ],
            [("2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25", FILENAME)],
            id="single-line-digest-multiple-spaces-with-dot",
        ),
        pytest.param(
            [
                "2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25         *sample.txt",
            ],
            [("2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25", FILENAME)],
            id="single-line-digest-multiple-spaces-with-asterisk",
        ),
        pytest.param(
            [
                "2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25         ./sample.txt",
            ],
            [("2a32d433bf82355a3f78318a5affa21866c9a98b151785494b386e6b08f40b25", FILENAME)],
            id="single-line-digest-multiple-spaces-with-dot-and-slash",
        ),
        pytest.param(
            [
                "a97e6837f60cec6da4491bab387296bbcd72bdba",
            ],
            [("a97e6837f60cec6da4491bab387296bbcd72bdba", FILENAME)],
            id="single-line-digest",
        ),
        pytest.param(
            [
                "a97e6837f60cec6da4491bab387296bbcd72bdba  sample.txt",
            ],
            [("a97e6837f60cec6da4491bab387296bbcd72bdba", FILENAME)],
            id="GNU-style-digest",
        ),
        pytest.param(
            [
                "SHA256 (sample.txt) = b1b6ce5073c8fac263a8fc5edfffdbd5dec1980c784e09c5bc69f8fb6056f006.",
            ],
            [
                (
                    "b1b6ce5073c8fac263a8fc5edfffdbd5dec1980c784e09c5bc69f8fb6056f006.",
                    FILENAME,
                )
            ],
            id="BSD-style-digest",
        ),
    ],
)
def test_parse_digest_lines(lines, expected):
    assert parse_digest_lines(filename=FILENAME, lines=lines) == expected
