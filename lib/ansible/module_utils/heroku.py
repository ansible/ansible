# Copyright: (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import env_fallback, missing_required_lib

HAS_HEROKU = False
HEROKU_IMP_ERR = None
try:
    import heroku3
    HAS_HEROKU = True
except ImportError:
    HEROKU_IMP_ERR = traceback.format_exc()


class HerokuHelper():
    def __init__(self, module):
        self.module = module
        self.check_lib()
        self.api_key = module.params["api_key"]

    def check_lib(self):
        if not HAS_HEROKU:
            self.module.fail_json(msg=missing_required_lib('heroku3'), exception=HEROKU_IMP_ERR)

    @staticmethod
    def heroku_argument_spec():
        return dict(
            api_key=dict(fallback=(env_fallback, ['HEROKU_API_KEY', 'TF_VAR_HEROKU_API_KEY']), type='str', no_log=True))

    def get_heroku_client(self):
        client = heroku3.from_key(self.api_key)

        if not client.is_authenticated:
            self.module.fail_json(msg='Heroku authentication failure, please check your API Key')

        return client
