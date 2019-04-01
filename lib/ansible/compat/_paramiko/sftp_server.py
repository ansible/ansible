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
Server-mode SFTP support.
"""

import os
import errno
import sys
from hashlib import md5, sha1

from paramiko import util
from paramiko.sftp import (
    BaseSFTP,
    Message,
    SFTP_FAILURE,
    SFTP_PERMISSION_DENIED,
    SFTP_NO_SUCH_FILE,
)
from paramiko.sftp_si import SFTPServerInterface
from paramiko.sftp_attr import SFTPAttributes
from paramiko.common import DEBUG
from paramiko.py3compat import long, string_types, bytes_types, b
from paramiko.server import SubsystemHandler


# known hash algorithms for the "check-file" extension
from paramiko.sftp import (
    CMD_HANDLE,
    SFTP_DESC,
    CMD_STATUS,
    SFTP_EOF,
    CMD_NAME,
    SFTP_BAD_MESSAGE,
    CMD_EXTENDED_REPLY,
    SFTP_FLAG_READ,
    SFTP_FLAG_WRITE,
    SFTP_FLAG_APPEND,
    SFTP_FLAG_CREATE,
    SFTP_FLAG_TRUNC,
    SFTP_FLAG_EXCL,
    CMD_NAMES,
    CMD_OPEN,
    CMD_CLOSE,
    SFTP_OK,
    CMD_READ,
    CMD_DATA,
    CMD_WRITE,
    CMD_REMOVE,
    CMD_RENAME,
    CMD_MKDIR,
    CMD_RMDIR,
    CMD_OPENDIR,
    CMD_READDIR,
    CMD_STAT,
    CMD_ATTRS,
    CMD_LSTAT,
    CMD_FSTAT,
    CMD_SETSTAT,
    CMD_FSETSTAT,
    CMD_READLINK,
    CMD_SYMLINK,
    CMD_REALPATH,
    CMD_EXTENDED,
    SFTP_OP_UNSUPPORTED,
)

_hash_class = {"sha1": sha1, "md5": md5}


class SFTPServer(BaseSFTP, SubsystemHandler):
    """
    Server-side SFTP subsystem support.  Since this is a `.SubsystemHandler`,
    it can be (and is meant to be) set as the handler for ``"sftp"`` requests.
    Use `.Transport.set_subsystem_handler` to activate this class.
    """

    def __init__(
        self,
        channel,
        name,
        server,
        sftp_si=SFTPServerInterface,
        *largs,
        **kwargs
    ):
        """
        The constructor for SFTPServer is meant to be called from within the
        `.Transport` as a subsystem handler.  ``server`` and any additional
        parameters or keyword parameters are passed from the original call to
        `.Transport.set_subsystem_handler`.

        :param .Channel channel: channel passed from the `.Transport`.
        :param str name: name of the requested subsystem.
        :param .ServerInterface server:
            the server object associated with this channel and subsystem
        :param sftp_si:
            a subclass of `.SFTPServerInterface` to use for handling individual
            requests.
        """
        BaseSFTP.__init__(self)
        SubsystemHandler.__init__(self, channel, name, server)
        transport = channel.get_transport()
        self.logger = util.get_logger(transport.get_log_channel() + ".sftp")
        self.ultra_debug = transport.get_hexdump()
        self.next_handle = 1
        # map of handle-string to SFTPHandle for files & folders:
        self.file_table = {}
        self.folder_table = {}
        self.server = sftp_si(server, *largs, **kwargs)

    def _log(self, level, msg):
        if issubclass(type(msg), list):
            for m in msg:
                super(SFTPServer, self)._log(
                    level, "[chan " + self.sock.get_name() + "] " + m
                )
        else:
            super(SFTPServer, self)._log(
                level, "[chan " + self.sock.get_name() + "] " + msg
            )

    def start_subsystem(self, name, transport, channel):
        self.sock = channel
        self._log(DEBUG, "Started sftp server on channel {!r}".format(channel))
        self._send_server_version()
        self.server.session_started()
        while True:
            try:
                t, data = self._read_packet()
            except EOFError:
                self._log(DEBUG, "EOF -- end of session")
                return
            except Exception as e:
                self._log(DEBUG, "Exception on channel: " + str(e))
                self._log(DEBUG, util.tb_strings())
                return
            msg = Message(data)
            request_number = msg.get_int()
            try:
                self._process(t, request_number, msg)
            except Exception as e:
                self._log(DEBUG, "Exception in server processing: " + str(e))
                self._log(DEBUG, util.tb_strings())
                # send some kind of failure message, at least
                try:
                    self._send_status(request_number, SFTP_FAILURE)
                except:
                    pass

    def finish_subsystem(self):
        self.server.session_ended()
        super(SFTPServer, self).finish_subsystem()
        # close any file handles that were left open
        # (so we can return them to the OS quickly)
        for f in self.file_table.values():
            f.close()
        for f in self.folder_table.values():
            f.close()
        self.file_table = {}
        self.folder_table = {}

    @staticmethod
    def convert_errno(e):
        """
        Convert an errno value (as from an ``OSError`` or ``IOError``) into a
        standard SFTP result code.  This is a convenience function for trapping
        exceptions in server code and returning an appropriate result.

        :param int e: an errno code, as from ``OSError.errno``.
        :return: an `int` SFTP error code like ``SFTP_NO_SUCH_FILE``.
        """
        if e == errno.EACCES:
            # permission denied
            return SFTP_PERMISSION_DENIED
        elif (e == errno.ENOENT) or (e == errno.ENOTDIR):
            # no such file
            return SFTP_NO_SUCH_FILE
        else:
            return SFTP_FAILURE

    @staticmethod
    def set_file_attr(filename, attr):
        """
        Change a file's attributes on the local filesystem.  The contents of
        ``attr`` are used to change the permissions, owner, group ownership,
        and/or modification & access time of the file, depending on which
        attributes are present in ``attr``.

        This is meant to be a handy helper function for translating SFTP file
        requests into local file operations.

        :param str filename:
            name of the file to alter (should usually be an absolute path).
        :param .SFTPAttributes attr: attributes to change.
        """
        if sys.platform != "win32":
            # mode operations are meaningless on win32
            if attr._flags & attr.FLAG_PERMISSIONS:
                os.chmod(filename, attr.st_mode)
            if attr._flags & attr.FLAG_UIDGID:
                os.chown(filename, attr.st_uid, attr.st_gid)
        if attr._flags & attr.FLAG_AMTIME:
            os.utime(filename, (attr.st_atime, attr.st_mtime))
        if attr._flags & attr.FLAG_SIZE:
            with open(filename, "w+") as f:
                f.truncate(attr.st_size)

    # ...internals...

    def _response(self, request_number, t, *arg):
        msg = Message()
        msg.add_int(request_number)
        for item in arg:
            if isinstance(item, long):
                msg.add_int64(item)
            elif isinstance(item, int):
                msg.add_int(item)
            elif isinstance(item, (string_types, bytes_types)):
                msg.add_string(item)
            elif type(item) is SFTPAttributes:
                item._pack(msg)
            else:
                raise Exception(
                    "unknown type for {!r} type {!r}".format(item, type(item))
                )
        self._send_packet(t, msg)

    def _send_handle_response(self, request_number, handle, folder=False):
        if not issubclass(type(handle), SFTPHandle):
            # must be error code
            self._send_status(request_number, handle)
            return
        handle._set_name(b("hx{:d}".format(self.next_handle)))
        self.next_handle += 1
        if folder:
            self.folder_table[handle._get_name()] = handle
        else:
            self.file_table[handle._get_name()] = handle
        self._response(request_number, CMD_HANDLE, handle._get_name())

    def _send_status(self, request_number, code, desc=None):
        if desc is None:
            try:
                desc = SFTP_DESC[code]
            except IndexError:
                desc = "Unknown"
        # some clients expect a "langauge" tag at the end
        # (but don't mind it being blank)
        self._response(request_number, CMD_STATUS, code, desc, "")

    def _open_folder(self, request_number, path):
        resp = self.server.list_folder(path)
        if issubclass(type(resp), list):
            # got an actual list of filenames in the folder
            folder = SFTPHandle()
            folder._set_files(resp)
            self._send_handle_response(request_number, folder, True)
            return
        # must be an error code
        self._send_status(request_number, resp)

    def _read_folder(self, request_number, folder):
        flist = folder._get_next_files()
        if len(flist) == 0:
            self._send_status(request_number, SFTP_EOF)
            return
        msg = Message()
        msg.add_int(request_number)
        msg.add_int(len(flist))
        for attr in flist:
            msg.add_string(attr.filename)
            msg.add_string(attr)
            attr._pack(msg)
        self._send_packet(CMD_NAME, msg)

    def _check_file(self, request_number, msg):
        # this extension actually comes from v6 protocol, but since it's an
        # extension, i feel like we can reasonably support it backported.
        # it's very useful for verifying uploaded files or checking for
        # rsync-like differences between local and remote files.
        handle = msg.get_binary()
        alg_list = msg.get_list()
        start = msg.get_int64()
        length = msg.get_int64()
        block_size = msg.get_int()
        if handle not in self.file_table:
            self._send_status(
                request_number, SFTP_BAD_MESSAGE, "Invalid handle"
            )
            return
        f = self.file_table[handle]
        for x in alg_list:
            if x in _hash_class:
                algname = x
                alg = _hash_class[x]
                break
        else:
            self._send_status(
                request_number, SFTP_FAILURE, "No supported hash types found"
            )
            return
        if length == 0:
            st = f.stat()
            if not issubclass(type(st), SFTPAttributes):
                self._send_status(request_number, st, "Unable to stat file")
                return
            length = st.st_size - start
        if block_size == 0:
            block_size = length
        if block_size < 256:
            self._send_status(
                request_number, SFTP_FAILURE, "Block size too small"
            )
            return

        sum_out = bytes()
        offset = start
        while offset < start + length:
            blocklen = min(block_size, start + length - offset)
            # don't try to read more than about 64KB at a time
            chunklen = min(blocklen, 65536)
            count = 0
            hash_obj = alg()
            while count < blocklen:
                data = f.read(offset, chunklen)
                if not isinstance(data, bytes_types):
                    self._send_status(
                        request_number, data, "Unable to hash file"
                    )
                    return
                hash_obj.update(data)
                count += len(data)
                offset += count
            sum_out += hash_obj.digest()

        msg = Message()
        msg.add_int(request_number)
        msg.add_string("check-file")
        msg.add_string(algname)
        msg.add_bytes(sum_out)
        self._send_packet(CMD_EXTENDED_REPLY, msg)

    def _convert_pflags(self, pflags):
        """convert SFTP-style open() flags to Python's os.open() flags"""
        if (pflags & SFTP_FLAG_READ) and (pflags & SFTP_FLAG_WRITE):
            flags = os.O_RDWR
        elif pflags & SFTP_FLAG_WRITE:
            flags = os.O_WRONLY
        else:
            flags = os.O_RDONLY
        if pflags & SFTP_FLAG_APPEND:
            flags |= os.O_APPEND
        if pflags & SFTP_FLAG_CREATE:
            flags |= os.O_CREAT
        if pflags & SFTP_FLAG_TRUNC:
            flags |= os.O_TRUNC
        if pflags & SFTP_FLAG_EXCL:
            flags |= os.O_EXCL
        return flags

    def _process(self, t, request_number, msg):
        self._log(DEBUG, "Request: {}".format(CMD_NAMES[t]))
        if t == CMD_OPEN:
            path = msg.get_text()
            flags = self._convert_pflags(msg.get_int())
            attr = SFTPAttributes._from_msg(msg)
            self._send_handle_response(
                request_number, self.server.open(path, flags, attr)
            )
        elif t == CMD_CLOSE:
            handle = msg.get_binary()
            if handle in self.folder_table:
                del self.folder_table[handle]
                self._send_status(request_number, SFTP_OK)
                return
            if handle in self.file_table:
                self.file_table[handle].close()
                del self.file_table[handle]
                self._send_status(request_number, SFTP_OK)
                return
            self._send_status(
                request_number, SFTP_BAD_MESSAGE, "Invalid handle"
            )
        elif t == CMD_READ:
            handle = msg.get_binary()
            offset = msg.get_int64()
            length = msg.get_int()
            if handle not in self.file_table:
                self._send_status(
                    request_number, SFTP_BAD_MESSAGE, "Invalid handle"
                )
                return
            data = self.file_table[handle].read(offset, length)
            if isinstance(data, (bytes_types, string_types)):
                if len(data) == 0:
                    self._send_status(request_number, SFTP_EOF)
                else:
                    self._response(request_number, CMD_DATA, data)
            else:
                self._send_status(request_number, data)
        elif t == CMD_WRITE:
            handle = msg.get_binary()
            offset = msg.get_int64()
            data = msg.get_binary()
            if handle not in self.file_table:
                self._send_status(
                    request_number, SFTP_BAD_MESSAGE, "Invalid handle"
                )
                return
            self._send_status(
                request_number, self.file_table[handle].write(offset, data)
            )
        elif t == CMD_REMOVE:
            path = msg.get_text()
            self._send_status(request_number, self.server.remove(path))
        elif t == CMD_RENAME:
            oldpath = msg.get_text()
            newpath = msg.get_text()
            self._send_status(
                request_number, self.server.rename(oldpath, newpath)
            )
        elif t == CMD_MKDIR:
            path = msg.get_text()
            attr = SFTPAttributes._from_msg(msg)
            self._send_status(request_number, self.server.mkdir(path, attr))
        elif t == CMD_RMDIR:
            path = msg.get_text()
            self._send_status(request_number, self.server.rmdir(path))
        elif t == CMD_OPENDIR:
            path = msg.get_text()
            self._open_folder(request_number, path)
            return
        elif t == CMD_READDIR:
            handle = msg.get_binary()
            if handle not in self.folder_table:
                self._send_status(
                    request_number, SFTP_BAD_MESSAGE, "Invalid handle"
                )
                return
            folder = self.folder_table[handle]
            self._read_folder(request_number, folder)
        elif t == CMD_STAT:
            path = msg.get_text()
            resp = self.server.stat(path)
            if issubclass(type(resp), SFTPAttributes):
                self._response(request_number, CMD_ATTRS, resp)
            else:
                self._send_status(request_number, resp)
        elif t == CMD_LSTAT:
            path = msg.get_text()
            resp = self.server.lstat(path)
            if issubclass(type(resp), SFTPAttributes):
                self._response(request_number, CMD_ATTRS, resp)
            else:
                self._send_status(request_number, resp)
        elif t == CMD_FSTAT:
            handle = msg.get_binary()
            if handle not in self.file_table:
                self._send_status(
                    request_number, SFTP_BAD_MESSAGE, "Invalid handle"
                )
                return
            resp = self.file_table[handle].stat()
            if issubclass(type(resp), SFTPAttributes):
                self._response(request_number, CMD_ATTRS, resp)
            else:
                self._send_status(request_number, resp)
        elif t == CMD_SETSTAT:
            path = msg.get_text()
            attr = SFTPAttributes._from_msg(msg)
            self._send_status(request_number, self.server.chattr(path, attr))
        elif t == CMD_FSETSTAT:
            handle = msg.get_binary()
            attr = SFTPAttributes._from_msg(msg)
            if handle not in self.file_table:
                self._response(
                    request_number, SFTP_BAD_MESSAGE, "Invalid handle"
                )
                return
            self._send_status(
                request_number, self.file_table[handle].chattr(attr)
            )
        elif t == CMD_READLINK:
            path = msg.get_text()
            resp = self.server.readlink(path)
            if isinstance(resp, (bytes_types, string_types)):
                self._response(
                    request_number, CMD_NAME, 1, resp, "", SFTPAttributes()
                )
            else:
                self._send_status(request_number, resp)
        elif t == CMD_SYMLINK:
            # the sftp 2 draft is incorrect here!
            # path always follows target_path
            target_path = msg.get_text()
            path = msg.get_text()
            self._send_status(
                request_number, self.server.symlink(target_path, path)
            )
        elif t == CMD_REALPATH:
            path = msg.get_text()
            rpath = self.server.canonicalize(path)
            self._response(
                request_number, CMD_NAME, 1, rpath, "", SFTPAttributes()
            )
        elif t == CMD_EXTENDED:
            tag = msg.get_text()
            if tag == "check-file":
                self._check_file(request_number, msg)
            elif tag == "posix-rename@openssh.com":
                oldpath = msg.get_text()
                newpath = msg.get_text()
                self._send_status(
                    request_number, self.server.posix_rename(oldpath, newpath)
                )
            else:
                self._send_status(request_number, SFTP_OP_UNSUPPORTED)
        else:
            self._send_status(request_number, SFTP_OP_UNSUPPORTED)


from paramiko.sftp_handle import SFTPHandle
