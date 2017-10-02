# (c) 2017, Peter Sprygada <psprygad@redhat.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import fcntl
import signal
import socket
import datetime
import time
import traceback
import errno

from ansible.plugins.loader import connection_loader
from ansible import constants as C

from ansible.module_utils._text import to_bytes
from ansible.module_utils.connection import send_data, recv_data
from ansible.utils.path import unfrackpath, makedirs_safe
from ansible.errors import AnsibleError
from ansible.executor.process import do_fork
from ansible.utils.jsonrpc import JsonRpcServer


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['ConnectionProcess']


class ConnectionProcess(object):
    '''
    The connection process wraps around a Connection object that manages
    the connection to a remote device that persists over the playbook
    '''
    def __init__(self, connection):
        self.connection = connection
        self.srv = JsonRpcServer()

    def listen(self, socket_path):
        display.vvvv('control socket path is %s' % socket_path, host=self.connection._play_context.remote_addr)

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(socket_path)
        self.socket.listen(1)

        display.vvvv('local socket is set to listening', host=self.connection._play_context.remote_addr)

    def start_connection(self):
        display.vvvv('attempting to start connection to remote device', host=self.connection._play_context.remote_addr)
        self.connection._connect()
        self.srv.register(self.connection)
        display.vvvv('connection to remote device started successfully', host=self.connection._play_context.remote_addr)

    def run(self):
        try:
            while True:
                signal.signal(signal.SIGALRM, self.connect_timeout)
                signal.alarm(C.PERSISTENT_CONNECT_TIMEOUT)

                display.vvvv('socket waiting for new connection', host=self.connection._play_context.remote_addr)
                (s, addr) = self.socket.accept()
                display.vvvv('incoming request accepted on persistent socket', host=self.connection._play_context.remote_addr)
                signal.alarm(0)

                while True:
                    data = recv_data(s)
                    if not data:
                        break

                    signal.signal(signal.SIGALRM, self.request_timeout)
                    signal.alarm(self.connection._play_context.timeout)

                    start = datetime.datetime.now()
                    resp = self.srv.handle_request(data)
                    end = datetime.datetime.now()

                    signal.alarm(0)

                    display.vvvv('request took %s seconds to execute' % (end - start), host=self.connection._play_context.remote_addr)
                    send_data(s, to_bytes(resp))

                s.close()

        except Exception as e:
            # socket.accept() will raise EINTR if the socket.close() is called
            if hasattr(e, 'errno'):
                if e.errno != errno.EINTR:
                    display.debug(traceback.format_exc())
            else:
                display.vvvv(str(e), host=self.connection._play_context.remote_addr)
                display.debug(traceback.format_exc())
                raise AnsibleError(str(e))

        finally:
            # when done, close the connection properly and cleanup
            # the socket file so it can be recreated
            self.shutdown()

    def connect_timeout(self, signum, frame):
        display.debug('persistent connection idle timeout triggered, timeout value is %s secs' % C.PERSISTENT_CONNECT_TIMEOUT)
        self.shutdown()

    def request_timeout(self, signum, frame):
        display.debug('command timeout triggered, timeout value is %s secs' % self.connection._play_context.timeout)
        self.shutdown()

    def shutdown(self):
        """ Shuts down the local domain socket
        """
        display.debug('starting shutdown of persistent connection socket %s [%s]' % (self.connection.socket_path, self.connection._play_context.remote_addr))

        if not os.path.exists(self.connection.socket_path):
            display.debug('persistent connection is not active, nothing to do!')
            return

        try:
            if self.socket:
                display.debug('closing local listener')
                self.socket.close()

            if self.connection:
                display.debug('closing the connection')
                self.connection.close()
        except:
            pass

        finally:
            if os.path.exists(self.connection.socket_path):
                display.debug('removing the local control socket')
                os.remove(self.connection.socket_path)
                setattr(self.connection, '_socket_path', None)
                setattr(self.connection, '_connected', False)

        display.debug('shutdown complete')

    def start(self):
        """ Called to initiate the connect to the remote device
        """
        play_context = self.connection._play_context

        ssh = connection_loader.get('ssh', class_only=True)
        cp = ssh._create_control_path(play_context.remote_addr, play_context.port, play_context.remote_user)

        # create the persistent connection dir if need be and create the paths
        # which we will be using later
        tmp_path = unfrackpath(C.PERSISTENT_CONTROL_PATH_DIR)
        makedirs_safe(tmp_path)

        lock_path = unfrackpath("%s/.ansible_pc_lock" % tmp_path)
        socket_path = unfrackpath(cp % dict(directory=tmp_path))

        setattr(self.connection, '_socket_path', socket_path)

        # if the socket file doesn't exist, spin up the daemon process
        lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.lockf(lock_fd, fcntl.LOCK_EX)

        display.vvvv('socket_path is %s' % socket_path, host=play_context.remote_addr)

        if not os.path.exists(socket_path):
            display.vvvv('forking process to start persistent connection', host=play_context.remote_addr)
            pid = do_fork()
            if pid == 0:
                rc = 0
                try:
                    self.start_connection()
                    self.listen(socket_path)
                except AnsibleError as exc:
                    display.vvvv(str(exc), host=play_context.remote_addr)
                    display.debug(traceback.format_exc())
                    rc = 1
                except Exception as exc:
                    display.vvvv('failed to create control socket for host %s' % play_context.remote_addr, host=play_context.remote_addr)
                    display.debug(traceback.format_exc())
                    rc = 1
                fcntl.lockf(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
                if rc == 0:
                    self.run()
                sys.exit(rc)
        else:
            display.vvvv('found existing socket, reusing it!', host=play_context.remote_addr)

        # increase the connect timeout value by one to avoid any race conditions
        timeout = C.PERSISTENT_CONNECT_TIMEOUT + 1
        while bool(timeout):
            if os.path.exists(socket_path):
                elapsed = (C.PERSISTENT_CONNECT_TIMEOUT + 1) - timeout
                display.vvvv('connected to local socket in %s second(s)' % elapsed, host=play_context.remote_addr)
                setattr(self.connection, '_connected', True)
                break
            time.sleep(1)
            timeout -= 1
        else:
            raise AnsibleError('timeout waiting for local socket', play_context.remote_addr)

        return socket_path
