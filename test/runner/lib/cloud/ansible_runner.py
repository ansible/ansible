"""Ansible-Runner plugin for integration tests."""

from __future__ import absolute_import, print_function

import os
import tempfile

from . import (
    CloudProvider,
    CloudEnvironment,
)

from ..util import (
    find_executable,
    display,
)

from ..docker_util import (
    docker_exec,
    docker_run,
    docker_rm,
    docker_inspect,
    docker_pull,
    docker_put,
    get_docker_container_id,
)

from .. import pytar


class AnsibleRunnerProvider(CloudProvider):
    """AnsibleRunner plugin.

    Prepares the ansible-runner test container.
    """

    DOCKER_SIMULATOR_NAME = 'ansible_runner_test'
    DOCKER_IMAGE = 'jctanner/ansible-runner'

    def __init__(self, args):
        """Set up container references for provider.

        :type args: TestConfig
        """
        super(AnsibleRunnerProvider, self).__init__(args)

        self.__container_from_env = os.getenv('ANSIBLE_RUNNER_CONTAINER')
        self.image = 'quay.io/ansible/ansible-runner-test-container:1.0'
        self.container_name = ''

    def filter(self, targets, exclude):
        """Filter out the tests with the necessary config and res unavailable.

        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        docker_cmd = 'docker'
        docker = find_executable(docker_cmd, required=False)

        if docker:
            return

        skip = 'cloud/%s/' % self.platform
        skipped = [target.name for target in targets if skip in target.aliases]

        if skipped:
            exclude.append(skip)
            display.warning(
                'Excluding tests marked "%s" '
                'which require the "%s" command: %s'
                % (skip.rstrip('/'), docker_cmd, ', '.join(skipped))
            )

    def setup(self):
        """Setup cloud resource before delegation and reg cleanup callback."""
        super(AnsibleRunnerProvider, self).setup()

        if self._use_static_config():
            self._setup_static()
        else:
            self._setup_dynamic()

    def get_docker_run_options(self):
        """Get additional options needed when delegating tests to a container.

        :rtype: list[str]
        """
        return ['--link', self.DOCKER_SIMULATOR_NAME] if self.managed else []

    def cleanup(self):
        """Clean up the resource and temporary configs files after tests."""
        if self.container_name:
            docker_rm(self.args, self.container_name)
        super(AnsibleRunnerProvider, self).cleanup()

    def _setup_dynamic(self):
        """Spawn an ansible-runner test container."""
        runner_port = 5000
        container_id = get_docker_container_id()

        if container_id:
            display.info(
                'Running in docker container: %s' % container_id,
                verbosity=1,
            )

        self.container_name = self.DOCKER_SIMULATOR_NAME

        results = docker_inspect(self.args, self.container_name)

        if results and not results[0].get('State', {}).get('Running'):
            docker_rm(self.args, self.container_name)
            results = []

        display.info(
            '%s Ansible Runner docker container.'
            % ('Using the existing' if results else 'Starting a new'),
            verbosity=1,
        )

        if not results:
            if self.args.docker or container_id:
                publish_ports = []
            else:
                # publish the simulator ports when not running inside docker
                publish_ports = [
                    '-p', ':'.join((str(runner_port), ) * 2),
                ]

            docker_run(
                self.args,
                self.image,
                ['-d', '--name', self.container_name] + publish_ports,
            )

        # if self.args.docker:
        #    runner_host = self.DOCKER_SIMULATOR_NAME
        # elif container_id:
        if True:
            runner_host = self._get_simulator_address()
            display.info(
                'Found ansible runner test container address: %s'
                % runner_host, verbosity=1
            )
        else:
            runner_host = 'localhost'

        self._set_cloud_config('ANSIBLE_RUNNER_HOST', runner_host)
        self._set_cloud_config('ANSIBLE_RUNNER_PORT', str(runner_port))
        self.delegate_checkout()

    def _get_simulator_address(self):
        results = docker_inspect(self.args, self.container_name)
        ip_address = results[0]['NetworkSettings']['IPAddress']
        return ip_address

    def _get_docker_container_id(self):
        results = docker_inspect(self.args, self.container_name)
        return results[0]['Id']

    def _setup_static(self):
        raise NotImplementedError

    def delegate_checkout(self):
        ''' This injects the PR's checkout into the container for ansible-runner to use '''
        with tempfile.NamedTemporaryFile(prefix='ansible-source-', suffix='.tgz') as local_source_fd:
            try:
                tar_filter = pytar.DefaultTarFilter()
                pytar.create_tarfile(local_source_fd.name, '.', tar_filter)
            except Exception as error:
                raise error
            container_id = self._get_docker_container_id()
            docker_put(self.args, container_id, local_source_fd.name, '/root/ansible.tgz')
            docker_exec(self.args, container_id, ['mkdir', '/root/ansible'])
            docker_exec(self.args, container_id, ['tar', 'oxzf', '/root/ansible.tgz', '-C', '/root/ansible'])
            docker_exec(self.args, container_id, ['pip', 'install', '/root/ansible'])


class AnsibleRunnerEnvironment(CloudEnvironment):

    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """

        # Send the container IP down to the integration test(s)
        env['ANSIBLE_RUNNER_HOST'] = self._get_cloud_config('ANSIBLE_RUNNER_HOST')
        env['ANSIBLE_RUNNER_PORT'] = self._get_cloud_config('ANSIBLE_RUNNER_PORT')
