# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2017, Tim Rightnour <thegarbledone@gmail.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback
from ansible.module_utils.basic import env_fallback, missing_required_lib

# Pull in pysnow
HAS_PYSNOW = False
PYSNOW_IMP_ERR = None
try:
    import pysnow
    HAS_PYSNOW = True
except ImportError:
    PYSNOW_IMP_ERR = traceback.format_exc()


class ServiceNowClient(object):
    def __init__(self, module):
        """
        Constructor
        """
        if not HAS_PYSNOW:
            module.fail_json(msg=missing_required_lib('pysnow'), exception=PYSNOW_IMP_ERR)

        self.module = module
        self.params = module.params
        self.client_id = self.params['client_id']
        self.client_secret = self.params['client_secret']
        self.username = self.params['username']
        self.password = self.params['password']
        self.instance = self.params['instance']
        self.session = {'token': None}
        self.conn = None

    def login(self):
        result = dict(
            changed=False
        )

        if self.params['client_id'] is not None:
            try:
                self.conn = pysnow.OAuthClient(client_id=self.client_id,
                                               client_secret=self.client_secret,
                                               token_updater=self.updater,
                                               instance=self.instance)
            except Exception as detail:
                self.module.fail_json(msg='Could not connect to ServiceNow: {0}'.format(str(detail)), **result)
            if not self.session['token']:
                # No previous token exists, Generate new.
                try:
                    self.session['token'] = self.conn.generate_token(self.username, self.password)
                except pysnow.exceptions.TokenCreateError as detail:
                    self.module.fail_json(msg='Unable to generate a new token: {0}'.format(str(detail)), **result)

                self.conn.set_token(self.session['token'])
        elif self.username is not None:
            try:
                self.conn = pysnow.Client(instance=self.instance,
                                          user=self.username,
                                          password=self.password)
            except Exception as detail:
                self.module.fail_json(msg='Could not connect to ServiceNow: {0}'.format(str(detail)), **result)
        else:
            snow_error = "Must specify username/password. Also client_id/client_secret if using OAuth."
            self.module.fail_json(msg=snow_error, **result)

    def updater(self, new_token):
        self.session['token'] = new_token
        self.conn = pysnow.OAuthClient(client_id=self.client_id,
                                       client_secret=self.client_secret,
                                       token_updater=self.updater,
                                       instance=self.instance)
        try:
            self.conn.set_token(self.session['token'])
        except pysnow.exceptions.MissingToken:
            snow_error = "Token is missing"
            self.module.fail_json(msg=snow_error)
        except Exception as detail:
            self.module.fail_json(msg='Could not refresh token: {0}'.format(str(detail)))

    @staticmethod
    def snow_argument_spec():
        return dict(
            instance=dict(type='str', required=False, fallback=(env_fallback, ['SN_INSTANCE'])),
            username=dict(type='str', required=False, fallback=(env_fallback, ['SN_USERNAME'])),
            password=dict(type='str', required=False, no_log=True, fallback=(env_fallback, ['SN_PASSWORD'])),
            client_id=dict(type='str', no_log=True),
            client_secret=dict(type='str', no_log=True),
        )
