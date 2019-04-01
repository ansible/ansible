# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of Paramiko.
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


from binascii import hexlify
import errno
import os
import stat
import threading
import time
import weakref
from paramiko import util
from paramiko.channel import Channel
from paramiko.message import Message
from paramiko.common import INFO, DEBUG, o777
from paramiko.py3compat import bytestring, b, u, long
from paramiko.sftp import (
    BaseSFTP,
    CMD_OPENDIR,
    CMD_HANDLE,
    SFTPError,
    CMD_READDIR,
    CMD_NAME,
    CMD_CLOSE,
    SFTP_FLAG_READ,
    SFTP_FLAG_WRITE,
    SFTP_FLAG_CREATE,
    SFTP_FLAG_TRUNC,
    SFTP_FLAG_APPEND,
    SFTP_FLAG_EXCL,
    CMD_OPEN,
    CMD_REMOVE,
    CMD_RENAME,
    CMD_MKDIR,
    CMD_RMDIR,
    CMD_STAT,
    CMD_ATTRS,
    CMD_LSTAT,
    CMD_SYMLINK,
    CMD_SETSTAT,
    CMD_READLINK,
    CMD_REALPATH,
    CMD_STATUS,
    CMD_EXTENDED,
    SFTP_OK,
    SFTP_EOF,
    SFTP_NO_SUCH_FILE,
    SFTP_PERMISSION_DENIED,
)

from paramiko.sftp_attr import SFTPAttributes
from paramiko.ssh_exception import SSHException
from paramiko.sftp_file import SFTPFile
from paramiko.util import ClosingContextManager


def _to_unicode(s):
    """
    decode a string as ascii or utf8 if possible (as required by the sftp
    protocol).  if neither works, just return a byte string because the server
    probably doesn't know the filename's encoding.
    """
    try:
        return s.encode("ascii")
    except (UnicodeError, AttributeError):
        try:
            return s.decode("utf-8")
        except UnicodeError:
            return s


b_slash = b"/"


