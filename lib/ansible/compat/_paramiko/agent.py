# Copyright (C) 2003-2007  John Rochester <john@jrochester.org>
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
SSH Agent interface
"""

import os
import socket
import struct
import sys
import threading
import time
import tempfile
import stat
from select import select
from paramiko.common import asbytes, io_sleep
from paramiko.py3compat import byte_chr

from paramiko.ssh_exception import SSHException, AuthenticationException
from paramiko.message import Message
from paramiko.pkey import PKey
from paramiko.util import retry_on_signal

cSSH2_AGENTC_REQUEST_IDENTITIES = byte_chr(11)
SSH2_AGENT_IDENTITIES_ANSWER = 12
cSSH2_AGENTC_SIGN_REQUEST = byte_chr(13)
SSH2_AGENT_SIGN_RESPONSE = 14


class AgentSSH(object):
    def __init__(self):
        self._conn = None
        self._keys = ()

    def get_keys(self):
        """
        Return the list of keys available through the SSH agent, if any.  If
        no SSH agent was running (or it couldn't be contacted), an empty list
        will be returned.

        :return:
            a tuple of `.AgentKey` objects representing keys available on the
            SSH agent
        """
        return self._keys

    def _connect(self, conn):
        self._conn = conn
        ptype, result = self._send_message(cSSH2_AGENTC_REQUEST_IDENTITIES)
        if ptype != SSH2_AGENT_IDENTITIES_ANSWER:
            raise SSHException("could not get keys from ssh-agent")
        keys = []
        for i in range(result.get_int()):
            keys.append(AgentKey(self, result.get_binary()))
            result.get_string()
        self._keys = tuple(keys)

    def _close(self):
        if self._conn is not None:
            self._conn.close()
        self._conn = None
        self._keys = ()

    def _send_message(self, msg):
        msg = asbytes(msg)
        self._conn.send(struct.pack(">I", len(msg)) + msg)
        l = self._read_all(4)
        msg = Message(self._read_all(struct.unpack(">I", l)[0]))
        return ord(msg.get_byte()), msg

    def _read_all(self, wanted):
        result = self._conn.recv(wanted)
        while len(result) < wanted:
            if len(result) == 0:
                raise SSHException("lost ssh-agent")
            extra = self._conn.recv(wanted - len(result))
            if len(extra) == 0:
                raise SSHException("lost ssh-agent")
            result += extra
        return result


class AgentProxyThread(threading.Thread):
    """
    Class in charge of communication between two channels.
    """

    def __init__(self, agent):
        threading.Thread.__init__(self, target=self.run)
        self._agent = agent
        self._exit = False

    def run(self):
        try:
            (r, addr) = self.get_connection()
            # Found that r should be either
            # a socket from the socket library or None
            self.__inr = r
            # The address should be an IP address as a string? or None
            self.__addr = addr
            self._agent.connect()
            if not isinstance(self._agent, int) and (
                self._agent._conn is None
                or not hasattr(self._agent._conn, "fileno")
            ):
                raise AuthenticationException("Unable to connect to SSH agent")
            self._communicate()
        except:
            # XXX Not sure what to do here ... raise or pass ?
            raise

    def _communicate(self):
        import fcntl

        oldflags = fcntl.fcntl(self.__inr, fcntl.F_GETFL)
        fcntl.fcntl(self.__inr, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
        while not self._exit:
            events = select([self._agent._conn, self.__inr], [], [], 0.5)
            for fd in events[0]:
                if self._agent._conn == fd:
                    data = self._agent._conn.recv(512)
                    if len(data) != 0:
                        self.__inr.send(data)
                    else:
                        self._close()
                        break
                elif self.__inr == fd:
                    data = self.__inr.recv(512)
                    if len(data) != 0:
                        self._agent._conn.send(data)
                    else:
                        self._close()
                        break
            time.sleep(io_sleep)

    def _close(self):
        self._exit = True
        self.__inr.close()
        self._agent._conn.close()


class AgentLocalProxy(AgentProxyThread):
    """
    Class to be used when wanting to ask a local SSH Agent being
    asked from a remote fake agent (so use a unix socket for ex.)
    """

    def __init__(self, agent):
        AgentProxyThread.__init__(self, agent)

    def get_connection(self):
        """
        Return a pair of socket object and string address.

        May block!
        """
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            conn.bind(self._agent._get_filename())
            conn.listen(1)
            (r, addr) = conn.accept()
            return r, addr
        except:
            raise


class AgentRemoteProxy(AgentProxyThread):
    """
    Class to be used when wanting to ask a remote SSH Agent
    """

    def __init__(self, agent, chan):
        AgentProxyThread.__init__(self, agent)
        self.__chan = chan

    def get_connection(self):
        return self.__chan, None


class AgentClientProxy(object):
    """
    Class proxying request as a client:

    #. client ask for a request_forward_agent()
    #. server creates a proxy and a fake SSH Agent
    #. server ask for establishing a connection when needed,
       calling the forward_agent_handler at client side.
    #. the forward_agent_handler launch a thread for connecting
       the remote fake agent and the local agent
    #. Communication occurs ...
    """

    def __init__(self, chanRemote):
        self._conn = None
        self.__chanR = chanRemote
        self.thread = AgentRemoteProxy(self, chanRemote)
        self.thread.start()

    def __del__(self):
        self.close()

    def connect(self):
        """
        Method automatically called by ``AgentProxyThread.run``.
        """
        if ("SSH_AUTH_SOCK" in os.environ) and (sys.platform != "win32"):
            conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                retry_on_signal(
                    lambda: conn.connect(os.environ["SSH_AUTH_SOCK"])
                )
            except:
                # probably a dangling env var: the ssh agent is gone
                return
        elif sys.platform == "win32":
            import paramiko.win_pageant as win_pageant

            if win_pageant.can_talk_to_agent():
                conn = win_pageant.PageantConnection()
            else:
                return
        else:
            # no agent support
            return
        self._conn = conn

    def close(self):
        """
        Close the current connection and terminate the agent
        Should be called manually
        """
        if hasattr(self, "thread"):
            self.thread._exit = True
            self.thread.join(1000)
        if self._conn is not None:
            self._conn.close()


class AgentServerProxy(AgentSSH):
    """
    :param .Transport t: Transport used for SSH Agent communication forwarding

    :raises: `.SSHException` -- mostly if we lost the agent
    """

    def __init__(self, t):
        AgentSSH.__init__(self)
        self.__t = t
        self._dir = tempfile.mkdtemp("sshproxy")
        os.chmod(self._dir, stat.S_IRWXU)
        self._file = self._dir + "/sshproxy.ssh"
        self.thread = AgentLocalProxy(self)
        self.thread.start()

    def __del__(self):
        self.close()

    def connect(self):
        conn_sock = self.__t.open_forward_agent_channel()
        if conn_sock is None:
            raise SSHException("lost ssh-agent")
        conn_sock.set_name("auth-agent")
        self._connect(conn_sock)

    def close(self):
        """
        Terminate the agent, clean the files, close connections
        Should be called manually
        """
        os.remove(self._file)
        os.rmdir(self._dir)
        self.thread._exit = True
        self.thread.join(1000)
        self._close()

    def get_env(self):
        """
        Helper for the environnement under unix

        :return:
            a dict containing the ``SSH_AUTH_SOCK`` environnement variables
        """
        return {"SSH_AUTH_SOCK": self._get_filename()}

    def _get_filename(self):
        return self._file


class AgentRequestHandler(object):
    """
    Primary/default implementation of SSH agent forwarding functionality.

    Simply instantiate this class, handing it a live command-executing session
    object, and it will handle forwarding any local SSH agent processes it
    finds.

    For example::

        # Connect
        client = SSHClient()
        client.connect(host, port, username)
        # Obtain session
        session = client.get_transport().open_session()
        # Forward local agent
        AgentRequestHandler(session)
        # Commands executed after this point will see the forwarded agent on
        # the remote end.
        session.exec_command("git clone https://my.git.repository/")
    """

    def __init__(self, chanClient):
        self._conn = None
        self.__chanC = chanClient
        chanClient.request_forward_agent(self._forward_agent_handler)
        self.__clientProxys = []

    def _forward_agent_handler(self, chanRemote):
        self.__clientProxys.append(AgentClientProxy(chanRemote))

    def __del__(self):
        self.close()

    def close(self):
        for p in self.__clientProxys:
            p.close()


class Agent(AgentSSH):
    """
    Client interface for using private keys from an SSH agent running on the
    local machine.  If an SSH agent is running, this class can be used to
    connect to it and retrieve `.PKey` objects which can be used when
    attempting to authenticate to remote SSH servers.

    Upon initialization, a session with the local machine's SSH agent is
    opened, if one is running. If no agent is running, initialization will
    succeed, but `get_keys` will return an empty tuple.

    :raises: `.SSHException` --
        if an SSH agent is found, but speaks an incompatible protocol
    """

    def __init__(self):
        AgentSSH.__init__(self)

        if ("SSH_AUTH_SOCK" in os.environ) and (sys.platform != "win32"):
            conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                conn.connect(os.environ["SSH_AUTH_SOCK"])
            except:
                # probably a dangling env var: the ssh agent is gone
                return
        elif sys.platform == "win32":
            from . import win_pageant

            if win_pageant.can_talk_to_agent():
                conn = win_pageant.PageantConnection()
            else:
                return
        else:
            # no agent support
            return
        self._connect(conn)

    def close(self):
        """
        Close the SSH agent connection.
        """
        self._close()


class AgentKey(PKey):
    """
    Private key held in a local SSH agent.  This type of key can be used for
    authenticating to a remote server (signing).  Most other key operations
    work as expected.
    """

    def __init__(self, agent, blob):
        self.agent = agent
        self.blob = blob
        self.public_blob = None
        self.name = Message(blob).get_text()

    def asbytes(self):
        return self.blob

    def __str__(self):
        return self.asbytes()

    def get_name(self):
        return self.name

    def sign_ssh_data(self, data):
        msg = Message()
        msg.add_byte(cSSH2_AGENTC_SIGN_REQUEST)
        msg.add_string(self.blob)
        msg.add_string(data)
        msg.add_int(0)
        ptype, result = self.agent._send_message(msg)
        if ptype != SSH2_AGENT_SIGN_RESPONSE:
            raise SSHException("key cannot be used for signing")
        return result.get_binary()
