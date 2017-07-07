"""Access Ansible Core CI remote services."""

from __future__ import absolute_import, print_function

import json
import os
import traceback
import uuid
import errno
import time

from lib.http import (
    HttpClient,
    HttpResponse,
    HttpError,
)

from lib.util import (
    ApplicationError,
    run_command,
    make_dirs,
    display,
    is_shippable,
)

from lib.config import (
    EnvironmentConfig,
)

AWS_ENDPOINTS = {
    'us-east-1': 'https://14blg63h2i.execute-api.us-east-1.amazonaws.com',
    'us-east-2': 'https://g5xynwbk96.execute-api.us-east-2.amazonaws.com',
}


class AnsibleCoreCI(object):
    """Client for Ansible Core CI services."""
    def __init__(self, args, platform, version, stage='prod', persist=True, name=None):
        """
        :type args: EnvironmentConfig
        :type platform: str
        :type version: str
        :type stage: str
        :type persist: bool
        :type name: str
        """
        self.args = args
        self.platform = platform
        self.version = version
        self.stage = stage
        self.client = HttpClient(args)
        self.connection = None
        self.instance_id = None
        self.name = name if name else '%s-%s' % (self.platform, self.version)
        self.ci_key = os.path.expanduser('~/.ansible-core-ci.key')

        aws_platforms = (
            'aws',
            'windows',
            'freebsd',
            'rhel',
            'vyos',
            'junos',
            'ios',
        )

        osx_platforms = (
            'osx',
        )

        if self.platform in aws_platforms:
            if args.remote_aws_region:
                # permit command-line override of region selection
                region = args.remote_aws_region
                # use a dedicated CI key when overriding the region selection
                self.ci_key += '.%s' % args.remote_aws_region
            elif is_shippable():
                # split Shippable jobs across multiple regions to maximize use of launch credits
                if self.platform == 'windows':
                    region = 'us-east-2'
                else:
                    region = 'us-east-1'
            else:
                # send all non-Shippable jobs to us-east-1 to reduce api key maintenance
                region = 'us-east-1'

            self.endpoint = AWS_ENDPOINTS[region]

            if self.platform == 'windows':
                self.ssh_key = None
                self.port = 5986
            else:
                self.ssh_key = SshKey(args)
                self.port = 22
        elif self.platform in osx_platforms:
            self.endpoint = 'https://osx.testing.ansible.com'

            self.ssh_key = SshKey(args)
            self.port = None
        else:
            raise ApplicationError('Unsupported platform: %s' % platform)

        self.path = os.path.expanduser('~/.ansible/test/instances/%s-%s' % (self.name, self.stage))

        if persist and self._load():
            try:
                display.info('Checking existing %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                             verbosity=1)

                self.connection = self.get(always_raise_on=[404])

                display.info('Loaded existing %s/%s from: %s' % (self.platform, self.version, self._uri), verbosity=1)
            except HttpError as ex:
                if ex.status != 404:
                    raise

                self._clear()

                display.info('Cleared stale %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                             verbosity=1)

                self.instance_id = None
        else:
            self.instance_id = None
            self._clear()

        if self.instance_id:
            self.started = True
        else:
            self.started = False
            self.instance_id = str(uuid.uuid4())

    def start(self):
        """Start instance."""
        if is_shippable():
            return self.start_shippable()

        return self.start_remote()

    def start_remote(self):
        """Start instance for remote development/testing."""
        with open(self.ci_key, 'r') as key_fd:
            auth_key = key_fd.read().strip()

        return self._start(dict(
            remote=dict(
                key=auth_key,
                nonce=None,
            ),
        ))

    def start_shippable(self):
        """Start instance on Shippable."""
        return self._start(dict(
            shippable=dict(
                run_id=os.environ['SHIPPABLE_BUILD_ID'],
                job_number=int(os.environ['SHIPPABLE_JOB_NUMBER']),
            ),
        ))

    def stop(self):
        """Stop instance."""
        if not self.started:
            display.info('Skipping invalid %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                         verbosity=1)
            return

        response = self.client.delete(self._uri)

        if response.status_code == 404:
            self._clear()
            display.info('Cleared invalid %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                         verbosity=1)
            return

        if response.status_code == 200:
            self._clear()
            display.info('Stopped running %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                         verbosity=1)
            return

        raise self._create_http_error(response)

    def get(self, tries=2, sleep=10, always_raise_on=None):
        """
        Get instance connection information.
        :type tries: int
        :type sleep: int
        :type always_raise_on: list[int] | None
        :rtype: InstanceConnection
        """
        if not self.started:
            display.info('Skipping invalid %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                         verbosity=1)
            return None

        if not always_raise_on:
            always_raise_on = []

        if self.connection and self.connection.running:
            return self.connection

        while True:
            tries -= 1
            response = self.client.get(self._uri)

            if response.status_code == 200:
                break

            error = self._create_http_error(response)

            if not tries or response.status_code in always_raise_on:
                raise error

            display.warning('%s. Trying again after %d seconds.' % (error, sleep))
            time.sleep(sleep)

        if self.args.explain:
            self.connection = InstanceConnection(
                running=True,
                hostname='cloud.example.com',
                port=self.port or 12345,
                username='username',
                password='password' if self.platform == 'windows' else None,
            )
        else:
            response_json = response.json()

            status = response_json['status']
            con = response_json['connection']

            self.connection = InstanceConnection(
                running=status == 'running',
                hostname=con['hostname'],
                port=int(con.get('port', self.port)),
                username=con['username'],
                password=con.get('password'),
            )

        status = 'running' if self.connection.running else 'starting'

        display.info('Status update: %s/%s on instance %s is %s.' %
                     (self.platform, self.version, self.instance_id, status),
                     verbosity=1)

        return self.connection

    def wait(self):
        """Wait for the instance to become ready."""
        for _ in range(1, 90):
            if self.get().running:
                return
            time.sleep(10)

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.platform, self.version, self.instance_id))

    @property
    def _uri(self):
        return '%s/%s/jobs/%s' % (self.endpoint, self.stage, self.instance_id)

    def _start(self, auth):
        """Start instance."""
        if self.started:
            display.info('Skipping started %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                         verbosity=1)
            return

        display.info('Initializing new %s/%s instance %s.' % (self.platform, self.version, self.instance_id), verbosity=1)

        if self.platform == 'windows':
            with open('examples/scripts/ConfigureRemotingForAnsible.ps1', 'rb') as winrm_config_fd:
                winrm_config = winrm_config_fd.read().decode('utf-8')
        else:
            winrm_config = None

        data = dict(
            config=dict(
                platform=self.platform,
                version=self.version,
                public_key=self.ssh_key.pub_contents if self.ssh_key else None,
                query=False,
                winrm_config=winrm_config,
            )
        )

        data.update(dict(auth=auth))

        headers = {
            'Content-Type': 'application/json',
        }

        tries = 2
        sleep = 10

        while True:
            tries -= 1
            response = self.client.put(self._uri, data=json.dumps(data), headers=headers)

            if response.status_code == 200:
                break

            error = self._create_http_error(response)

            if not tries:
                raise error

            display.warning('%s. Trying again after %d seconds.' % (error, sleep))
            time.sleep(sleep)

        self.started = True
        self._save()

        display.info('Started %s/%s from: %s' % (self.platform, self.version, self._uri), verbosity=1)

        if self.args.explain:
            return {}

        return response.json()

    def _clear(self):
        """Clear instance information."""
        try:
            self.connection = None
            os.remove(self.path)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise

    def _load(self):
        """Load instance information."""
        try:
            with open(self.path, 'r') as instance_fd:
                self.instance_id = instance_fd.read()
                self.started = True
        except IOError as ex:
            if ex.errno != errno.ENOENT:
                raise
            self.instance_id = None

        return self.instance_id

    def _save(self):
        """Save instance information."""
        if self.args.explain:
            return

        make_dirs(os.path.dirname(self.path))

        with open(self.path, 'w') as instance_fd:
            instance_fd.write(self.instance_id)

    @staticmethod
    def _create_http_error(response):
        """
        :type response: HttpResponse
        :rtype: ApplicationError
        """
        response_json = response.json()
        stack_trace = ''

        if 'message' in response_json:
            message = response_json['message']
        elif 'errorMessage' in response_json:
            message = response_json['errorMessage'].strip()
            if 'stackTrace' in response_json:
                trace = '\n'.join([x.rstrip() for x in traceback.format_list(response_json['stackTrace'])])
                stack_trace = ('\nTraceback (from remote server):\n%s' % trace)
        else:
            message = str(response_json)

        return HttpError(response.status_code, '%s%s' % (message, stack_trace))


class SshKey(object):
    """Container for SSH key used to connect to remote instances."""
    def __init__(self, args):
        """
        :type args: EnvironmentConfig
        """
        tmp = os.path.expanduser('~/.ansible/test/')

        self.key = os.path.join(tmp, 'id_rsa')
        self.pub = os.path.join(tmp, 'id_rsa.pub')

        if not os.path.isfile(self.pub):
            if not args.explain:
                make_dirs(tmp)

            run_command(args, ['ssh-keygen', '-q', '-t', 'rsa', '-N', '', '-f', self.key])

        if args.explain:
            self.pub_contents = None
        else:
            with open(self.pub, 'r') as pub_fd:
                self.pub_contents = pub_fd.read().strip()


class InstanceConnection(object):
    """Container for remote instance status and connection details."""
    def __init__(self, running, hostname, port, username, password):
        """
        :type running: bool
        :type hostname: str
        :type port: int
        :type username: str
        :type password: str | None
        """
        self.running = running
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

    def __str__(self):
        if self.password:
            return '%s:%s [%s:%s]' % (self.hostname, self.port, self.username, self.password)

        return '%s:%s [%s]' % (self.hostname, self.port, self.username)
