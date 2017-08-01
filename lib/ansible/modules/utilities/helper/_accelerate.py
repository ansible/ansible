#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, James Cammarata <jcammarata@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: accelerate
short_description: Enable accelerated mode on remote node
deprecated: "Use SSH with ControlPersist instead."
description:
     - This modules launches an ephemeral I(accelerate) daemon on the remote node which
       Ansible can use to communicate with nodes at high speed.
     - The daemon listens on a configurable port for a configurable amount of time.
     - Fireball mode is AES encrypted
version_added: "1.3"
options:
  port:
    description:
      - TCP port for the socket connection
    required: false
    default: 5099
    aliases: []
  timeout:
    description:
      - The number of seconds the socket will wait for data. If none is received when the timeout value is reached, the connection will be closed.
    required: false
    default: 300
    aliases: []
  minutes:
    description:
      - The I(accelerate) listener daemon is started on nodes and will stay around for
        this number of minutes before turning itself off.
    required: false
    default: 30
  ipv6:
    description:
      - The listener daemon on the remote host will bind to the ipv6 localhost socket
        if this parameter is set to true.
    required: false
    default: false
  multi_key:
    description:
      - When enabled, the daemon will open a local socket file which can be used by future daemon executions to
        upload a new key to the already running daemon, so that multiple users can connect using different keys.
        This access still requires an ssh connection as the uid for which the daemon is currently running.
    required: false
    default: no
    version_added: "1.6"
notes:
    - See the advanced playbooks chapter for more about using accelerated mode.
requirements:
    - "python >= 2.4"
    - "python-keyczar"
author: "James Cammarata (@jimi-c)"
'''

EXAMPLES = '''
# To use accelerate mode, simply add "accelerate: true" to your play. The initial
# key exchange and starting up of the daemon will occur over SSH, but all commands and
# subsequent actions will be conducted over the raw socket connection using AES encryption

- hosts: devservers
  accelerate: true
  tasks:
      - command: /usr/bin/anything
