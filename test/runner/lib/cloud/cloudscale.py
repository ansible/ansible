# -*- coding: utf-8 -*-
#
# (c) 2018, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Cloudscale plugin for integration tests."""
from __future__ import absolute_import, print_function

from os.path import isfile

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
)

from lib.util import ConfigParser, display


class CloudscaleCloudProvider(CloudProvider):
    """Cloudscale cloud provider plugin. Sets up cloud resources before
       delegation.
    """

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(CloudscaleCloudProvider, self).__init__(args, config_extension='.ini')

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if isfile(self.config_static_path):
            return

        super(CloudscaleCloudProvider, self).filter(targets, exclude)

    def setup(self):
        super(CloudscaleCloudProvider, self).setup()

        if isfile(self.config_static_path):
            display.info('Using existing %s cloud config: %s'
                         % (self.platform, self.config_static_path),
                         verbosity=1)
            self.config_path = self.config_static_path
            self.managed = False
            return True

        return False


class CloudscaleCloudEnvironment(CloudEnvironment):
    """Cloudscale cloud environment plugin. Updates integration test environment
       after delegation.
    """
    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        parser = ConfigParser()
        parser.read(self.config_path)

        changes = dict(
            CLOUDSCALE_API_TOKEN=parser.get('default', 'cloudscale_api_token'),
        )

        env.update(changes)

        cmd.append('-e')
        cmd.append('cloudscale_resource_prefix=%s' % self.resource_prefix)
