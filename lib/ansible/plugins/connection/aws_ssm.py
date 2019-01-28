# Based on the ssh connection plugin by Michael DeHaan
#
# Copyright: (c) 2018, Pat Sharkey <psharkey@cleo.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
author: psharkey@cleo.com
connection: aws_ssm
short_description: execute via AWS Systems Manager
description:
- This connection plugin allows ansible to execute tasks on an EC2 instance via the aws ssm CLI.
version_added: "2.8"
requirements:
- The control machine and the remote EC2 instance must have the aws CLI installed.
- The control machine and the remote EC2 instance must have access to the S3 bucket.
- The control machine must have the aws session manager plugin installed.
options:
  instance_id:
    description: The EC2 instance ID.
    vars:
    - name: instance_id
    - name: aws_instance_id
  region:
    description: The region the EC2 instance is located.
    vars:
    - name: region
    - name: aws_region
    default: 'us-east-1'
  bucket_name:
    description: The name of the S3 bucket used for file transfers.
    vars:
    - name: bucket_name
  executable:
    description: This defines the location of the aws binary.
    vars:
    - name: aws_executable
    default: '/usr/local/bin/aws'
  retries:
    description: Number of attempts to connect.
    default: 3
    type: integer
    vars:
    - name: ansible_ssm_retries
  timeout:
    description: Connection timeout seconds.
    default: 60
    type: integer
    vars:
    - name: ansible_ssm_timeout
