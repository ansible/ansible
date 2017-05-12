#
# (c) 2017, Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import pkg_resources
except Exception:
    pass

import fcntl
import os
import shlex
import signal
import socket
import struct
import sys
import time
import traceback
import syslog
import datetime
import logging

from io import BytesIO

from ansible import constants as C
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.six.moves import cPickle, StringIO
from ansible.playbook.play_context import PlayContext
from ansible.plugins import connection_loader
from ansible.utils.path import unfrackpath, makedirs_safe
from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.utils.display import Display
from ansible.cli import CLI

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def do_fork():
    '''
    Does the required double fork for a daemon process. Based on
    http://code.activestate.com/recipes/66012-fork-a-daemon-process-on-unix/
    '''
    try:
        pid = os.fork()
        if pid > 0:
            return pid

        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)

            if C.DEFAULT_LOG_PATH != '':
                out_file = file(C.DEFAULT_LOG_PATH, 'a+')
                err_file = file(C.DEFAULT_LOG_PATH, 'a+', 0)
            else:
                out_file = file('/dev/null', 'a+')
                err_file = file('/dev/null', 'a+', 0)

            os.dup2(out_file.fileno(), sys.stdout.fileno())
            os.dup2(err_file.fileno(), sys.stderr.fileno())
            os.close(sys.stdin.fileno())

            return pid
        except OSError as e:
            sys.exit(1)
    except OSError as e:
        sys.exit(1)


def send_data(s, data):
    packed_len = struct.pack('!Q', len(data))
    return s.sendall(packed_len + data)


def recv_data(s):
    header_len = 8  # size of a packed unsigned long long
    data = b""
    while len(data) < header_len:
        d = s.recv(header_len - len(data))
        if not d:
            return None
        data += d
    data_len = struct.unpack('!Q', data[:header_len])[0]
    data = data[header_len:]
    while len(data) < data_len:
        d = s.recv(data_len - len(data))
        if not d:
            return None
        data += d
    return data


class Server:

    def __init__(self, path, play_context):

        self.path = path
        self.play_context = play_context

        display.display("starting new persistent socket with path %s" % path, log_only=True)
        display.display(
            'creating new control socket for host %s:%s as user %s' %
            (play_context.remote_addr, play_context.port, play_context.remote_user)
        )

        display.display('control socket path is %s' % path, log_only=True)
        display.display('current working directory is %s' % os.getcwd(), log_only=True)

        self._start_time = datetime.datetime.now()

        display.display("using connection plugin %s" % self.play_context.connection, log_only=True)

        self.conn = connection_loader.get(play_context.connection, play_context, sys.stdin)
        self.conn._connect()
        if not self.conn.connected:
            raise AnsibleConnectionFailure('unable to connect to remote host %s' % self._play_context.remote_addr)

        connection_time = datetime.datetime.now() - self._start_time
        display.display('connection established to %s in %s' % (play_context.remote_addr, connection_time), log_only=True)

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(path)
        self.socket.listen(1)

        signal.signal(signal.SIGALRM, self.alarm_handler)

    def dispatch(self, obj, name, *args, **kwargs):
        meth = getattr(obj, name, None)
        if meth:
            return meth(*args, **kwargs)

    def alarm_handler(self, signum, frame):
        '''
        Alarm handler
        '''
        # FIXME: this should also set internal flags for other
        #        areas of code to check, so they can terminate
        #        earlier than the socket going back to the accept
        #        call and failing there.
        #
        # hooks the connection plugin to handle any cleanup
        self.dispatch(self.conn, 'alarm_handler', signum, frame)
        self.socket.close()

    def run(self):
        try:
            while True:
                # set the alarm, if we don't get an accept before it
                # goes off we exit (via an exception caused by the socket
                # getting closed while waiting on accept())
                # FIXME: is this the best way to exit? as noted above in the
                #        handler we should probably be setting a flag to check
                #        here and in other parts of the code
                signal.alarm(C.PERSISTENT_CONNECT_TIMEOUT)
                try:
                    (s, addr) = self.socket.accept()
                    display.display('incoming request accepted on persistent socket', log_only=True)
                    # clear the alarm
                    # FIXME: potential race condition here between the accept and
                    #        time to this call.
                    signal.alarm(0)
                except:
                    break

                while True:
                    data = recv_data(s)
                    if not data:
                        break

                    signal.alarm(C.DEFAULT_TIMEOUT)

                    rc = 255
                    try:
                        if data.startswith(b'EXEC: '):
                            display.display("socket operation is EXEC", log_only=True)
                            cmd = data.split(b'EXEC: ')[1]
                            (rc, stdout, stderr) = self.conn.exec_command(cmd)
                        elif data.startswith(b'PUT: ') or data.startswith(b'FETCH: '):
                            (op, src, dst) = shlex.split(to_native(data))
                            stdout = stderr = ''
                            try:
                                if op == 'FETCH:':
                                    display.display("socket operation is FETCH", log_only=True)
                                    self.conn.fetch_file(src, dst)
                                elif op == 'PUT:':
                                    display.display("socket operation is PUT", log_only=True)
                                    self.conn.put_file(src, dst)
                                rc = 0
                            except:
                                pass
                        elif data.startswith(b'CONTEXT: '):
                            display.display("socket operation is CONTEXT", log_only=True)
                            pc_data = data.split(b'CONTEXT: ')[1]

                            src = StringIO(pc_data)
                            pc_data = cPickle.load(src)
                            src.close()

                            pc = PlayContext()
                            pc.deserialize(pc_data)

                            self.dispatch(self.conn, 'update_play_context', pc)
                            continue
                        else:
                            display.display("socket operation is UNKNOWN", log_only=True)
                            stdout = ''
                            stderr = 'Invalid action specified'
                    except:
                        stdout = ''
                        stderr = traceback.format_exc()

                    signal.alarm(0)

                    display.display("socket operation completed with rc %s" % rc, log_only=True)

                    send_data(s, to_bytes(str(rc)))
                    send_data(s, to_bytes(stdout))
                    send_data(s, to_bytes(stderr))
                s.close()
        except Exception as e:
            display.display(traceback.format_exec(), log_only=True)
        finally:
            # when done, close the connection properly and cleanup
            # the socket file so it can be recreated
            end_time = datetime.datetime.now()
            delta = end_time - self._start_time
            display.display('shutting down control socket, connection was active for %s secs' % delta, log_only=True)
            try:
                self.conn.close()
                self.socket.close()
            except Exception as e:
                pass
            os.remove(self.path)


