# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import textwrap
import time

from ansible import context
from ansible.errors import AnsibleError
from ansible.galaxy.user_agent import user_agent
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.urls import open_url
from ansible.utils.color import stringc
from ansible.utils.display import Display
from collections import Mapping

display = Display()


class GitHubOAuthTokenCreator(object):
    '''
    Uses OAuth 2.0 device auth grant (RFC8628) to create limited user authorization token in an
    out-of-band browser session using the GitHub OAuth device flow as described in
    https://docs.github.com/en/developers/apps/authorizing-oauth-apps#device-flow
    '''
    GITHUB_DEVICE_AUTH_URL = 'https://github.com/login/device/code'
    GITHUB_TOKEN_POLL_URL = 'https://github.com/login/oauth/access_token'
    GITHUB_DEVICE_AUTH_HEADERS = {
        "Accept": "application/vnd.github.v3+json,application/vnd.github.machine-man-preview+json,text/json,application/json",
        "Content-Type": "application/json",
    }
    GITHUB_OAUTH_GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:device_code'

    def __init__(self):
        self._validate_certs = not context.CLIARGS['ignore_certs']
        self._code_resp = None
        self._token_resp = None

        # FIXME: each Galaxy server has its own OAuth client_id; we need to somehow ask the Galaxy endpoint we're trying to
        # auth against for its client_id in order to make this work with arbitrary instances...
        # self._oauth_client_id = "3e92491593df34c92089"  # prod galaxy.ansible.com
        self._oauth_client_id = '2e6b1de3b2832a7cf974'  # qa galaxy-qa.ansible.com
        # self._oauth_client_id = "c22abb706831655d49b8"  # nitzmahone/GalaxyAuthTest2 OAuth app

    def github_interactive_device_flow_auth(self):
        display.display('\n\nPreparing for interactive GitHub login...')
        self._code_resp = self._create_github_device_code()

        device_auth_uri = self._code_resp['verification_uri']
        user_code = self._code_resp['user_code']
        timeout_min = int(round(self._code_resp['expires_in'] / 60))  # response is in seconds

        instr = textwrap.wrap('To authenticate to Ansible Galaxy via GitHub, browse to {0} and enter the code {1} within '
                              '{2} minutes.\nUse the {3} argument if you need to provide a fixed token for scripting purposes.'
                              .format(stringc(device_auth_uri, 'bright cyan'),
                                      stringc(user_code, 'bright cyan'),
                                      timeout_min,
                                      stringc("--github-token", 'yellow')), width=display.columns)
        display.display('\n'+'\n'.join(instr), screen_only=True)

        display.display('\nAwaiting GitHub authorization...')
        self._token_resp = self._await_device_auth()
        display.display('\nGitHub authorization succeeded.')

        return self._token_resp['access_token']

    def _create_github_device_code(self):
        ''' Request creation of device and user codes from GitHub for the target endpoint OAuth client_id '''
        device_code_req = {"client_id": self._oauth_client_id, "scope": "public_repo"}
        device_code_resp = self._github_oauth_post(self.GITHUB_DEVICE_AUTH_URL, req_dict=device_code_req)

        if 'error' in device_code_resp:
            raise AnsibleError('error requesting GitHub device authorization code: {0}'.format(device_code_resp['error']))

        missing_resp_keys = [k for k in ['verification_uri', 'user_code', 'expires_in', 'interval'] if k not in device_code_resp]

        if missing_resp_keys:
            raise AnsibleError('missing response keys {0} in GitHub device authorization response'.format(missing_resp_keys))

        return device_code_resp

    def _await_device_auth(self):
        sleep_sec = self._code_resp['interval']

        poll_req = {'client_id': self._oauth_client_id, 'device_code': self._code_resp['device_code'],
                    'grant_type': self.GITHUB_OAUTH_GRANT_TYPE}

        while True:
            time.sleep(sleep_sec)
            resp = self._github_oauth_post(self.GITHUB_TOKEN_POLL_URL, req_dict=poll_req)

            err_code = resp.get('error')
            if not err_code:
                return resp
            if err_code == 'authorization_pending':
                continue  # normal polling, user hasn't completed the authorization yet
            elif err_code == 'slow_down':
                sleep_sec += 5  # the server asked us to add 5s to our polling interval
                continue
            elif err_code == 'access_denied':
                raise AnsibleError('User did not authorize Ansible Galaxy GitHub app')
            else:
                raise AnsibleError('unexpected response while polling GitHub OAuth services: {0}'.format(err_code))

    def _github_oauth_post(self, url, req_dict):
        req_json = json.dumps(req_dict)
        try:
            resp = open_url(url, method='POST', headers=self.GITHUB_DEVICE_AUTH_HEADERS, data=req_json,
                            validate_certs=self._validate_certs, http_agent=user_agent())
        except HTTPError as e:
            raise AnsibleError('unexpected HTTP error contacting GitHub OAuth services: {0}'.format(e))

        try:
            resp_dict = json.load(resp)
        except ValueError as e:
            raise AnsibleError('invalid non-JSON response from GitHub OAuth services: {0}'.format(e))

        if not isinstance(resp_dict, Mapping):
            raise AnsibleError('invalid non-dictionary response from GitHub OAuth services: {0}'.format(e))

        return resp_dict
