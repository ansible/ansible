# Copyright (C) 2003-2006 Robey Pointer <robeypointer@gmail.com>
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

import stat
import time
from paramiko.common import x80000000, o700, o70, xffffffff
from paramiko.py3compat import long, b


class SFTPAttributes(object):
    """
    Representation of the attributes of a file (or proxied file) for SFTP in
    client or server mode.  It attemps to mirror the object returned by
    `os.stat` as closely as possible, so it may have the following fields,
    with the same meanings as those returned by an `os.stat` object:

        - ``st_size``
        - ``st_uid``
        - ``st_gid``
        - ``st_mode``
        - ``st_atime``
        - ``st_mtime``

    Because SFTP allows flags to have other arbitrary named attributes, these
    are stored in a dict named ``attr``.  Occasionally, the filename is also
    stored, in ``filename``.
    """

    FLAG_SIZE = 1
    FLAG_UIDGID = 2
    FLAG_PERMISSIONS = 4
    FLAG_AMTIME = 8
    FLAG_EXTENDED = x80000000

    def __init__(self):
        """
        Create a new (empty) SFTPAttributes object.  All fields will be empty.
        """
        self._flags = 0
        self.st_size = None
        self.st_uid = None
        self.st_gid = None
        self.st_mode = None
        self.st_atime = None
        self.st_mtime = None
        self.attr = {}

    @classmethod
    def from_stat(cls, obj, filename=None):
        """
        Create an `.SFTPAttributes` object from an existing ``stat`` object (an
        object returned by `os.stat`).

        :param object obj: an object returned by `os.stat` (or equivalent).
        :param str filename: the filename associated with this file.
        :return: new `.SFTPAttributes` object with the same attribute fields.
        """
        attr = cls()
        attr.st_size = obj.st_size
        attr.st_uid = obj.st_uid
        attr.st_gid = obj.st_gid
        attr.st_mode = obj.st_mode
        attr.st_atime = obj.st_atime
        attr.st_mtime = obj.st_mtime
        if filename is not None:
            attr.filename = filename
        return attr

    def __repr__(self):
        return "<SFTPAttributes: {}>".format(self._debug_str())

    # ...internals...
    @classmethod
    def _from_msg(cls, msg, filename=None, longname=None):
        attr = cls()
        attr._unpack(msg)
        if filename is not None:
            attr.filename = filename
        if longname is not None:
            attr.longname = longname
        return attr

    def _unpack(self, msg):
        self._flags = msg.get_int()
        if self._flags & self.FLAG_SIZE:
            self.st_size = msg.get_int64()
        if self._flags & self.FLAG_UIDGID:
            self.st_uid = msg.get_int()
            self.st_gid = msg.get_int()
        if self._flags & self.FLAG_PERMISSIONS:
            self.st_mode = msg.get_int()
        if self._flags & self.FLAG_AMTIME:
            self.st_atime = msg.get_int()
            self.st_mtime = msg.get_int()
        if self._flags & self.FLAG_EXTENDED:
            count = msg.get_int()
            for i in range(count):
                self.attr[msg.get_string()] = msg.get_string()

    def _pack(self, msg):
        self._flags = 0
        if self.st_size is not None:
            self._flags |= self.FLAG_SIZE
        if (self.st_uid is not None) and (self.st_gid is not None):
            self._flags |= self.FLAG_UIDGID
        if self.st_mode is not None:
            self._flags |= self.FLAG_PERMISSIONS
        if (self.st_atime is not None) and (self.st_mtime is not None):
            self._flags |= self.FLAG_AMTIME
        if len(self.attr) > 0:
            self._flags |= self.FLAG_EXTENDED
        msg.add_int(self._flags)
        if self._flags & self.FLAG_SIZE:
            msg.add_int64(self.st_size)
        if self._flags & self.FLAG_UIDGID:
            msg.add_int(self.st_uid)
            msg.add_int(self.st_gid)
        if self._flags & self.FLAG_PERMISSIONS:
            msg.add_int(self.st_mode)
        if self._flags & self.FLAG_AMTIME:
            # throw away any fractional seconds
            msg.add_int(long(self.st_atime))
            msg.add_int(long(self.st_mtime))
        if self._flags & self.FLAG_EXTENDED:
            msg.add_int(len(self.attr))
            for key, val in self.attr.items():
                msg.add_string(key)
                msg.add_string(val)
        return

    def _debug_str(self):
        out = "[ "
        if self.st_size is not None:
            out += "size={} ".format(self.st_size)
        if (self.st_uid is not None) and (self.st_gid is not None):
            out += "uid={} gid={} ".format(self.st_uid, self.st_gid)
        if self.st_mode is not None:
            out += "mode=" + oct(self.st_mode) + " "
        if (self.st_atime is not None) and (self.st_mtime is not None):
            out += "atime={} mtime={} ".format(self.st_atime, self.st_mtime)
        for k, v in self.attr.items():
            out += '"{}"={!r} '.format(str(k), v)
        out += "]"
        return out

    @staticmethod
    def _rwx(n, suid, sticky=False):
        if suid:
            suid = 2
        out = "-r"[n >> 2] + "-w"[(n >> 1) & 1]
        if sticky:
            out += "-xTt"[suid + (n & 1)]
        else:
            out += "-xSs"[suid + (n & 1)]
        return out

    def __str__(self):
        """create a unix-style long description of the file (like ls -l)"""
        if self.st_mode is not None:
            kind = stat.S_IFMT(self.st_mode)
            if kind == stat.S_IFIFO:
                ks = "p"
            elif kind == stat.S_IFCHR:
                ks = "c"
            elif kind == stat.S_IFDIR:
                ks = "d"
            elif kind == stat.S_IFBLK:
                ks = "b"
            elif kind == stat.S_IFREG:
                ks = "-"
            elif kind == stat.S_IFLNK:
                ks = "l"
            elif kind == stat.S_IFSOCK:
                ks = "s"
            else:
                ks = "?"
            ks += self._rwx(
                (self.st_mode & o700) >> 6, self.st_mode & stat.S_ISUID
            )
            ks += self._rwx(
                (self.st_mode & o70) >> 3, self.st_mode & stat.S_ISGID
            )
            ks += self._rwx(
                self.st_mode & 7, self.st_mode & stat.S_ISVTX, True
            )
        else:
            ks = "?---------"
        # compute display date
        if (self.st_mtime is None) or (self.st_mtime == xffffffff):
            # shouldn't really happen
            datestr = "(unknown date)"
        else:
            if abs(time.time() - self.st_mtime) > 15552000:
                # (15552000 = 6 months)
                datestr = time.strftime(
                    "%d %b %Y", time.localtime(self.st_mtime)
                )
            else:
                datestr = time.strftime(
                    "%d %b %H:%M", time.localtime(self.st_mtime)
                )
        filename = getattr(self, "filename", "?")

        # not all servers support uid/gid
        uid = self.st_uid
        gid = self.st_gid
        size = self.st_size
        if uid is None:
            uid = 0
        if gid is None:
            gid = 0
        if size is None:
            size = 0

        # TODO: not sure this actually worked as expected beforehand, leaving
        # it untouched for the time being, re: .format() upgrade, until someone
        # has time to doublecheck
        return "%s   1 %-8d %-8d %8d %-12s %s" % (
            ks,
            uid,
            gid,
            size,
            datestr,
            filename,
        )

    def asbytes(self):
        return b(str(self))
