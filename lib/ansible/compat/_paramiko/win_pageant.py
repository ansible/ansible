# Copyright (C) 2005 John Arbash-Meinel <john@arbash-meinel.com>
# Modified up by: Todd Whiteman <ToddW@ActiveState.com>
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
Functions for communicating with Pageant, the basic windows ssh agent program.
"""

import array
import ctypes.wintypes
import platform
import struct
from paramiko.common import zero_byte
from paramiko.py3compat import b

try:
    import _thread as thread  # Python 3.x
except ImportError:
    import thread  # Python 2.5-2.7

from . import _winapi


_AGENT_COPYDATA_ID = 0x804e50ba
_AGENT_MAX_MSGLEN = 8192
# Note: The WM_COPYDATA value is pulled from win32con, as a workaround
# so we do not have to import this huge library just for this one variable.
win32con_WM_COPYDATA = 74


def _get_pageant_window_object():
    return ctypes.windll.user32.FindWindowA(b"Pageant", b"Pageant")


def can_talk_to_agent():
    """
    Check to see if there is a "Pageant" agent we can talk to.

    This checks both if we have the required libraries (win32all or ctypes)
    and if there is a Pageant currently running.
    """
    return bool(_get_pageant_window_object())


if platform.architecture()[0] == "64bit":
    ULONG_PTR = ctypes.c_uint64
else:
    ULONG_PTR = ctypes.c_uint32


class COPYDATASTRUCT(ctypes.Structure):
    """
    ctypes implementation of
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms649010%28v=vs.85%29.aspx
    """

    _fields_ = [
        ("num_data", ULONG_PTR),
        ("data_size", ctypes.wintypes.DWORD),
        ("data_loc", ctypes.c_void_p),
    ]


def _query_pageant(msg):
    """
    Communication with the Pageant process is done through a shared
    memory-mapped file.
    """
    hwnd = _get_pageant_window_object()
    if not hwnd:
        # Raise a failure to connect exception, pageant isn't running anymore!
        return None

    # create a name for the mmap
    map_name = "PageantRequest%08x" % thread.get_ident()

    pymap = _winapi.MemoryMap(
        map_name, _AGENT_MAX_MSGLEN, _winapi.get_security_attributes_for_user()
    )
    with pymap:
        pymap.write(msg)
        # Create an array buffer containing the mapped filename
        char_buffer = array.array("b", b(map_name) + zero_byte)  # noqa
        char_buffer_address, char_buffer_size = char_buffer.buffer_info()
        # Create a string to use for the SendMessage function call
        cds = COPYDATASTRUCT(
            _AGENT_COPYDATA_ID, char_buffer_size, char_buffer_address
        )

        response = ctypes.windll.user32.SendMessageA(
            hwnd, win32con_WM_COPYDATA, ctypes.sizeof(cds), ctypes.byref(cds)
        )

        if response > 0:
            pymap.seek(0)
            datalen = pymap.read(4)
            retlen = struct.unpack(">I", datalen)[0]
            return datalen + pymap.read(retlen)
        return None


class PageantConnection(object):
    """
    Mock "connection" to an agent which roughly approximates the behavior of
    a unix local-domain socket (as used by Agent).  Requests are sent to the
    pageant daemon via special Windows magick, and responses are buffered back
    for subsequent reads.
    """

    def __init__(self):
        self._response = None

    def send(self, data):
        self._response = _query_pageant(data)

    def recv(self, n):
        if self._response is None:
            return ""
        ret = self._response[:n]
        self._response = self._response[n:]
        if self._response == "":
            self._response = None
        return ret

    def close(self):
        pass
