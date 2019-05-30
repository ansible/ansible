"""Access Ansible Core CI remote services."""

from __future__ import absolute_import, print_function

import json
import os
import traceback
import uuid
import errno
import time
import shutil

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
    def __init__(self, args, platform, version, stage='prod', persist=True, load=True, name=None, provider=None):
        """
        :type args: EnvironmentConfig
        :type platform: str
        :type version: str
        :type stage: str
        :type persist: bool
        :type load: bool
        :type name: str
        """
        self.args = args
        self.platform = platform
        self.version = version
        self.stage = stage
        self.client = HttpClient(args)
        self.connection = None
        self.instance_id = None
        self.endpoint = None
        self.max_threshold = 1
        self.name = name if name else '%s-%s' % (self.platform, self.version)
        self.ci_key = os.path.expanduser('~/.ansible-core-ci.key')
        self.resource = 'jobs'

        # Assign each supported platform to one provider.
        # This is used to determine the provider from the platform when no provider is specified.
        providers = dict(
            aws=(
                'aws',
                'windows',
                'freebsd',
                'vyos',
                'junos',
                'ios',
                'tower',
                'rhel',
                'hetzner',
            ),
            azure=(
                'azure',
            ),
            parallels=(
                'osx',
            ),
        )

        if provider:
            # override default provider selection (not all combinations are valid)
            self.provider = provider
        else:
            for candidate in providers:
                if platform in providers[candidate]:
                    # assign default provider based on platform
                    self.provider = candidate
                    break
            for candidate in providers:
                if '%s/%s' % (platform, version) in providers[candidate]:
                    # assign default provider based on platform and version
                    self.provider = candidate
                    break

        self.path = os.path.expanduser('~/.ansible/test/instances/%s-%s-%s' % (self.name, self.provider, self.stage))

        if self.provider in ('aws', 'azure'):
            if self.provider != 'aws':
                self.resource = self.provider

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

            self.path = "%s-%s" % (self.path, region)
            self.endpoints = (AWS_ENDPOINTS[region],)
            self.ssh_key = SshKey(args)

            if self.platform == 'windows':
                self.port = 5986
            else:
                self.port = 22
        elif self.provider == 'parallels':
            self.endpoints = self._get_parallels_endpoints()
            self.max_threshold = 6

            self.ssh_key = SshKey(args)
            self.port = None
        else:
            raise ApplicationError('Unsupported platform: %s' % platform)

        if persist and load and self._load():
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
                self.endpoint = None
        elif not persist:
            self.instance_id = None
            self.endpoint = None
            self._clear()

        if self.instance_id:
            self.started = True
        else:
            self.started = False
            self.instance_id = str(uuid.uuid4())
            self.endpoint = None

            display.sensitive.add(self.instance_id)

    def _get_parallels_endpoints(self):
        """
        :rtype: tuple[str]
        """
        client = HttpClient(self.args, always=True)
        display.info('Getting available endpoints...', verbosity=1)
        sleep = 3

        for _ in range(1, 10):
            response = client.get('https://s3.amazonaws.com/ansible-ci-files/ansible-test/parallels-endpoints.txt')

            if response.status_code == 200:
                endpoints = tuple(response.response.splitlines())
                display.info('Available endpoints (%d):\n%s' % (len(endpoints), '\n'.join(' - %s' % endpoint for endpoint in endpoints)), verbosity=1)
                return endpoints

            display.warning('HTTP %d error getting endpoints, trying again in %d seconds.' % (response.status_code, sleep))
            time.sleep(sleep)

        raise ApplicationError('Unable to get available endpoints.')

    def start(self):
        """Start instance."""
        if self.started:
            display.info('Skipping started %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                         verbosity=1)
            return None

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

    def get(self, tries=3, sleep=15, always_raise_on=None):
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

            if self.connection.password:
                display.sensitive.add(str(self.connection.password))

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
        return '%s/%s/%s/%s' % (self.endpoint, self.stage, self.resource, self.instance_id)

    def _start(self, auth):
        """Start instance."""
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

        response = self._start_try_endpoints(data, headers)

        self.started = True
        self._save()

        display.info('Started %s/%s from: %s' % (self.platform, self.version, self._uri), verbosity=1)

        if self.args.explain:
            return {}

        return response.json()

    def _start_try_endpoints(self, data, headers):
        """
        :type data: dict[str, any]
        :type headers: dict[str, str]
        :rtype: HttpResponse
        """
        threshold = 1

        while threshold <= self.max_threshold:
            for self.endpoint in self.endpoints:
                try:
                    return self._start_at_threshold(data, headers, threshold)
                except CoreHttpError as ex:
                    if ex.status == 503:
                        display.info('Service Unavailable: %s' % ex.remote_message, verbosity=1)
                        continue
                    display.error(ex.remote_message)
                except HttpError as ex:
                    display.error(u'%s' % ex)

                time.sleep(3)

            threshold += 1

        raise ApplicationError('Maximum threshold reached and all endpoints exhausted.')

    def _start_at_threshold(self, data, headers, threshold):
        """
        :type data: dict[str, any]
        :type headers: dict[str, str]
        :type threshold: int
        :rtype: HttpResponse | None
        """
        tries = 3
        sleep = 15

        data['threshold'] = threshold

        display.info('Trying endpoint: %s (threshold %d)' % (self.endpoint, threshold), verbosity=1)

        while True:
            tries -= 1
            response = self.client.put(self._uri, data=json.dumps(data), headers=headers)

            if response.status_code == 200:
                return response

            error = self._create_http_error(response)

            if response.status_code == 503:
                raise error

            if not tries:
                raise error

            display.warning('%s. Trying again after %d seconds.' % (error, sleep))
            time.sleep(sleep)

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
                data = instance_fd.read()
        except IOError as ex:
            if ex.errno != errno.ENOENT:
                raise

            return False

        if not data.startswith('{'):
            return False  # legacy format

        config = json.loads(data)

        return self.load(config)

    def load(self, config):
        """
        :type config: dict[str, str]
        :rtype: bool
        """
        self.instance_id = str(config['instance_id'])
        self.endpoint = config['endpoint']
        self.started = True

        display.sensitive.add(self.instance_id)

        return True

    def _save(self):
        """Save instance information."""
        if self.args.explain:
            return

        config = self.save()

        make_dirs(os.path.dirname(self.path))

        with open(self.path, 'w') as instance_fd:
            instance_fd.write(json.dumps(config, indent=4, sort_keys=True))

    def save(self):
        """
        :rtype: dict[str, str]
        """
        return dict(
            platform_version='%s/%s' % (self.platform, self.version),
            instance_id=self.instance_id,
            endpoint=self.endpoint,
        )

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
                traceback_lines = response_json['stackTrace']

                # AWS Lambda on Python 2.7 returns a list of tuples
                # AWS Lambda on Python 3.7 returns a list of strings
                if traceback_lines and isinstance(traceback_lines[0], list):
                    traceback_lines = traceback.format_list(traceback_lines)

                trace = '\n'.join([x.rstrip() for x in traceback_lines])
                stack_trace = ('\nTraceback (from remote server):\n%s' % trace)
        else:
            message = str(response_json)

        return CoreHttpError(response.status_code, message, stack_trace)


class CoreHttpError(HttpError):
    """HTTP response as an error."""
    def __init__(self, status, remote_message, remote_stack_trace):
        """
        :type status: int
        :type remote_message: str
        :type remote_stack_trace: str
        """
        super(CoreHttpError, self).__init__(status, '%s%s' % (remote_message, remote_stack_trace))

        self.remote_message = remote_message
        self.remote_stack_trace = remote_stack_trace


class SshKey(object):
    """Container for SSH key used to connect to remote instances."""
    KEY_NAME = 'id_rsa'
    PUB_NAME = 'id_rsa.pub'

    def __init__(self, args):
        """
        :type args: EnvironmentConfig
        """
        cache_dir = 'test/cache'

        self.key = os.path.join(cache_dir, self.KEY_NAME)
        self.pub = os.path.join(cache_dir, self.PUB_NAME)

        if not os.path.isfile(self.key) or not os.path.isfile(self.pub):
            base_dir = os.path.expanduser('~/.ansible/test/')

            key = os.path.join(base_dir, self.KEY_NAME)
            pub = os.path.join(base_dir, self.PUB_NAME)

            if not args.explain:
                make_dirs(base_dir)

            if not os.path.isfile(key) or not os.path.isfile(pub):
                run_command(args, ['ssh-keygen', '-m', 'PEM', '-q', '-t', 'rsa', '-N', '', '-f', key])

            if not args.explain:
                shutil.copy2(key, self.key)
                shutil.copy2(pub, self.pub)

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
