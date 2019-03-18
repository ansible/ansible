# Based on the ssh connection plugin by Michael DeHaan
#
# Copyright: (c) 2018, Pat Sharkey <psharkey@cleo.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
author:
- Pat Sharkey (@psharkey) <psharkey@cleo.com>
- HanumanthaRao MVL (@hanumantharaomvl) <hanumanth@flux7.com>
- Gaurav Ashtikar (@gau1991 )<gaurav.ashtikar@flux7.com>
connection: aws_ssm
short_description: execute via AWS Systems Manager
description:
- This connection plugin allows ansible to execute tasks on an EC2 instance via the aws ssm CLI.
version_added: "2.8"
requirements:
- The remote EC2 instance must be running the AWS Systems Manager Agent (SSM Agent).
- The control machine must have the aws session manager plugin installed.
- The remote EC2 instance must have the curl installed.
options:
  instance_id:
    description: The EC2 instance ID.
    vars:
    - name: ansible_aws_ssm_instance_id
  region:
    description: The region the EC2 instance is located.
    vars:
    - name: ansible_aws_ssm_region
    default: 'us-east-1'
  bucket_name:
    description: The name of the S3 bucket used for file transfers.
    vars:
    - name: ansible_aws_ssm_bucket_name
  plugin:
    description: This defines the location of the session-manager-plugin binary.
    vars:
    - name: ansible_aws_ssm_plugin
    default: '/usr/local/bin/session-manager-plugin'
  retries:
    description: Number of attempts to connect.
    default: 3
    type: integer
    vars:
    - name: ansible_aws_ssm_retries
  timeout:
    description: Connection timeout seconds.
    default: 60
    type: integer
    vars:
    - name: ansible_ssm_timeout