"""

import os
import getpass
import random
import select
import string
import subprocess
import time

from functools import wraps
from ansible import constants as C
from ansible.errors import AnsibleConnectionFailure, AnsibleError, AnsibleFileNotFound
from ansible.module_utils.six.moves import xrange
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

display = Display()


def _ssm_retry(func):
    """
    Decorator to retry in the case of a connection failure
    Will retry if:
    * an exception is caught
    Will not retry if
    * remaining_tries is <2
    * retries limit reached
    """
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        remaining_tries = int(self.get_option('retries')) + 1
        cmd_summary = "%s..." % args[0]
        for attempt in range(remaining_tries):
            cmd = args[0]

            try:
                return_tuple = func(self, *args, **kwargs)
                display.vvv(return_tuple, host=self.host)
                break

            except (AnsibleConnectionFailure, Exception) as e:
                if attempt == remaining_tries - 1:
                    raise
                else:
                    pause = 2 ** attempt - 1
                    if pause > 30:
                        pause = 30

                    if isinstance(e, AnsibleConnectionFailure):
                        msg = "ssm_retry: attempt: %d, cmd (%s), pausing for %d seconds" % (attempt, cmd_summary, pause)
                    else:
                        msg = "ssm_retry: attempt: %d, caught exception(%s) from cmd (%s), pausing for %d seconds" % (attempt, e, cmd_summary, pause)

                    display.vv(msg, host=self.host)

                    time.sleep(pause)

                    # Do not attempt to reuse the existing session on retries
                    self.close()

                    continue

        return return_tuple
    return wrapped


class Connection(ConnectionBase):
    ''' AWS SSM based connections '''

    transport = 'aws_ssm'
    has_pipelining = False
    _session = None
    _session_id = ''
    _timeout = False
    MARK_LENGTH = 52
    SESSION_START = 'Starting session with SessionId:'

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

        self.host = self._play_context.remote_addr

    def _connect(self):
        ''' connect to the host via ssm '''

        self._play_context.remote_user = getpass.getuser()

        if not self._connected:
            self.start_session()
            self._connected = True
        return self

    def start_session(self):
        ''' start ssm session '''

        display.vvv(u"ESTABLISH SSM CONNECTION TO: {0}".format(self.get_option('instance_id')), host=self.host)

        executable = self.get_option('executable')
        if not os.path.exists(to_bytes(executable, errors='surrogate_or_strict')):
            raise AnsibleError("failed to find the executable specified %s."
                               " Please verify if the executable exists and re-try." % executable)

        cmd = [
            executable, 'ssm', 'start-session',
            '--target', self.get_option('instance_id'),
            '--region', self.get_option('region')
        ]

        display.vvv(u"SSM COMMAND: {0}".format(to_text(cmd)), host=self.host)

        session = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Disable command echo and prompt.
        session.stdin.write("stty -echo\n")
        session.stdin.write("PS1=''\n")

        self._session = session
        self._poll_stdout = select.poll()
        self._poll_stdout.register(session.stdout, select.POLLIN)

        # Get session ID e.g.: Starting session with SessionId: i-0581917898742e40f-0112e9036923cb673
        while session.poll() is None:
            line = self._stdin_readline()
            if self.SESSION_START in line:
                self._session_id = line.split(self.SESSION_START)[1].strip()
                break

        display.vvv(u"SSM CONNECTION ID: {0}".format(self._session_id), host=self.host)

        return session

    @_ssm_retry
    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the ssm host '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.vvv(u"EXEC {0}".format(to_text(cmd)), host=self.host)

        session = self._session

        mark_start = "".join([random.choice(string.letters) for i in xrange(self.MARK_LENGTH)])
        mark_end = "".join([random.choice(string.letters) for i in xrange(self.MARK_LENGTH)])

        # Echo start marker.
        session.stdin.write("echo '" + mark_start + "'\n")
        self._flush_stderr(session)

        # Send the command
        session.stdin.write(cmd + "\n")

        # echo command status and end marker
        session.stdin.write("echo $'\\n'$?\n")
        session.stdin.write("echo '" + mark_end + "'\n")

        # Read stdout between the markers
        stdout = ''
        begin = False
        stop_time = int(round(time.time())) + self.get_option('timeout')
        while session.poll() is None:
            remaining = stop_time - int(round(time.time()))
            if remaining < 1:
                self._timeout = True
                raise AnsibleConnectionFailure("SSM exec_command timeout on host: %s"
                                           % self.get_option('instance_id'))
            if self._poll_stdout.poll(1000):
                line = self._session.stdout.readline()
                display.vvvv(u"EXEC stdout line: {0}".format(to_text(line)), host=self.host)
            else:
                display.vvvv(u"EXEC remaining: {0}".format(remaining), host=self.host)
                continue

            if mark_start in line:
                begin = True
                continue
            if begin:
                if line.startswith(mark_end):
                    # Get command return code and throw away ending lines
                    returncode = stdout.splitlines()[-1]
                    for x in range(0, 3):
                        stdout = stdout[:stdout.rfind('\n')]
                    break
                elif begin:
                    stdout = stdout + line

        stderr = self._flush_stderr(session)

        return (int(returncode), stdout, stderr)

    def _stdin_readline(self):
        poll_timeout = self.get_option('timeout') * 1000
        if self._poll_stdout.poll(poll_timeout):
            line = self._session.stdout.readline()
            display.vvvv(u"stdout line: {0}".format(to_text(line)), host=self.host)
            return line
        else:
            self._timeout = True
            raise AnsibleConnectionFailure("SSM connection failure on host: %s"
                                           % self.get_option('instance_id'))

    def _flush_stderr(self, subprocess):
        ''' read and return stderr with minimal blocking '''

        poll_stderr = select.poll()
        poll_stderr.register(subprocess.stderr, select.POLLIN)
        stderr = ''

        while subprocess.poll() is None:
            if poll_stderr.poll(1):
                line = subprocess.stderr.readline()
                display.vvvv(u"stderr line: {0}".format(to_text(line)), host=self.host)
                stderr = stderr + line
            else:
                break

        return stderr

    @_ssm_retry
    def _file_transport_command(self, in_path, out_path, ssm_action):
        ''' transfer a file from using an intermediate S3 bucket '''

        bucket_url = 's3://%s/%s' % (self.get_option('bucket_name'), out_path)
        command = 'aws s3 cp %s %s'

        if ssm_action == 'get':
            (returncode, stdout, stderr) = self.exec_command(command % (in_path, bucket_url), in_data=None, sudoable=False)
            subprocess.check_output(command % (bucket_url, out_path), shell=True)
        else:
            subprocess.check_output(command % (in_path, bucket_url), shell=True)
            (returncode, stdout, stderr) = self.exec_command(command % (bucket_url, out_path), in_data=None, sudoable=False)

        # Check the return code
        if returncode == 0:
            return (returncode, stdout, stderr)
        else:
            raise AnsibleError("failed to transfer file to %s %s:\n%s\n%s" %
                               (to_native(in_path), to_native(out_path), to_native(stdout), to_native(stderr)))

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        super(Connection, self).put_file(in_path, out_path)

        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self.host)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_native(in_path)))

        return self._file_transport_command(in_path, out_path, 'put')

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self.host)
        return self._file_transport_command(in_path, out_path, 'get')

    def close(self):
        ''' terminate the connection '''
        if self.connected:

            display.vvv(u"CLOSING SSM CONNECTION TO: {0}".format(self.get_option('instance_id')), host=self.host)
            if self._timeout:
                self._session.terminate()
            else:
                self._session.communicate("exit\n")

            # Ensure session is terminated
            cmd = [
                self.get_option('executable'), 'ssm', 'terminate-session',
                '--session-id', self._session_id,
                '--region', self.get_option('region')
            ]

            display.vvvv(u"TERMINATE SSM SESSION: {0}".format(cmd), host=self.host)
            subprocess.check_output(cmd)

            self._connected = False
