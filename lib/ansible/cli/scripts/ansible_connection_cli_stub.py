# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import io
import os
import pickle
import signal
import socket
import sys
import time
import traceback
import typing as t
import errno
import json

from ansible import constants as C
from ansible.cli.arguments import option_helpers as opt_help
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.module_utils.connection import Connection, ConnectionError, send_data, recv_data
from ansible.module_utils.service import fork_process
from ansible.module_utils._internal._json._profiles import _tagless
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import (
    _get_persistent_connection_lock_path,
    _get_persistent_connection_socket_path,
    _persistent_connection_lock,
)
from ansible.plugins.loader import connection_loader, init_plugin_loader
from ansible.utils.path import unfrackpath, makedirs_safe
from ansible.utils.display import Display
from ansible.utils.jsonrpc import JsonRpcServer

display = Display()


class _ConnectionProcessRpc:
    """Expose controller-owned operations on a persistent connection."""

    def __init__(self, connection: t.Any, socket_path: str) -> None:
        self.connection = connection
        self.socket_path = socket_path

    def set_options_ansible_connection_cli_stub(
        self,
        options: dict[str, t.Any],
        play_context_data: str,
        task_uuid: str,
    ) -> dict[str, t.Any]:
        """Synchronize task-specific connection state in a single RPC."""
        messages = [('vvvv', 'found existing local domain socket, using it!')]
        result: dict[str, t.Any] = {}
        set_options_failed = False

        try:
            try:
                self.connection.set_options(direct=options)
            except Exception:
                set_options_failed = True
                raise ConnectionError('Unable to decode JSON from response set_options. See the debug log for more information.') from None

            if update_play_context := getattr(self.connection, 'update_play_context', None):
                update_play_context(play_context_data)
            if set_check_prompt := getattr(self.connection, 'set_check_prompt', None):
                set_check_prompt(task_uuid)
        except Exception as exc:
            result.update({
                'error': to_text(exc),
                'exception': traceback.format_exc(),
            })

        connection_messages = self.connection.pop_messages()
        if not set_options_failed:
            messages.extend(connection_messages)
        result.update({
            'messages': messages,
            'socket_path': self.socket_path,
        })

        return result


def read_stream(byte_stream):
    size = int(byte_stream.readline().strip())

    data = byte_stream.read(size)
    if len(data) < size:
        raise Exception("EOF found before data was complete")

    return data


class ConnectionProcess(object):
    """
    The connection process wraps around a Connection object that manages
    the connection to a remote device that persists over the playbook
    """
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

    def start(self, options):
        messages = list()
        result = {}

        try:
            messages.append(('vvvv', 'control socket path is %s' % self.socket_path))

            # If this is a relative path (~ gets expanded later) then plug the
            # key's path on to the directory we originally came from, so we can
            # find it now that our cwd is /
            if self.play_context.private_key_file and self.play_context.private_key_file[0] not in '~/':
                self.play_context.private_key_file = os.path.join(self.original_path, self.play_context.private_key_file)
            self.connection = connection_loader.get(self.play_context.connection, self.play_context, '/dev/null',
                                                    task_uuid=self._task_uuid, ansible_playbook_pid=self._ansible_playbook_pid)
            try:
                self.connection.set_options(direct=options)
            except ConnectionError as exc:
                messages.append(('debug', to_text(exc)))
                raise ConnectionError('Unable to decode JSON from response set_options. See the debug log for more information.')

            self.connection._socket_path = self.socket_path
            self.srv.register(self.connection)
            self.srv.register(_ConnectionProcessRpc(self.connection, self.socket_path))
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
            self.fd.write(json.dumps(result, cls=_tagless.Encoder))
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
        lock_path = _get_persistent_connection_lock_path(self.socket_path)
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


def main(args=None):
    """ Called to initiate the connect to the remote device
    """

    parser = opt_help.create_base_parser(prog=None)
    opt_help.add_verbosity_options(parser)
    parser.add_argument('playbook_pid')
    parser.add_argument('task_uuid')
    args = parser.parse_args(args[1:] if args is not None else args)
    init_plugin_loader()

    # initialize verbosity
    display.verbosity = args.verbosity

    rc = 0
    result = {}
    messages = list()
    socket_path = None

    # Need stdin as a byte stream
    stdin = sys.stdin.buffer

    # Note: update the below log capture code after Display.display() is refactored.
    saved_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # read the play context data via stdin, which means depickling it
        opts_data = read_stream(stdin)
        init_data = read_stream(stdin)

        pc_data = pickle.loads(init_data, encoding='bytes')
        options = pickle.loads(opts_data, encoding='bytes')

        play_context = PlayContext()
        play_context.from_attrs(pc_data)

    except Exception as e:
        rc = 1
        result.update({
            'error': to_text(e),
            'exception': traceback.format_exc()
        })

    if rc == 0:
        ansible_playbook_pid = args.playbook_pid
        task_uuid = args.task_uuid
        # create the persistent connection dir if need be and create the paths
        # which we will be using later
        tmp_path = unfrackpath(C.PERSISTENT_CONTROL_PATH_DIR)
        makedirs_safe(tmp_path)

        socket_path = _get_persistent_connection_socket_path(play_context, ansible_playbook_pid)
        lock_path = _get_persistent_connection_lock_path(socket_path)

        with _persistent_connection_lock(lock_path):
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
                        process.start(options)
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
                    data = json.loads(rfd.read(), cls=_tagless.Decoder)
                    messages.extend(data.pop('messages'))
                    result.update(data)

            else:
                messages.append(('vvvv', 'found existing local domain socket, using it!'))
                conn = Connection(socket_path)
                try:
                    conn.set_options(direct=options)
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
        sys.stderr.write(json.dumps(result, cls=_tagless.Encoder))
    else:
        rc = 0
        sys.stdout.write(json.dumps(result, cls=_tagless.Encoder))

    sys.exit(rc)


if __name__ == '__main__':
    main()
