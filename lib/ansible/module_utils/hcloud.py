# Copyright: (c) 2019, Hetzner Cloud GmbH <info@hetzner-cloud.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.ansible_release import __version__
from ansible.module_utils.basic import env_fallback

try:
    import hcloud

    HCLOUD_AVAILABLE = True
except ImportError:
    HCLOUD_AVAILABLE = False


class Hcloud(object):
    def __init__(self, module, represent):
        self.module = module
        self.represent = represent
        self.result = {"changed": False, self.represent: None}
        if not HCLOUD_AVAILABLE:
            module.fail_json(msg="hcloud-python must be available to use this module")
        self._build_client()

    def _build_client(self):
        self.client = hcloud.Client(
            token=self.module.params["api_token"],
            api_endpoint=self.module.params["endpoint"],
            application_name="ansible-module",
            application_version=__version__,
        )

    def _mark_as_changed(self):
        self.result["changed"] = True

    @staticmethod
    def base_module_arguments():
        return {
            "api_token": {
                "type": "str",
                "required": True,
                "fallback": (env_fallback, ["HCLOUD_TOKEN"]),
            },
            "endpoint": {"type": "str", "default": "https://api.hetzner.cloud/v1"},
        }

    def _prepare_result(self):
        """Prepare the result for every module

        :return: dict
        """
        return {}

    def get_result(self):
        if getattr(self, self.represent) is not None:
            self.result[self.represent] = self._prepare_result()
        return self.result
