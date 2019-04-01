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
`.ServerInterface` is an interface to override for server support.
"""

import threading
from paramiko import util
from paramiko.common import (
    DEBUG,
    ERROR,
    OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED,
    AUTH_FAILED,
    AUTH_SUCCESSFUL,
)
from paramiko.py3compat import string_types


class ServerInterface(object):
    """
    This class defines an interface for controlling the behavior of Paramiko
    in server mode.

    Methods on this class are called from Paramiko's primary thread, so you
    shouldn't do too much work in them.  (Certainly nothing that blocks or
    sleeps.)
    """

    def check_channel_request(self, kind, chanid):
        """
        Determine if a channel request of a given type will be granted, and
        return ``OPEN_SUCCEEDED`` or an error code.  This method is
        called in server mode when the client requests a channel, after
        authentication is complete.

        If you allow channel requests (and an ssh server that didn't would be
        useless), you should also override some of the channel request methods
        below, which are used to determine which services will be allowed on
        a given channel:

            - `check_channel_pty_request`
            - `check_channel_shell_request`
            - `check_channel_subsystem_request`
            - `check_channel_window_change_request`
            - `check_channel_x11_request`
            - `check_channel_forward_agent_request`

        The ``chanid`` parameter is a small number that uniquely identifies the
        channel within a `.Transport`.  A `.Channel` object is not created
        unless this method returns ``OPEN_SUCCEEDED`` -- once a
        `.Channel` object is created, you can call `.Channel.get_id` to
        retrieve the channel ID.

        The return value should either be ``OPEN_SUCCEEDED`` (or
        ``0``) to allow the channel request, or one of the following error
        codes to reject it:

            - ``OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED``
            - ``OPEN_FAILED_CONNECT_FAILED``
            - ``OPEN_FAILED_UNKNOWN_CHANNEL_TYPE``
            - ``OPEN_FAILED_RESOURCE_SHORTAGE``

        The default implementation always returns
        ``OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED``.

        :param str kind:
            the kind of channel the client would like to open (usually
            ``"session"``).
        :param int chanid: ID of the channel
        :return: an `int` success or failure code (listed above)
        """
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        """
        Return a list of authentication methods supported by the server.
        This list is sent to clients attempting to authenticate, to inform them
        of authentication methods that might be successful.

        The "list" is actually a string of comma-separated names of types of
        authentication.  Possible values are ``"password"``, ``"publickey"``,
        and ``"none"``.

        The default implementation always returns ``"password"``.

        :param str username: the username requesting authentication.
        :return: a comma-separated `str` of authentication types
        """
        return "password"

    def check_auth_none(self, username):
        """
        Determine if a client may open channels with no (further)
        authentication.

        Return ``AUTH_FAILED`` if the client must authenticate, or
        ``AUTH_SUCCESSFUL`` if it's okay for the client to not
        authenticate.

        The default implementation always returns ``AUTH_FAILED``.

        :param str username: the username of the client.
        :return:
            ``AUTH_FAILED`` if the authentication fails; ``AUTH_SUCCESSFUL`` if
            it succeeds.
        :rtype: int
        """
        return AUTH_FAILED

    def check_auth_password(self, username, password):
        """
        Determine if a given username and password supplied by the client is
        acceptable for use in authentication.

        Return ``AUTH_FAILED`` if the password is not accepted,
        ``AUTH_SUCCESSFUL`` if the password is accepted and completes
        the authentication, or ``AUTH_PARTIALLY_SUCCESSFUL`` if your
        authentication is stateful, and this key is accepted for
        authentication, but more authentication is required.  (In this latter
        case, `get_allowed_auths` will be called to report to the client what
        options it has for continuing the authentication.)

        The default implementation always returns ``AUTH_FAILED``.

        :param str username: the username of the authenticating client.
        :param str password: the password given by the client.
        :return:
            ``AUTH_FAILED`` if the authentication fails; ``AUTH_SUCCESSFUL`` if
            it succeeds; ``AUTH_PARTIALLY_SUCCESSFUL`` if the password auth is
            successful, but authentication must continue.
        :rtype: int
        """
        return AUTH_FAILED

    def check_auth_publickey(self, username, key):
        """
        Determine if a given key supplied by the client is acceptable for use
        in authentication.  You should override this method in server mode to
        check the username and key and decide if you would accept a signature
        made using this key.

        Return ``AUTH_FAILED`` if the key is not accepted,
        ``AUTH_SUCCESSFUL`` if the key is accepted and completes the
        authentication, or ``AUTH_PARTIALLY_SUCCESSFUL`` if your
        authentication is stateful, and this password is accepted for
        authentication, but more authentication is required.  (In this latter
        case, `get_allowed_auths` will be called to report to the client what
        options it has for continuing the authentication.)

        Note that you don't have to actually verify any key signtature here.
        If you're willing to accept the key, Paramiko will do the work of
        verifying the client's signature.

        The default implementation always returns ``AUTH_FAILED``.

        :param str username: the username of the authenticating client
        :param .PKey key: the key object provided by the client
        :return:
            ``AUTH_FAILED`` if the client can't authenticate with this key;
            ``AUTH_SUCCESSFUL`` if it can; ``AUTH_PARTIALLY_SUCCESSFUL`` if it
            can authenticate with this key but must continue with
            authentication
        :rtype: int
        """
        return AUTH_FAILED

    def check_auth_interactive(self, username, submethods):
        """
        Begin an interactive authentication challenge, if supported.  You
        should override this method in server mode if you want to support the
        ``"keyboard-interactive"`` auth type, which requires you to send a
        series of questions for the client to answer.

        Return ``AUTH_FAILED`` if this auth method isn't supported.  Otherwise,
        you should return an `.InteractiveQuery` object containing the prompts
        and instructions for the user.  The response will be sent via a call
        to `check_auth_interactive_response`.

        The default implementation always returns ``AUTH_FAILED``.

        :param str username: the username of the authenticating client
        :param str submethods:
            a comma-separated list of methods preferred by the client (usually
            empty)
        :return:
            ``AUTH_FAILED`` if this auth method isn't supported; otherwise an
            object containing queries for the user
        :rtype: int or `.InteractiveQuery`
        """
        return AUTH_FAILED

    def check_auth_interactive_response(self, responses):
        """
        Continue or finish an interactive authentication challenge, if
        supported.  You should override this method in server mode if you want
        to support the ``"keyboard-interactive"`` auth type.

        Return ``AUTH_FAILED`` if the responses are not accepted,
        ``AUTH_SUCCESSFUL`` if the responses are accepted and complete
        the authentication, or ``AUTH_PARTIALLY_SUCCESSFUL`` if your
        authentication is stateful, and this set of responses is accepted for
        authentication, but more authentication is required.  (In this latter
        case, `get_allowed_auths` will be called to report to the client what
        options it has for continuing the authentication.)

        If you wish to continue interactive authentication with more questions,
        you may return an `.InteractiveQuery` object, which should cause the
        client to respond with more answers, calling this method again.  This
        cycle can continue indefinitely.

        The default implementation always returns ``AUTH_FAILED``.

        :param responses: list of `str` responses from the client
        :return:
            ``AUTH_FAILED`` if the authentication fails; ``AUTH_SUCCESSFUL`` if
            it succeeds; ``AUTH_PARTIALLY_SUCCESSFUL`` if the interactive auth
            is successful, but authentication must continue; otherwise an
            object containing queries for the user
        :rtype: int or `.InteractiveQuery`
        """
        return AUTH_FAILED

    def check_auth_gssapi_with_mic(
        self, username, gss_authenticated=AUTH_FAILED, cc_file=None
    ):
        """
        Authenticate the given user to the server if he is a valid krb5
        principal.

        :param str username: The username of the authenticating client
        :param int gss_authenticated: The result of the krb5 authentication
        :param str cc_filename: The krb5 client credentials cache filename
        :return: ``AUTH_FAILED`` if the user is not authenticated otherwise
                 ``AUTH_SUCCESSFUL``
        :rtype: int
        :note: Kerberos credential delegation is not supported.
        :see: `.ssh_gss`
        :note: : We are just checking in L{AuthHandler} that the given user is
                 a valid krb5 principal!
                 We don't check if the krb5 principal is allowed to log in on
                 the server, because there is no way to do that in python. So
                 if you develop your own SSH server with paramiko for a cetain
                 plattform like Linux, you should call C{krb5_kuserok()} in
                 your local kerberos library to make sure that the
                 krb5_principal has an account on the server and is allowed to
                 log in as a user.
        :see: http://www.unix.com/man-page/all/3/krb5_kuserok/
        """
        if gss_authenticated == AUTH_SUCCESSFUL:
            return AUTH_SUCCESSFUL
        return AUTH_FAILED

    def check_auth_gssapi_keyex(
        self, username, gss_authenticated=AUTH_FAILED, cc_file=None
    ):
        """
        Authenticate the given user to the server if he is a valid krb5
        principal and GSS-API Key Exchange was performed.
        If GSS-API Key Exchange was not performed, this authentication method
        won't be available.

        :param str username: The username of the authenticating client
        :param int gss_authenticated: The result of the krb5 authentication
        :param str cc_filename: The krb5 client credentials cache filename
        :return: ``AUTH_FAILED`` if the user is not authenticated otherwise
                 ``AUTH_SUCCESSFUL``
        :rtype: int
        :note: Kerberos credential delegation is not supported.
        :see: `.ssh_gss` `.kex_gss`
        :note: : We are just checking in L{AuthHandler} that the given user is
                 a valid krb5 principal!
                 We don't check if the krb5 principal is allowed to log in on
                 the server, because there is no way to do that in python. So
                 if you develop your own SSH server with paramiko for a cetain
                 plattform like Linux, you should call C{krb5_kuserok()} in
                 your local kerberos library to make sure that the
                 krb5_principal has an account on the server and is allowed
                 to log in as a user.
        :see: http://www.unix.com/man-page/all/3/krb5_kuserok/
        """
        if gss_authenticated == AUTH_SUCCESSFUL:
            return AUTH_SUCCESSFUL
        return AUTH_FAILED

    def enable_auth_gssapi(self):
        """
        Overwrite this function in your SSH server to enable GSSAPI
        authentication.
        The default implementation always returns false.

        :returns bool: Whether GSSAPI authentication is enabled.
        :see: `.ssh_gss`
        """
        UseGSSAPI = False
        return UseGSSAPI

    def check_port_forward_request(self, address, port):
        """
        Handle a request for port forwarding.  The client is asking that
        connections to the given address and port be forwarded back across
        this ssh connection.  An address of ``"0.0.0.0"`` indicates a global
        address (any address associated with this server) and a port of ``0``
        indicates that no specific port is requested (usually the OS will pick
        a port).

        The default implementation always returns ``False``, rejecting the
        port forwarding request.  If the request is accepted, you should return
        the port opened for listening.

        :param str address: the requested address
        :param int port: the requested port
        :return:
            the port number (`int`) that was opened for listening, or ``False``
            to reject
        """
        return False

    def cancel_port_forward_request(self, address, port):
        """
        The client would like to cancel a previous port-forwarding request.
        If the given address and port is being forwarded across this ssh
        connection, the port should be closed.

        :param str address: the forwarded address
        :param int port: the forwarded port
        """
        pass

    def check_global_request(self, kind, msg):
        """
        Handle a global request of the given ``kind``.  This method is called
        in server mode and client mode, whenever the remote host makes a global
        request.  If there are any arguments to the request, they will be in
        ``msg``.

        There aren't any useful global requests defined, aside from port
        forwarding, so usually this type of request is an extension to the
        protocol.

        If the request was successful and you would like to return contextual
        data to the remote host, return a tuple.  Items in the tuple will be
        sent back with the successful result.  (Note that the items in the
        tuple can only be strings, ints, longs, or bools.)

        The default implementation always returns ``False``, indicating that it
        does not support any global requests.

        .. note:: Port forwarding requests are handled separately, in
            `check_port_forward_request`.

        :param str kind: the kind of global request being made.
        :param .Message msg: any extra arguments to the request.
        :return:
            ``True`` or a `tuple` of data if the request was granted; ``False``
            otherwise.
        """
        return False

    # ...Channel requests...

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        """
        Determine if a pseudo-terminal of the given dimensions (usually
        requested for shell access) can be provided on the given channel.

        The default implementation always returns ``False``.

        :param .Channel channel: the `.Channel` the pty request arrived on.
        :param str term: type of terminal requested (for example, ``"vt100"``).
        :param int width: width of screen in characters.
        :param int height: height of screen in characters.
        :param int pixelwidth:
            width of screen in pixels, if known (may be ``0`` if unknown).
        :param int pixelheight:
            height of screen in pixels, if known (may be ``0`` if unknown).
        :return:
            ``True`` if the pseudo-terminal has been allocated; ``False``
            otherwise.
        """
        return False

    def check_channel_shell_request(self, channel):
        """
        Determine if a shell will be provided to the client on the given
        channel.  If this method returns ``True``, the channel should be
        connected to the stdin/stdout of a shell (or something that acts like
        a shell).

        The default implementation always returns ``False``.

        :param .Channel channel: the `.Channel` the request arrived on.
        :return:
            ``True`` if this channel is now hooked up to a shell; ``False`` if
            a shell can't or won't be provided.
        """
        return False

    def check_channel_exec_request(self, channel, command):
        """
        Determine if a shell command will be executed for the client.  If this
        method returns ``True``, the channel should be connected to the stdin,
        stdout, and stderr of the shell command.

        The default implementation always returns ``False``.

        :param .Channel channel: the `.Channel` the request arrived on.
        :param str command: the command to execute.
        :return:
            ``True`` if this channel is now hooked up to the stdin, stdout, and
            stderr of the executing command; ``False`` if the command will not
            be executed.

        .. versionadded:: 1.1
        """
        return False

    def check_channel_subsystem_request(self, channel, name):
        """
        Determine if a requested subsystem will be provided to the client on
        the given channel.  If this method returns ``True``, all future I/O
        through this channel will be assumed to be connected to the requested
        subsystem.  An example of a subsystem is ``sftp``.

        The default implementation checks for a subsystem handler assigned via
        `.Transport.set_subsystem_handler`.
        If one has been set, the handler is invoked and this method returns
        ``True``.  Otherwise it returns ``False``.

        .. note:: Because the default implementation uses the `.Transport` to
            identify valid subsystems, you probably won't need to override this
            method.

        :param .Channel channel: the `.Channel` the pty request arrived on.
        :param str name: name of the requested subsystem.
        :return:
            ``True`` if this channel is now hooked up to the requested
            subsystem; ``False`` if that subsystem can't or won't be provided.
        """
        transport = channel.get_transport()
        handler_class, larg, kwarg = transport._get_subsystem_handler(name)
        if handler_class is None:
            return False
        handler = handler_class(channel, name, self, *larg, **kwarg)
        handler.start()
        return True

    def check_channel_window_change_request(
        self, channel, width, height, pixelwidth, pixelheight
    ):
        """
        Determine if the pseudo-terminal on the given channel can be resized.
        This only makes sense if a pty was previously allocated on it.

        The default implementation always returns ``False``.

        :param .Channel channel: the `.Channel` the pty request arrived on.
        :param int width: width of screen in characters.
        :param int height: height of screen in characters.
        :param int pixelwidth:
            width of screen in pixels, if known (may be ``0`` if unknown).
        :param int pixelheight:
            height of screen in pixels, if known (may be ``0`` if unknown).
        :return: ``True`` if the terminal was resized; ``False`` if not.
        """
        return False

    def check_channel_x11_request(
        self,
        channel,
        single_connection,
        auth_protocol,
        auth_cookie,
        screen_number,
    ):
        """
        Determine if the client will be provided with an X11 session.  If this
        method returns ``True``, X11 applications should be routed through new
        SSH channels, using `.Transport.open_x11_channel`.

        The default implementation always returns ``False``.

        :param .Channel channel: the `.Channel` the X11 request arrived on
        :param bool single_connection:
            ``True`` if only a single X11 channel should be opened, else
            ``False``.
        :param str auth_protocol: the protocol used for X11 authentication
        :param str auth_cookie: the cookie used to authenticate to X11
        :param int screen_number: the number of the X11 screen to connect to
        :return: ``True`` if the X11 session was opened; ``False`` if not
        """
        return False

    def check_channel_forward_agent_request(self, channel):
        """
        Determine if the client will be provided with an forward agent session.
        If this method returns ``True``, the server will allow SSH Agent
        forwarding.

        The default implementation always returns ``False``.

        :param .Channel channel: the `.Channel` the request arrived on
        :return: ``True`` if the AgentForward was loaded; ``False`` if not
        """
        return False

    def check_channel_direct_tcpip_request(self, chanid, origin, destination):
        """
        Determine if a local port forwarding channel will be granted, and
        return ``OPEN_SUCCEEDED`` or an error code.  This method is
        called in server mode when the client requests a channel, after
        authentication is complete.

        The ``chanid`` parameter is a small number that uniquely identifies the
        channel within a `.Transport`.  A `.Channel` object is not created
        unless this method returns ``OPEN_SUCCEEDED`` -- once a
        `.Channel` object is created, you can call `.Channel.get_id` to
        retrieve the channel ID.

        The origin and destination parameters are (ip_address, port) tuples
        that correspond to both ends of the TCP connection in the forwarding
        tunnel.

        The return value should either be ``OPEN_SUCCEEDED`` (or
        ``0``) to allow the channel request, or one of the following error
        codes to reject it:

            - ``OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED``
            - ``OPEN_FAILED_CONNECT_FAILED``
            - ``OPEN_FAILED_UNKNOWN_CHANNEL_TYPE``
            - ``OPEN_FAILED_RESOURCE_SHORTAGE``

        The default implementation always returns
        ``OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED``.

        :param int chanid: ID of the channel
        :param tuple origin:
            2-tuple containing the IP address and port of the originator
            (client side)
        :param tuple destination:
            2-tuple containing the IP address and port of the destination
            (server side)
        :return: an `int` success or failure code (listed above)
        """
        return OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_env_request(self, channel, name, value):
        """
        Check whether a given environment variable can be specified for the
        given channel.  This method should return ``True`` if the server
        is willing to set the specified environment variable.  Note that
        some environment variables (e.g., PATH) can be exceedingly
        dangerous, so blindly allowing the client to set the environment
        is almost certainly not a good idea.

        The default implementation always returns ``False``.

        :param channel: the `.Channel` the env request arrived on
        :param str name: name
        :param str value: Channel value
        :returns: A boolean
        """
        return False

    def get_banner(self):
        """
        A pre-login banner to display to the user. The message may span
        multiple lines separated by crlf pairs. The language should be in
        rfc3066 style, for example: en-US

        The default implementation always returns ``(None, None)``.

        :returns: A tuple containing the banner and language code.

        .. versionadded:: 2.3
        """
        return (None, None)


class InteractiveQuery(object):
    """
    A query (set of prompts) for a user during interactive authentication.
    """

    def __init__(self, name="", instructions="", *prompts):
        """
        Create a new interactive query to send to the client.  The name and
        instructions are optional, but are generally displayed to the end
        user.  A list of prompts may be included, or they may be added via
        the `add_prompt` method.

        :param str name: name of this query
        :param str instructions:
            user instructions (usually short) about this query
        :param str prompts: one or more authentication prompts
        """
        self.name = name
        self.instructions = instructions
        self.prompts = []
        for x in prompts:
            if isinstance(x, string_types):
                self.add_prompt(x)
            else:
                self.add_prompt(x[0], x[1])

    def add_prompt(self, prompt, echo=True):
        """
        Add a prompt to this query.  The prompt should be a (reasonably short)
        string.  Multiple prompts can be added to the same query.

        :param str prompt: the user prompt
        :param bool echo:
            ``True`` (default) if the user's response should be echoed;
            ``False`` if not (for a password or similar)
        """
        self.prompts.append((prompt, echo))


class SubsystemHandler(threading.Thread):
    """
    Handler for a subsytem in server mode.  If you create a subclass of this
    class and pass it to `.Transport.set_subsystem_handler`, an object of this
    class will be created for each request for this subsystem.  Each new object
    will be executed within its own new thread by calling `start_subsystem`.
    When that method completes, the channel is closed.

    For example, if you made a subclass ``MP3Handler`` and registered it as the
    handler for subsystem ``"mp3"``, then whenever a client has successfully
    authenticated and requests subsytem ``"mp3"``, an object of class
    ``MP3Handler`` will be created, and `start_subsystem` will be called on
    it from a new thread.
    """

    def __init__(self, channel, name, server):
        """
        Create a new handler for a channel.  This is used by `.ServerInterface`
        to start up a new handler when a channel requests this subsystem.  You
        don't need to override this method, but if you do, be sure to pass the
        ``channel`` and ``name`` parameters through to the original
        ``__init__`` method here.

        :param .Channel channel: the channel associated with this
            subsystem request.
        :param str name: name of the requested subsystem.
        :param .ServerInterface server:
            the server object for the session that started this subsystem
        """
        threading.Thread.__init__(self, target=self._run)
        self.__channel = channel
        self.__transport = channel.get_transport()
        self.__name = name
        self.__server = server

    def get_server(self):
        """
        Return the `.ServerInterface` object associated with this channel and
        subsystem.
        """
        return self.__server

    def _run(self):
        try:
            self.__transport._log(
                DEBUG, "Starting handler for subsystem {}".format(self.__name)
            )
            self.start_subsystem(self.__name, self.__transport, self.__channel)
        except Exception as e:
            self.__transport._log(
                ERROR,
                'Exception in subsystem handler for "{}": {}'.format(
                    self.__name, e
                ),
            )
            self.__transport._log(ERROR, util.tb_strings())
        try:
            self.finish_subsystem()
        except:
            pass

    def start_subsystem(self, name, transport, channel):
        """
        Process an ssh subsystem in server mode.  This method is called on a
        new object (and in a new thread) for each subsystem request.  It is
        assumed that all subsystem logic will take place here, and when the
        subsystem is finished, this method will return.  After this method
        returns, the channel is closed.

        The combination of ``transport`` and ``channel`` are unique; this
        handler corresponds to exactly one `.Channel` on one `.Transport`.

        .. note::
            It is the responsibility of this method to exit if the underlying
            `.Transport` is closed.  This can be done by checking
            `.Transport.is_active` or noticing an EOF on the `.Channel`.  If
            this method loops forever without checking for this case, your
            Python interpreter may refuse to exit because this thread will
            still be running.

        :param str name: name of the requested subsystem.
        :param .Transport transport: the server-mode `.Transport`.
        :param .Channel channel: the channel associated with this subsystem
            request.
        """
        pass

    def finish_subsystem(self):
        """
        Perform any cleanup at the end of a subsystem.  The default
        implementation just closes the channel.

        .. versionadded:: 1.1
        """
        self.__channel.close()
