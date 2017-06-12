# -*- coding: utf-8 -*-

# (c) 2017, Alex Braverman Masis <alexbmasis@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

"""ManageIQ plugin for integration tests."""
from __future__ import absolute_import, print_function

import os

from lib.util import (
    find_executable,
    display,
)

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
)

from lib.docker_util import (
    docker_run,
    docker_rm,
    docker_inspect,
    docker_pull,
    docker_exec
)


class ManageIQCloudProvider(CloudProvider):
    """ManageIQ cloud provider plugin.
    Sets up cloud resources before delegation."""
    NODE = 'manageiq_node'
    MASTER = 'manageiq_master'

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(ManageIQCloudProvider, self).__init__(args)
        self.image = 'manageiq/manageiq'
        self.node = ''
        self.master = ''

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources
        are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        docker = find_executable('docker')

        if docker:
            return

        super(ManageIQCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup
        callback."""
        super(ManageIQCloudProvider, self).setup()

        if not self._use_static_config():
            self._setup_dynamic()

    def _setup_dynamic(self):
        """Deploy ManageIQ using Docker"""

        docker_pull(self.args, self.image)
        self.master = self.MASTER
        self.node = self.NODE
        self.deploy_manageiq_container(self.master, [
            '-d', '--name', self.master, '-e', "container=docker", '-v',
            '/sys/fs/cgroup:/sys/fs/cgroup', '--privileged'])
        self.deploy_manageiq_container(self.node, [
            '-d', '--link', self.master, '-e', "container=docker", '-v',
            '/sys/fs/cgroup:/sys/fs/cgroup', '--name', self.node,
            '--privileged'])
        self._initialize_manageiq_container(self.master)
        self._initialize_manageiq_container(self.node)

        config = self._read_config_template()
        self._write_config(config)

    def deploy_manageiq_container(self, name, options):
        """Create a ManageIQ appliance using Docker"""
        display.info('Removing previous ManageIQ dep.', verbosity=1)
        if docker_inspect(self.args, name):
            docker_rm(self.args, name)

        display.info('Starting ManageIQ container: %s' % name, verbosity=1)
        docker_run(self.args, self.image, options)

    def cleanup(self):
        """Clean up the cloud resource and any temporary configuration files
        after tests complete."""
        if self.node:
            docker_rm(self.args, self.node)
        if self.master:
            docker_rm(self.args, self.master)

        super(ManageIQCloudProvider, self).cleanup()

    def get_docker_run_options(self):
        """Get any additional options needed when delegating tests to a docker
        container.
        :rtype: list[str]
        """
        if self.managed:
            return ['--link', self.NODE, '--link', self.MASTER]

        return []

    def _initialize_manageiq_container(self, container_id):
        docker_exec(self.args, container_id, [
            "/usr/bin/systemctl", "stop", "appliance-initialize", "evmserverd",
            "evminit", "evm-watchdog", "miqvmstat", "miqtop"])
        docker_exec(self.args, container_id, [
            "rm", "-rf", "/var/opt/rh/rh-postgresql95/lib/pgsql/data/*"
        ])
        docker_exec(self.args, container_id, [
            "rm", "-rf", "/var/www/miq/vmdb/certs/*"])


class ManageIQCloudEnvironment(CloudEnvironment):
    """ManageIQ cloud environment plugin.
    Updates integration test environment after delegation."""
    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        env.update(dict(ANSIBLE_TEST_REMOTE_INTERPRETER='/usr/bin/python'))
        cmd.append('-e')
        cmd.append('@%s' % self.config_path)

        cmd.append('-e')
        cmd.append('manageiq_resource_prefix=%s' % self.resource_prefix)

    @property
    def inventory_hosts(self):
        """
        :rtype: str | None
        """
        return 'manageiq'