"""

EXAMPLES = '''

# Stop Spooler Process on Windows Instances
- name: Stop Spooler Service on Windows Instances
  vars:
    ansible_connection: aws_ssm
    ansible_shell_executable: powershell
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-east-1
  tasks:
    - name: Stop spooler service
      win_service:
        name: spooler
        state: stopped

# Install a Nginx Package on Linux Instance
- name: Install a Nginx Package
  vars:
    ansible_connection: aws_ssm
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-west-2
  tasks:
    - name: Install a Nginx Package
      yum:
        name: nginx
        state: present

# Create a directory in Windows Instances
- name: Create a directory in Windows Instance
  vars:
    ansible_connection: aws_ssm
    ansible_shell_executable: powershell
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-east-1
  tasks:
    - name: Create a Directory
      win_file:
        path: "Windows path here"
        state: directory
'''

import os
import boto3
import getpass
import json
import os
import pty
import random
import re
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
    allow_executable = False
    allow_extras = True
    has_pipelining = False
    is_windows = False
    _client = None
    _session = None
    _stdout = None
    _session_id = ''
    _timeout = False
    MARK_LENGTH = 26

    def __init__(self, *args, **kwargs):

        super(Connection, self).__init__(*args, **kwargs)
        self.host = self._play_context.remote_addr

        if getattr(self._shell, "SHELL_FAMILY", '') == 'powershell':
            self.delegate = None
            self.has_native_async = True
            self.always_pipeline_modules = True
            self.module_implementation_preferences = ('.ps1', '.exe', '')
            self.protocol = None
            self.shell_id = None

    def _connect(self):
        ''' connect to the host via ssm '''

        self._play_context.remote_user = getpass.getuser()

        if getattr(self._shell, "SHELL_FAMILY", '') == 'powershell':
            self.is_windows = True
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

        display.vvvv(u"SSM COMMAND: {0}".format(to_text(cmd)), host=self.host)

        stdout_r, stdout_w = pty.openpty()
        session = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=stdout_w,
            stderr=subprocess.PIPE,
            close_fds=True,
            bufsize=0,
        )

        os.close(stdout_w)
        self._stdout = os.fdopen(stdout_r, 'rb', 0)
        self._session = session
        self._poll_stdout = select.poll()
        self._poll_stdout.register(self._stdout, select.POLLIN)

        # Disable command echo and prompt.
        self._prepare_terminal()

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

        # Wrap command in markers accordingly for the shell used
        cmd = self._wrap_command(cmd, sudoable, mark_start, mark_end)

        self._flush_stderr(session)

        # Handle the back-end throttling
        display.vvvvv(u"EXEC write: '{0}'".format(to_text(cmd)), host=self.host)
        for c in cmd.encode('utf-8'):
            session.stdin.write(c)
            time.sleep(10 / 1000.0)

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
                line = self._filter_ansi(self._stdout.readline())
                display.vvvv(u"EXEC stdout line: {0}".format(to_text(line)), host=self.host)
            else:
                display.vvvv(u"EXEC remaining: {0}".format(remaining), host=self.host)
                continue

            if mark_start in line:
                begin = True
                if not line.startswith(mark_start):
                    stdout = ''
                continue
            if begin:
                if mark_end in line:
                    for line in stdout.splitlines():
                        display.vvvvv(u"POST_PROCESS: {0}".format(to_text(line)), host=self.host)
                    returncode, stdout = self._post_process(stdout)
                    break
                else:
                    stdout = stdout + line

        stderr = self._flush_stderr(session)

        return (returncode, stdout, stderr)

    def _prepare_terminal(self):
        ''' perform any one-time terminal settings '''

        if not self.is_windows:
            self._session.stdin.write("stty -echo\n")
            self._session.stdin.write("PS1=''\n")

    def _wrap_command(self, cmd, sudoable, mark_start, mark_end):
        ''' wrap commad so stdout and status can be extracted '''

        if self.is_windows:
            return cmd + "; echo $? $LASTEXITCODE; echo '" + mark_start + "'\n" + "echo '" + mark_end + "'\n"
        else:
            if sudoable:
                cmd = "sudo " + cmd
            return "echo '" + mark_start + "'\n" + cmd + "\necho $'\\n'$?\n" + "echo '" + mark_end + "'\n"

    def _post_process(self, stdout):
        ''' extract command status and strip unwanted lines '''

        if self.is_windows:
            success = stdout.rfind('True')
            fail = stdout.rfind('False')

            if success > fail:
                returncode = 0
                stdout = stdout[:success]
            elif fail > success:
                try:
                    # test using: ansible -m raw -a 'cmd /c exit 99'
                    returncode = int(stdout[fail:].split()[1])
                except (IndexError, ValueError):
                    returncode = -1
                stdout = stdout[:fail]
            else:
                returncode = -51

            return (returncode, stdout)
        else:
            # Get command return code
            returncode = int(stdout.splitlines()[-2])

            # Throw away ending lines
            for x in range(0, 3):
                stdout = stdout[:stdout.rfind('\n')]

            return (returncode, stdout)

    def _filter_ansi(self, line):
        ''' remove any ANSI terminal control codes '''

        if self.is_windows:
            ansi_filter = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
            line = ansi_filter.sub('', line)

            # Replace or strip sequence (at terminal width)
            line = line.replace('\r\r\n', '\n')
            if len(line) == 201:
                line = line[:-1]

        return line

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
        return client.generate_presigned_url(client_method, Params={'Bucket': bucket_name, 'Key': out_path}, ExpiresIn=3600, HttpMethod=http_method)

    @_ssm_retry
    def _file_transport_command(self, in_path, out_path, ssm_action):
        ''' transfer a file from using an intermediate S3 bucket '''

        s3_path = out_path.replace('\\', '/')
        bucket_url = 's3://%s/%s' % (self.get_option('bucket_name'), s3_path)

        if self.is_windows:
            put_command = "curl -Method PUT -InFile '%s' -Uri '%s'" % (in_path, self._get_url('put_object', self.get_option('bucket_name'), s3_path, 'PUT'))
        else:
            put_command = "curl --request PUT --upload-file '%s' '%s'" % (in_path, self._get_url('put_object', self.get_option('bucket_name'), s3_path, 'PUT'))

        get_command = "curl '%s' -o '%s'" % (self._get_url('get_object', self.get_option('bucket_name'), s3_path, 'GET'), out_path)

        client = boto3.client('s3')
        if ssm_action == 'get':
            (returncode, stdout, stderr) = self.exec_command(put_command, in_data=None, sudoable=False)
            with open(out_path.encode('utf-8'), 'wb') as data:
                client.download_fileobj(self.get_option('bucket_name'), s3_path, data)
        else:
            with open(in_path.encode('utf-8'), 'rb') as data:
                client.upload_fileobj(data, self.get_option('bucket_name'), s3_path)
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
