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
  plugin:
    description: This defines the location of the session-manager-plugin binary.
    vars:
    - name: session_manager_plugin
    default: '/usr/local/bin/session-manager-plugin'
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
import boto3
import getpass
import json
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
    _client = None
    _session = None
    _session_id = ''
    _timeout = False
    MARK_LENGTH = 26
    SESSION_START = 'Starting session with SessionId:'

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

        self.host = self._play_context.remote_addr

    def _connect(self):
        ''' connect to the host via ssm '''

        self._play_context.remote_user = getpass.getuser()

        if not self._session_id:
            self.start_session()
        return self

    def start_session(self):
        ''' start ssm session '''

        display.vvv(u"ESTABLISH SSM CONNECTION TO: {0}".format(self.get_option('instance_id')), host=self.host)

        executable = self.get_option('plugin')
        if not os.path.exists(to_bytes(executable, errors='surrogate_or_strict')):
            raise AnsibleError("failed to find the executable specified %s."
                               " Please verify if the executable exists and re-try." % executable)

        profile_name = ''
        region_name = self.get_option('region')
        ssm_parameters = dict()

        client = boto3.client('ssm', region_name=region_name)
        self._client = client
        response = client.start_session(Target=self.get_option('instance_id'), Parameters=ssm_parameters)
        self._session_id = response['SessionId']

        cmd = [
            executable,
            json.dumps(response),
            region_name,
            "StartSession",
            profile_name,
            json.dumps(ssm_parameters),
            client.meta.endpoint_url
        ]

        display.vvv(u"SSM COMMAND: {0}".format(to_text(cmd)), host=self.host)

        session = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            bufsize=0,
        )

        # Disable command echo and prompt.
        session.stdin.write("stty -echo\n")
        session.stdin.write("PS1=''\n")

        self._session = session
        self._poll_stdout = select.poll()
        self._poll_stdout.register(session.stdout, select.POLLIN)

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
        if sudoable == True:
            cmd = "sudo " + cmd

        # Handle the back-end throttling 
        for c in cmd:
            session.stdin.write(c)
            time.sleep(10 / 1000.0)
        session.stdin.write("\n")

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
                display.vvvv(u"EXEC timeout stdout: {0}".format(to_text(stdout)), host=self.host)
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
                if mark_end in line:
                    # Get command return code and throw away ending lines
                    returncode = stdout.splitlines()[-1]
                    for x in range(0, 3):
                        stdout = stdout[:stdout.rfind('\n')]
                    break
                else:
                    stdout = stdout + line

        stderr = self._flush_stderr(session)

        return (int(returncode), stdout, stderr)

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

    def _get_url(self, client_method, bucket_name, out_path, http_method):
        ''' Generate URL for get_object / put_object '''
        client = boto3.client('s3')
        url = client.generate_presigned_url(client_method, Params={'Bucket': bucket_name, 'Key': out_path}, ExpiresIn=3600, HttpMethod=http_method)
        return (url.encode())

    @_ssm_retry
    def _file_transport_command(self, in_path, out_path, ssm_action):
        ''' transfer a file from using an intermediate S3 bucket '''

        bucket_url = 's3://%s/%s' % (self.get_option('bucket_name'), out_path)
        put_command = 'curl --request PUT --upload-file %s "%s"' % (in_path, self._get_url('put_object', self.get_option('bucket_name'), out_path, 'PUT'))
        get_command = 'curl -v "%s" -o %s' % (self._get_url('get_object', self.get_option('bucket_name'), out_path, 'GET'), out_path)

        if ssm_action == 'get':
            (returncode, stdout, stderr) = self.exec_command(put_command, in_data=None, sudoable=False)
            subprocess.check_output(get_command, shell=True)
        else:
            subprocess.check_output(put_command, shell=True)
            (returncode, stdout, stderr) = self.exec_command(get_command, in_data=None, sudoable=False)

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
        if self._session_id:

            display.vvv(u"CLOSING SSM CONNECTION TO: {0}".format(self.get_option('instance_id')), host=self.host)
            if self._timeout:
                self._session.terminate()
            else:
                self._session.communicate("exit\n")

            display.vvvv(u"TERMINATE SSM SESSION: {0}".format(self._session_id), host=self.host)
            self._client.terminate_session(SessionId=self._session_id)
            self._session_id = ''
