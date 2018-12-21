# Copyright: (c) 2018, Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""GCP plugin for integration tests."""
from __future__ import absolute_import, print_function

import os

from lib.util import (
    display,
)

from lib.cloud import (
    CloudProvider,
    CloudEnvironment,
)


class GcpCloudProvider(CloudProvider):
    """GCP cloud provider plugin. Sets up cloud resources before delegation."""

    def filter(self, targets, exclude):
        """Filter out the cloud tests when the necessary config and resources are not available.
        :type targets: tuple[TestTarget]
        :type exclude: list[str]
        """

        if os.path.isfile(self.config_static_path):
            return

        super(GcpCloudProvider, self).filter(targets, exclude)

    def setup(self):
        """Setup the cloud resource before delegation and register a cleanup callback."""
        super(GcpCloudProvider, self).setup()

        if not self._use_static_config():
            display.notice(
                'static configuration could not be used. are you missing a template file?'
            )


class GcpCloudEnvironment(CloudEnvironment):
    """GCP cloud environment plugin. Updates integration test environment after delegation."""

    def configure_environment(self, env, cmd):
        """
        :type env: dict[str, str]
        :type cmd: list[str]
        """
        cmd.append('-e')
        cmd.append('@%s' % self.config_path)

        cmd.append('-e')
        cmd.append('resource_prefix=%s' % self.resource_prefix)

    def on_failure(self, target, tries):
        """
        :type target: TestTarget
        :type tries: int
        """
        if not tries and self.managed:
            display.notice('%s failed' % target.name)