class SFTPClient(BaseSFTP, ClosingContextManager):
    """
    SFTP client object.

    Used to open an SFTP session across an open SSH `.Transport` and perform
    remote file operations.

    Instances of this class may be used as context managers.
    """

    def __init__(self, sock):
        """
        Create an SFTP client from an existing `.Channel`.  The channel
        should already have requested the ``"sftp"`` subsystem.

        An alternate way to create an SFTP client context is by using
        `from_transport`.

        :param .Channel sock: an open `.Channel` using the ``"sftp"`` subsystem

        :raises:
            `.SSHException` -- if there's an exception while negotiating sftp
        """
        BaseSFTP.__init__(self)
        self.sock = sock
        self.ultra_debug = False
        self.request_number = 1
        # lock for request_number
        self._lock = threading.Lock()
        self._cwd = None
        # request # -> SFTPFile
        self._expecting = weakref.WeakValueDictionary()
        if type(sock) is Channel:
            # override default logger
            transport = self.sock.get_transport()
            self.logger = util.get_logger(
                transport.get_log_channel() + ".sftp"
            )
            self.ultra_debug = transport.get_hexdump()
        try:
            server_version = self._send_version()
        except EOFError:
            raise SSHException("EOF during negotiation")
        self._log(
            INFO,
            "Opened sftp connection (server version {})".format(
                server_version
            ),
        )

    @classmethod
    def from_transport(cls, t, window_size=None, max_packet_size=None):
        """
        Create an SFTP client channel from an open `.Transport`.

        Setting the window and packet sizes might affect the transfer speed.
        The default settings in the `.Transport` class are the same as in
        OpenSSH and should work adequately for both files transfers and
        interactive sessions.

        :param .Transport t: an open `.Transport` which is already
            authenticated
        :param int window_size:
            optional window size for the `.SFTPClient` session.
        :param int max_packet_size:
            optional max packet size for the `.SFTPClient` session..

        :return:
            a new `.SFTPClient` object, referring to an sftp session (channel)
            across the transport

        .. versionchanged:: 1.15
            Added the ``window_size`` and ``max_packet_size`` arguments.
        """
        chan = t.open_session(
            window_size=window_size, max_packet_size=max_packet_size
        )
        if chan is None:
            return None
        chan.invoke_subsystem("sftp")
        return cls(chan)

    def _log(self, level, msg, *args):
        if isinstance(msg, list):
            for m in msg:
                self._log(level, m, *args)
        else:
            # NOTE: these bits MUST continue using %-style format junk because
            # logging.Logger.log() explicitly requires it. Grump.
            # escape '%' in msg (they could come from file or directory names)
            # before logging
            msg = msg.replace("%", "%%")
            super(SFTPClient, self)._log(
                level,
                "[chan %s] " + msg,
                *([self.sock.get_name()] + list(args))
            )

    def close(self):
        """
        Close the SFTP session and its underlying channel.

        .. versionadded:: 1.4
        """
        self._log(INFO, "sftp session closed.")
        self.sock.close()

    def get_channel(self):
        """
        Return the underlying `.Channel` object for this SFTP session.  This
        might be useful for doing things like setting a timeout on the channel.

        .. versionadded:: 1.7.1
        """
        return self.sock

    def listdir(self, path="."):
        """
        Return a list containing the names of the entries in the given
        ``path``.

        The list is in arbitrary order.  It does not include the special
        entries ``'.'`` and ``'..'`` even if they are present in the folder.
        This method is meant to mirror ``os.listdir`` as closely as possible.
        For a list of full `.SFTPAttributes` objects, see `listdir_attr`.

        :param str path: path to list (defaults to ``'.'``)
        """
        return [f.filename for f in self.listdir_attr(path)]

    def listdir_attr(self, path="."):
        """
        Return a list containing `.SFTPAttributes` objects corresponding to
        files in the given ``path``.  The list is in arbitrary order.  It does
        not include the special entries ``'.'`` and ``'..'`` even if they are
        present in the folder.

        The returned `.SFTPAttributes` objects will each have an additional
        field: ``longname``, which may contain a formatted string of the file's
        attributes, in unix format.  The content of this string will probably
        depend on the SFTP server implementation.

        :param str path: path to list (defaults to ``'.'``)
        :return: list of `.SFTPAttributes` objects

        .. versionadded:: 1.2
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "listdir({!r})".format(path))
        t, msg = self._request(CMD_OPENDIR, path)
        if t != CMD_HANDLE:
            raise SFTPError("Expected handle")
        handle = msg.get_binary()
        filelist = []
        while True:
            try:
                t, msg = self._request(CMD_READDIR, handle)
            except EOFError:
                # done with handle
                break
            if t != CMD_NAME:
                raise SFTPError("Expected name response")
            count = msg.get_int()
            for i in range(count):
                filename = msg.get_text()
                longname = msg.get_text()
                attr = SFTPAttributes._from_msg(msg, filename, longname)
                if (filename != ".") and (filename != ".."):
                    filelist.append(attr)
        self._request(CMD_CLOSE, handle)
        return filelist

    def listdir_iter(self, path=".", read_aheads=50):
        """
        Generator version of `.listdir_attr`.

        See the API docs for `.listdir_attr` for overall details.

        This function adds one more kwarg on top of `.listdir_attr`:
        ``read_aheads``, an integer controlling how many
        ``SSH_FXP_READDIR`` requests are made to the server. The default of 50
        should suffice for most file listings as each request/response cycle
        may contain multiple files (dependent on server implementation.)

        .. versionadded:: 1.15
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "listdir({!r})".format(path))
        t, msg = self._request(CMD_OPENDIR, path)

        if t != CMD_HANDLE:
            raise SFTPError("Expected handle")

        handle = msg.get_string()

        nums = list()
        while True:
            try:
                # Send out a bunch of readdir requests so that we can read the
                # responses later on Section 6.7 of the SSH file transfer RFC
                # explains this
                # http://filezilla-project.org/specs/draft-ietf-secsh-filexfer-02.txt
                for i in range(read_aheads):
                    num = self._async_request(type(None), CMD_READDIR, handle)
                    nums.append(num)

                # For each of our sent requests
                # Read and parse the corresponding packets
                # If we're at the end of our queued requests, then fire off
                # some more requests
                # Exit the loop when we've reached the end of the directory
                # handle
                for num in nums:
                    t, pkt_data = self._read_packet()
                    msg = Message(pkt_data)
                    new_num = msg.get_int()
                    if num == new_num:
                        if t == CMD_STATUS:
                            self._convert_status(msg)
                    count = msg.get_int()
                    for i in range(count):
                        filename = msg.get_text()
                        longname = msg.get_text()
                        attr = SFTPAttributes._from_msg(
                            msg, filename, longname
                        )
                        if (filename != ".") and (filename != ".."):
                            yield attr

                # If we've hit the end of our queued requests, reset nums.
                nums = list()

            except EOFError:
                self._request(CMD_CLOSE, handle)
                return

    def open(self, filename, mode="r", bufsize=-1):
        """
        Open a file on the remote server.  The arguments are the same as for
        Python's built-in `python:file` (aka `python:open`).  A file-like
        object is returned, which closely mimics the behavior of a normal
        Python file object, including the ability to be used as a context
        manager.

        The mode indicates how the file is to be opened: ``'r'`` for reading,
        ``'w'`` for writing (truncating an existing file), ``'a'`` for
        appending, ``'r+'`` for reading/writing, ``'w+'`` for reading/writing
        (truncating an existing file), ``'a+'`` for reading/appending.  The
        Python ``'b'`` flag is ignored, since SSH treats all files as binary.
        The ``'U'`` flag is supported in a compatible way.

        Since 1.5.2, an ``'x'`` flag indicates that the operation should only
        succeed if the file was created and did not previously exist.  This has
        no direct mapping to Python's file flags, but is commonly known as the
        ``O_EXCL`` flag in posix.

        The file will be buffered in standard Python style by default, but
        can be altered with the ``bufsize`` parameter.  ``0`` turns off
        buffering, ``1`` uses line buffering, and any number greater than 1
        (``>1``) uses that specific buffer size.

        :param str filename: name of the file to open
        :param str mode: mode (Python-style) to open in
        :param int bufsize: desired buffering (-1 = default buffer size)
        :return: an `.SFTPFile` object representing the open file

        :raises: ``IOError`` -- if the file could not be opened.
        """
        filename = self._adjust_cwd(filename)
        self._log(DEBUG, "open({!r}, {!r})".format(filename, mode))
        imode = 0
        if ("r" in mode) or ("+" in mode):
            imode |= SFTP_FLAG_READ
        if ("w" in mode) or ("+" in mode) or ("a" in mode):
            imode |= SFTP_FLAG_WRITE
        if "w" in mode:
            imode |= SFTP_FLAG_CREATE | SFTP_FLAG_TRUNC
        if "a" in mode:
            imode |= SFTP_FLAG_CREATE | SFTP_FLAG_APPEND
        if "x" in mode:
            imode |= SFTP_FLAG_CREATE | SFTP_FLAG_EXCL
        attrblock = SFTPAttributes()
        t, msg = self._request(CMD_OPEN, filename, imode, attrblock)
        if t != CMD_HANDLE:
            raise SFTPError("Expected handle")
        handle = msg.get_binary()
        self._log(
            DEBUG,
            "open({!r}, {!r}) -> {}".format(
                filename, mode, u(hexlify(handle))
            ),
        )
        return SFTPFile(self, handle, mode, bufsize)

    # Python continues to vacillate about "open" vs "file"...
    file = open

    def remove(self, path):
        """
        Remove the file at the given path.  This only works on files; for
        removing folders (directories), use `rmdir`.

        :param str path: path (absolute or relative) of the file to remove

        :raises: ``IOError`` -- if the path refers to a folder (directory)
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "remove({!r})".format(path))
        self._request(CMD_REMOVE, path)

    unlink = remove

    def rename(self, oldpath, newpath):
        """
        Rename a file or folder from ``oldpath`` to ``newpath``.

        .. note::
            This method implements 'standard' SFTP ``RENAME`` behavior; those
            seeking the OpenSSH "POSIX rename" extension behavior should use
            `posix_rename`.

        :param str oldpath:
            existing name of the file or folder
        :param str newpath:
            new name for the file or folder, must not exist already

        :raises:
            ``IOError`` -- if ``newpath`` is a folder, or something else goes
            wrong
        """
        oldpath = self._adjust_cwd(oldpath)
        newpath = self._adjust_cwd(newpath)
        self._log(DEBUG, "rename({!r}, {!r})".format(oldpath, newpath))
        self._request(CMD_RENAME, oldpath, newpath)

    def posix_rename(self, oldpath, newpath):
        """
        Rename a file or folder from ``oldpath`` to ``newpath``, following
        posix conventions.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder, will be
            overwritten if it already exists

        :raises:
            ``IOError`` -- if ``newpath`` is a folder, posix-rename is not
            supported by the server or something else goes wrong

        :versionadded: 2.2
        """
        oldpath = self._adjust_cwd(oldpath)
        newpath = self._adjust_cwd(newpath)
        self._log(DEBUG, "posix_rename({!r}, {!r})".format(oldpath, newpath))
        self._request(
            CMD_EXTENDED, "posix-rename@openssh.com", oldpath, newpath
        )

    def mkdir(self, path, mode=o777):
        """
        Create a folder (directory) named ``path`` with numeric mode ``mode``.
        The default mode is 0777 (octal).  On some systems, mode is ignored.
        Where it is used, the current umask value is first masked out.

        :param str path: name of the folder to create
        :param int mode: permissions (posix-style) for the newly-created folder
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "mkdir({!r}, {!r})".format(path, mode))
        attr = SFTPAttributes()
        attr.st_mode = mode
        self._request(CMD_MKDIR, path, attr)

    def rmdir(self, path):
        """
        Remove the folder named ``path``.

        :param str path: name of the folder to remove
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "rmdir({!r})".format(path))
        self._request(CMD_RMDIR, path)

    def stat(self, path):
        """
        Retrieve information about a file on the remote system.  The return
        value is an object whose attributes correspond to the attributes of
        Python's ``stat`` structure as returned by ``os.stat``, except that it
        contains fewer fields.  An SFTP server may return as much or as little
        info as it wants, so the results may vary from server to server.

        Unlike a Python `python:stat` object, the result may not be accessed as
        a tuple.  This is mostly due to the author's slack factor.

        The fields supported are: ``st_mode``, ``st_size``, ``st_uid``,
        ``st_gid``, ``st_atime``, and ``st_mtime``.

        :param str path: the filename to stat
        :return:
            an `.SFTPAttributes` object containing attributes about the given
            file
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "stat({!r})".format(path))
        t, msg = self._request(CMD_STAT, path)
        if t != CMD_ATTRS:
            raise SFTPError("Expected attributes")
        return SFTPAttributes._from_msg(msg)

    def lstat(self, path):
        """
        Retrieve information about a file on the remote system, without
        following symbolic links (shortcuts).  This otherwise behaves exactly
        the same as `stat`.

        :param str path: the filename to stat
        :return:
            an `.SFTPAttributes` object containing attributes about the given
            file
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "lstat({!r})".format(path))
        t, msg = self._request(CMD_LSTAT, path)
        if t != CMD_ATTRS:
            raise SFTPError("Expected attributes")
        return SFTPAttributes._from_msg(msg)

    def symlink(self, source, dest):
        """
        Create a symbolic link to the ``source`` path at ``destination``.

        :param str source: path of the original file
        :param str dest: path of the newly created symlink
        """
        dest = self._adjust_cwd(dest)
        self._log(DEBUG, "symlink({!r}, {!r})".format(source, dest))
        source = bytestring(source)
        self._request(CMD_SYMLINK, source, dest)

    def chmod(self, path, mode):
        """
        Change the mode (permissions) of a file.  The permissions are
        unix-style and identical to those used by Python's `os.chmod`
        function.

        :param str path: path of the file to change the permissions of
        :param int mode: new permissions
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "chmod({!r}, {!r})".format(path, mode))
        attr = SFTPAttributes()
        attr.st_mode = mode
        self._request(CMD_SETSTAT, path, attr)

    def chown(self, path, uid, gid):
        """
        Change the owner (``uid``) and group (``gid``) of a file.  As with
        Python's `os.chown` function, you must pass both arguments, so if you
        only want to change one, use `stat` first to retrieve the current
        owner and group.

        :param str path: path of the file to change the owner and group of
        :param int uid: new owner's uid
        :param int gid: new group id
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "chown({!r}, {!r}, {!r})".format(path, uid, gid))
        attr = SFTPAttributes()
        attr.st_uid, attr.st_gid = uid, gid
        self._request(CMD_SETSTAT, path, attr)

    def utime(self, path, times):
        """
        Set the access and modified times of the file specified by ``path``.
        If ``times`` is ``None``, then the file's access and modified times
        are set to the current time.  Otherwise, ``times`` must be a 2-tuple
        of numbers, of the form ``(atime, mtime)``, which is used to set the
        access and modified times, respectively.  This bizarre API is mimicked
        from Python for the sake of consistency -- I apologize.

        :param str path: path of the file to modify
        :param tuple times:
            ``None`` or a tuple of (access time, modified time) in standard
            internet epoch time (seconds since 01 January 1970 GMT)
        """
        path = self._adjust_cwd(path)
        if times is None:
            times = (time.time(), time.time())
        self._log(DEBUG, "utime({!r}, {!r})".format(path, times))
        attr = SFTPAttributes()
        attr.st_atime, attr.st_mtime = times
        self._request(CMD_SETSTAT, path, attr)

    def truncate(self, path, size):
        """
        Change the size of the file specified by ``path``.  This usually
        extends or shrinks the size of the file, just like the `~file.truncate`
        method on Python file objects.

        :param str path: path of the file to modify
        :param int size: the new size of the file
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "truncate({!r}, {!r})".format(path, size))
        attr = SFTPAttributes()
        attr.st_size = size
        self._request(CMD_SETSTAT, path, attr)

    def readlink(self, path):
        """
        Return the target of a symbolic link (shortcut).  You can use
        `symlink` to create these.  The result may be either an absolute or
        relative pathname.

        :param str path: path of the symbolic link file
        :return: target path, as a `str`
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "readlink({!r})".format(path))
        t, msg = self._request(CMD_READLINK, path)
        if t != CMD_NAME:
            raise SFTPError("Expected name response")
        count = msg.get_int()
        if count == 0:
            return None
        if count != 1:
            raise SFTPError("Readlink returned {} results".format(count))
        return _to_unicode(msg.get_string())

    def normalize(self, path):
        """
        Return the normalized path (on the server) of a given path.  This
        can be used to quickly resolve symbolic links or determine what the
        server is considering to be the "current folder" (by passing ``'.'``
        as ``path``).

        :param str path: path to be normalized
        :return: normalized form of the given path (as a `str`)

        :raises: ``IOError`` -- if the path can't be resolved on the server
        """
        path = self._adjust_cwd(path)
        self._log(DEBUG, "normalize({!r})".format(path))
        t, msg = self._request(CMD_REALPATH, path)
        if t != CMD_NAME:
            raise SFTPError("Expected name response")
        count = msg.get_int()
        if count != 1:
            raise SFTPError("Realpath returned {} results".format(count))
        return msg.get_text()

    def chdir(self, path=None):
        """
        Change the "current directory" of this SFTP session.  Since SFTP
        doesn't really have the concept of a current working directory, this is
        emulated by Paramiko.  Once you use this method to set a working
        directory, all operations on this `.SFTPClient` object will be relative
        to that path. You can pass in ``None`` to stop using a current working
        directory.

        :param str path: new current working directory

        :raises:
            ``IOError`` -- if the requested path doesn't exist on the server

        .. versionadded:: 1.4
        """
        if path is None:
            self._cwd = None
            return
        if not stat.S_ISDIR(self.stat(path).st_mode):
            code = errno.ENOTDIR
            raise SFTPError(code, "{}: {}".format(os.strerror(code), path))
        self._cwd = b(self.normalize(path))

    def getcwd(self):
        """
        Return the "current working directory" for this SFTP session, as
        emulated by Paramiko.  If no directory has been set with `chdir`,
        this method will return ``None``.

        .. versionadded:: 1.4
        """
        # TODO: make class initialize with self._cwd set to self.normalize('.')
        return self._cwd and u(self._cwd)

    def _transfer_with_callback(self, reader, writer, file_size, callback):
        size = 0
        while True:
            data = reader.read(32768)
            writer.write(data)
            size += len(data)
            if len(data) == 0:
                break
            if callback is not None:
                callback(size, file_size)
        return size

    def putfo(self, fl, remotepath, file_size=0, callback=None, confirm=True):
        """
        Copy the contents of an open file object (``fl``) to the SFTP server as
        ``remotepath``. Any exception raised by operations will be passed
        through.

        The SFTP operations use pipelining for speed.

        :param fl: opened file or file-like object to copy
        :param str remotepath: the destination path on the SFTP server
        :param int file_size:
            optional size parameter passed to callback. If none is specified,
            size defaults to 0
        :param callable callback:
            optional callback function (form: ``func(int, int)``) that accepts
            the bytes transferred so far and the total bytes to be transferred
            (since 1.7.4)
        :param bool confirm:
            whether to do a stat() on the file afterwards to confirm the file
            size (since 1.7.7)

        :return:
            an `.SFTPAttributes` object containing attributes about the given
            file.

        .. versionadded:: 1.10
        """
        with self.file(remotepath, "wb") as fr:
            fr.set_pipelined(True)
            size = self._transfer_with_callback(
                reader=fl, writer=fr, file_size=file_size, callback=callback
            )
        if confirm:
            s = self.stat(remotepath)
            if s.st_size != size:
                raise IOError(
                    "size mismatch in put!  {} != {}".format(s.st_size, size)
                )
        else:
            s = SFTPAttributes()
        return s

    def put(self, localpath, remotepath, callback=None, confirm=True):
        """
        Copy a local file (``localpath``) to the SFTP server as ``remotepath``.
        Any exception raised by operations will be passed through.  This
        method is primarily provided as a convenience.

        The SFTP operations use pipelining for speed.

        :param str localpath: the local file to copy
        :param str remotepath: the destination path on the SFTP server. Note
            that the filename should be included. Only specifying a directory
            may result in an error.
        :param callable callback:
            optional callback function (form: ``func(int, int)``) that accepts
            the bytes transferred so far and the total bytes to be transferred
        :param bool confirm:
            whether to do a stat() on the file afterwards to confirm the file
            size

        :return: an `.SFTPAttributes` object containing attributes about the
            given file

        .. versionadded:: 1.4
        .. versionchanged:: 1.7.4
            ``callback`` and rich attribute return value added.
        .. versionchanged:: 1.7.7
            ``confirm`` param added.
        """
        file_size = os.stat(localpath).st_size
        with open(localpath, "rb") as fl:
            return self.putfo(fl, remotepath, file_size, callback, confirm)

    def getfo(self, remotepath, fl, callback=None):
        """
        Copy a remote file (``remotepath``) from the SFTP server and write to
        an open file or file-like object, ``fl``.  Any exception raised by
        operations will be passed through.  This method is primarily provided
        as a convenience.

        :param object remotepath: opened file or file-like object to copy to
        :param str fl:
            the destination path on the local host or open file object
        :param callable callback:
            optional callback function (form: ``func(int, int)``) that accepts
            the bytes transferred so far and the total bytes to be transferred
        :return: the `number <int>` of bytes written to the opened file object

        .. versionadded:: 1.10
        """
        file_size = self.stat(remotepath).st_size
        with self.open(remotepath, "rb") as fr:
            fr.prefetch(file_size)
            return self._transfer_with_callback(
                reader=fr, writer=fl, file_size=file_size, callback=callback
            )

    def get(self, remotepath, localpath, callback=None):
        """
        Copy a remote file (``remotepath``) from the SFTP server to the local
        host as ``localpath``.  Any exception raised by operations will be
        passed through.  This method is primarily provided as a convenience.

        :param str remotepath: the remote file to copy
        :param str localpath: the destination path on the local host
        :param callable callback:
            optional callback function (form: ``func(int, int)``) that accepts
            the bytes transferred so far and the total bytes to be transferred

        .. versionadded:: 1.4
        .. versionchanged:: 1.7.4
            Added the ``callback`` param
        """
        with open(localpath, "wb") as fl:
            size = self.getfo(remotepath, fl, callback)
        s = os.stat(localpath)
        if s.st_size != size:
            raise IOError(
                "size mismatch in get!  {} != {}".format(s.st_size, size)
            )

    # ...internals...

    def _request(self, t, *arg):
        num = self._async_request(type(None), t, *arg)
        return self._read_response(num)

    def _async_request(self, fileobj, t, *arg):
        # this method may be called from other threads (prefetch)
        self._lock.acquire()
        try:
            msg = Message()
            msg.add_int(self.request_number)
            for item in arg:
                if isinstance(item, long):
                    msg.add_int64(item)
                elif isinstance(item, int):
                    msg.add_int(item)
                elif isinstance(item, SFTPAttributes):
                    item._pack(msg)
                else:
                    # For all other types, rely on as_string() to either coerce
                    # to bytes before writing or raise a suitable exception.
                    msg.add_string(item)
            num = self.request_number
            self._expecting[num] = fileobj
            self.request_number += 1
        finally:
            self._lock.release()
        self._send_packet(t, msg)
        return num

    def _read_response(self, waitfor=None):
        while True:
            try:
                t, data = self._read_packet()
            except EOFError as e:
                raise SSHException("Server connection dropped: {}".format(e))
            msg = Message(data)
            num = msg.get_int()
            self._lock.acquire()
            try:
                if num not in self._expecting:
                    # might be response for a file that was closed before
                    # responses came back
                    self._log(DEBUG, "Unexpected response #{}".format(num))
                    if waitfor is None:
                        # just doing a single check
                        break
                    continue
                fileobj = self._expecting[num]
                del self._expecting[num]
            finally:
                self._lock.release()
            if num == waitfor:
                # synchronous
                if t == CMD_STATUS:
                    self._convert_status(msg)
                return t, msg

            # can not rewrite this to deal with E721, either as a None check
            # nor as not an instance of None or NoneType
            if fileobj is not type(None):  # noqa
                fileobj._async_response(t, msg, num)
            if waitfor is None:
                # just doing a single check
                break
        return None, None

    def _finish_responses(self, fileobj):
        while fileobj in self._expecting.values():
            self._read_response()
            fileobj._check_exception()

    def _convert_status(self, msg):
        """
        Raises EOFError or IOError on error status; otherwise does nothing.
        """
        code = msg.get_int()
        text = msg.get_text()
        if code == SFTP_OK:
            return
        elif code == SFTP_EOF:
            raise EOFError(text)
        elif code == SFTP_NO_SUCH_FILE:
            # clever idea from john a. meinel: map the error codes to errno
            raise IOError(errno.ENOENT, text)
        elif code == SFTP_PERMISSION_DENIED:
            raise IOError(errno.EACCES, text)
        else:
            raise IOError(text)

    def _adjust_cwd(self, path):
        """
        Return an adjusted path if we're emulating a "current working
        directory" for the server.
        """
        path = b(path)
        if self._cwd is None:
            return path
        if len(path) and path[0:1] == b_slash:
            # absolute path
            return path
        if self._cwd == b_slash:
            return self._cwd + path
        return self._cwd + b_slash + path


class SFTP(SFTPClient):
    """
    An alias for `.SFTPClient` for backwards compatibility.
    """

    pass
