# https://github.com/ansible/ansible/blob/devel/lib/ansible/module_utils/basic.py

import os
# from ansible.module_utils.urls import fetch_url_mock
from .mock_urls import fetch_url_mock


class AnsibleModule(object):
    def __init__(
        self,
        argument_spec,
        bypass_checks=False,
        no_log=False,
        check_invalid_arguments=None,
        mutually_exclusive=None,
        required_together=None,
        required_one_of=None,
        add_file_common_args=False,
        supports_check_mode=False,
        required_if=None
    ):

        self.params = argument_spec

        self._debug = False
        self.check_mode = False
        self._tmpdir = None

        self.mock = fetch_url_mock()

    def fail_json(self, **kwargs):

        self.params.update(kwargs)

    def exit_json(self, **kwargs):

        self.params.update(kwargs)

    def warn(self, message):

        self.params['warn'] = message

    def deprecate(self, message):

        self.params['deprecate'] = message

    @property
    def tmpdir(self):

        return self._tmpdir