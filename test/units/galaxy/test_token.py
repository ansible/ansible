# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest

import ansible.constants as C
from ansible.galaxy.token import GalaxyToken, NoTokenSentinel
from ansible.module_utils._text import to_bytes, to_text


@pytest.fixture()
def b_token_file(request, tmp_path_factory):
    b_test_dir = to_bytes(tmp_path_factory.mktemp('test-ÅÑŚÌβŁÈ Token'))
    b_token_path = os.path.join(b_test_dir, b"token.yml")

    token = getattr(request, 'param', None)
    if token:
        with open(b_token_path, 'wb') as token_fd:
            token_fd.write(b"token: %s" % to_bytes(token))

    orig_token_path = C.GALAXY_TOKEN_PATH
    C.GALAXY_TOKEN_PATH = to_text(b_token_path)
    try:
        yield b_token_path
    finally:
        C.GALAXY_TOKEN_PATH = orig_token_path


def test_token_explicit(b_token_file):
    assert GalaxyToken(token="explicit").get() == "explicit"


@pytest.mark.parametrize('b_token_file', ['file'], indirect=True)
def test_token_explicit_override_file(b_token_file):
    assert GalaxyToken(token="explicit").get() == "explicit"


@pytest.mark.parametrize('b_token_file', ['file'], indirect=True)
def test_token_from_file(b_token_file):
    assert GalaxyToken().get() == "file"


def test_token_from_file_missing(b_token_file):
    assert GalaxyToken().get() is None


@pytest.mark.parametrize('b_token_file', ['file'], indirect=True)
def test_token_none(b_token_file):
    assert GalaxyToken(token=NoTokenSentinel).get() is None
