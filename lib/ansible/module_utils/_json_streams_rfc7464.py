"""RFC 7464 implementation of JSON documents streaming."""

from __future__ import annotations

import json


CHUNK_SIZE = 2 ** 16  # 64KB
RS_DELIMITER = b'\x1E'
RS_DELIMITER_ORD = ord(RS_DELIMITER)
LF_DELIMITER = b'\x0A'  # ==LF==\n
LF_DELIMITER_ORD = ord(LF_DELIMITER)


def find_documents_in_chunk(chunk, doc_start=None):
    """Emit subchunk positions of JSON record delimiters."""
    for pos, char in enumerate(chunk):
        if char == RS_DELIMITER_ORD:
            doc_start = pos

        if char == LF_DELIMITER_ORD and doc_start is not None:
            yield doc_start, pos
            doc_start = None

    if doc_start is not None:
        # last doc chunk is hanging
        yield doc_start, None


def get_chunk_positions(input_mv):
    """Emit chunks for stream processing."""
    return (
        (n * CHUNK_SIZE, (n + 1) * CHUNK_SIZE)
        for n in range((input_mv.nbytes // CHUNK_SIZE) + 1)
    )


def find_absolute_doc_positions_in_stream(input_mv):
    """Emit absolute positions of document boundaries in stream."""
    hanging_doc_pos = None
    for stream_chunk_start, stream_chunk_end in get_chunk_positions(input_mv):
        if hanging_doc_pos is not None:
            hanging_doc_pos -= CHUNK_SIZE

        b_stream_chunk = input_mv[stream_chunk_start: stream_chunk_end].tobytes()
        stream_chunk_pos_iter = find_documents_in_chunk(
            b_stream_chunk,
            hanging_doc_pos,
        )
        document_positions = (c for c in stream_chunk_pos_iter if c)

        for doc_chunk_start, doc_chunk_end in document_positions:
            hanging_doc_pos = None
            if doc_chunk_end is None:
                hanging_doc_pos = doc_chunk_start
                break
            yield doc_chunk_start + stream_chunk_start + 1, doc_chunk_end + stream_chunk_start


def read_json_document_strings(input_byte_stream):
    """Emit document strings as they are found in the stream."""
    input_mv = memoryview(input_byte_stream.read())

    def get_text_from_mv_slice(start, end):
        return input_mv[start:end].tobytes().decode('utf-8')

    return (
        get_text_from_mv_slice(*doc_pos)
        for doc_pos in find_absolute_doc_positions_in_stream(input_mv)
    )


def read_json_documents(input_byte_stream):
    """Load JSON objects from the given stream."""
    return (
        json.loads(d)
        for d in read_json_document_strings(input_byte_stream)
    )


def write_json_documents_to_stream(objects, output_byte_stream):
    """Write RS-delimited UTF8-encoded JSON-strings to the stream.

    This follows :rfc:`7464`. It writes <RS> before
    the JSON string and puts <LF> after it.
    """
    def dump_object(obj):
        return b''.join(
            (
                RS_DELIMITER,
                json.dumps(obj).encode('utf-8'),
                LF_DELIMITER,
            ),
        )

    def write_marked_object(obj):
        bytes_written = 0
        bytes_written += output_byte_stream.write(RS_DELIMITER)
        bytes_written += output_byte_stream.write(obj)
        bytes_written += output_byte_stream.write(LF_DELIMITER)
        output_byte_stream.flush()
        return bytes_written

    return sum(
        write_marked_object(dump_object(o))
        for o in objects
    )
