#!/usr/bin/env python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type


import fcntl
import hashlib
import os
import signal
import socket
import sys
import time
import traceback
import errno
import json

from contextlib import contextmanager

from ansible import constants as C
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves import cPickle, StringIO
from ansible.module_utils.connection import Connection, ConnectionError, send_data, recv_data
from ansible.module_utils.service import fork_process
from ansible.parsing.ajson import AnsibleJSONEncoder, AnsibleJSONDecoder
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader
from ansible.utils.path import unfrackpath, makedirs_safe
from ansible.utils.display import Display
from ansible.utils.jsonrpc import JsonRpcServer


def read_stream(byte_stream):
    size = int(byte_stream.readline().strip())

    data = byte_stream.read(size)
    if len(data) < size:
        raise Exception("EOF found before data was complete")

    data_hash = to_text(byte_stream.readline().strip())
    if data_hash != hashlib.sha1(data).hexdigest():
        raise Exception("Read {0} bytes, but data did not match checksum".format(size))

    # restore escaped loose \r characters
    data = data.replace(br'\r', b'\r')

    return data


@contextmanager
def file_lock(lock_path):
    """
    Uses contextmanager to create and release a file lock based on the
    given path. This allows us to create locks using `with file_lock()`
    to prevent deadlocks related to failure to unlock properly.
    """

    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.lockf(lock_fd, fcntl.LOCK_EX)
    yield
    fcntl.lockf(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)


class ConnectionProcess(object):
    '''
    The connection process wraps around a Connection object that manages
    the connection to a remote device that persists over the playbook
    '''
    def __init__(self, fd, play_context, socket_path, original_path, task_uuid=None, ansible_playbook_pid=None):
        self.play_context = play_context
        self.socket_path = socket_path
        self.original_path = original_path
        self._task_uuid = task_uuid

        self.fd = fd
        self.exception = None

        self.srv = JsonRpcServer()
        self.sock = None

        self.connection = None
        self._ansible_playbook_pid = ansible_playbook_pid

    def start(self, variables):
        try:
            messages = list()
            result = {}

            messages.append(('vvvv', 'control socket path is %s' % self.socket_path))

            # If this is a relative path (~ gets expanded later) then plug the
            # key's path on to the directory we originally came from, so we can
            # find it now that our cwd is /
            if self.play_context.private_key_file and self.play_context.private_key_file[0] not in '~/':
                self.play_context.private_key_file = os.path.join(self.original_path, self.play_context.private_key_file)
            self.connection = connection_loader.get(self.play_context.connection, self.play_context, '/dev/null',
                                                    task_uuid=self._task_uuid, ansible_playbook_pid=self._ansible_playbook_pid)
            try:
                self.connection.set_options(var_options=variables)
            except ConnectionError as exc:
                messages.append(('debug', to_text(exc)))
                raise ConnectionError('Unable to decode JSON from response set_options. See the debug log for more information.')

            self.connection._socket_path = self.socket_path
            self.srv.register(self.connection)
            messages.extend([('vvvv', msg) for msg in sys.stdout.getvalue().splitlines()])

            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.bind(self.socket_path)
            self.sock.listen(1)
            messages.append(('vvvv', 'local domain socket listeners started successfully'))
        except Exception as exc:
            messages.extend(self.connection.pop_messages())
            result['error'] = to_text(exc)
            result['exception'] = traceback.format_exc()
        finally:
            result['messages'] = messages
            self.fd.write(json.dumps(result, cls=AnsibleJSONEncoder))
            self.fd.close()

    def run(self):
        try:
            log_messages = self.connection.get_option('persistent_log_messages')
            while not self.connection._conn_closed:
                signal.signal(signal.SIGALRM, self.connect_timeout)
                signal.signal(signal.SIGTERM, self.handler)
                signal.alarm(self.connection.get_option('persistent_connect_timeout'))

                self.exception = None
                (s, addr) = self.sock.accept()
                signal.alarm(0)
                signal.signal(signal.SIGALRM, self.command_timeout)
                while True:
                    data = recv_data(s)
                    if not data:
                        break

                    if log_messages:
                        display.display("jsonrpc request: %s" % data, log_only=True)

                    request = json.loads(to_text(data, errors='surrogate_or_strict'))
                    if request.get('method') == "exec_command" and not self.connection.connected:
                        self.connection._connect()

                    signal.alarm(self.connection.get_option('persistent_command_timeout'))

                    resp = self.srv.handle_request(data)
                    signal.alarm(0)

                    if log_messages:
                        display.display("jsonrpc response: %s" % resp, log_only=True)

                    send_data(s, to_bytes(resp))

                s.close()

        except Exception as e:
            # socket.accept() will raise EINTR if the socket.close() is called
            if hasattr(e, 'errno'):
                if e.errno != errno.EINTR:
                    self.exception = traceback.format_exc()
            else:
                self.exception = traceback.format_exc()

        finally:
            # allow time for any exception msg send over socket to receive at other end before shutting down
            time.sleep(0.1)

            # when done, close the connection properly and cleanup the socket file so it can be recreated
            self.shutdown()

    def connect_timeout(self, signum, frame):
        msg = 'persistent connection idle timeout triggered, timeout value is %s secs.\nSee the timeout setting options in the Network Debug and ' \
              'Troubleshooting Guide.' % self.connection.get_option('persistent_connect_timeout')
        display.display(msg, log_only=True)
        raise Exception(msg)

    def command_timeout(self, signum, frame):
        msg = 'command timeout triggered, timeout value is %s secs.\nSee the timeout setting options in the Network Debug and Troubleshooting Guide.'\
              % self.connection.get_option('persistent_command_timeout')
        display.display(msg, log_only=True)
        raise Exception(msg)

    def handler(self, signum, frame):
        msg = 'signal handler called with signal %s.' % signum
        display.display(msg, log_only=True)
        raise Exception(msg)

    def shutdown(self):
        """ Shuts down the local domain socket
        """
        lock_path = unfrackpath("%s/.ansible_pc_lock_%s" % os.path.split(self.socket_path))
        if os.path.exists(self.socket_path):
            try:
                if self.sock:
                    self.sock.close()
                if self.connection:
                    self.connection.close()
                    if self.connection.get_option("persistent_log_messages"):
                        for _level, message in self.connection.pop_messages():
                            display.display(message, log_only=True)
            except Exception:
                pass
            finally:
                if os.path.exists(self.socket_path):
                    os.remove(self.socket_path)
                    setattr(self.connection, '_socket_path', None)
                    setattr(self.connection, '_connected', False)

        if os.path.exists(lock_path):
            os.remove(lock_path)

        display.display('shutdown complete', log_only=True)


