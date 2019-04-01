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

import select
import socket
import struct

from paramiko import util
from paramiko.common import asbytes, DEBUG
from paramiko.message import Message
from paramiko.py3compat import byte_chr, byte_ord


(
    CMD_INIT,
    CMD_VERSION,
    CMD_OPEN,
    CMD_CLOSE,
    CMD_READ,
    CMD_WRITE,
    CMD_LSTAT,
    CMD_FSTAT,
    CMD_SETSTAT,
    CMD_FSETSTAT,
    CMD_OPENDIR,
    CMD_READDIR,
    CMD_REMOVE,
    CMD_MKDIR,
    CMD_RMDIR,
    CMD_REALPATH,
    CMD_STAT,
    CMD_RENAME,
    CMD_READLINK,
    CMD_SYMLINK,
) = range(1, 21)
(CMD_STATUS, CMD_HANDLE, CMD_DATA, CMD_NAME, CMD_ATTRS) = range(101, 106)
(CMD_EXTENDED, CMD_EXTENDED_REPLY) = range(200, 202)

SFTP_OK = 0
(
    SFTP_EOF,
    SFTP_NO_SUCH_FILE,
    SFTP_PERMISSION_DENIED,
    SFTP_FAILURE,
    SFTP_BAD_MESSAGE,
    SFTP_NO_CONNECTION,
    SFTP_CONNECTION_LOST,
    SFTP_OP_UNSUPPORTED,
) = range(1, 9)

SFTP_DESC = [
    "Success",
    "End of file",
    "No such file",
    "Permission denied",
    "Failure",
    "Bad message",
    "No connection",
    "Connection lost",
    "Operation unsupported",
]

SFTP_FLAG_READ = 0x1
SFTP_FLAG_WRITE = 0x2
SFTP_FLAG_APPEND = 0x4
SFTP_FLAG_CREATE = 0x8
SFTP_FLAG_TRUNC = 0x10
SFTP_FLAG_EXCL = 0x20

_VERSION = 3


# for debugging
CMD_NAMES = {
    CMD_INIT: "init",
    CMD_VERSION: "version",
    CMD_OPEN: "open",
    CMD_CLOSE: "close",
    CMD_READ: "read",
    CMD_WRITE: "write",
    CMD_LSTAT: "lstat",
    CMD_FSTAT: "fstat",
    CMD_SETSTAT: "setstat",
    CMD_FSETSTAT: "fsetstat",
    CMD_OPENDIR: "opendir",
    CMD_READDIR: "readdir",
    CMD_REMOVE: "remove",
    CMD_MKDIR: "mkdir",
    CMD_RMDIR: "rmdir",
    CMD_REALPATH: "realpath",
    CMD_STAT: "stat",
    CMD_RENAME: "rename",
    CMD_READLINK: "readlink",
    CMD_SYMLINK: "symlink",
    CMD_STATUS: "status",
    CMD_HANDLE: "handle",
    CMD_DATA: "data",
    CMD_NAME: "name",
    CMD_ATTRS: "attrs",
    CMD_EXTENDED: "extended",
    CMD_EXTENDED_REPLY: "extended_reply",
}


class SFTPError(Exception):
    pass


class BaseSFTP(object):
    def __init__(self):
        self.logger = util.get_logger("paramiko.sftp")
        self.sock = None
        self.ultra_debug = False

    # ...internals...

    def _send_version(self):
        self._send_packet(CMD_INIT, struct.pack(">I", _VERSION))
        t, data = self._read_packet()
        if t != CMD_VERSION:
            raise SFTPError("Incompatible sftp protocol")
        version = struct.unpack(">I", data[:4])[0]
        #        if version != _VERSION:
        #            raise SFTPError('Incompatible sftp protocol')
        return version

    def _send_server_version(self):
        # winscp will freak out if the server sends version info before the
        # client finishes sending INIT.
        t, data = self._read_packet()
        if t != CMD_INIT:
            raise SFTPError("Incompatible sftp protocol")
        version = struct.unpack(">I", data[:4])[0]
        # advertise that we support "check-file"
        extension_pairs = ["check-file", "md5,sha1"]
        msg = Message()
        msg.add_int(_VERSION)
        msg.add(*extension_pairs)
        self._send_packet(CMD_VERSION, msg)
        return version

    def _log(self, level, msg, *args):
        self.logger.log(level, msg, *args)

    def _write_all(self, out):
        while len(out) > 0:
            n = self.sock.send(out)
            if n <= 0:
                raise EOFError()
            if n == len(out):
                return
            out = out[n:]
        return

    def _read_all(self, n):
        out = bytes()
        while n > 0:
            if isinstance(self.sock, socket.socket):
                # sometimes sftp is used directly over a socket instead of
                # through a paramiko channel.  in this case, check periodically
                # if the socket is closed.  (for some reason, recv() won't ever
                # return or raise an exception, but calling select on a closed
                # socket will.)
                while True:
                    read, write, err = select.select([self.sock], [], [], 0.1)
                    if len(read) > 0:
                        x = self.sock.recv(n)
                        break
            else:
                x = self.sock.recv(n)

            if len(x) == 0:
                raise EOFError()
            out += x
            n -= len(x)
        return out

    def _send_packet(self, t, packet):
        packet = asbytes(packet)
        out = struct.pack(">I", len(packet) + 1) + byte_chr(t) + packet
        if self.ultra_debug:
            self._log(DEBUG, util.format_binary(out, "OUT: "))
        self._write_all(out)

    def _read_packet(self):
        x = self._read_all(4)
        # most sftp servers won't accept packets larger than about 32k, so
        # anything with the high byte set (> 16MB) is just garbage.
        if byte_ord(x[0]):
            raise SFTPError("Garbage packet received")
        size = struct.unpack(">I", x)[0]
        data = self._read_all(size)
        if self.ultra_debug:
            self._log(DEBUG, util.format_binary(data, "IN: "))
        if size > 0:
            t = byte_ord(data[0])
            return t, data[1:]
        return 0, bytes()