class ConnectionCLI(CLI):

    def __init__(self, args):
        super(ConnectionCLI, self).__init__(args)

        self._play_context = PlayContext()

    def parse(self):
        """ Build parser for ansible-connection
        """
        self.parser = CLI.base_parser(
            usage="usage: %prog [options]",
            desc="ansible persistent connection"
        )

        super(ConnectionCLI, self).parse()

        display.verbosity = self.options.verbosity

    def run(self):
        super(ConnectionCLI, self).run()

        init_data = ''
        src = None

        # load play context read from stdin
        line = sys.stdin.readline()
        while line.strip() != '#END_INIT#':
            if line == '':
                raise AnsibleException('EOL found before init data was complete')
            init_data += line
            line = sys.stdin.readline()

        src = BytesIO(to_bytes(init_data))
        pc_data = cPickle.load(src)

        self._play_context.deserialize(pc_data)

        ssh = connection_loader.get('ssh', class_only=True)
        control_path = ssh._create_control_path(self._play_context.remote_addr,
                                                self._play_context.port,
                                                self._play_context.remote_user)

        tmp_path = unfrackpath(C.PERSISTENT_CONNECT_CONTROL_PATH)
        makedirs_safe(tmp_path)

        lk_path = unfrackpath('%s/.ansible_pc_lock' % tmp_path)
        cp_path = unfrackpath(control_path % dict(directory=tmp_path))

        display.display('cp_path is %s' % cp_path, log_only=True)

        lock_fd = os.open(lk_path, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.lockf(lock_fd, fcntl.LOCK_EX)

        if not os.path.exists(cp_path):
            pid = do_fork()
            if pid == 0:
                rc = 0
                try:
                    server = Server(cp_path, self._play_context)
                except AnsibleConnectionFailure as exc:
                    display.display('connecting to host %s returned an error' % pc.remote_addr, log_only=True)
                    display.display(str(exc), log_only=True)
                    rc = 1
                except Exception as exc:
                    display.display('failed to create control socket for host %s' % pc.remote_addr, log_only=True)
                    display.display(traceback.format_exc(), log_only=True)
                    rc = 1

                fcntl.lockf(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)

                if rc == 0:
                    server.run()

                return rc

        else:
            display.display('re-using existing socket for %s@%s%s' % (pc.remote_user, pc.remote_addr, pc.port), log_only=True)

        fcntl.lockf(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)

        # now connect to the daemon process
        # FIXME: if the socket file existed but the daemonized process was killed,
        #        the connection will timeout here. Need to make this more resilient.
        rc = 0
        while rc == 0:
            data = sys.stdin.readline()
            if data == '':
                break
            if data.strip() == '':
                continue
            sf = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            attempts = 1
            while True:
                try:
                    sf.connect(cp_path)
                    break
                except socket.error:
                    # FIXME: better error handling/logging/message here
                    time.sleep(C.PERSISTENT_CONNECT_INTERVAL)
                    attempts += 1
                    if attempts > C.PERSISTENT_CONNECT_RETRIES:
                        display.display(
                            'number of connection attempts exceeded, unable to connect to control socket',
                            self._play_context.remote_addr, self._play_context.remote_user, log_only=True
                        )

                        display.display(
                            'persistent_connect_interval=%s, persistent_connect_retries=%s' %
                            (C.PERSISTENT_CONNECT_INTERVAL, C.PERSISTENT_CONNECT_RETRIES),
                            self._play_context.remote_addr, self._play_context.remote_user, log_only=True
                        )

                        raise AnsibleError('failed to connect to control socket')

            # send the play_context back into the connection so the connection
            # can handle any privilege escalation activities
            pc_data = 'CONTEXT: %s' % src.getvalue()
            send_data(sf, to_bytes(pc_data))
            src.close()

            send_data(sf, to_bytes(data.strip()))

            rc = int(recv_data(sf), 10)
            stdout = recv_data(sf)
            stderr = recv_data(sf)

            sys.stdout.write(to_native(stdout))
            sys.stderr.write(to_native(stderr))

            sf.close()
            break

        return rc
