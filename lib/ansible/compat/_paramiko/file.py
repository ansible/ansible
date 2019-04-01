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
from paramiko.common import (
    linefeed_byte_value,
    crlf,
    cr_byte,
    linefeed_byte,
    cr_byte_value,
)
from paramiko.py3compat import BytesIO, PY2, u, bytes_types, text_type

from paramiko.util import ClosingContextManager


class BufferedFile(ClosingContextManager):
    """
    Reusable base class to implement Python-style file buffering around a
    simpler stream.
    """

    _DEFAULT_BUFSIZE = 8192

    SEEK_SET = 0
    SEEK_CUR = 1
    SEEK_END = 2

    FLAG_READ = 0x1
    FLAG_WRITE = 0x2
    FLAG_APPEND = 0x4
    FLAG_BINARY = 0x10
    FLAG_BUFFERED = 0x20
    FLAG_LINE_BUFFERED = 0x40
    FLAG_UNIVERSAL_NEWLINE = 0x80

    def __init__(self):
        self.newlines = None
        self._flags = 0
        self._bufsize = self._DEFAULT_BUFSIZE
        self._wbuffer = BytesIO()
        self._rbuffer = bytes()
        self._at_trailing_cr = False
        self._closed = False
        # pos - position within the file, according to the user
        # realpos - position according the OS
        # (these may be different because we buffer for line reading)
        self._pos = self._realpos = 0
        # size only matters for seekable files
        self._size = 0

    def __del__(self):
        self.close()

    def __iter__(self):
        """
        Returns an iterator that can be used to iterate over the lines in this
        file.  This iterator happens to return the file itself, since a file is
        its own iterator.

        :raises: ``ValueError`` -- if the file is closed.
        """
        if self._closed:
            raise ValueError("I/O operation on closed file")
        return self

    def close(self):
        """
        Close the file.  Future read and write operations will fail.
        """
        self.flush()
        self._closed = True

    def flush(self):
        """
        Write out any data in the write buffer.  This may do nothing if write
        buffering is not turned on.
        """
        self._write_all(self._wbuffer.getvalue())
        self._wbuffer = BytesIO()
        return

    if PY2:

        def next(self):
            """
            Returns the next line from the input, or raises
            ``StopIteration`` when EOF is hit.  Unlike Python file
            objects, it's okay to mix calls to `next` and `readline`.

            :raises: ``StopIteration`` -- when the end of the file is reached.

            :returns: a line (`str`) read from the file.
            """
            line = self.readline()
            if not line:
                raise StopIteration
            return line

    else:

        def __next__(self):
            """
            Returns the next line from the input, or raises ``StopIteration``
            when EOF is hit.  Unlike python file objects, it's okay to mix
            calls to `.next` and `.readline`.

            :raises: ``StopIteration`` -- when the end of the file is reached.

            :returns: a line (`str`) read from the file.
            """
            line = self.readline()
            if not line:
                raise StopIteration
            return line

    def readable(self):
        """
        Check if the file can be read from.

        :returns:
            `True` if the file can be read from. If `False`, `read` will raise
            an exception.
        """
        return (self._flags & self.FLAG_READ) == self.FLAG_READ

    def writable(self):
        """
        Check if the file can be written to.

        :returns:
            `True` if the file can be written to. If `False`, `write` will
            raise an exception.
        """
        return (self._flags & self.FLAG_WRITE) == self.FLAG_WRITE

    def seekable(self):
        """
        Check if the file supports random access.

        :returns:
            `True` if the file supports random access. If `False`, `seek` will
            raise an exception.
        """
        return False

    def readinto(self, buff):
        """
        Read up to ``len(buff)`` bytes into ``bytearray`` *buff* and return the
        number of bytes read.

        :returns:
            The number of bytes read.
        """
        data = self.read(len(buff))
        buff[: len(data)] = data
        return len(data)

    def read(self, size=None):
        """
        Read at most ``size`` bytes from the file (less if we hit the end of
        the file first).  If the ``size`` argument is negative or omitted,
        read all the remaining data in the file.

        .. note::
            ``'b'`` mode flag is ignored (``self.FLAG_BINARY`` in
            ``self._flags``), because SSH treats all files as binary, since we
            have no idea what encoding the file is in, or even if the file is
            text data.

        :param int size: maximum number of bytes to read
        :returns:
            data read from the file (as bytes), or an empty string if EOF was
            encountered immediately
        """
        if self._closed:
            raise IOError("File is closed")
        if not (self._flags & self.FLAG_READ):
            raise IOError("File is not open for reading")
        if (size is None) or (size < 0):
            # go for broke
            result = self._rbuffer
            self._rbuffer = bytes()
            self._pos += len(result)
            while True:
                try:
                    new_data = self._read(self._DEFAULT_BUFSIZE)
                except EOFError:
                    new_data = None
                if (new_data is None) or (len(new_data) == 0):
                    break
                result += new_data
                self._realpos += len(new_data)
                self._pos += len(new_data)
            return result
        if size <= len(self._rbuffer):
            result = self._rbuffer[:size]
            self._rbuffer = self._rbuffer[size:]
            self._pos += len(result)
            return result
        while len(self._rbuffer) < size:
            read_size = size - len(self._rbuffer)
            if self._flags & self.FLAG_BUFFERED:
                read_size = max(self._bufsize, read_size)
            try:
                new_data = self._read(read_size)
            except EOFError:
                new_data = None
            if (new_data is None) or (len(new_data) == 0):
                break
            self._rbuffer += new_data
            self._realpos += len(new_data)
        result = self._rbuffer[:size]
        self._rbuffer = self._rbuffer[size:]
        self._pos += len(result)
        return result

    def readline(self, size=None):
        """
        Read one entire line from the file.  A trailing newline character is
        kept in the string (but may be absent when a file ends with an
        incomplete line).  If the size argument is present and non-negative, it
        is a maximum byte count (including the trailing newline) and an
        incomplete line may be returned.  An empty string is returned only when
        EOF is encountered immediately.

        .. note::
            Unlike stdio's ``fgets``, the returned string contains null
            characters (``'\\0'``) if they occurred in the input.

        :param int size: maximum length of returned string.
        :returns:
            next line of the file, or an empty string if the end of the
            file has been reached.

            If the file was opened in binary (``'b'``) mode: bytes are returned
            Else: the encoding of the file is assumed to be UTF-8 and character
            strings (`str`) are returned
        """
        # it's almost silly how complex this function is.
        if self._closed:
            raise IOError("File is closed")
        if not (self._flags & self.FLAG_READ):
            raise IOError("File not open for reading")
        line = self._rbuffer
        truncated = False
        while True:
            if (
                self._at_trailing_cr
                and self._flags & self.FLAG_UNIVERSAL_NEWLINE
                and len(line) > 0
            ):
                # edge case: the newline may be '\r\n' and we may have read
                # only the first '\r' last time.
                if line[0] == linefeed_byte_value:
                    line = line[1:]
                    self._record_newline(crlf)
                else:
                    self._record_newline(cr_byte)
                self._at_trailing_cr = False
            # check size before looking for a linefeed, in case we already have
            # enough.
            if (size is not None) and (size >= 0):
                if len(line) >= size:
                    # truncate line
                    self._rbuffer = line[size:]
                    line = line[:size]
                    truncated = True
                    break
                n = size - len(line)
            else:
                n = self._bufsize
            if linefeed_byte in line or (
                self._flags & self.FLAG_UNIVERSAL_NEWLINE and cr_byte in line
            ):
                break
            try:
                new_data = self._read(n)
            except EOFError:
                new_data = None
            if (new_data is None) or (len(new_data) == 0):
                self._rbuffer = bytes()
                self._pos += len(line)
                return line if self._flags & self.FLAG_BINARY else u(line)
            line += new_data
            self._realpos += len(new_data)
        # find the newline
        pos = line.find(linefeed_byte)
        if self._flags & self.FLAG_UNIVERSAL_NEWLINE:
            rpos = line.find(cr_byte)
            if (rpos >= 0) and (rpos < pos or pos < 0):
                pos = rpos
        if pos == -1:
            # we couldn't find a newline in the truncated string, return it
            self._pos += len(line)
            return line if self._flags & self.FLAG_BINARY else u(line)
        xpos = pos + 1
        if (
            line[pos] == cr_byte_value
            and xpos < len(line)
            and line[xpos] == linefeed_byte_value
        ):
            xpos += 1
        # if the string was truncated, _rbuffer needs to have the string after
        # the newline character plus the truncated part of the line we stored
        # earlier in _rbuffer
        if truncated:
            self._rbuffer = line[xpos:] + self._rbuffer
        else:
            self._rbuffer = line[xpos:]

        lf = line[pos:xpos]
        line = line[:pos] + linefeed_byte
        if (len(self._rbuffer) == 0) and (lf == cr_byte):
            # we could read the line up to a '\r' and there could still be a
            # '\n' following that we read next time.  note that and eat it.
            self._at_trailing_cr = True
        else:
            self._record_newline(lf)
        self._pos += len(line)
        return line if self._flags & self.FLAG_BINARY else u(line)

    def readlines(self, sizehint=None):
        """
        Read all remaining lines using `readline` and return them as a list.
        If the optional ``sizehint`` argument is present, instead of reading up
        to EOF, whole lines totalling approximately sizehint bytes (possibly
        after rounding up to an internal buffer size) are read.

        :param int sizehint: desired maximum number of bytes to read.
        :returns: list of lines read from the file.
        """
        lines = []
        byte_count = 0
        while True:
            line = self.readline()
            if len(line) == 0:
                break
            lines.append(line)
            byte_count += len(line)
            if (sizehint is not None) and (byte_count >= sizehint):
                break
        return lines

    def seek(self, offset, whence=0):
        """
        Set the file's current position, like stdio's ``fseek``.  Not all file
        objects support seeking.

        .. note::
            If a file is opened in append mode (``'a'`` or ``'a+'``), any seek
            operations will be undone at the next write (as the file position
            will move back to the end of the file).

        :param int offset:
            position to move to within the file, relative to ``whence``.
        :param int whence:
            type of movement: 0 = absolute; 1 = relative to the current
            position; 2 = relative to the end of the file.

        :raises: ``IOError`` -- if the file doesn't support random access.
        """
        raise IOError("File does not support seeking.")

    def tell(self):
        """
        Return the file's current position.  This may not be accurate or
        useful if the underlying file doesn't support random access, or was
        opened in append mode.

        :returns: file position (`number <int>` of bytes).
        """
        return self._pos

    def write(self, data):
        """
        Write data to the file.  If write buffering is on (``bufsize`` was
        specified and non-zero), some or all of the data may not actually be
        written yet.  (Use `flush` or `close` to force buffered data to be
        written out.)

        :param data: ``str``/``bytes`` data to write
        """
        if isinstance(data, text_type):
            # Accept text and encode as utf-8 for compatibility only.
            data = data.encode("utf-8")
        if self._closed:
            raise IOError("File is closed")
        if not (self._flags & self.FLAG_WRITE):
            raise IOError("File not open for writing")
        if not (self._flags & self.FLAG_BUFFERED):
            self._write_all(data)
            return
        self._wbuffer.write(data)
        if self._flags & self.FLAG_LINE_BUFFERED:
            # only scan the new data for linefeed, to avoid wasting time.
            last_newline_pos = data.rfind(linefeed_byte)
            if last_newline_pos >= 0:
                wbuf = self._wbuffer.getvalue()
                last_newline_pos += len(wbuf) - len(data)
                self._write_all(wbuf[: last_newline_pos + 1])
                self._wbuffer = BytesIO()
                self._wbuffer.write(wbuf[last_newline_pos + 1 :])
            return
        # even if we're line buffering, if the buffer has grown past the
        # buffer size, force a flush.
        if self._wbuffer.tell() >= self._bufsize:
            self.flush()
        return

    def writelines(self, sequence):
        """
        Write a sequence of strings to the file.  The sequence can be any
        iterable object producing strings, typically a list of strings.  (The
        name is intended to match `readlines`; `writelines` does not add line
        separators.)

        :param sequence: an iterable sequence of strings.
        """
        for line in sequence:
            self.write(line)
        return

    def xreadlines(self):
        """
        Identical to ``iter(f)``.  This is a deprecated file interface that
        predates Python iterator support.
        """
        return self

    @property
    def closed(self):
        return self._closed

    # ...overrides...

    def _read(self, size):
        """
        (subclass override)
        Read data from the stream.  Return ``None`` or raise ``EOFError`` to
        indicate EOF.
        """
        raise EOFError()

    def _write(self, data):
        """
        (subclass override)
        Write data into the stream.
        """
        raise IOError("write not implemented")

    def _get_size(self):
        """
        (subclass override)
        Return the size of the file.  This is called from within `_set_mode`
        if the file is opened in append mode, so the file position can be
        tracked and `seek` and `tell` will work correctly.  If the file is
        a stream that can't be randomly accessed, you don't need to override
        this method,
        """
        return 0

    # ...internals...

    def _set_mode(self, mode="r", bufsize=-1):
        """
        Subclasses call this method to initialize the BufferedFile.
        """
        # set bufsize in any event, because it's used for readline().
        self._bufsize = self._DEFAULT_BUFSIZE
        if bufsize < 0:
            # do no buffering by default, because otherwise writes will get
            # buffered in a way that will probably confuse people.
            bufsize = 0
        if bufsize == 1:
            # apparently, line buffering only affects writes.  reads are only
            # buffered if you call readline (directly or indirectly: iterating
            # over a file will indirectly call readline).
            self._flags |= self.FLAG_BUFFERED | self.FLAG_LINE_BUFFERED
        elif bufsize > 1:
            self._bufsize = bufsize
            self._flags |= self.FLAG_BUFFERED
            self._flags &= ~self.FLAG_LINE_BUFFERED
        elif bufsize == 0:
            # unbuffered
            self._flags &= ~(self.FLAG_BUFFERED | self.FLAG_LINE_BUFFERED)

        if ("r" in mode) or ("+" in mode):
            self._flags |= self.FLAG_READ
        if ("w" in mode) or ("+" in mode):
            self._flags |= self.FLAG_WRITE
        if "a" in mode:
            self._flags |= self.FLAG_WRITE | self.FLAG_APPEND
            self._size = self._get_size()
            self._pos = self._realpos = self._size
        if "b" in mode:
            self._flags |= self.FLAG_BINARY
        if "U" in mode:
            self._flags |= self.FLAG_UNIVERSAL_NEWLINE
            # built-in file objects have this attribute to store which kinds of
            # line terminations they've seen:
            # <http://www.python.org/doc/current/lib/built-in-funcs.html>
            self.newlines = None

    def _write_all(self, data):
        # the underlying stream may be something that does partial writes (like
        # a socket).
        while len(data) > 0:
            count = self._write(data)
            data = data[count:]
            if self._flags & self.FLAG_APPEND:
                self._size += count
                self._pos = self._realpos = self._size
            else:
                self._pos += count
                self._realpos += count
        return None

    def _record_newline(self, newline):
        # silliness about tracking what kinds of newlines we've seen.
        # i don't understand why it can be None, a string, or a tuple, instead
        # of just always being a tuple, but we'll emulate that behavior anyway.
        if not (self._flags & self.FLAG_UNIVERSAL_NEWLINE):
            return
        if self.newlines is None:
            self.newlines = newline
        elif self.newlines != newline and isinstance(
            self.newlines, bytes_types
        ):
            self.newlines = (self.newlines, newline)
        elif newline not in self.newlines:
            self.newlines += (newline,)
