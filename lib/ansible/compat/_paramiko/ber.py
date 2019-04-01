# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.
from paramiko.common import max_byte, zero_byte
from paramiko.py3compat import b, byte_ord, byte_chr, long

import paramiko.util as util


class BERException(Exception):
    pass


class BER(object):
    """
    Robey's tiny little attempt at a BER decoder.
    """

    def __init__(self, content=bytes()):
        self.content = b(content)
        self.idx = 0

    def asbytes(self):
        return self.content

    def __str__(self):
        return self.asbytes()

    def __repr__(self):
        return "BER('" + repr(self.content) + "')"

    def decode(self):
        return self.decode_next()

    def decode_next(self):
        if self.idx >= len(self.content):
            return None
        ident = byte_ord(self.content[self.idx])
        self.idx += 1
        if (ident & 31) == 31:
            # identifier > 30
            ident = 0
            while self.idx < len(self.content):
                t = byte_ord(self.content[self.idx])
                self.idx += 1
                ident = (ident << 7) | (t & 0x7f)
                if not (t & 0x80):
                    break
        if self.idx >= len(self.content):
            return None
        # now fetch length
        size = byte_ord(self.content[self.idx])
        self.idx += 1
        if size & 0x80:
            # more complimicated...
            # FIXME: theoretically should handle indefinite-length (0x80)
            t = size & 0x7f
            if self.idx + t > len(self.content):
                return None
            size = util.inflate_long(
                self.content[self.idx : self.idx + t], True
            )
            self.idx += t
        if self.idx + size > len(self.content):
            # can't fit
            return None
        data = self.content[self.idx : self.idx + size]
        self.idx += size
        # now switch on id
        if ident == 0x30:
            # sequence
            return self.decode_sequence(data)
        elif ident == 2:
            # int
            return util.inflate_long(data)
        else:
            # 1: boolean (00 false, otherwise true)
            msg = "Unknown ber encoding type {:d} (robey is lazy)"
            raise BERException(msg.format(ident))

    @staticmethod
    def decode_sequence(data):
        out = []
        ber = BER(data)
        while True:
            x = ber.decode_next()
            if x is None:
                break
            out.append(x)
        return out

    def encode_tlv(self, ident, val):
        # no need to support ident > 31 here
        self.content += byte_chr(ident)
        if len(val) > 0x7f:
            lenstr = util.deflate_long(len(val))
            self.content += byte_chr(0x80 + len(lenstr)) + lenstr
        else:
            self.content += byte_chr(len(val))
        self.content += val

    def encode(self, x):
        if type(x) is bool:
            if x:
                self.encode_tlv(1, max_byte)
            else:
                self.encode_tlv(1, zero_byte)
        elif (type(x) is int) or (type(x) is long):
            self.encode_tlv(2, util.deflate_long(x))
        elif type(x) is str:
            self.encode_tlv(4, x)
        elif (type(x) is list) or (type(x) is tuple):
            self.encode_tlv(0x30, self.encode_sequence(x))
        else:
            raise BERException(
                "Unknown type for encoding: {!r}".format(type(x))
            )

    @staticmethod
    def encode_sequence(data):
        ber = BER()
        for item in data:
            ber.encode(item)
        return ber.asbytes()
