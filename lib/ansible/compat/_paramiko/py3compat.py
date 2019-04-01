import sys
import base64

__all__ = [
    "PY2",
    "string_types",
    "integer_types",
    "text_type",
    "bytes_types",
    "bytes",
    "long",
    "input",
    "decodebytes",
    "encodebytes",
    "bytestring",
    "byte_ord",
    "byte_chr",
    "byte_mask",
    "b",
    "u",
    "b2s",
    "StringIO",
    "BytesIO",
    "is_callable",
    "MAXSIZE",
    "next",
    "builtins",
]

PY2 = sys.version_info[0] < 3

if PY2:
    string_types = basestring  # NOQA
    text_type = unicode  # NOQA
    bytes_types = str
    bytes = str
    integer_types = (int, long)  # NOQA
    long = long  # NOQA
    input = raw_input  # NOQA
    decodebytes = base64.decodestring
    encodebytes = base64.encodestring

    import __builtin__ as builtins

    def bytestring(s):  # NOQA
        if isinstance(s, unicode):  # NOQA
            return s.encode("utf-8")
        return s

    byte_ord = ord  # NOQA
    byte_chr = chr  # NOQA

    def byte_mask(c, mask):
        return chr(ord(c) & mask)

    def b(s, encoding="utf8"):  # NOQA
        """cast unicode or bytes to bytes"""
        if isinstance(s, str):
            return s
        elif isinstance(s, unicode):  # NOQA
            return s.encode(encoding)
        elif isinstance(s, buffer):  # NOQA
            return s
        else:
            raise TypeError("Expected unicode or bytes, got {!r}".format(s))

    def u(s, encoding="utf8"):  # NOQA
        """cast bytes or unicode to unicode"""
        if isinstance(s, str):
            return s.decode(encoding)
        elif isinstance(s, unicode):  # NOQA
            return s
        elif isinstance(s, buffer):  # NOQA
            return s.decode(encoding)
        else:
            raise TypeError("Expected unicode or bytes, got {!r}".format(s))

    def b2s(s):
        return s

    import cStringIO

    StringIO = cStringIO.StringIO
    BytesIO = StringIO

    def is_callable(c):  # NOQA
        return callable(c)

    def get_next(c):  # NOQA
        return c.next

    def next(c):
        return c.next()

    # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
    class X(object):
        def __len__(self):
            return 1 << 31

    try:
        len(X())
    except OverflowError:
        # 32-bit
        MAXSIZE = int((1 << 31) - 1)  # NOQA
    else:
        # 64-bit
        MAXSIZE = int((1 << 63) - 1)  # NOQA
    del X
else:
    import collections
    import struct
    import builtins

    string_types = str
    text_type = str
    bytes = bytes
    bytes_types = bytes
    integer_types = int

    class long(int):
        pass

    input = input
    decodebytes = base64.decodebytes
    encodebytes = base64.encodebytes

    def bytestring(s):
        return s

    def byte_ord(c):
        # In case we're handed a string instead of an int.
        if not isinstance(c, int):
            c = ord(c)
        return c

    def byte_chr(c):
        assert isinstance(c, int)
        return struct.pack("B", c)

    def byte_mask(c, mask):
        assert isinstance(c, int)
        return struct.pack("B", c & mask)

    def b(s, encoding="utf8"):
        """cast unicode or bytes to bytes"""
        if isinstance(s, bytes):
            return s
        elif isinstance(s, str):
            return s.encode(encoding)
        else:
            raise TypeError("Expected unicode or bytes, got {!r}".format(s))

    def u(s, encoding="utf8"):
        """cast bytes or unicode to unicode"""
        if isinstance(s, bytes):
            return s.decode(encoding)
        elif isinstance(s, str):
            return s
        else:
            raise TypeError("Expected unicode or bytes, got {!r}".format(s))

    def b2s(s):
        return s.decode() if isinstance(s, bytes) else s

    import io

    StringIO = io.StringIO  # NOQA
    BytesIO = io.BytesIO  # NOQA

    def is_callable(c):
        return isinstance(c, collections.Callable)

    def get_next(c):
        return c.__next__

    next = next

    MAXSIZE = sys.maxsize  # NOQA
