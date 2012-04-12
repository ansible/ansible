# scp.py
# Copyright (C) 2008 James Bardin <jbardin@bu.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


"""
Utilities for sending files over ssh using the scp1 protocol.
"""

import os
from socket import timeout as SocketTimeout

class SCPClient(object):
    """
    An scp1 implementation, compatible with openssh scp.
    Raises SCPException for all transport related errors. Local filesystem
    and OS errors pass through. 

    Main public methods are .put and .get 
    The get method is controlled by the remote scp instance, and behaves 
    accordingly. This means that symlinks are resolved, and the transfer is
    halted after too many levels of symlinks are detected.
    The put method uses os.walk for recursion, and sends files accordingly.
    Since scp doesn't support symlinks, we send file symlinks as the file
    (matching scp behaviour), but we make no attempt at symlinked directories.

    Convenience methods:
        put_r:  put with recursion
        put_p:  put preserving times
        put_rp: put with recursion, preserving times
        get_r:  get with recursion
        get_p:  get preserving times
        get_rp: get with recursion, preserving times
    """
    def __init__(self, transport, buff_size = 16384, socket_timeout = 5.0,
                 callback = None):
        """
        Create an scp1 client.

        @param transport: an existing paramiko L{Transport}
        @type transport: L{Transport}
        @param buff_size: size of the scp send buffer.
        @type buff_size: int
        @param socket_timeout: channel socket timeout in seconds
        @type socket_timeout: float
        @param callback: callback function for transfer status
        @type callback: func
        """
        self.transport = transport
        self.buff_size = buff_size
        self.socket_timeout = socket_timeout
        self.channel = None
        self.preserve_times = False
        self.callback = callback
        self._recv_dir = ''
        self._utime = None
        self._dirtimes = {}

    def put(self, files, remote_path = '.', 
            recursive = False, preserve_times = False):
        """
        Transfer files to remote host.

        @param files: A single path, or a list of paths to be transfered.
            recursive must be True to transfer directories.
        @type files: string OR list of strings
        @param remote_path: path in which to receive the files on the remote
            host. defaults to '.'
        @type remote_path: str
        @param recursive: transfer files and directories recursively
        @type recursive: bool
        @param preserve_times: preserve mtime and atime of transfered files
            and directories.
        @type preserve_times: bool
        """
        self.preserve_times = preserve_times
        self.channel = self.transport.open_session()
        self.channel.settimeout(self.socket_timeout)
        scp_command = ('scp -t %s\n', 'scp -r -t %s\n')[recursive]
        self.channel.exec_command(scp_command % remote_path)
        self._recv_confirm()
       
        if not isinstance(files, (list, tuple)):
            files = [files]
        
        if recursive:
            self._send_recursive(files)
        else:
            self._send_files(files)
        
        if self.channel:
            self.channel.close()
    
    def put_r(self, files, remote_path = '.'):
        """
        Convenience function for a recursive put

        @param files: A single path, or a list of paths to be transfered.
        @type files: str, list
        @param remote_path: path in which to receive the files on the remote
            host. defaults to '.'
        @type remote_path: bool
        """
        self.put(files, remote_path, recursive = True)

    def put_p(self, files, remote_path = '.'):
        """
        Convenience function to put preserving times.

        @param files: A single path, or a list of paths to be transfered.
        @type files: str, list
        @param remote_path: path in which to receive the files on the remote
            host. defaults to '.'
        @type remote_path: bool
        """
        self.put(files, remote_path, preserve_times = True)
   
    def put_rp(self, files, remote_path = '.'):
        """
        Convenience function for a recursive put, preserving times.

        @param files: A single path, or a list of paths to be transfered.
        @type files: str, list
        @param remote_path: path in which to receive the files on the remote
            host. defaults to '.'
        @type remote_path: bool
        """
        self.put(files, remote_path, recursive = True, preserve_times = True)

    def get(self, remote_path, local_path = '',
            recursive = False, preserve_times = False):
        """
        Transfer files from remote host to localhost

        @param remote_path: path to retreive from remote host. since this is
            evaluated by scp on the remote host, shell wildcards and 
            environment variables may be used.
        @type remote_path: str
        @param local_path: path in which to receive files locally
        @type local_path: str
        @param recursive: transfer files and directories recursively
        @type recursive: bool
        @param preserve_times: preserve mtime and atime of transfered files
            and directories.
        @type preserve_times: bool
        """
        self._recv_dir = local_path or os.getcwd() 
        rcsv = ('', ' -r')[recursive]
        prsv = ('', ' -p')[preserve_times]
        self.channel = self.transport.open_session()
        self.channel.settimeout(self.socket_timeout)
        self.channel.exec_command('scp%s%s -f %s' % (rcsv, prsv, remote_path))
        self._recv_all()
        
        if self.channel:
            self.channel.close()

    def get_r(self, remote_path, local_path = '.'):
        """
        Convenience function for a recursive get

        @param remote_path: path to retrieve from server
        @type remote_path: str
        @param local_path: path in which to recieve files. default cwd
        @type local_path: str
        """
        self.get(remote_path, local_path, recursive = True)

    def get_p(self, remote_path, local_path = '.'):
        """
        Convenience function for get, preserving times.

        @param remote_path: path to retrieve from server
        @type remote_path: str
        @param local_path: path in which to recieve files. default cwd
        @type local_path: str
        """
        self.get(remote_path, local_path, preserve_times = True)

    def get_rp(self, remote_path, local_path = '.'):
        """
        Convenience function for a recursive get, preserving times.

        @param remote_path: path to retrieve from server
        @type remote_path: str
        @param local_path: path in which to recieve files. default cwd
        @type local_path: str
        """
        self.get(remote_path, local_path, recursive = True, preserve_times = True)

    def _read_stats(self, name):
        """return just the file stats needed for scp"""
        stats = os.stat(name)
        mode = oct(stats.st_mode)[-4:]
        size = stats.st_size
        atime = int(stats.st_atime)
        mtime = int(stats.st_mtime)
        return (mode, size, mtime, atime)

    def _send_files(self, files): 
        for name in files:
            basename = os.path.basename(name)
            (mode, size, mtime, atime) = self._read_stats(name)
            if self.preserve_times:
                self._send_time(mtime, atime)
            file_hdl = file(name, 'rb')
            self.channel.sendall('C%s %d %s\n' % (mode, size, basename))
            self._recv_confirm()
            file_pos = 0
            buff_size = self.buff_size
            chan = self.channel
            while file_pos < size:
                chan.sendall(file_hdl.read(buff_size))
                file_pos = file_hdl.tell()
                if self.callback:
                    self.callback(file_pos, size)
            chan.sendall('\x00')
            file_hdl.close()

    def _send_recursive(self, files):
        for base in files:
            lastdir = base
            for root, dirs, fls in os.walk(base):
                # pop back out to the next dir in the walk
                while lastdir != os.path.commonprefix([lastdir, root]):
                    self._send_popd()
                    lastdir = os.path.split(lastdir)[0]
                self._send_pushd(root)
                lastdir = root
                self._send_files([os.path.join(root, f) for f in fls])
        
    def _send_pushd(self, directory):
        (mode, size, mtime, atime) = self._read_stats(directory)
        basename = os.path.basename(directory)
        if self.preserve_times:
            self._send_time(mtime, atime)
        self.channel.sendall('D%s 0 %s\n' % (mode, basename))
        self._recv_confirm()

    def _send_popd(self):
        self.channel.sendall('E\n')
        self._recv_confirm()

    def _send_time(self, mtime, atime):
        self.channel.sendall('T%d 0 %d 0\n' % (mtime, atime))
        self._recv_confirm()

    def _recv_confirm(self):
        # read scp response
        msg = ''
        try:
            msg = self.channel.recv(512)
        except SocketTimeout:
            raise SCPException('Timout waiting for scp response')
        if msg and msg[0] == '\x00':
            return
        elif msg and msg[0] == '\x01':
            raise SCPException(msg[1:])
        elif self.channel.recv_stderr_ready():
            msg = self.channel.recv_stderr(512)
            raise SCPException(msg)
        elif not msg:
            raise SCPException('No response from server')
        else:
            raise SCPException('Invalid response from server: ' + msg)
    
    def _recv_all(self):
        # loop over scp commands, and recive as necessary
        command = {'C': self._recv_file,
                   'T': self._set_time,
                   'D': self._recv_pushd,
                   'E': self._recv_popd}
        while not self.channel.closed:
            # wait for command as long as we're open
            self.channel.sendall('\x00')
            msg = self.channel.recv(1024)
            if not msg: # chan closed while recving
                break
            code = msg[0]
            try:
                command[code](msg[1:])
            except KeyError:
                raise SCPException(repr(msg))
        # directory times can't be set until we're done writing files
        self._set_dirtimes()
    
    def _set_time(self, cmd):
        try:
            times = cmd.split()
            mtime = int(times[0])
            atime = int(times[2]) or mtime
        except:
            self.channel.send('\x01')
            raise SCPException('Bad time format')
        # save for later
        self._utime = (mtime, atime)

    def _recv_file(self, cmd):
        chan = self.channel
        parts = cmd.split()
        try:
            mode = int(parts[0], 8)
            size = int(parts[1])
            path = os.path.join(self._recv_dir, parts[2])
        except:
            chan.send('\x01')
            chan.close()
            raise SCPException('Bad file format')
        
        try:
            file_hdl = file(path, 'wb')
        except IOError, e:
            chan.send('\x01'+e.message)
            chan.close()
            raise

        buff_size = self.buff_size
        pos = 0
        chan.send('\x00')
        try:
            while pos < size:
                # we have to make sure we don't read the final byte
                if size - pos <= buff_size:
                    buff_size = size - pos
                file_hdl.write(chan.recv(buff_size))
                pos = file_hdl.tell()
                if self.callback:
                    self.callback(pos, size)
            
            msg = chan.recv(512)
            if msg and msg[0] != '\x00':
                raise SCPException(msg[1:])
        except SocketTimeout:
            chan.close()
            raise SCPException('Error receiving, socket.timeout')

        file_hdl.truncate()
        try:
            os.utime(path, self._utime)
            self._utime = None
            os.chmod(path, mode)
            # should we notify the other end?
        finally:
            file_hdl.close()
        # '\x00' confirmation sent in _recv_all

    def _recv_pushd(self, cmd):
        parts = cmd.split()
        try:
            mode = int(parts[0], 8)
            path = os.path.join(self._recv_dir, parts[2])
        except:
            self.channel.send('\x01')
            raise SCPException('Bad directory format')
        try:
            if not os.path.exists(path):
                os.mkdir(path, mode)
            elif os.path.isdir(path):
                os.chmod(path, mode)
            else:
                raise SCPException('%s: Not a directory' % path)
            self._dirtimes[path] = (self._utime)
            self._utime = None
            self._recv_dir = path
        except (OSError, SCPException), e:
            self.channel.send('\x01'+e.message)
            raise

    def _recv_popd(self, *cmd):
        self._recv_dir = os.path.split(self._recv_dir)[0]
        
    def _set_dirtimes(self):
        try:
            for d in self._dirtimes:
                os.utime(d, self._dirtimes[d])
        finally:
            self._dirtimes = {}


class SCPException(Exception):
    """SCP exception class"""
    pass
