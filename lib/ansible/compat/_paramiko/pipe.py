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

"""
Abstraction of a one-way pipe where the read end can be used in
`select.select`. Normally this is trivial, but Windows makes it nearly
impossible.

The pipe acts like an Event, which can be set or cleared. When set, the pipe
will trigger as readable in `select <select.select>`.
"""

import sys
import os
import socket


def make_pipe():
    if sys.platform[:3] != "win":
        p = PosixPipe()
    else:
        p = WindowsPipe()
    return p


class PosixPipe(object):
    def __init__(self):
        self._rfd, self._wfd = os.pipe()
        self._set = False
        self._forever = False
        self._closed = False

    def close(self):
        os.close(self._rfd)
        os.close(self._wfd)
        # used for unit tests:
        self._closed = True

    def fileno(self):
        return self._rfd

    def clear(self):
        if not self._set or self._forever:
            return
        os.read(self._rfd, 1)
        self._set = False

    def set(self):
        if self._set or self._closed:
            return
        self._set = True
        os.write(self._wfd, b"*")

    def set_forever(self):
        self._forever = True
        self.set()


class WindowsPipe(object):
    """
    On Windows, only an OS-level "WinSock" may be used in select(), but reads
    and writes must be to the actual socket object.
    """

    def __init__(self):
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv.bind(("127.0.0.1", 0))
        serv.listen(1)

        # need to save sockets in _rsock/_wsock so they don't get closed
        self._rsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._rsock.connect(("127.0.0.1", serv.getsockname()[1]))

        self._wsock, addr = serv.accept()
        serv.close()
        self._set = False
        self._forever = False
        self._closed = False

    def close(self):
        self._rsock.close()
        self._wsock.close()
        # used for unit tests:
        self._closed = True

    def fileno(self):
        return self._rsock.fileno()

    def clear(self):
        if not self._set or self._forever:
            return
        self._rsock.recv(1)
        self._set = False

    def set(self):
        if self._set or self._closed:
            return
        self._set = True
        self._wsock.send(b"*")

    def set_forever(self):
        self._forever = True
        self.set()


class OrPipe(object):
    def __init__(self, pipe):
        self._set = False
        self._partner = None
        self._pipe = pipe

    def set(self):
        self._set = True
        if not self._partner._set:
            self._pipe.set()

    def clear(self):
        self._set = False
        if not self._partner._set:
            self._pipe.clear()


def make_or_pipe(pipe):
    """
    wraps a pipe into two pipe-like objects which are "or"d together to
    affect the real pipe. if either returned pipe is set, the wrapped pipe
    is set. when both are cleared, the wrapped pipe is cleared.
    """
    p1 = OrPipe(pipe)
    p2 = OrPipe(pipe)
    p1._partner = p2
    p2._partner = p1
    return p1, p2
