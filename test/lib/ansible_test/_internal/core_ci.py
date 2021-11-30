"""Access Ansible Core CI remote services."""
from __future__ import annotations

import json
import os
import re
import traceback
import uuid
import errno
import time
import typing as t

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
    ANSIBLE_TEST_TARGET_ROOT,
    mutex,
)

from .util_common import (
    run_command,
    ResultType,
)

from .config import (
    EnvironmentConfig,
)

from .ci import (
    get_ci_provider,
)

from .data import (
    data_context,
)


class AnsibleCoreCI:
    """Client for Ansible Core CI services."""
    DEFAULT_ENDPOINT = 'https://ansible-core-ci.testing.ansible.com'

    def __init__(
            self,
            args,  # type: EnvironmentConfig
            platform,  # type: str
            version,  # type: str
            provider,  # type: str
            persist=True,  # type: bool
            load=True,  # type: bool
            suffix=None,  # type: t.Optional[str]
    ):  # type: (...) -> None
        self.args = args
        self.platform = platform
        self.version = version
        self.stage = args.remote_stage
        self.client = HttpClient(args)
        self.connection = None
        self.instance_id = None
        self.endpoint = None
        self.default_endpoint = args.remote_endpoint or self.DEFAULT_ENDPOINT
        self.retries = 3
        self.ci_provider = get_ci_provider()
        self.provider = provider
        self.name = '%s-%s' % (self.platform, self.version)

        if suffix:
            self.name += '-' + suffix

        self.path = os.path.expanduser('~/.ansible/test/instances/%s-%s-%s' % (self.name, self.provider, self.stage))
        self.ssh_key = SshKey(args)

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

        if not self.endpoint:
            self.endpoint = self.default_endpoint

    @property
    def available(self):
        """Return True if Ansible Core CI is supported."""
        return self.ci_provider.supports_core_ci_auth()

    def start(self):
        """Start instance."""
        if self.started:
            display.info('Skipping started %s/%s instance %s.' % (self.platform, self.version, self.instance_id),
                         verbosity=1)
            return None

        return self._start(self.ci_provider.prepare_core_ci_auth())

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

    def get(self, tries=3, sleep=15, always_raise_on=None):  # type: (int, int, t.Optional[t.List[int]]) -> t.Optional[InstanceConnection]
        """Get instance connection information."""
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
                port=12345,
                username='root',
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
                    port=int(con['port']),
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
            winrm_config = read_text_file(os.path.join(ANSIBLE_TEST_TARGET_ROOT, 'setup', 'ConfigureRemotingForAnsible.ps1'))
        else:
            winrm_config = None

        data = dict(
            config=dict(
                platform=self.platform,
                version=self.version,
                public_key=self.ssh_key.pub_contents,
                query=False,
                winrm_config=winrm_config,
            )
        )

        data.update(dict(auth=auth))

        headers = {
            'Content-Type': 'application/json',
        }

        response = self._start_endpoint(data, headers)

        self.started = True
        self._save()

        display.info('Started %s/%s from: %s' % (self.platform, self.version, self._uri), verbosity=1)

        if self.args.explain:
            return {}

        return response.json()

    def _start_endpoint(self, data, headers):  # type: (t.Dict[str, t.Any], t.Dict[str, str]) -> HttpResponse
        tries = self.retries
        sleep = 15

        display.info('Trying endpoint: %s' % self.endpoint, verbosity=1)

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

    def load(self, config):  # type: (t.Dict[str, str]) -> bool
        """Load the instance from the provided dictionary."""
        self.instance_id = str(config['instance_id'])
        self.endpoint = config['endpoint']
        self.started = True

        display.sensitive.add(self.instance_id)

        return True

    def _save(self):  # type: () -> None
        """Save instance information."""
        if self.args.explain:
            return

        config = self.save()

        write_json_file(self.path, config, create_directories=True)

    def save(self):  # type: () -> t.Dict[str, str]
        """Save instance details and return as a dictionary."""
        return dict(
            platform_version='%s/%s' % (self.platform, self.version),
            instance_id=self.instance_id,
            endpoint=self.endpoint,
        )

    @staticmethod
    def _create_http_error(response):  # type: (HttpResponse) -> ApplicationError
        """Return an exception created from the given HTTP resposne."""
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
    def __init__(self, status, remote_message, remote_stack_trace):  # type: (int, str, str) -> None
        super().__init__(status, '%s%s' % (remote_message, remote_stack_trace))

        self.remote_message = remote_message
        self.remote_stack_trace = remote_stack_trace


class SshKey:
    """Container for SSH key used to connect to remote instances."""
    KEY_TYPE = 'rsa'  # RSA is used to maintain compatibility with paramiko and EC2
    KEY_NAME = 'id_%s' % KEY_TYPE
    PUB_NAME = '%s.pub' % KEY_NAME

    @mutex
    def __init__(self, args):  # type: (EnvironmentConfig) -> None
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
            self.key_contents = None
        else:
            self.pub_contents = read_text_file(self.pub).strip()
            self.key_contents = read_text_file(self.key).strip()

    @staticmethod
    def get_relative_in_tree_private_key_path():  # type: () -> str
        """Return the ansible-test SSH private key path relative to the content tree."""
        temp_dir = ResultType.TMP.relative_path

        key = os.path.join(temp_dir, SshKey.KEY_NAME)

        return key

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
            run_command(args, ['ssh-keygen', '-m', 'PEM', '-q', '-t', self.KEY_TYPE, '-N', '', '-f', key])

            if args.explain:
                return key, pub

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