def main():
    """ Called to initiate the connect to the remote device
    """
    rc = 0
    result = {}
    messages = list()
    socket_path = None

    # Need stdin as a byte stream
    if PY3:
        stdin = sys.stdin.buffer
    else:
        stdin = sys.stdin

    # Note: update the below log capture code after Display.display() is refactored.
    saved_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        # read the play context data via stdin, which means depickling it
        vars_data = read_stream(stdin)
        init_data = read_stream(stdin)

        if PY3:
            pc_data = cPickle.loads(init_data, encoding='bytes')
            variables = cPickle.loads(vars_data, encoding='bytes')
        else:
            pc_data = cPickle.loads(init_data)
            variables = cPickle.loads(vars_data)

        play_context = PlayContext()
        play_context.deserialize(pc_data)
        display.verbosity = play_context.verbosity

    except Exception as e:
        rc = 1
        result.update({
            'error': to_text(e),
            'exception': traceback.format_exc()
        })

    if rc == 0:
        ssh = connection_loader.get('ssh', class_only=True)
        ansible_playbook_pid = sys.argv[1]
        task_uuid = sys.argv[2]
        cp = ssh._create_control_path(play_context.remote_addr, play_context.port, play_context.remote_user, play_context.connection, ansible_playbook_pid)
        # create the persistent connection dir if need be and create the paths
        # which we will be using later
        tmp_path = unfrackpath(C.PERSISTENT_CONTROL_PATH_DIR)
        makedirs_safe(tmp_path)

        socket_path = unfrackpath(cp % dict(directory=tmp_path))
        lock_path = unfrackpath("%s/.ansible_pc_lock_%s" % os.path.split(socket_path))

        with file_lock(lock_path):
            if not os.path.exists(socket_path):
                messages.append(('vvvv', 'local domain socket does not exist, starting it'))
                original_path = os.getcwd()
                r, w = os.pipe()
                pid = fork_process()

                if pid == 0:
                    try:
                        os.close(r)
                        wfd = os.fdopen(w, 'w')
                        process = ConnectionProcess(wfd, play_context, socket_path, original_path, task_uuid, ansible_playbook_pid)
                        process.start(variables)
                    except Exception:
                        messages.append(('error', traceback.format_exc()))
                        rc = 1

                    if rc == 0:
                        process.run()
                    else:
                        process.shutdown()

                    sys.exit(rc)

                else:
                    os.close(w)
                    rfd = os.fdopen(r, 'r')
                    data = json.loads(rfd.read(), cls=AnsibleJSONDecoder)
                    messages.extend(data.pop('messages'))
                    result.update(data)

            else:
                messages.append(('vvvv', 'found existing local domain socket, using it!'))
                conn = Connection(socket_path)
                try:
                    conn.set_options(var_options=variables)
                except ConnectionError as exc:
                    messages.append(('debug', to_text(exc)))
                    raise ConnectionError('Unable to decode JSON from response set_options. See the debug log for more information.')
                pc_data = to_text(init_data)
                try:
                    conn.update_play_context(pc_data)
                    conn.set_check_prompt(task_uuid)
                except Exception as exc:
                    # Only network_cli has update_play context and set_check_prompt, so missing this is
                    # not fatal e.g. netconf
                    if isinstance(exc, ConnectionError) and getattr(exc, 'code', None) == -32601:
                        pass
                    else:
                        result.update({
                            'error': to_text(exc),
                            'exception': traceback.format_exc()
                        })

    if os.path.exists(socket_path):
        messages.extend(Connection(socket_path).pop_messages())
    messages.append(('vvvv', sys.stdout.getvalue()))
    result.update({
        'messages': messages,
        'socket_path': socket_path
    })

    sys.stdout = saved_stdout
    if 'exception' in result:
        rc = 1
        sys.stderr.write(json.dumps(result, cls=AnsibleJSONEncoder))
    else:
        rc = 0
        sys.stdout.write(json.dumps(result, cls=AnsibleJSONEncoder))

    sys.exit(rc)


if __name__ == '__main__':
    display = Display()
    main()
