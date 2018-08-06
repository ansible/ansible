########################################################################
#
# (C) 2015, Chris Houseknecht <chouse@ansible.com>
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
########################################################################

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import getpass
import json
import sys

from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils.six import PY2
from ansible.module_utils.six import binary_type
from ansible.module_utils.six.moves import input
from ansible.module_utils.six.moves.urllib.parse import quote as urlquote, urlparse
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.urls import open_url
from ansible.utils.color import stringc
from ansible.utils.display import Display

display = Display()


def http_error_message(error):
    flat_resp = error.read()
    if isinstance(flat_resp, binary_type):
        flat_resp = flat_resp.decode()
    res = json.loads(flat_resp)
    return res['message']


class GalaxyLogin(object):
    ''' Class to handle authenticating user with Galaxy API prior to performing CUD operations '''

    GITHUB_AUTH = 'https://api.github.com/authorizations'

    def __init__(self, galaxy, github_token=None):
        self.galaxy = galaxy
        self.github_username = None
        self.github_password = None

        if github_token is None:
            self.get_credentials()

    def get_credentials(self):
        display.display(u'\n\n' + "We need your " + stringc("GitHub login", 'bright cyan') +
                        " to identify you.", screen_only=True)
        display.display("This information will " + stringc("not be sent to Galaxy", 'bright cyan') +
                        ", only to " + stringc("api.github.com.", "yellow"), screen_only=True)
        display.display("The password will not be displayed." + u'\n\n', screen_only=True)
        display.display("Use " + stringc("--github-token", 'yellow') +
                        " if you do not want to enter your password." + u'\n\n', screen_only=True)

        try:
            self.github_username = input("GitHub Username: ")
        except Exception:
            pass

        try:
            self.github_password = getpass.getpass("Password for %s: " % self.github_username)
        except Exception:
            pass

        if not self.github_username or not self.github_password:
            raise AnsibleError("Invalid GitHub credentials. Username and password are required.")

    def remove_github_token(self):
        '''
        If for some reason an ansible-galaxy token was left from a prior login, remove it. We cannot
        retrieve the token after creation, so we are forced to create a new one.
        '''
        try:
            opened = open_url(self.GITHUB_AUTH,
                              url_username=self.github_username,
                              url_password=self.github_password,
                              force_basic_auth=True,)
            resp = opened.read()
            if not PY2:
                resp = resp.decode()
            tokens = json.loads(resp)
        except HTTPError as e:
            msg = http_error_message(e)
            raise AnsibleError(msg)

        for token in tokens:
            if token['note'] == 'ansible-galaxy login':
                display.vvvvv('removing token: %s' % token['token_last_eight'])
                try:
                    open_url('https://api.github.com/authorizations/%d' % token['id'], url_username=self.github_username,
                             url_password=self.github_password, method='DELETE', force_basic_auth=True)
                except HTTPError as e:
                    msg = http_error_message(e)
                    raise AnsibleError(msg)

    def create_github_token(self):
        '''
        Create a personal authorization token with a note of 'ansible-galaxy login'
        '''
        self.remove_github_token()
        args = json.dumps({"scopes": ["public_repo"], "note": "ansible-galaxy login"})
        try:
            opened = open_url(self.GITHUB_AUTH,
                              url_username=self.github_username,
                              url_password=self.github_password,
                              force_basic_auth=True, data=args)
            resp = opened.read()
            if not PY2:
                resp = resp.decode()
            data = json.loads(resp)
        except HTTPError as e:
            msg = http_error_message(e)
            raise AnsibleError(msg)
        return data['token']
