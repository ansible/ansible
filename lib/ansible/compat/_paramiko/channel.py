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
Abstraction for an SSH2 channel.
"""

import binascii
import os
import socket
import time
import threading

# TODO: switch as much of py3compat.py to 'six' as possible, then use six.wraps
from functools import wraps

from paramiko import util
from paramiko.common import (
    cMSG_CHANNEL_REQUEST,
    cMSG_CHANNEL_WINDOW_ADJUST,
    cMSG_CHANNEL_DATA,
    cMSG_CHANNEL_EXTENDED_DATA,
    DEBUG,
    ERROR,
    cMSG_CHANNEL_SUCCESS,
    cMSG_CHANNEL_FAILURE,
    cMSG_CHANNEL_EOF,
    cMSG_CHANNEL_CLOSE,
)
from paramiko.message import Message
from paramiko.py3compat import bytes_types
from paramiko.ssh_exception import SSHException
from paramiko.file import BufferedFile
from paramiko.buffered_pipe import BufferedPipe, PipeTimeout
from paramiko import pipe
from paramiko.util import ClosingContextManager


def open_only(func):
    """
    Decorator for `.Channel` methods which performs an openness check.

    :raises:
        `.SSHException` -- If the wrapped method is called on an unopened
        `.Channel`.
    """

    @wraps(func)
    def _check(self, *args, **kwds):
        if (
            self.closed
            or self.eof_received
            or self.eof_sent
            or not self.active
        ):
            raise SSHException("Channel is not open")
        return func(self, *args, **kwds)

    return _check


class Channel(ClosingContextManager):
    """
    A secure tunnel across an SSH `.Transport`.  A Channel is meant to behave
    like a socket, and has an API that should be indistinguishable from the
    Python socket API.

    Because SSH2 has a windowing kind of flow control, if you stop reading data
    from a Channel and its buffer fills up, the server will be unable to send
    you any more data until you read some of it.  (This won't affect other
    channels on the same transport -- all channels on a single transport are
    flow-controlled independently.)  Similarly, if the server isn't reading
    data you send, calls to `send` may block, unless you set a timeout.  This
    is exactly like a normal network socket, so it shouldn't be too surprising.

    Instances of this class may be used as context managers.
    """

    def __init__(self, chanid):
        """
        Create a new channel.  The channel is not associated with any
        particular session or `.Transport` until the Transport attaches it.
        Normally you would only call this method from the constructor of a
        subclass of `.Channel`.

        :param int chanid:
            the ID of this channel, as passed by an existing `.Transport`.
        """
        #: Channel ID
        self.chanid = chanid
        #: Remote channel ID
        self.remote_chanid = 0
        #: `.Transport` managing this channel
        self.transport = None
        #: Whether the connection is presently active
        self.active = False
        self.eof_received = 0
        self.eof_sent = 0
        self.in_buffer = BufferedPipe()
        self.in_stderr_buffer = BufferedPipe()
        self.timeout = None
        #: Whether the connection has been closed
        self.closed = False
        self.ultra_debug = False
        self.lock = threading.Lock()
        self.out_buffer_cv = threading.Condition(self.lock)
        self.in_window_size = 0
        self.out_window_size = 0
        self.in_max_packet_size = 0
        self.out_max_packet_size = 0
        self.in_window_threshold = 0
        self.in_window_sofar = 0
        self.status_event = threading.Event()
        self._name = str(chanid)
        self.logger = util.get_logger("paramiko.transport")
        self._pipe = None
        self.event = threading.Event()
        self.event_ready = False
        self.combine_stderr = False
        self.exit_status = -1
        self.origin_addr = None

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def __repr__(self):
        """
        Return a string representation of this object, for debugging.
        """
        out = "<paramiko.Channel {}".format(self.chanid)
        if self.closed:
            out += " (closed)"
        elif self.active:
            if self.eof_received:
                out += " (EOF received)"
            if self.eof_sent:
                out += " (EOF sent)"
            out += " (open) window={}".format(self.out_window_size)
            if len(self.in_buffer) > 0:
                out += " in-buffer={}".format(len(self.in_buffer))
        out += " -> " + repr(self.transport)
        out += ">"
        return out

    @open_only
    def get_pty(
        self,
        term="vt100",
        width=80,
        height=24,
        width_pixels=0,
        height_pixels=0,
    ):
        """
        Request a pseudo-terminal from the server.  This is usually used right
        after creating a client channel, to ask the server to provide some
        basic terminal semantics for a shell invoked with `invoke_shell`.
        It isn't necessary (or desirable) to call this method if you're going
        to execute a single command with `exec_command`.

        :param str term: the terminal type to emulate
            (for example, ``'vt100'``)
        :param int width: width (in characters) of the terminal screen
        :param int height: height (in characters) of the terminal screen
        :param int width_pixels: width (in pixels) of the terminal screen
        :param int height_pixels: height (in pixels) of the terminal screen

        :raises:
            `.SSHException` -- if the request was rejected or the channel was
            closed
        """
        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("pty-req")
        m.add_boolean(True)
        m.add_string(term)
        m.add_int(width)
        m.add_int(height)
        m.add_int(width_pixels)
        m.add_int(height_pixels)
        m.add_string(bytes())
        self._event_pending()
        self.transport._send_user_message(m)
        self._wait_for_event()

    @open_only
    def invoke_shell(self):
        """
        Request an interactive shell session on this channel.  If the server
        allows it, the channel will then be directly connected to the stdin,
        stdout, and stderr of the shell.

        Normally you would call `get_pty` before this, in which case the
        shell will operate through the pty, and the channel will be connected
        to the stdin and stdout of the pty.

        When the shell exits, the channel will be closed and can't be reused.
        You must open a new channel if you wish to open another shell.

        :raises:
            `.SSHException` -- if the request was rejected or the channel was
            closed
        """
        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("shell")
        m.add_boolean(True)
        self._event_pending()
        self.transport._send_user_message(m)
        self._wait_for_event()

    @open_only
    def exec_command(self, command):
        """
        Execute a command on the server.  If the server allows it, the channel
        will then be directly connected to the stdin, stdout, and stderr of
        the command being executed.

        When the command finishes executing, the channel will be closed and
        can't be reused.  You must open a new channel if you wish to execute
        another command.

        :param str command: a shell command to execute.

        :raises:
            `.SSHException` -- if the request was rejected or the channel was
            closed
        """
        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("exec")
        m.add_boolean(True)
        m.add_string(command)
        self._event_pending()
        self.transport._send_user_message(m)
        self._wait_for_event()

    @open_only
    def invoke_subsystem(self, subsystem):
        """
        Request a subsystem on the server (for example, ``sftp``).  If the
        server allows it, the channel will then be directly connected to the
        requested subsystem.

        When the subsystem finishes, the channel will be closed and can't be
        reused.

        :param str subsystem: name of the subsystem being requested.

        :raises:
            `.SSHException` -- if the request was rejected or the channel was
            closed
        """
        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("subsystem")
        m.add_boolean(True)
        m.add_string(subsystem)
        self._event_pending()
        self.transport._send_user_message(m)
        self._wait_for_event()

    @open_only
    def resize_pty(self, width=80, height=24, width_pixels=0, height_pixels=0):
        """
        Resize the pseudo-terminal.  This can be used to change the width and
        height of the terminal emulation created in a previous `get_pty` call.

        :param int width: new width (in characters) of the terminal screen
        :param int height: new height (in characters) of the terminal screen
        :param int width_pixels: new width (in pixels) of the terminal screen
        :param int height_pixels: new height (in pixels) of the terminal screen

        :raises:
            `.SSHException` -- if the request was rejected or the channel was
            closed
        """
        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("window-change")
        m.add_boolean(False)
        m.add_int(width)
        m.add_int(height)
        m.add_int(width_pixels)
        m.add_int(height_pixels)
        self.transport._send_user_message(m)

    @open_only
    def update_environment(self, environment):
        """
        Updates this channel's remote shell environment.

        .. note::
            This operation is additive - i.e. the current environment is not
            reset before the given environment variables are set.

        .. warning::
            Servers may silently reject some environment variables; see the
            warning in `set_environment_variable` for details.

        :param dict environment:
            a dictionary containing the name and respective values to set
        :raises:
            `.SSHException` -- if any of the environment variables was rejected
            by the server or the channel was closed
        """
        for name, value in environment.items():
            try:
                self.set_environment_variable(name, value)
            except SSHException as e:
                err = 'Failed to set environment variable "{}".'
                raise SSHException(err.format(name), e)

    @open_only
    def set_environment_variable(self, name, value):
        """
        Set the value of an environment variable.

        .. warning::
            The server may reject this request depending on its ``AcceptEnv``
            setting; such rejections will fail silently (which is common client
            practice for this particular request type). Make sure you
            understand your server's configuration before using!

        :param str name: name of the environment variable
        :param str value: value of the environment variable

        :raises:
            `.SSHException` -- if the request was rejected or the channel was
            closed
        """
        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("env")
        m.add_boolean(False)
        m.add_string(name)
        m.add_string(value)
        self.transport._send_user_message(m)

    def exit_status_ready(self):
        """
        Return true if the remote process has exited and returned an exit
        status. You may use this to poll the process status if you don't
        want to block in `recv_exit_status`. Note that the server may not
        return an exit status in some cases (like bad servers).

        :return:
            ``True`` if `recv_exit_status` will return immediately, else
            ``False``.

        .. versionadded:: 1.7.3
        """
        return self.closed or self.status_event.is_set()

    def recv_exit_status(self):
        """
        Return the exit status from the process on the server.  This is
        mostly useful for retrieving the results of an `exec_command`.
        If the command hasn't finished yet, this method will wait until
        it does, or until the channel is closed.  If no exit status is
        provided by the server, -1 is returned.

        .. warning::
            In some situations, receiving remote output larger than the current
            `.Transport` or session's ``window_size`` (e.g. that set by the
            ``default_window_size`` kwarg for `.Transport.__init__`) will cause
            `.recv_exit_status` to hang indefinitely if it is called prior to a
            sufficiently large `.Channel.recv` (or if there are no threads
            calling `.Channel.recv` in the background).

            In these cases, ensuring that `.recv_exit_status` is called *after*
            `.Channel.recv` (or, again, using threads) can avoid the hang.

        :return: the exit code (as an `int`) of the process on the server.

        .. versionadded:: 1.2
        """
        self.status_event.wait()
        assert self.status_event.is_set()
        return self.exit_status

    def send_exit_status(self, status):
        """
        Send the exit status of an executed command to the client.  (This
        really only makes sense in server mode.)  Many clients expect to
        get some sort of status code back from an executed command after
        it completes.

        :param int status: the exit code of the process

        .. versionadded:: 1.2
        """
        # in many cases, the channel will not still be open here.
        # that's fine.
        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("exit-status")
        m.add_boolean(False)
        m.add_int(status)
        self.transport._send_user_message(m)

    @open_only
    def request_x11(
        self,
        screen_number=0,
        auth_protocol=None,
        auth_cookie=None,
        single_connection=False,
        handler=None,
    ):
        """
        Request an x11 session on this channel.  If the server allows it,
        further x11 requests can be made from the server to the client,
        when an x11 application is run in a shell session.

        From :rfc:`4254`::

            It is RECOMMENDED that the 'x11 authentication cookie' that is
            sent be a fake, random cookie, and that the cookie be checked and
            replaced by the real cookie when a connection request is received.

        If you omit the auth_cookie, a new secure random 128-bit value will be
        generated, used, and returned.  You will need to use this value to
        verify incoming x11 requests and replace them with the actual local
        x11 cookie (which requires some knowledge of the x11 protocol).

        If a handler is passed in, the handler is called from another thread
        whenever a new x11 connection arrives.  The default handler queues up
        incoming x11 connections, which may be retrieved using
        `.Transport.accept`.  The handler's calling signature is::

            handler(channel: Channel, (address: str, port: int))

        :param int screen_number: the x11 screen number (0, 10, etc.)
        :param str auth_protocol:
            the name of the X11 authentication method used; if none is given,
            ``"MIT-MAGIC-COOKIE-1"`` is used
        :param str auth_cookie:
            hexadecimal string containing the x11 auth cookie; if none is
            given, a secure random 128-bit value is generated
        :param bool single_connection:
            if True, only a single x11 connection will be forwarded (by
            default, any number of x11 connections can arrive over this
            session)
        :param handler:
            an optional callable handler to use for incoming X11 connections
        :return: the auth_cookie used
        """
        if auth_protocol is None:
            auth_protocol = "MIT-MAGIC-COOKIE-1"
        if auth_cookie is None:
            auth_cookie = binascii.hexlify(os.urandom(16))

        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("x11-req")
        m.add_boolean(True)
        m.add_boolean(single_connection)
        m.add_string(auth_protocol)
        m.add_string(auth_cookie)
        m.add_int(screen_number)
        self._event_pending()
        self.transport._send_user_message(m)
        self._wait_for_event()
        self.transport._set_x11_handler(handler)
        return auth_cookie

    @open_only
    def request_forward_agent(self, handler):
        """
        Request for a forward SSH Agent on this channel.
        This is only valid for an ssh-agent from OpenSSH !!!

        :param handler:
            a required callable handler to use for incoming SSH Agent
            connections

        :return: True if we are ok, else False
            (at that time we always return ok)

        :raises: SSHException in case of channel problem.
        """
        m = Message()
        m.add_byte(cMSG_CHANNEL_REQUEST)
        m.add_int(self.remote_chanid)
        m.add_string("auth-agent-req@openssh.com")
        m.add_boolean(False)
        self.transport._send_user_message(m)
        self.transport._set_forward_agent_handler(handler)
        return True

    def get_transport(self):
        """
        Return the `.Transport` associated with this channel.
        """
        return self.transport

    def set_name(self, name):
        """
        Set a name for this channel.  Currently it's only used to set the name
        of the channel in logfile entries.  The name can be fetched with the
        `get_name` method.

        :param str name: new channel name
        """
        self._name = name

    def get_name(self):
        """
        Get the name of this channel that was previously set by `set_name`.
        """
        return self._name

    def get_id(self):
        """
        Return the `int` ID # for this channel.

        The channel ID is unique across a `.Transport` and usually a small
        number.  It's also the number passed to
        `.ServerInterface.check_channel_request` when determining whether to
        accept a channel request in server mode.
        """
        return self.chanid

    def set_combine_stderr(self, combine):
        """
        Set whether stderr should be combined into stdout on this channel.
        The default is ``False``, but in some cases it may be convenient to
        have both streams combined.

        If this is ``False``, and `exec_command` is called (or ``invoke_shell``
        with no pty), output to stderr will not show up through the `recv`
        and `recv_ready` calls.  You will have to use `recv_stderr` and
        `recv_stderr_ready` to get stderr output.

        If this is ``True``, data will never show up via `recv_stderr` or
        `recv_stderr_ready`.

        :param bool combine:
            ``True`` if stderr output should be combined into stdout on this
            channel.
        :return: the previous setting (a `bool`).

        .. versionadded:: 1.1
        """
        data = bytes()
        self.lock.acquire()
        try:
            old = self.combine_stderr
            self.combine_stderr = combine
            if combine and not old:
                # copy old stderr buffer into primary buffer
                data = self.in_stderr_buffer.empty()
        finally:
            self.lock.release()
        if len(data) > 0:
            self._feed(data)
        return old

    # ...socket API...

    def settimeout(self, timeout):
        """
        Set a timeout on blocking read/write operations.  The ``timeout``
        argument can be a nonnegative float expressing seconds, or ``None``.
        If a float is given, subsequent channel read/write operations will
        raise a timeout exception if the timeout period value has elapsed
        before the operation has completed.  Setting a timeout of ``None``
        disables timeouts on socket operations.

        ``chan.settimeout(0.0)`` is equivalent to ``chan.setblocking(0)``;
        ``chan.settimeout(None)`` is equivalent to ``chan.setblocking(1)``.

        :param float timeout:
            seconds to wait for a pending read/write operation before raising
            ``socket.timeout``, or ``None`` for no timeout.
        """
        self.timeout = timeout

    def gettimeout(self):
        """
        Returns the timeout in seconds (as a float) associated with socket
        operations, or ``None`` if no timeout is set.  This reflects the last
        call to `setblocking` or `settimeout`.
        """
        return self.timeout

    def setblocking(self, blocking):
        """
        Set blocking or non-blocking mode of the channel: if ``blocking`` is 0,
        the channel is set to non-blocking mode; otherwise it's set to blocking
        mode. Initially all channels are in blocking mode.

        In non-blocking mode, if a `recv` call doesn't find any data, or if a
        `send` call can't immediately dispose of the data, an error exception
        is raised. In blocking mode, the calls block until they can proceed. An
        EOF condition is considered "immediate data" for `recv`, so if the
        channel is closed in the read direction, it will never block.

        ``chan.setblocking(0)`` is equivalent to ``chan.settimeout(0)``;
        ``chan.setblocking(1)`` is equivalent to ``chan.settimeout(None)``.

        :param int blocking:
            0 to set non-blocking mode; non-0 to set blocking mode.
        """
        if blocking:
            self.settimeout(None)
        else:
            self.settimeout(0.0)

    def getpeername(self):
        """
        Return the address of the remote side of this Channel, if possible.

        This simply wraps `.Transport.getpeername`, used to provide enough of a
        socket-like interface to allow asyncore to work. (asyncore likes to
        call ``'getpeername'``.)
        """
        return self.transport.getpeername()

    def close(self):
        """
        Close the channel.  All future read/write operations on the channel
        will fail.  The remote end will receive no more data (after queued data
        is flushed).  Channels are automatically closed when their `.Transport`
        is closed or when they are garbage collected.
        """
        self.lock.acquire()
        try:
            # only close the pipe when the user explicitly closes the channel.
            # otherwise they will get unpleasant surprises.  (and do it before
            # checking self.closed, since the remote host may have already
            # closed the connection.)
            if self._pipe is not None:
                self._pipe.close()
                self._pipe = None

            if not self.active or self.closed:
                return
            msgs = self._close_internal()
        finally:
            self.lock.release()
        for m in msgs:
            if m is not None:
                self.transport._send_user_message(m)

    def recv_ready(self):
        """
        Returns true if data is buffered and ready to be read from this
        channel.  A ``False`` result does not mean that the channel has closed;
        it means you may need to wait before more data arrives.

        :return:
            ``True`` if a `recv` call on this channel would immediately return
            at least one byte; ``False`` otherwise.
        """
        return self.in_buffer.read_ready()

    def recv(self, nbytes):
        """
        Receive data from the channel.  The return value is a string
        representing the data received.  The maximum amount of data to be
        received at once is specified by ``nbytes``.  If a string of
        length zero is returned, the channel stream has closed.

        :param int nbytes: maximum number of bytes to read.
        :return: received data, as a ``str``/``bytes``.

        :raises socket.timeout:
            if no data is ready before the timeout set by `settimeout`.
        """
        try:
            out = self.in_buffer.read(nbytes, self.timeout)
        except PipeTimeout:
            raise socket.timeout()

        ack = self._check_add_window(len(out))
        # no need to hold the channel lock when sending this
        if ack > 0:
            m = Message()
            m.add_byte(cMSG_CHANNEL_WINDOW_ADJUST)
            m.add_int(self.remote_chanid)
            m.add_int(ack)
            self.transport._send_user_message(m)

        return out

    def recv_stderr_ready(self):
        """
        Returns true if data is buffered and ready to be read from this
        channel's stderr stream.  Only channels using `exec_command` or
        `invoke_shell` without a pty will ever have data on the stderr
        stream.

        :return:
            ``True`` if a `recv_stderr` call on this channel would immediately
            return at least one byte; ``False`` otherwise.

        .. versionadded:: 1.1
        """
        return self.in_stderr_buffer.read_ready()

    def recv_stderr(self, nbytes):
        """
        Receive data from the channel's stderr stream.  Only channels using
        `exec_command` or `invoke_shell` without a pty will ever have data
        on the stderr stream.  The return value is a string representing the
        data received.  The maximum amount of data to be received at once is
        specified by ``nbytes``.  If a string of length zero is returned, the
        channel stream has closed.

        :param int nbytes: maximum number of bytes to read.
        :return: received data as a `str`

        :raises socket.timeout: if no data is ready before the timeout set by
            `settimeout`.

        .. versionadded:: 1.1
        """
        try:
            out = self.in_stderr_buffer.read(nbytes, self.timeout)
        except PipeTimeout:
            raise socket.timeout()

        ack = self._check_add_window(len(out))
        # no need to hold the channel lock when sending this
        if ack > 0:
            m = Message()
            m.add_byte(cMSG_CHANNEL_WINDOW_ADJUST)
            m.add_int(self.remote_chanid)
            m.add_int(ack)
            self.transport._send_user_message(m)

        return out

    def send_ready(self):
        """
        Returns true if data can be written to this channel without blocking.
        This means the channel is either closed (so any write attempt would
        return immediately) or there is at least one byte of space in the
        outbound buffer. If there is at least one byte of space in the
        outbound buffer, a `send` call will succeed immediately and return
        the number of bytes actually written.

        :return:
            ``True`` if a `send` call on this channel would immediately succeed
            or fail
        """
        self.lock.acquire()
        try:
            if self.closed or self.eof_sent:
                return True
            return self.out_window_size > 0
        finally:
            self.lock.release()

    def send(self, s):
        """
        Send data to the channel.  Returns the number of bytes sent, or 0 if
        the channel stream is closed.  Applications are responsible for
        checking that all data has been sent: if only some of the data was
        transmitted, the application needs to attempt delivery of the remaining
        data.

        :param str s: data to send
        :return: number of bytes actually sent, as an `int`

        :raises socket.timeout: if no data could be sent before the timeout set
            by `settimeout`.
        """

        m = Message()
        m.add_byte(cMSG_CHANNEL_DATA)
        m.add_int(self.remote_chanid)
        return self._send(s, m)

    def send_stderr(self, s):
        """
        Send data to the channel on the "stderr" stream.  This is normally
        only used by servers to send output from shell commands -- clients
        won't use this.  Returns the number of bytes sent, or 0 if the channel
        stream is closed.  Applications are responsible for checking that all
        data has been sent: if only some of the data was transmitted, the
        application needs to attempt delivery of the remaining data.

        :param str s: data to send.
        :return: number of bytes actually sent, as an `int`.

        :raises socket.timeout:
            if no data could be sent before the timeout set by `settimeout`.

        .. versionadded:: 1.1
        """

        m = Message()
        m.add_byte(cMSG_CHANNEL_EXTENDED_DATA)
        m.add_int(self.remote_chanid)
        m.add_int(1)
        return self._send(s, m)

    def sendall(self, s):
        """
        Send data to the channel, without allowing partial results.  Unlike
        `send`, this method continues to send data from the given string until
        either all data has been sent or an error occurs.  Nothing is returned.

        :param str s: data to send.

        :raises socket.timeout:
            if sending stalled for longer than the timeout set by `settimeout`.
        :raises socket.error:
            if an error occurred before the entire string was sent.

        .. note::
            If the channel is closed while only part of the data has been
            sent, there is no way to determine how much data (if any) was sent.
            This is irritating, but identically follows Python's API.
        """
        while s:
            sent = self.send(s)
            s = s[sent:]
        return None

    def sendall_stderr(self, s):
        """
        Send data to the channel's "stderr" stream, without allowing partial
        results.  Unlike `send_stderr`, this method continues to send data
        from the given string until all data has been sent or an error occurs.
        Nothing is returned.

        :param str s: data to send to the client as "stderr" output.

        :raises socket.timeout:
            if sending stalled for longer than the timeout set by `settimeout`.
        :raises socket.error:
            if an error occurred before the entire string was sent.

        .. versionadded:: 1.1
        """
        while s:
            sent = self.send_stderr(s)
            s = s[sent:]
        return None

    def makefile(self, *params):
        """
        Return a file-like object associated with this channel.  The optional
        ``mode`` and ``bufsize`` arguments are interpreted the same way as by
        the built-in ``file()`` function in Python.

        :return: `.ChannelFile` object which can be used for Python file I/O.
        """
        return ChannelFile(*([self] + list(params)))

    def makefile_stderr(self, *params):
        """
        Return a file-like object associated with this channel's stderr
        stream.   Only channels using `exec_command` or `invoke_shell`
        without a pty will ever have data on the stderr stream.

        The optional ``mode`` and ``bufsize`` arguments are interpreted the
        same way as by the built-in ``file()`` function in Python.  For a
        client, it only makes sense to open this file for reading.  For a
        server, it only makes sense to open this file for writing.

        :return: `.ChannelFile` object which can be used for Python file I/O.

        .. versionadded:: 1.1
        """
        return ChannelStderrFile(*([self] + list(params)))

    def fileno(self):
        """
        Returns an OS-level file descriptor which can be used for polling, but
        but not for reading or writing.  This is primarily to allow Python's
        ``select`` module to work.

        The first time ``fileno`` is called on a channel, a pipe is created to
        simulate real OS-level file descriptor (FD) behavior.  Because of this,
        two OS-level FDs are created, which will use up FDs faster than normal.
        (You won't notice this effect unless you have hundreds of channels
        open at the same time.)

        :return: an OS-level file descriptor (`int`)

        .. warning::
            This method causes channel reads to be slightly less efficient.
        """
        self.lock.acquire()
        try:
            if self._pipe is not None:
                return self._pipe.fileno()
            # create the pipe and feed in any existing data
            self._pipe = pipe.make_pipe()
            p1, p2 = pipe.make_or_pipe(self._pipe)
            self.in_buffer.set_event(p1)
            self.in_stderr_buffer.set_event(p2)
            return self._pipe.fileno()
        finally:
            self.lock.release()

    def shutdown(self, how):
        """
        Shut down one or both halves of the connection.  If ``how`` is 0,
        further receives are disallowed.  If ``how`` is 1, further sends
        are disallowed.  If ``how`` is 2, further sends and receives are
        disallowed.  This closes the stream in one or both directions.

        :param int how:
            0 (stop receiving), 1 (stop sending), or 2 (stop receiving and
              sending).
        """
        if (how == 0) or (how == 2):
            # feign "read" shutdown
            self.eof_received = 1
        if (how == 1) or (how == 2):
            self.lock.acquire()
            try:
                m = self._send_eof()
            finally:
                self.lock.release()
            if m is not None:
                self.transport._send_user_message(m)

    def shutdown_read(self):
        """
        Shutdown the receiving side of this socket, closing the stream in
        the incoming direction.  After this call, future reads on this
        channel will fail instantly.  This is a convenience method, equivalent
        to ``shutdown(0)``, for people who don't make it a habit to
        memorize unix constants from the 1970s.

        .. versionadded:: 1.2
        """
        self.shutdown(0)

    def shutdown_write(self):
        """
        Shutdown the sending side of this socket, closing the stream in
        the outgoing direction.  After this call, future writes on this
        channel will fail instantly.  This is a convenience method, equivalent
        to ``shutdown(1)``, for people who don't make it a habit to
        memorize unix constants from the 1970s.

        .. versionadded:: 1.2
        """
        self.shutdown(1)

    @property
    def _closed(self):
        # Concession to Python 3's socket API, which has a private ._closed
        # attribute instead of a semipublic .closed attribute.
        return self.closed

    # ...calls from Transport

    def _set_transport(self, transport):
        self.transport = transport
        self.logger = util.get_logger(self.transport.get_log_channel())

    def _set_window(self, window_size, max_packet_size):
        self.in_window_size = window_size
        self.in_max_packet_size = max_packet_size
        # threshold of bytes we receive before we bother to send
        # a window update
        self.in_window_threshold = window_size // 10
        self.in_window_sofar = 0
        self._log(DEBUG, "Max packet in: {} bytes".format(max_packet_size))

    def _set_remote_channel(self, chanid, window_size, max_packet_size):
        self.remote_chanid = chanid
        self.out_window_size = window_size
        self.out_max_packet_size = self.transport._sanitize_packet_size(
            max_packet_size
        )
        self.active = 1
        self._log(
            DEBUG, "Max packet out: {} bytes".format(self.out_max_packet_size)
        )

    def _request_success(self, m):
        self._log(DEBUG, "Sesch channel {} request ok".format(self.chanid))
        self.event_ready = True
        self.event.set()
        return

    def _request_failed(self, m):
        self.lock.acquire()
        try:
            msgs = self._close_internal()
        finally:
            self.lock.release()
        for m in msgs:
            if m is not None:
                self.transport._send_user_message(m)

    def _feed(self, m):
        if isinstance(m, bytes_types):
            # passed from _feed_extended
            s = m
        else:
            s = m.get_binary()
        self.in_buffer.feed(s)

    def _feed_extended(self, m):
        code = m.get_int()
        s = m.get_binary()
        if code != 1:
            self._log(
                ERROR, "unknown extended_data type {}; discarding".format(code)
            )
            return
        if self.combine_stderr:
            self._feed(s)
        else:
            self.in_stderr_buffer.feed(s)

    def _window_adjust(self, m):
        nbytes = m.get_int()
        self.lock.acquire()
        try:
            if self.ultra_debug:
                self._log(DEBUG, "window up {}".format(nbytes))
            self.out_window_size += nbytes
            self.out_buffer_cv.notifyAll()
        finally:
            self.lock.release()

    def _handle_request(self, m):
        key = m.get_text()
        want_reply = m.get_boolean()
        server = self.transport.server_object
        ok = False
        if key == "exit-status":
            self.exit_status = m.get_int()
            self.status_event.set()
            ok = True
        elif key == "xon-xoff":
            # ignore
            ok = True
        elif key == "pty-req":
            term = m.get_string()
            width = m.get_int()
            height = m.get_int()
            pixelwidth = m.get_int()
            pixelheight = m.get_int()
            modes = m.get_string()
            if server is None:
                ok = False
            else:
                ok = server.check_channel_pty_request(
                    self, term, width, height, pixelwidth, pixelheight, modes
                )
        elif key == "shell":
            if server is None:
                ok = False
            else:
                ok = server.check_channel_shell_request(self)
        elif key == "env":
            name = m.get_string()
            value = m.get_string()
            if server is None:
                ok = False
            else:
                ok = server.check_channel_env_request(self, name, value)
        elif key == "exec":
            cmd = m.get_string()
            if server is None:
                ok = False
            else:
                ok = server.check_channel_exec_request(self, cmd)
        elif key == "subsystem":
            name = m.get_text()
            if server is None:
                ok = False
            else:
                ok = server.check_channel_subsystem_request(self, name)
        elif key == "window-change":
            width = m.get_int()
            height = m.get_int()
            pixelwidth = m.get_int()
            pixelheight = m.get_int()
            if server is None:
                ok = False
            else:
                ok = server.check_channel_window_change_request(
                    self, width, height, pixelwidth, pixelheight
                )
        elif key == "x11-req":
            single_connection = m.get_boolean()
            auth_proto = m.get_text()
            auth_cookie = m.get_binary()
            screen_number = m.get_int()
            if server is None:
                ok = False
            else:
                ok = server.check_channel_x11_request(
                    self,
                    single_connection,
                    auth_proto,
                    auth_cookie,
                    screen_number,
                )
        elif key == "auth-agent-req@openssh.com":
            if server is None:
                ok = False
            else:
                ok = server.check_channel_forward_agent_request(self)
        else:
            self._log(DEBUG, 'Unhandled channel request "{}"'.format(key))
            ok = False
        if want_reply:
            m = Message()
            if ok:
                m.add_byte(cMSG_CHANNEL_SUCCESS)
            else:
                m.add_byte(cMSG_CHANNEL_FAILURE)
            m.add_int(self.remote_chanid)
            self.transport._send_user_message(m)

    def _handle_eof(self, m):
        self.lock.acquire()
        try:
            if not self.eof_received:
                self.eof_received = True
                self.in_buffer.close()
                self.in_stderr_buffer.close()
                if self._pipe is not None:
                    self._pipe.set_forever()
        finally:
            self.lock.release()
        self._log(DEBUG, "EOF received ({})".format(self._name))

    def _handle_close(self, m):
        self.lock.acquire()
        try:
            msgs = self._close_internal()
            self.transport._unlink_channel(self.chanid)
        finally:
            self.lock.release()
        for m in msgs:
            if m is not None:
                self.transport._send_user_message(m)

    # ...internals...

    def _send(self, s, m):
        size = len(s)
        self.lock.acquire()
        try:
            if self.closed:
                # this doesn't seem useful, but it is the documented behavior
                # of Socket
                raise socket.error("Socket is closed")
            size = self._wait_for_send_window(size)
            if size == 0:
                # eof or similar
                return 0
            m.add_string(s[:size])
        finally:
            self.lock.release()
        # Note: We release self.lock before calling _send_user_message.
        # Otherwise, we can deadlock during re-keying.
        self.transport._send_user_message(m)
        return size

    def _log(self, level, msg, *args):
        self.logger.log(level, "[chan " + self._name + "] " + msg, *args)

    def _event_pending(self):
        self.event.clear()
        self.event_ready = False

    def _wait_for_event(self):
        self.event.wait()
        assert self.event.is_set()
        if self.event_ready:
            return
        e = self.transport.get_exception()
        if e is None:
            e = SSHException("Channel closed.")
        raise e

    def _set_closed(self):
        # you are holding the lock.
        self.closed = True
        self.in_buffer.close()
        self.in_stderr_buffer.close()
        self.out_buffer_cv.notifyAll()
        # Notify any waiters that we are closed
        self.event.set()
        self.status_event.set()
        if self._pipe is not None:
            self._pipe.set_forever()

    def _send_eof(self):
        # you are holding the lock.
        if self.eof_sent:
            return None
        m = Message()
        m.add_byte(cMSG_CHANNEL_EOF)
        m.add_int(self.remote_chanid)
        self.eof_sent = True
        self._log(DEBUG, "EOF sent ({})".format(self._name))
        return m

    def _close_internal(self):
        # you are holding the lock.
        if not self.active or self.closed:
            return None, None
        m1 = self._send_eof()
        m2 = Message()
        m2.add_byte(cMSG_CHANNEL_CLOSE)
        m2.add_int(self.remote_chanid)
        self._set_closed()
        # can't unlink from the Transport yet -- the remote side may still
        # try to send meta-data (exit-status, etc)
        return m1, m2

    def _unlink(self):
        # server connection could die before we become active:
        # still signal the close!
        if self.closed:
            return
        self.lock.acquire()
        try:
            self._set_closed()
            self.transport._unlink_channel(self.chanid)
        finally:
            self.lock.release()

    def _check_add_window(self, n):
        self.lock.acquire()
        try:
            if self.closed or self.eof_received or not self.active:
                return 0
            if self.ultra_debug:
                self._log(DEBUG, "addwindow {}".format(n))
            self.in_window_sofar += n
            if self.in_window_sofar <= self.in_window_threshold:
                return 0
            if self.ultra_debug:
                self._log(
                    DEBUG, "addwindow send {}".format(self.in_window_sofar)
                )
            out = self.in_window_sofar
            self.in_window_sofar = 0
            return out
        finally:
            self.lock.release()

    def _wait_for_send_window(self, size):
        """
        (You are already holding the lock.)
        Wait for the send window to open up, and allocate up to ``size`` bytes
        for transmission.  If no space opens up before the timeout, a timeout
        exception is raised.  Returns the number of bytes available to send
        (may be less than requested).
        """
        # you are already holding the lock
        if self.closed or self.eof_sent:
            return 0
        if self.out_window_size == 0:
            # should we block?
            if self.timeout == 0.0:
                raise socket.timeout()
            # loop here in case we get woken up but a different thread has
            # filled the buffer
            timeout = self.timeout
            while self.out_window_size == 0:
                if self.closed or self.eof_sent:
                    return 0
                then = time.time()
                self.out_buffer_cv.wait(timeout)
                if timeout is not None:
                    timeout -= time.time() - then
                    if timeout <= 0.0:
                        raise socket.timeout()
        # we have some window to squeeze into
        if self.closed or self.eof_sent:
            return 0
        if self.out_window_size < size:
            size = self.out_window_size
        if self.out_max_packet_size - 64 < size:
            size = self.out_max_packet_size - 64
        self.out_window_size -= size
        if self.ultra_debug:
            self._log(DEBUG, "window down to {}".format(self.out_window_size))
        return size


class ChannelFile(BufferedFile):
    """
    A file-like wrapper around `.Channel`.  A ChannelFile is created by calling
    `Channel.makefile`.

    .. warning::
        To correctly emulate the file object created from a socket's `makefile
        <python:socket.socket.makefile>` method, a `.Channel` and its
        `.ChannelFile` should be able to be closed or garbage-collected
        independently. Currently, closing the `ChannelFile` does nothing but
        flush the buffer.
    """

    def __init__(self, channel, mode="r", bufsize=-1):
        self.channel = channel
        BufferedFile.__init__(self)
        self._set_mode(mode, bufsize)

    def __repr__(self):
        """
        Returns a string representation of this object, for debugging.
        """
        return "<paramiko.ChannelFile from " + repr(self.channel) + ">"

    def _read(self, size):
        return self.channel.recv(size)

    def _write(self, data):
        self.channel.sendall(data)
        return len(data)


class ChannelStderrFile(ChannelFile):
    def __init__(self, channel, mode="r", bufsize=-1):
        ChannelFile.__init__(self, channel, mode, bufsize)

    def _read(self, size):
        return self.channel.recv_stderr(size)

    def _write(self, data):
        self.channel.sendall_stderr(data)
        return len(data)


# vim: set shiftwidth=4 expandtab :
