"""Tower plugin for integration tests."""
from __future__ import absolute_import, print_function

import os
import time

try:
    # noinspection PyPep8Naming
    import ConfigParser as configparser
except ImportError:
    # noinspection PyUnresolvedReferences
    import configparser

from lib.util import (
    display,
    ApplicationError,
    is_shippable,
    find_pip,
    run_command,
    generate_password,
    SubprocessError,
)

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
)

from lib.core_ci import (
    AnsibleCoreCI,
    InstanceConnection,
)

from lib.manage_ci import (
    ManagePosixCI,
)

from lib.http import (
    HttpClient,
)


class TowerCloudProvider(CloudProvider):
    """Tower cloud provider plugin. Sets up cloud resources before delegation."""
    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(TowerCloudProvider, self).__init__(args, config_extension='.cfg')

        self.aci = None
        self.version = ''

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        aci = get_tower_aci(self.args)

        if os.path.isfile(aci.ci_key):
            return

        if is_shippable():
            return

        super(TowerCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(TowerCloudProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def check_tower_version(self, fallback=None):
        """Check the Tower version being tested and determine the correct CLI version to use.
        :type fallback: str | None
        """
        tower_cli_version_map = {
            '3.1.5': '3.1.8',
            '3.2.3': '3.2.1',
        }

        cli_version = tower_cli_version_map.get(self.version, fallback)

        if not cli_version:
            raise ApplicationError('Mapping to ansible-tower-cli version required for Tower version: %s' % self.version)

        self._set_cloud_config('tower_cli_version', cli_version)

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files after tests complete."""
        # cleanup on success or failure is not yet supported due to how cleanup is called
        if self.aci and self.args.remote_terminate == 'always':
            self.aci.stop()

        super(TowerCloudProvider, self).cleanup()

    def _setup_static(self):
        config = TowerConfig.parse(self.config_static_path)

        self.version = config.version
        self.check_tower_version()

    def _setup_dynamic(self):
        """Request Tower credentials through the Ansible Core CI service."""
        display.info('Provisioning %s cloud environment.' % self.platform, verbosity=1)

        # temporary solution to allow version selection
        self.version = os.environ.get('TOWER_VERSION', '3.2.3')
        self.check_tower_version(os.environ.get('TOWER_CLI_VERSION'))

        aci = get_tower_aci(self.args, self.version)
        aci.start()

        connection = aci.get()

        self._set_cloud_config('ssh_hostname', connection.hostname)
        self._set_cloud_config('ssh_username', connection.username)
        self._set_cloud_config('ssh_port', connection.port)

        config = self._read_config_template()

        if not self.args.explain:
            self.aci = aci

            values = dict(
                VERSION=self.version,
                HOST=connection.hostname,
                USERNAME='admin',
                PASSWORD=generate_password(),
            )

            config = self._populate_config_template(config, values)

        self._write_config(config)


class TowerCloudEnvironment(CloudEnvironment):
    """Tower cloud environment plugin. Updates integration test environment after delegation."""
    def setup(self):
        """Setup which should be done once per environment instead of once per test target."""
        self.setup_cli()

        if self.managed:
            self.setup_dynamic()

        self.ping_tower_api()
        self.disable_pendo()

    def setup_dynamic(self):
        """Dynamic setup which should be done once per environment instead of once per test target."""
        display.info('Waiting for Tower instance to become reachable over SSH')

        ssh_hostname = self._get_cloud_config('ssh_hostname')
        ssh_username = self._get_cloud_config('ssh_username')
        ssh_port = self._get_cloud_config('ssh_port')

        config = TowerConfig.parse(self.config_path)

        aci = get_tower_aci(self.args)
        aci.connection = InstanceConnection(True, ssh_hostname, ssh_port, ssh_username, None)

        mci = ManagePosixCI(aci)
        mci.wait()

        display.info('Waiting for Tower to be reconfigured')

        attempts = 60

        while attempts:
            attempts -= 1

            try:
                # Tower is supposed to drop a /etc/tower/reset/.reconfigured file when it is reconfigured.
                # However, the playbook sometimes fails, so we'll look for the completion of the playbook in the log instead.
                mci.ssh(['grep', '--quiet', '--no-messages', 'PLAY RECAP', '/etc/tower/reset/reset.log'])
                break
            except SubprocessError:
                time.sleep(5)
        else:
            raise ApplicationError('Timed out waiting for Tower to be reconfigured.')

        display.info('Updating the Tower %s password' % config.username)

        cmd = ['awx-manage', 'update_password', '--username', config.username, '--password', config.password]
        mci.ssh(cmd)

    def setup_cli(self):
        """Install the correct Tower CLI for the version of Tower being tested."""
        tower_cli_version = self._get_cloud_config('tower_cli_version')

        display.info('Installing Tower CLI version: %s' % tower_cli_version)

        pip = find_pip(version=self.args.python_version)
        cmd = [pip, 'install', '--disable-pip-version-check', 'ansible-tower-cli==%s' % tower_cli_version]

        run_command(self.args, cmd)

    def ping_tower_api(self):
        """Wait for Tower API to become available."""
        display.info('Waiting for the Tower API to become reachable')

        config = TowerConfig.parse(self.config_path)

        http = HttpClient(self.args, insecure=True)
        http.username = config.username
        http.password = config.password

        uri = 'https://%s/api/v1/ping/' % config.host

        attempts = 60

        while attempts:
            attempts -= 1
            response = http.get(uri)

            if response.status_code == 200:
                return

            time.sleep(5)

        raise ApplicationError('Timed out waiting for Tower API to become reachable.')

    def disable_pendo(self):
        """Disable Pendo tracking."""
        display.info('Disable Pendo tracking')

        config = TowerConfig.parse(self.config_path)

        # tower-cli does not recognize TOWER_ environment variables
        cmd = ['tower-cli', 'setting', 'modify', 'PENDO_TRACKING_STATE', 'off',
               '-h', config.host, '-u', config.username, '-p', config.password]

        run_command(self.args, cmd)

    def configure_environment(self, env, cmd):
        """Configuration which should be done once for each test target.
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        config = TowerConfig.parse(self.config_path)

        env.update(config.environment)


class TowerConfig(object):
    """Tower settings."""
    def __init__(self, values):
        self.version = values.get('version')
        self.host = values.get('host')
        self.username = values.get('username')
        self.password = values.get('password')

        if self.password:
            display.sensitive.add(self.password)

    @property
    def environment(self):
        """Tower settings as environment variables.
        :rtype: dict[str, str]
        """
        env = dict(
            TOWER_HOST=self.host,
            TOWER_USERNAME=self.username,
            TOWER_PASSWORD=self.password,
        )

        return env

    @staticmethod
    def parse(path):
        """
        :type path: str
        :rtype: TowerConfig
        """
        parser = configparser.RawConfigParser()
        parser.read(path)

        keys = (
            'version',
            'host',
            'username',
            'password',
        )

        values = dict((k, parser.get('general', k)) for k in keys)
        config = TowerConfig(values)

        return config


def get_tower_aci(args, version=None):
    """
    :type args: EnvironmentConfig
    :type version: str | None
    :rtype: AnsibleCoreCI
    """
    if version:
        persist = True
    else:
        version = ''
        persist = False

    return AnsibleCoreCI(args, 'tower', version, persist=persist, stage=args.remote_stage, provider=args.remote_provider)
