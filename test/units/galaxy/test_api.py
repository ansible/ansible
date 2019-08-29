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
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {}


def test_api_no_auth_but_required():
    expected = "No access token or username set. A token can be set with --api-key, with 'ansible-galaxy login', " \
               "or set in ansible.cfg."
    with pytest.raises(AnsibleError, match=expected):
        GalaxyAPI(None, "test", "https://galaxy.ansible.com")._add_auth_token({}, "", required=True)


def test_api_token_auth():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {'Authorization': 'Token my_token'}


def test_api_token_auth_with_token_type():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = {}
    api._add_auth_token(actual, "", token_type="Bearer")
    assert actual == {'Authorization': 'Bearer my_token'}


def test_api_token_auth_with_v3_url():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = {}
    api._add_auth_token(actual, "https://galaxy.ansible.com/api/v3/resource/name")
    assert actual == {'Authorization': 'Bearer my_token'}


def test_api_token_auth_with_v2_url():
    token = GalaxyToken(token=u"my_token")
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", token=token)
    actual = {}
    # Add v3 to random part of URL but response should only see the v2 as the full URI path segment.
    api._add_auth_token(actual, "https://galaxy.ansible.com/api/v2/resourcev3/name")
    assert actual == {'Authorization': 'Token my_token'}


def test_api_basic_auth_password():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", username=u"user", password=u"pass")
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {'Authorization': 'Basic dXNlcjpwYXNz'}


def test_api_basic_auth_no_password():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com", username=u"user",)
    actual = {}
    api._add_auth_token(actual, "")
    assert actual == {'Authorization': 'Basic dXNlcjo='}


def test_api_dont_override_auth_header():
    api = GalaxyAPI(None, "test", "https://galaxy.ansible.com")
    actual = {'Authorization': 'Custom token'}
    api._add_auth_token(actual, "")
    assert actual == {'Authorization': 'Custom token'}

