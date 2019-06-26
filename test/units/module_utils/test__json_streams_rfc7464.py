# -*- coding: utf-8 -*-
"""Tests for RFC 7464 JSON documents streaming utils."""
# pylint: disable=redefined-outer-name

from __future__ import annotations

from io import BytesIO
import json
import os
import random

import pytest

from ansible.module_utils._json_streams_rfc7464 import (
    find_documents_in_chunk,
    get_chunk_positions,
    read_json_documents,
    write_json_documents_to_stream,
    CHUNK_SIZE,
    LF_DELIMITER,
    RS_DELIMITER,
)


PURE_PAYLOAD_SIZE = 143  # JSON byte strings + wrapping delimiter bytes


@pytest.fixture
def objects_sequence():
    """Clean sequence of objects for transmission."""
    return (
        ["r", "🚑x", "s"],
        {"x☃": "y"},
        0,
        "👷",
        [
            "one",
            "two",
            {
                "three": {
                    "four": 5,
                    "six": "🐍even",
                }
            }
        ],
    )


@pytest.fixture
def json_stream_payload(objects_sequence):
    """Stream with JSON records and garbage bytes."""
    random_garbage_chunks = [
        os.urandom(CHUNK_SIZE * i).
        replace(LF_DELIMITER, b'\r').
        replace(RS_DELIMITER, b'\x2e')
        for i in range(len(objects_sequence) + 1)
    ]
    random.shuffle(random_garbage_chunks)
    in_stream_jsons = map(json.dumps, objects_sequence)
    marked_in_stream_jsons = (
        b''.join((RS_DELIMITER, j.encode('utf-8'), LF_DELIMITER))
        for j in in_stream_jsons
    )
    return BytesIO(b''.join(
        b''.join(c)
        for c in zip(random_garbage_chunks, marked_in_stream_jsons)
    ))


@pytest.mark.parametrize(
    'b_chunk,hanging_pos,chunk_positions',
    (
        pytest.param(
            b''.join((
                b'sadf089uj',
                RS_DELIMITER, b'r54mg9a3;45YS;s[', LF_DELIMITER,
                b'sdaify8)(nf8SDFlx9xIK',
            )),
            None,
            ((9, 26), ),
            id='document fits',
        ),
        pytest.param(
            b''.join((
                b'sadf089uj',
                RS_DELIMITER,
                b'r54mg9a3;45YS;s[sdaify8)(nf8SDFlx9xIK',
            )),
            None,
            ((9, None), ),
            id='document exceeds',
        ),
        pytest.param(
            b''.join((
                b'sadf089uj',
                LF_DELIMITER,
                b'r54mg9a3;45YS;s[sdaify8)(nf8SDFlx9xIK',
            )),
            -1243,
            ((-1243, 9), ),
            id='document starts in the previous chunk',
        ),
        pytest.param(
            b''.join((
                b'sadf089ujr54mg9a3;45YS;s[sdaify8)(nf8SDFlx9xIK',
            ) * 50),
            -1243,
            ((-1243, None), ),
            id="doc starts in the prev chunk and doesn't end",
        ),
        pytest.param(
            b''.join((
                b'sadf089ujr54mg9a3;45YS;s[sdaify8)(nf8SDFlx9xIK',
            ) * 50),
            None,
            (),
            id='no document in the chunk',
        ),
    )
)
def test_find_documents_in_chunk(b_chunk, hanging_pos, chunk_positions):
    """Test that document boundaries are found in chunks correctly."""
    chunks_iter = find_documents_in_chunk(b_chunk, hanging_pos)
    assert tuple(chunks_iter) == chunk_positions


@pytest.mark.parametrize(
    'b_input,chunk_positions',
    (
        pytest.param(b'x' * 64000, ((0, 65536), ), id='64000 bytes'),
        pytest.param(
            b'x' * 66000, ((0, 65536), (65536, 131072)),
            id='66000 bytes',
        ),
        pytest.param(
            b'x' * 666000,
            (
                (0, 65536),
                (65536, 131072),
                (131072, 196608),
                (196608, 262144),
                (262144, 327680),
                (327680, 393216),
                (393216, 458752),
                (458752, 524288),
                (524288, 589824),
                (589824, 655360),
                (655360, 720896),
            ),
            id='666000 bytes',
        ),
    ),
)
def test_get_chunk_positions(b_input, chunk_positions):
    """Test that stream reader selects proper chunks for processing."""
    inp = memoryview(b_input)
    assert tuple(get_chunk_positions(inp)) == chunk_positions


def test_read_json_documents(json_stream_payload, objects_sequence):
    """Test that JSON records with garbage in between can be read."""
    assert tuple(read_json_documents(json_stream_payload)) == objects_sequence


def test_write_json_documents_to_stream(objects_sequence):
    """Test that JSON docs sequence written into stream can be read."""
    with BytesIO() as json_stream:
        size = write_json_documents_to_stream(objects_sequence, json_stream)
        assert size == PURE_PAYLOAD_SIZE
        json_stream.seek(0)
        assert tuple(read_json_documents(json_stream)) == objects_sequence
