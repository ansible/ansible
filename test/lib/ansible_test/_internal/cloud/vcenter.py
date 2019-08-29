"""VMware vCenter plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..util import (
    find_executable,
    display,
    is_shippable,
    ConfigParser,
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
            self.image = 'quay.io/ansible/vcenter-test-container:1.7.0'
        self.container_name = ''

        # VMware tests can be run on govcsim or baremetal, either BYO with a static config
        # file or hosted in worldstream.  Using an env var value of 'worldstream' with appropriate
        # CI credentials will deploy a dynamic baremetal environment. The simulator is the default
        # if no other config if provided.
        self.vmware_test_platform = os.environ.get('VMWARE_TEST_PLATFORM', 'govcsim')
        self.aci = None
        self.insecure = False
        self.proxy = None
        self.platform = 'vcenter'

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if self.vmware_test_platform == 'govcsim' or (self.vmware_test_platform == '' and not os.path.isfile(self.config_static_path)):
            docker = find_executable('docker', required=False)

            if docker:
                return

            skip = 'cloud/%s/' % self.platform
            skipped = [target.name for target in targets if skip in target.aliases]

            if skipped:
                exclude.append(skip)
                display.warning('Excluding tests marked "%s" which require the "docker" command or config (see "%s"): %s'
                                % (skip.rstrip('/'), self.config_template_path, ', '.join(skipped)))
        elif self.vmware_test_platform == 'static':
            if os.path.isfile(self.config_static_path):
                return

            super(VcenterProvider, self).filter(targets, exclude)
        elif self.vmware_test_platform == 'worldstream':
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
        if self.vmware_test_platform == 'govcsim':
            self._setup_dynamic_simulator()
            self.managed = True
        elif self.vmware_test_platform == 'worldstream':
            self._setup_dynamic_baremetal()
            self.managed = True
        elif self.vmware_test_platform == 'static':
            self._use_static_config()
            self._setup_static()
        else:
            display.error('Unknown vmware_test_platform: %s' % self.vmware_test_platform)
            exit(1)

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
            vcenter_hostname = self.DOCKER_SIMULATOR_NAME
        elif container_id:
            vcenter_hostname = self._get_simulator_address()
            display.info('Found vCenter simulator container address: %s' % vcenter_hostname, verbosity=1)
        else:
            vcenter_hostname = 'localhost'

        self._set_cloud_config('vcenter_hostname', vcenter_hostname)

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
            self.aci = aci
            aci.start()
            aci.wait(iterations=160)

            data = aci.get().response_json.get('data')
            for key, value in data.items():
                if key.endswith('PASSWORD'):
                    display.sensitive.add(value)
            config = self._populate_config_template(config, data)
            self._write_config(config)

    def _create_ansible_core_ci(self):
        """
        :rtype: AnsibleCoreCI
        """
        return AnsibleCoreCI(self.args, 'vmware', 'vmware',
                             persist=False, stage=self.args.remote_stage,
                             provider='vmware')

    def _setup_static(self):
        if not os.path.exists(self.config_static_path):
            display.error('Configuration file does not exist: %s' % self.config_static_path)
            exit(1)
        parser = ConfigParser({
            'vcenter_port': '443',
            'vmware_proxy_host': '',
            'vmware_proxy_port': '8080'})
        parser.read(self.config_static_path)

        if parser.get('DEFAULT', 'vmware_validate_certs').lower() in ('no', 'false'):
            self.insecure = True
        proxy_host = parser.get('DEFAULT', 'vmware_proxy_host')
        proxy_port = int(parser.get('DEFAULT', 'vmware_proxy_port'))
        if proxy_host and proxy_port:
            self.proxy = 'http://%s:%d' % (proxy_host, proxy_port)


class VcenterEnvironment(CloudEnvironment):
    """VMware vcenter/esx environment plugin. Updates integration test environment after delegation."""
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        try:
            # We may be in a container, so we cannot just reach VMWARE_TEST_PLATFORM,
            # We do a try/except instead
            parser = ConfigParser()
            parser.read(self.config_path)  # Worldstream and static

            # Most of the test cases use ansible_vars, but we plan to refactor these
            # to use env_vars, output both for now
            env_vars = dict(
                (key.upper(), value) for key, value in parser.items('DEFAULT', raw=True))

            ansible_vars = dict(
                resource_prefix=self.resource_prefix,
            )
            ansible_vars.update(dict(parser.items('DEFAULT', raw=True)))
        except KeyError:  # govcsim
            env_vars = dict(
                VCENTER_HOSTNAME=self._get_cloud_config('vcenter_hostname'),
                VCENTER_USERNAME='user',
                VCENTER_PASSWORD='pass',
            )

            ansible_vars = dict(
                vcsim=self._get_cloud_config('vcenter_hostname'),
            )

        for key, value in ansible_vars.items():
            if key.endswith('_password'):
                display.sensitive.add(value)

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
