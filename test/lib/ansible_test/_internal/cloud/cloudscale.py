# -*- coding: utf-8 -*-
#
# (c) 2018, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Cloudscale plugin for integration tests."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from . import (
    CloudProvider,
    CloudEnvironment,
    CloudEnvironmentConfig,
)

from ..util import ConfigParser, display


class CloudscaleCloudProvider(CloudProvider):
    """Cloudscale cloud provider plugin. Sets up cloud resources before
       delegation.
    """

    def __init__(self, args):
        """
        :type args: TestConfig
        """
        super(CloudscaleCloudProvider, self).__init__(args)

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """
        if os.path.isfile(self.config_static_path):
            return

        super(CloudscaleCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(CloudscaleCloudProvider, self).setup()

        if os.path.isfile(self.config_static_path):
            display.info('Using existing %s cloud config: %s'
                         % (self.platform, self.config_static_path),
                         verbosity=1)
            self.config_path = self.config_static_path
            self.managed = False


class CloudscaleCloudEnvironment(CloudEnvironment):
    """Cloudscale cloud environment plugin. Updates integration test environment
       after delegation.
    """
    def get_environment_config(self):
        """
        :rtype: CloudEnvironmentConfig
        """
        parser = ConfigParser()
        parser.read(self.config_path)

        env_vars = dict(
            CLOUDSCALE_API_TOKEN=parser.get('default', 'cloudscale_api_token'),
        )

        display.sensitive.add(env_vars['CLOUDSCALE_API_TOKEN'])

        ansible_vars = dict(
            cloudscale_resource_prefix=self.resource_prefix,
        )

        ansible_vars.update(dict((key.lower(), value) for key, value in env_vars.items()))

        return CloudEnvironmentConfig(
            env_vars=env_vars,
            ansible_vars=ansible_vars,
        )
