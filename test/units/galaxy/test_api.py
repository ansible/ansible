# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible import context
from ansible.errors import AnsibleError
from ansible.galaxy.api import GalaxyAPI
from ansible.galaxy.token import GalaxyToken
from ansible.utils import context_objects as co


@pytest.fixture(autouse='function')
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    # Required to initialise the GalaxyAPI object
    context.CLIARGS._store = {'ignore_certs': False}
    yield
    co.GlobalCLIArgs._Singleton__instance = None


def test_api_no_auth():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com")
    actual = api._auth_header(required=False)
    assert actual == {}


def test_api_no_auth_but_required():
    expected = "No access token or username set. A token can be set with --api-key, with 'ansible-galaxy login', " \
               "or set in ansible.cfg."
    with pytest.raises(AnsibleError, match=expected):
        GalaxyAPI(None, "test", "https://galaxy.ansible.com")._auth_header()


def test_api_token_auth():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = api._auth_header()
    assert actual == {'Authorization': 'Token my_token'}


def test_api_basic_auth_password():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", username=u"user", password=u"pass")
    actual = api._auth_header()
    assert actual == {'Authorization': 'Basic dXNlcjpwYXNz'}


def test_api_basic_auth_no_password():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", username=u"user",)
    actual = api._auth_header()
    assert actual == {'Authorization': 'Basic dXNlcjo='}
