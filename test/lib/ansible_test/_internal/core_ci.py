"""Access Ansible Core CI remote services."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import re
import traceback
import uuid
import errno
import time

from . import types as t

from .http import (
    HttpClient,
    HttpResponse,
    HttpError,
)

from .io import (
    make_dirs,
    read_text_file,
    write_json_file,
    write_text_file,
)

from .util import (
    ApplicationError,
    display,
    ANSIBLE_TEST_DATA_ROOT,
)

from .util_common import (
    run_command,
    ResultType,
)

from .config import (
    EnvironmentConfig,
)

from .ci import (
    AuthContext,
    get_ci_provider,
)

from .data import (
    data_context,
)

AWS_ENDPOINTS = {
    'us-east-1': 'https://ansible-core-ci.testing.ansible.com',
}


class AnsibleCoreCI:
    """Client for Ansible Core CI services."""
    def __init__(self, args, platform, version, stage='prod', persist=True, load=True, provider=None, arch=None):
        """
        :type args: EnvironmentConfig
        :type platform: str
        :type version: str
        :type stage: str
        :type persist: bool
        :type load: bool
        :type provider: str | None
        :type arch: str | None
        """
        self.args = args
        self.arch = arch
        self.platform = platform
        self.version = version
        self.stage = stage
        self.client = HttpClient(args)
        self.connection = None
        self.instance_id = None
        self.endpoint = None
        self.max_threshold = 1
        self.retries = 3
        self.ci_provider = get_ci_provider()
        self.auth_context = AuthContext()

        if self.arch:
            self.name = '%s-%s-%s' % (self.arch, self.platform, self.version)
        else:
            self.name = '%s-%s' % (self.platform, self.version)

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
            ibmps=(
                'aix',
                'ibmi',
            ),
            ibmvpc=(
                'centos arch=power',  # avoid ibmvpc as default for no-arch centos to avoid making centos default to power
            ),
            parallels=(
                'macos',
                'osx',
            ),
        )

        # Currently ansible-core-ci has no concept of arch selection. This effectively means each provider only supports one arch.
        # The list below identifies which platforms accept an arch, and which one. These platforms can only be used with the specified arch.
        provider_arches = dict(
            ibmvpc='power',
        )

        if provider:
            # override default provider selection (not all combinations are valid)
            self.provider = provider
        else:
            self.provider = None

            for candidate in providers:
                choices = [
                    platform,
                    '%s arch=%s' % (platform, arch),
                ]

                if any(choice in providers[candidate] for choice in choices):
                    # assign default provider based on platform
                    self.provider = candidate
                    break

        # If a provider has been selected, make sure the correct arch (or none) has been selected.
        if self.provider:
            required_arch = provider_arches.get(self.provider)

            if self.arch != required_arch:
                if required_arch:
                    if self.arch:
                        raise ApplicationError('Provider "%s" requires the "%s" arch instead of "%s".' % (self.provider, required_arch, self.arch))

                    raise ApplicationError('Provider "%s" requires the "%s" arch.' % (self.provider, required_arch))

                raise ApplicationError('Provider "%s" does not support specification of an arch.' % self.provider)

        self.path = os.path.expanduser('~/.ansible/test/instances/%s-%s-%s' % (self.name, self.provider, self.stage))

        if self.provider in ('aws', 'azure', 'ibmps', 'ibmvpc'):
            if args.remote_aws_region:
                display.warning('The --remote-aws-region option is obsolete and will be removed in a future version of ansible-test.')
                # permit command-line override of region selection
                region = args.remote_aws_region
                # use a dedicated CI key when overriding the region selection
                self.auth_context.region = args.remote_aws_region
            else:
                region = 'us-east-1'

            self.path = "%s-%s" % (self.path, region)

            if self.args.remote_endpoint:
                self.endpoints = (self.args.remote_endpoint,)
            else:
                self.endpoints = (AWS_ENDPOINTS[region],)

            self.ssh_key = SshKey(args)

            if self.platform == 'windows':
                self.port = 5986
            else:
                self.port = 22

            if self.provider == 'ibmps':
                # Additional retries are neededed to accommodate images transitioning
                # to the active state in the IBM cloud. This operation can take up to
                # 90 seconds
                self.retries = 7
        elif self.provider == 'parallels':
            if self.args.remote_endpoint:
                self.endpoints = (self.args.remote_endpoint,)
            else:
                self.endpoints = (AWS_ENDPOINTS['us-east-1'],)

            self.ssh_key = SshKey(args)
            self.port = None
        else:
            if self.arch:
                raise ApplicationError('Provider not detected for platform "%s" on arch "%s".' % (self.platform, self.arch))

            raise ApplicationError('Provider not detected for platform "%s" with no arch specified.' % self.platform)

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

        for _iteration in range(1, 10):
            response = client.get('https://ansible-ci-files.s3.amazonaws.com/ansible-test/parallels-endpoints.txt')

            if response.status_code == 200:
                endpoints = tuple(response.response.splitlines())
                display.info('Available endpoints (%d):\n%s' % (len(endpoints), '\n'.join(' - %s' % endpoint for endpoint in endpoints)), verbosity=1)
                return endpoints

            display.warning('HTTP %d error getting endpoints, trying again in %d seconds.' % (response.status_code, sleep))
            time.sleep(sleep)

        raise ApplicationError('Unable to get available endpoints.')

    @property
    def available(self):
        """Return True if Ansible Core CI is supported."""
        return self.ci_provider.supports_core_ci_auth(self.auth_context)

    def start(self):
        """Start instance."""
        if self.started:
            display.info('Skipping started %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                         verbosity=1)
            return None

        return self._start(self.ci_provider.prepare_core_ci_auth(self.auth_context))

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
            con = response_json.get('connection')

            if con:
                self.connection = InstanceConnection(
                    running=status == 'running',
                    hostname=con['hostname'],
                    port=int(con.get('port', self.port)),
                    username=con['username'],
                    password=con.get('password'),
                    response_json=response_json,
                )
            else:
                self.connection = InstanceConnection(
                    running=status == 'running',
                    response_json=response_json,
                )

        if self.connection.password:
            display.sensitive.add(str(self.connection.password))

        status = 'running' if self.connection.running else 'starting'

        display.info('Status update: %s/%s on instance %s is %s.' %
                     (self.platform, self.version, self.instance_id, status),
                     verbosity=1)

        return self.connection

    def wait(self, iterations=90):  # type: (t.Optional[int]) -> None
        """Wait for the instance to become ready."""
        for _iteration in range(1, iterations):
            if self.get().running:
                return
            time.sleep(10)

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.platform, self.version, self.instance_id))

    @property
    def _uri(self):
        return '%s/%s/%s/%s' % (self.endpoint, self.stage, self.provider, self.instance_id)

    def _start(self, auth):
        """Start instance."""
        display.info('Initializing new %s/%s instance %s.' % (self.platform, self.version, self.instance_id), verbosity=1)

        if self.platform == 'windows':
            winrm_config = read_text_file(os.path.join(ANSIBLE_TEST_DATA_ROOT, 'setup', 'ConfigureRemotingForAnsible.ps1'))
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
        tries = self.retries
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
            data = read_text_file(self.path)
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

        write_json_file(self.path, config, create_directories=True)

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


class SshKey:
    """Container for SSH key used to connect to remote instances."""
    KEY_NAME = 'id_rsa'
    PUB_NAME = 'id_rsa.pub'

    def __init__(self, args):
        """
        :type args: EnvironmentConfig
        """
        key_pair = self.get_key_pair()

        if not key_pair:
            key_pair = self.generate_key_pair(args)

        key, pub = key_pair
        key_dst, pub_dst = self.get_in_tree_key_pair_paths()

        def ssh_key_callback(files):  # type: (t.List[t.Tuple[str, str]]) -> None
            """
            Add the SSH keys to the payload file list.
            They are either outside the source tree or in the cache dir which is ignored by default.
            """
            files.append((key, os.path.relpath(key_dst, data_context().content.root)))
            files.append((pub, os.path.relpath(pub_dst, data_context().content.root)))

        data_context().register_payload_callback(ssh_key_callback)

        self.key, self.pub = key, pub

        if args.explain:
            self.pub_contents = None
        else:
            self.pub_contents = read_text_file(self.pub).strip()

    def get_in_tree_key_pair_paths(self):  # type: () -> t.Optional[t.Tuple[str, str]]
        """Return the ansible-test SSH key pair paths from the content tree."""
        temp_dir = ResultType.TMP.path

        key = os.path.join(temp_dir, self.KEY_NAME)
        pub = os.path.join(temp_dir, self.PUB_NAME)

        return key, pub

    def get_source_key_pair_paths(self):  # type: () -> t.Optional[t.Tuple[str, str]]
        """Return the ansible-test SSH key pair paths for the current user."""
        base_dir = os.path.expanduser('~/.ansible/test/')

        key = os.path.join(base_dir, self.KEY_NAME)
        pub = os.path.join(base_dir, self.PUB_NAME)

        return key, pub

    def get_key_pair(self):  # type: () -> t.Optional[t.Tuple[str, str]]
        """Return the ansible-test SSH key pair paths if present, otherwise return None."""
        key, pub = self.get_in_tree_key_pair_paths()

        if os.path.isfile(key) and os.path.isfile(pub):
            return key, pub

        key, pub = self.get_source_key_pair_paths()

        if os.path.isfile(key) and os.path.isfile(pub):
            return key, pub

        return None

    def generate_key_pair(self, args):  # type: (EnvironmentConfig) -> t.Tuple[str, str]
        """Generate an SSH key pair for use by all ansible-test invocations for the current user."""
        key, pub = self.get_source_key_pair_paths()

        if not args.explain:
            make_dirs(os.path.dirname(key))

        if not os.path.isfile(key) or not os.path.isfile(pub):
            run_command(args, ['ssh-keygen', '-m', 'PEM', '-q', '-t', 'rsa', '-N', '', '-f', key])

            # newer ssh-keygen PEM output (such as on RHEL 8.1) is not recognized by paramiko
            key_contents = read_text_file(key)
            key_contents = re.sub(r'(BEGIN|END) PRIVATE KEY', r'\1 RSA PRIVATE KEY', key_contents)

            write_text_file(key, key_contents)

        return key, pub


class InstanceConnection:
    """Container for remote instance status and connection details."""
    def __init__(self,
                 running,  # type: bool
                 hostname=None,  # type: t.Optional[str]
                 port=None,  # type: t.Optional[int]
                 username=None,  # type: t.Optional[str]
                 password=None,  # type: t.Optional[str]
                 response_json=None,  # type: t.Optional[t.Dict[str, t.Any]]
                 ):  # type: (...) -> None
        self.running = running
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.response_json = response_json or {}

    def __str__(self):
        if self.password:
            return '%s:%s [%s:%s]' % (self.hostname, self.port, self.username, self.password)

        return '%s:%s [%s]' % (self.hostname, self.port, self.username)