'''

import base64
import errno
import getpass
import json
import os
import os.path
import pwd
import signal
import socket
import struct
import sys
import syslog
import tempfile
import time
import traceback


import datetime
from threading import Thread, Lock

# import module snippets
# we must import this here at the top so we can use get_module_path()
from ansible.module_utils.basic import AnsibleModule, get_module_path
from ansible.module_utils.six.moves import socketserver

# the chunk size to read and send, assuming mtu 1500 and
# leaving room for base64 (+33%) encoding and header (100 bytes)
# 4 * (975/3) + 100 = 1400
# which leaves room for the TCP/IP header
CHUNK_SIZE=10240

# FIXME: this all should be moved to module_common, as it's
#        pretty much a copy from the callbacks/util code
DEBUG_LEVEL=0
def log(msg, cap=0):
    global DEBUG_LEVEL
    if DEBUG_LEVEL >= cap:
        syslog.syslog(syslog.LOG_NOTICE|syslog.LOG_DAEMON, msg)

def v(msg):
    log(msg, cap=1)

def vv(msg):
    log(msg, cap=2)

def vvv(msg):
    log(msg, cap=3)

def vvvv(msg):
    log(msg, cap=4)


HAS_KEYCZAR = False
try:
    from keyczar.keys import AesKey
    HAS_KEYCZAR = True
except ImportError:
    pass

SOCKET_FILE = os.path.join(get_module_path(), '.ansible-accelerate', ".local.socket")

def get_pid_location(module):
    """
    Try to find a pid directory in the common locations, falling
    back to the user's home directory if no others exist
    """
    for dir in ['/var/run', '/var/lib/run', '/run', os.path.expanduser("~/")]:
        try:
            if os.path.isdir(dir) and os.access(dir, os.R_OK|os.W_OK):
                return os.path.join(dir, '.accelerate.pid')
        except:
            pass
    module.fail_json(msg="couldn't find any valid directory to use for the accelerate pid file")


# NOTE: this shares a fair amount of code in common with async_wrapper, if async_wrapper were a new module we could move
# this into utils.module_common and probably should anyway

def daemonize_self(module, password, port, minutes, pid_file):
    # daemonizing code: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
    try:
        pid = os.fork()
        if pid > 0:
            vvv("exiting pid %s" % pid)
            # exit first parent
            module.exit_json(msg="daemonized accelerate on port %s for %s minutes with pid %s" % (port, minutes, str(pid)))
    except OSError as e:
        message = "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        module.fail_json(msg=message)

    # decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(int('O22', 8))

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            log("daemon pid %s, writing %s" % (pid, pid_file))
            pid_file = open(pid_file, "w")
            pid_file.write("%s" % pid)
            pid_file.close()
            vvv("pid file written")
            sys.exit(0)
    except OSError as e:
        log('fork #2 failed: %d (%s)' % (e.errno, e.strerror))
        sys.exit(1)

    dev_null = open('/dev/null','rw')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())
    os.dup2(dev_null.fileno(), sys.stdout.fileno())
    os.dup2(dev_null.fileno(), sys.stderr.fileno())
    log("daemonizing successful")

class LocalSocketThread(Thread):
    server = None
    terminated = False

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        self.server = kwargs.get('server')
        Thread.__init__(self, group, target, name, args, kwargs, Verbose)

    def run(self):
        try:
            if os.path.exists(SOCKET_FILE):
                os.remove(SOCKET_FILE)
            else:
                dir = os.path.dirname(SOCKET_FILE)
                if os.path.exists(dir):
                    if not os.path.isdir(dir):
                        log("The socket file path (%s) exists, but is not a directory. No local connections will be available" % dir)
                        return
                    else:
                        # make sure the directory is accessible only to this
                        # user, as socket files derive their permissions from
                        # the directory that contains them
                        os.chmod(dir, int('0700', 8))
                elif not os.path.exists(dir):
                    os.makedirs(dir, int('O700', 8))
        except OSError:
            pass
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.bind(SOCKET_FILE)
        self.s.listen(5)
        while not self.terminated:
            try:
                conn, addr = self.s.accept()
                vv("received local connection")
                data = ""
                while "\n" not in data:
                    data += conn.recv(2048)
                try:
                    try:
                        new_key = AesKey.Read(data.strip())
                        found = False
                        for key in self.server.key_list:
                            try:
                                new_key.Decrypt(key.Encrypt("foo"))
                                found = True
                                break
                            except:
                                pass
                        if not found:
                            vv("adding new key to the key list")
                            self.server.key_list.append(new_key)
                            conn.sendall("OK\n")
                        else:
                            vv("key already exists in the key list, ignoring")
                            conn.sendall("EXISTS\n")

                        # update the last event time so the server doesn't
                        # shutdown sooner than expected for new clients
                        try:
                            self.server.last_event_lock.acquire()
                            self.server.last_event = datetime.datetime.now()
                        finally:
                            self.server.last_event_lock.release()
                    except Exception as e:
                        vv("key loaded locally was invalid, ignoring (%s)" % e)
                        conn.sendall("BADKEY\n")
                finally:
                    try:
                        conn.close()
                    except:
                        pass
            except:
                pass

    def terminate(self):
        super(LocalSocketThread, self).terminate()
        self.terminated = True
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs, Verbose)
        self._return = None

    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(*self._Thread__args,
                                                **self._Thread__kwargs)

    def join(self,timeout=None):
        Thread.join(self, timeout=timeout)
        return self._return

class ThreadedTCPServer(socketserver.ThreadingTCPServer):
    key_list = []
    last_event = datetime.datetime.now()
    last_event_lock = Lock()
    def __init__(self, server_address, RequestHandlerClass, module, password, timeout, use_ipv6=False):
        self.module = module
        self.key_list.append(AesKey.Read(password))
        self.allow_reuse_address = True
        self.timeout = timeout

        if use_ipv6:
            self.address_family = socket.AF_INET6

        if self.module.params.get('multi_key', False):
            vv("starting thread to handle local connections for multiple keys")
            self.local_thread = LocalSocketThread(kwargs=dict(server=self))
            self.local_thread.start()

        socketserver.ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)

    def shutdown(self):
        self.running = False
        socketserver.ThreadingTCPServer.shutdown(self)

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    # the key to use for this connection
    active_key = None

    def send_data(self, data):
        try:
            self.server.last_event_lock.acquire()
            self.server.last_event = datetime.datetime.now()
        finally:
            self.server.last_event_lock.release()

        packed_len = struct.pack('!Q', len(data))
        return self.request.sendall(packed_len + data)

    def recv_data(self):
        header_len = 8 # size of a packed unsigned long long
        data = ""
        vvvv("in recv_data(), waiting for the header")
        while len(data) < header_len:
            try:
                d = self.request.recv(header_len - len(data))
                if not d:
                    vvv("received nothing, bailing out")
                    return None
                data += d
            except:
                # probably got a connection reset
                vvvv("exception received while waiting for recv(), returning None")
                return None
        vvvv("in recv_data(), got the header, unpacking")
        data_len = struct.unpack('!Q',data[:header_len])[0]
        data = data[header_len:]
        vvvv("data received so far (expecting %d): %d" % (data_len,len(data)))
        while len(data) < data_len:
            try:
                d = self.request.recv(data_len - len(data))
                if not d:
                    vvv("received nothing, bailing out")
                    return None
                data += d
                vvvv("data received so far (expecting %d): %d" % (data_len,len(data)))
            except:
                # probably got a connection reset
                vvvv("exception received while waiting for recv(), returning None")
                return None
        vvvv("received all of the data, returning")

        try:
            self.server.last_event_lock.acquire()
            self.server.last_event = datetime.datetime.now()
        finally:
            self.server.last_event_lock.release()

        return data

    def handle(self):
        try:
            while True:
                vvvv("waiting for data")
                data = self.recv_data()
                if not data:
                    vvvv("received nothing back from recv_data(), breaking out")
                    break
                vvvv("got data, decrypting")
                if not self.active_key:
                    for key in self.server.key_list:
                        try:
                            data = key.Decrypt(data)
                            self.active_key = key
                            break
                        except:
                            pass
                    else:
                        vv("bad decrypt, exiting the connection handler")
                        return
                else:
                    try:
                        data = self.active_key.Decrypt(data)
                    except:
                        vv("bad decrypt, exiting the connection handler")
                        return

                vvvv("decryption done, loading json from the data")
                data = json.loads(data)

                mode = data['mode']
                response = {}
                last_pong = datetime.datetime.now()
                if mode == 'command':
                    vvvv("received a command request, running it")
                    twrv = ThreadWithReturnValue(target=self.command, args=(data,))
                    twrv.start()
                    response = None
                    while twrv.is_alive():
                        if (datetime.datetime.now() - last_pong).seconds >= 15:
                            last_pong = datetime.datetime.now()
                            vvvv("command still running, sending keepalive packet")
                            data2 = json.dumps(dict(pong=True))
                            data2 = self.active_key.Encrypt(data2)
                            self.send_data(data2)
                        time.sleep(0.1)
                    response = twrv._return
                    vvvv("thread is done, response from join was %s" % response)
                elif mode == 'put':
                    vvvv("received a put request, putting it")
                    response = self.put(data)
                elif mode == 'fetch':
                    vvvv("received a fetch request, getting it")
                    response = self.fetch(data)
                elif mode == 'validate_user':
                    vvvv("received a request to validate the user id")
                    response = self.validate_user(data)

                vvvv("response result is %s" % str(response))
                json_response = json.dumps(response)
                vvvv("dumped json is %s" % json_response)
                data2 = self.active_key.Encrypt(json_response)
                vvvv("sending the response back to the controller")
                self.send_data(data2)
                vvvv("done sending the response")

                if mode == 'validate_user' and response.get('rc') == 1:
                    vvvv("detected a uid mismatch, shutting down")
                    self.server.shutdown()
        except:
            tb = traceback.format_exc()
            log("encountered an unhandled exception in the handle() function")
            log("error was:\n%s" % tb)
            if self.active_key:
                data2 = json.dumps(dict(rc=1, failed=True, msg="unhandled error in the handle() function"))
                data2 = self.active_key.Encrypt(data2)
                self.send_data(data2)

    def validate_user(self, data):
        if 'username' not in data:
            return dict(failed=True, msg='No username specified')

        vvvv("validating we're running as %s" % data['username'])

        # get the current uid
        c_uid = os.getuid()
        try:
            # the target uid
            t_uid = pwd.getpwnam(data['username']).pw_uid
        except:
            vvvv("could not find user %s" % data['username'])
            return dict(failed=True, msg='could not find user %s' % data['username'])

        # and return rc=0 for success, rc=1 for failure
        if c_uid == t_uid:
            return dict(rc=0)
        else:
            return dict(rc=1)

    def command(self, data):
        if 'cmd' not in data:
            return dict(failed=True, msg='internal error: cmd is required')

        vvvv("executing: %s" % data['cmd'])

        use_unsafe_shell = False
        executable = data.get('executable')
        if executable:
            use_unsafe_shell = True

        rc, stdout, stderr = self.server.module.run_command(data['cmd'], executable=executable, use_unsafe_shell=use_unsafe_shell, close_fds=True)
        if stdout is None:
            stdout = ''
        if stderr is None:
            stderr = ''
        vvvv("got stdout: %s" % stdout)
        vvvv("got stderr: %s" % stderr)

        return dict(rc=rc, stdout=stdout, stderr=stderr)

    def fetch(self, data):
        if 'in_path' not in data:
            return dict(failed=True, msg='internal error: in_path is required')

        try:
            fd = open(data['in_path'], 'rb')
            fstat = os.stat(data['in_path'])
            vvv("FETCH file is %d bytes" % fstat.st_size)
            while fd.tell() < fstat.st_size:
                data = fd.read(CHUNK_SIZE)
                last = False
                if fd.tell() >= fstat.st_size:
                    last = True
                data = dict(data=base64.b64encode(data), last=last)
                data = json.dumps(data)
                data = self.active_key.Encrypt(data)

                if self.send_data(data):
                    return dict(failed=True, stderr="failed to send data")

                response = self.recv_data()
                if not response:
                    log("failed to get a response, aborting")
                    return dict(failed=True, stderr="Failed to get a response from %s" % self.host)
                response = self.active_key.Decrypt(response)
                response = json.loads(response)

                if response.get('failed',False):
                    log("got a failed response from the master")
                    return dict(failed=True, stderr="Master reported failure, aborting transfer")
        except Exception as e:
            fd.close()
            tb = traceback.format_exc()
            log("failed to fetch the file: %s" % tb)
            return dict(failed=True, stderr="Could not fetch the file: %s" % e)

        fd.close()
        return dict()

    def put(self, data):
        if 'data' not in data:
            return dict(failed=True, msg='internal error: data is required')
        if 'out_path' not in data:
            return dict(failed=True, msg='internal error: out_path is required')

        final_path = None
        if 'user' in data and data.get('user') != getpass.getuser():
            vvv("the target user doesn't match this user, we'll move the file into place via sudo")
            tmp_path = os.path.expanduser('~/.ansible/tmp/')
            if not os.path.exists(tmp_path):
                try:
                    os.makedirs(tmp_path, int('O700', 8))
                except:
                    return dict(failed=True, msg='could not create a temporary directory at %s' % tmp_path)
            (fd,out_path) = tempfile.mkstemp(prefix='ansible.', dir=tmp_path)
            out_fd = os.fdopen(fd, 'w', 0)
            final_path = data['out_path']
        else:
            out_path = data['out_path']
            out_fd = open(out_path, 'w')

        try:
            bytes=0
            while True:
                out = base64.b64decode(data['data'])
                bytes += len(out)
                out_fd.write(out)
                response = json.dumps(dict())
                response = self.active_key.Encrypt(response)
                self.send_data(response)
                if data['last']:
                    break
                data = self.recv_data()
                if not data:
                    raise ""
                data = self.active_key.Decrypt(data)
                data = json.loads(data)
        except:
            out_fd.close()
            tb = traceback.format_exc()
            log("failed to put the file: %s" % tb)
            return dict(failed=True, stdout="Could not write the file")

        vvvv("wrote %d bytes" % bytes)
        out_fd.close()

        if final_path:
            vvv("moving %s to %s" % (out_path, final_path))
            self.server.module.atomic_move(out_path, final_path)
        return dict()

def daemonize(module, password, port, timeout, minutes, use_ipv6, pid_file):
    try:
        daemonize_self(module, password, port, minutes, pid_file)

        def timer_handler(signum, _):
            try:
                try:
                    server.last_event_lock.acquire()
                    td = datetime.datetime.now() - server.last_event
                    # older python timedelta objects don't have total_seconds(),
                    # so we use the formula from the docs to calculate it
                    total_seconds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
                    if total_seconds >= minutes * 60:
                        log("server has been idle longer than the timeout, shutting down")
                        server.running = False
                        server.shutdown()
                    else:
                        # reschedule the check
                        signal.alarm(1)
                except:
                    pass
            finally:
                server.last_event_lock.release()

        signal.signal(signal.SIGALRM, timer_handler)
        signal.alarm(1)

        tries = 5
        while tries > 0:
            try:
                if use_ipv6:
                    address = ("::", port)
                else:
                    address = ("0.0.0.0", port)
                server = ThreadedTCPServer(address, ThreadedTCPRequestHandler, module, password, timeout, use_ipv6=use_ipv6)
                server.allow_reuse_address = True
                break
            except Exception as e:
                vv("Failed to create the TCP server (tries left = %d) (error: %s) " % (tries,e))
            tries -= 1
            time.sleep(0.2)

        if tries == 0:
            vv("Maximum number of attempts to create the TCP server reached, bailing out")
            raise Exception("max # of attempts to serve reached")

        # run the server in a separate thread to make signal handling work
        server_thread = Thread(target=server.serve_forever, kwargs=dict(poll_interval=0.1))
        server_thread.start()
        server.running = True

        v("serving!")
        while server.running:
            time.sleep(1)

        # wait for the thread to exit fully
        server_thread.join()

        v("server thread terminated, exiting!")
        sys.exit(0)
    except Exception as e:
        tb = traceback.format_exc()
        log("exception caught, exiting accelerated mode: %s\n%s" % (e, tb))
        sys.exit(0)

def main():
    global DEBUG_LEVEL
    module = AnsibleModule(
        argument_spec = dict(
            port=dict(required=False, default=5099),
            ipv6=dict(required=False, default=False, type='bool'),
            multi_key=dict(required=False, default=False, type='bool'),
            timeout=dict(required=False, default=300),
            password=dict(required=True, no_log=True),
            minutes=dict(required=False, default=30),
            debug=dict(required=False, default=0, type='int')
        ),
        supports_check_mode=True
    )

    syslog.openlog('ansible-%s' % module._name)

    password  = base64.b64decode(module.params['password'])
    port      = int(module.params['port'])
    timeout   = int(module.params['timeout'])
    minutes   = int(module.params['minutes'])
    debug     = int(module.params['debug'])
    ipv6      = module.params['ipv6']
    multi_key = module.params['multi_key']

    if not HAS_KEYCZAR:
        module.fail_json(msg="keyczar is not installed (on the remote side)")

    DEBUG_LEVEL=debug
    pid_file = get_pid_location(module)

    daemon_pid = None
    daemon_running = False
    if os.path.exists(pid_file):
        try:
            daemon_pid = int(open(pid_file).read())
            try:
                # sending signal 0 doesn't do anything to the
                # process, other than tell the calling program
                # whether other signals can be sent
                os.kill(daemon_pid, 0)
            except OSError as e:
                message  = 'the accelerate daemon appears to be running'
                message += 'as a different user that this user cannot access'
                message += 'pid=%s' % daemon_pid

                if e.errno == errno.EPERM:
                    # no permissions means the pid is probably
                    # running, but as a different user, so fail
                    module.fail_json(msg=message)
            else:
                daemon_running = True
        except ValueError:
            # invalid pid file, unlink it - otherwise we don't care
            try:
                os.unlink(pid_file)
            except:
                pass

    if daemon_running and multi_key:
        # try to connect to the file socket for the daemon if it exists
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            try:
                s.connect(SOCKET_FILE)
                s.sendall(password + '\n')
                data = ""
                while '\n' not in data:
                    data += s.recv(2048)
                res = data.strip()
            except:
                module.fail_json(msg="failed to connect to the local socket file")
        finally:
            try:
                s.close()
            except:
                pass

        if res in ("OK", "EXISTS"):
            module.exit_json(msg="transferred new key to the existing daemon")
        else:
            module.fail_json(msg="could not transfer new key: %s" % data.strip())
    else:
        # try to start up the daemon
        daemonize(module, password, port, timeout, minutes, ipv6, pid_file)

if __name__ == '__main__':
    main()
