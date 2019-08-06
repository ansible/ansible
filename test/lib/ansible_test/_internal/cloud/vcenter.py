"""VMware vCenter plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..util import (
    find_executable,
    display,
    ApplicationError,
    is_shippable,
    ConfigParser,
    SubprocessError,
)

from ..docker_util import (
    docker_run,
    docker_rm,
    docker_inspect,
    docker_pull,
    get_docker_container_id,
)

from ..core_ci import (
    AnsibleCoreCI,
)

from ..http import (
    HttpClient,
)


class VcenterProvider(CloudProvider):
    """VMware vcenter/esx plugin. Sets up cloud resources for tests."""
    DOCKER_SIMULATOR_NAME = 'vcenter-simulator'

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(VcenterProvider, self).__init__(args)

        # The simulator must be pinned to a specific version to guarantee CI passes with the version used.
        if os.environ.get('ANSIBLE_VCSIM_CONTAINER'):
            self.image = os.environ.get('ANSIBLE_VCSIM_CONTAINER')
        else:
            self.image = 'quay.io/ansible/vcenter-test-container:1.5.0'
        self.container_name = ''

        # VMware tests can be run on govcsim or baremetal, either BYO with a static config
        # file or hosted in worldstream.  Using an env var value of 'worldstream' with appropriate
        # CI credentials will deploy a dynamic baremetal environment. The simulator is the default
        # if no other config if provided.
        self.vmware_test_platform = os.environ.get('VMWARE_TEST_PLATFORM', '')
        self.aci = None
        self.insecure = False
        self.endpoint = ''
        self.hostname = ''
        self.port = 443
        self.proxy = None

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if self.vmware_test_platform is None or 'govcsim':
            docker = find_executable('docker', required=False)

            if docker:
                return

            skip = 'cloud/%s/' % self.platform
            skipped = [target.name for target in targets if skip in target.aliases]

            if skipped:
                exclude.append(skip)
                display.warning('Excluding tests marked "%s" which require the "docker" command: %s'
                                % (skip.rstrip('/'), ', '.join(skipped)))
        else:
            if os.path.isfile(self.config_static_path):
                return

            aci = self._create_ansible_core_ci()

            if os.path.isfile(aci.ci_key):
                return

            if is_shippable():
                return

            super(VcenterProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(VcenterProvider, self).setup()

        self._set_cloud_config('vmware_test_platform', self.vmware_test_platform)
        if self._use_static_config():
            self._set_cloud_config('vmware_test_platform', 'static')
            self._setup_static()
        elif self.vmware_test_platform == 'worldstream':
            self._setup_dynamic_baremetal()
        else:
            self._setup_dynamic_simulator()

    def get_docker_run_options(self):
        """Get any additional options needed when delegating tests to a docker container.
        :rtype: list[str]
        """
        if self.managed and self.vmware_test_platform != 'worldstream':
            return ['--link', self.DOCKER_SIMULATOR_NAME]

        return []

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files after tests complete."""
        if self.vmware_test_platform == 'worldstream':

            if self.aci:
                self.aci.stop()

        if self.container_name:
            docker_rm(self.args, self.container_name)

        super(VcenterProvider, self).cleanup()

    def _setup_dynamic_simulator(self):
        """Create a vcenter simulator using docker."""
        container_id = get_docker_container_id()

        if container_id:
            display.info('Running in docker container: %s' % container_id, verbosity=1)

        self.container_name = self.DOCKER_SIMULATOR_NAME

        results = docker_inspect(self.args, self.container_name)

        if results and not results[0].get('State', {}).get('Running'):
            docker_rm(self.args, self.container_name)
            results = []

        if results:
            display.info('Using the existing vCenter simulator docker container.', verbosity=1)
        else:
            display.info('Starting a new vCenter simulator docker container.', verbosity=1)

            if not self.args.docker and not container_id:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', '80:80',
                    '-p', '443:443',
                    '-p', '8080:8080',
                    '-p', '8989:8989',
                    '-p', '5000:5000',  # control port for flask app in simulator
                ]
            else:
                publish_ports = []

            if not os.environ.get('ANSIBLE_VCSIM_CONTAINER'):
                docker_pull(self.args, self.image)

            docker_run(
                self.args,
                self.image,
                ['-d', '--name', self.container_name] + publish_ports,
            )

        if self.args.docker:
            vcenter_host = self.DOCKER_SIMULATOR_NAME
        elif container_id:
            vcenter_host = self._get_simulator_address()
            display.info('Found vCenter simulator container address: %s' % vcenter_host, verbosity=1)
        else:
            vcenter_host = 'localhost'

        self._set_cloud_config('vcenter_host', vcenter_host)

    def _get_simulator_address(self):
        results = docker_inspect(self.args, self.container_name)
        ipaddress = results[0]['NetworkSettings']['IPAddress']
        return ipaddress

    def _setup_dynamic_baremetal(self):
        """Request Esxi credentials through the Ansible Core CI service."""
        display.info('Provisioning %s cloud environment.' % self.platform,
                     verbosity=1)

        config = self._read_config_template()

        aci = self._create_ansible_core_ci()

        if not self.args.explain:
            response = aci.start()
            self.aci = aci

            config = self._populate_config_template(config, response)
            self._write_config(config)

    def _create_ansible_core_ci(self):
        """
        :rtype: AnsibleCoreCI
        """
        return AnsibleCoreCI(self.args, 'vmware', 'vmware',
                             persist=False, stage=self.args.remote_stage,
                             provider='vmware')

    def _setup_static(self):
        parser = ConfigParser({
            'vcenter_port': '443',
            'vmware_proxy_host': '',
            'vmware_proxy_port': ''})
        parser.read(self.config_static_path)

        self.endpoint = parser.get('DEFAULT', 'vcenter_hostname')
        self.port = parser.get('DEFAULT', 'vcenter_port')

        if parser.get('DEFAULT', 'vmware_validate_certs').lower() in ('no', 'false'):
            self.insecure = True
        proxy_host = parser.get('DEFAULT', 'vmware_proxy_host')
        proxy_port = int(parser.get('DEFAULT', 'vmware_proxy_port'))
        if proxy_host and proxy_port:
            self.proxy = 'http://%s:%d' % (proxy_host, proxy_port)

        self._wait_for_service()

    def _wait_for_service(self):
        """Wait for the vCenter service endpoint to accept connections."""
        if self.args.explain:
            return

        client = HttpClient(self.args, always=True, insecure=self.insecure, proxy=self.proxy)
        endpoint = 'https://%s:%s' % (self.endpoint, self.port)

        for i in range(1, 30):
            display.info('Waiting for vCenter service: %s' % endpoint, verbosity=1)

            try:
                client.get(endpoint)
                return
            except SubprocessError:
                pass

            time.sleep(10)

        raise ApplicationError('Timeout waiting for vCenter service.')


class VcenterEnvironment(CloudEnvironment):
    """VMware vcenter/esx environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        vmware_test_platform = self._get_cloud_config('vmware_test_platform')
        if vmware_test_platform in ('worldstream', 'static'):
            parser = ConfigParser()
            parser.read(self.config_path)

            # Most of the test cases use ansible_vars, but we plan to refactor these
            # to use env_vars, output both for now
            env_vars = dict(
                (key.upper(), value) for key, value in parser.items('DEFAULT', raw=True))

            ansible_vars = dict(
                resource_prefix=self.resource_prefix,
            )
            ansible_vars.update(dict(parser.items('DEFAULT', raw=True)))

        else:
            env_vars = dict(
                VCENTER_HOST=self._get_cloud_config('vcenter_host'),
            )

            ansible_vars = dict(
                vcsim=self._get_cloud_config('vcenter_host'),
            )

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
