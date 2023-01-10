# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import json
import os
import pytest

from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers, RSAPrivateNumbers
from cryptography.hazmat.primitives.hashes import SHA256
from datetime import datetime, timedelta, timezone
from io import StringIO

import ansible.constants as C
import ansible.galaxy.token as token_lib
from ansible.cli.galaxy import GalaxyCLI, SERVER_DEF
from ansible.galaxy.token import GalaxyToken, NoTokenSentinel, KeycloakToken, b64urlsafe_to_long
from ansible.module_utils.common.text.converters import to_bytes, to_text


def create_token_payload(private_key, expiration):
    header = {'alg': 'RS256', 'typ': 'JWT', 'kid': 'key_id'}
    payload = {'exp': expiration}
    signing_input = json_to_b64url(header) + b'.' + json_to_b64url(payload)
    signature = private_key.sign(signing_input, PKCS1v15(), SHA256())
    b64_signature = base64.urlsafe_b64encode(signature)
    return to_text(signing_input + b'.' + b64_signature, errors='surrogate_or_strict')


def json_to_b64url(data):
    return base64.urlsafe_b64encode(
        to_bytes(json.dumps(data), errors='surrogate_or_strict')
    )


@pytest.fixture
def public_key_numbers():
    return {
        "n": (
            "ofgWCuLjybRlzo0tZWJjNiuSfb4p4fAkd_wWJcyQoTbji9k0l8W26mPddxHmfHQp-"
            "Vaw-4qPCJrcS2mJPMEzP1Pt0Bm4d4QlL-yRT-SFd2lZS-pCgNMsD1W_YpRPEwOWvG"
            "6b32690r2jZ47soMZo9wGzjb_7OMg0LOL-bSf63kpaSHSXndS5z5rexMdbBYUsLA9"
            "e-KXBdQOS-UTo7WTBEMa2R2CapHg665xsmtdVMTBQY4uDZlxvb3qCo5ZwKh9kG4LT"
            "6_I5IhlJH7aGhyxXFvUK-DWNmoudF8NAco9_h9iaGNj8q2ethFkMLs91kzk2PAcDT"
            "W9gb54h4FRWyuXpoQ"
        ),
        "e": "AQAB"
    }


@pytest.fixture
def private_key(public_key_numbers):
    private_key_data = {
        "kty": "RSA",
        "d": (
            "Eq5xpGnNCivDflJsRQBXHx1hdR1k6Ulwe2JZD50LpXyWPEAeP88vLNO97IjlA7_GQ"
            "5sLKMgvfTeXZx9SE-7YwVol2NXOoAJe46sui395IW_GO-pWJ1O0BkTGoVEn2bKVRU"
            "Cgu-GjBVaYLU6f3l9kJfFNS3E0QbVdxzubSu3Mkqzjkn439X0M_V51gfpRLI9JYan"
            "rC4D4qAdGcopV_0ZHHzQlBjudU2QvXt4ehNYTCBr6XCLQUShb1juUO1ZdiYoFaFQT"
            "5Tw8bGUl_x_jTj3ccPDVZFD9pIuhLhBOneufuBiB4cS98l2SR_RQyGWSeWjnczT0Q"
            "U91p1DhOVRuOopznQ"
        ),
        "p": (
            "4BzEEOtIpmVdVEZNCqS7baC4crd0pqnRH_5IB3jw3bcxGn6QLvnEtfdUdiYrqBdss"
            "1l58BQ3KhooKeQTa9AB0Hw_Py5PJdTJNPY8cQn7ouZ2KKDcmnPGBY5t7yLc1QlQ5x"
            "HdwW1VhvKn-nXqhJTBgIPgtldC-KDV5z-y2XDwGUc"
        ),
        "q": (
            "uQPEfgmVtjL0Uyyx88GZFF1fOunH3-7cepKmtH4pxhtCoHqpWmT8YAmZxaewHgHAj"
            "LYsp1ZSe7zFYHj7C6ul7TjeLQeZD_YwD66t62wDmpe_HlB-TnBA-njbglfIsRLtXl"
            "nDzQkv5dTltRJ11BKBBypeeF6689rjcJIDEz9RWdc"
        ),
        "dp": (
            "BwKfV3Akq5_MFZDFZCnW-wzl-CCo83WoZvnLQwCTeDv8uzluRSnm71I3QCLdhrqE2"
            "e9YkxvuxdBfpT_PI7Yz-FOKnu1R6HsJeDCjn12Sk3vmAktV2zb34MCdy7cpdTh_YV"
            "r7tss2u6vneTwrA86rZtu5Mbr1C1XsmvkxHQAdYo0"
        ),
        "dq": (
            "h_96-mK1R_7glhsum81dZxjTnYynPbZpHziZjeeHcXYsXaaMwkOlODsWa7I9xXDoR"
            "wbKgB719rrmI2oKr6N3Do9U0ajaHF-NKJnwgjMd2w9cjz3_-kyNlxAr2v4IKhGNpm"
            "M5iIgOS1VZnOZ68m6_pbLBSp3nssTdlqvd0tIiTHU"
        ),
        "qi": (
            "IYd7DHOhrWvxkwPQsRM2tOgrjbcrfvtQJipd-DlcxyVuuM9sQLdgjVk2oy26F0Emp"
            "ScGLq2MowX7fhd_QJQ3ydy5cY7YIBi87w93IKLEdfnbJtoOPLUW0ITrJReOgo1cq9"
            "SbsxYawBgfp_gh6A5603k2-ZQwVK0JKSHuLFkuQ3U"
        ),
    }
    private_key_data.update(public_key_numbers)

    e = b64urlsafe_to_long(private_key_data['e'])
    n = b64urlsafe_to_long(private_key_data['n'])
    public_numbers = RSAPublicNumbers(e, n)

    p = b64urlsafe_to_long(private_key_data['p'])
    q = b64urlsafe_to_long(private_key_data['q'])
    d = b64urlsafe_to_long(private_key_data['d'])
    dmp1 = b64urlsafe_to_long(private_key_data['dp'])
    dmq1 = b64urlsafe_to_long(private_key_data['dq'])
    iqmp = b64urlsafe_to_long(private_key_data['qi'])

    private_numbers = RSAPrivateNumbers(p, q, d, dmp1, dmq1, iqmp, public_numbers)
    return private_numbers.private_key()


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


def test_client_id(monkeypatch, mocker):
    monkeypatch.setattr(C, 'GALAXY_SERVER_LIST', ['server1', 'server2'])

    test_server_config = {option[0]: None for option in SERVER_DEF}
    test_server_config.update(
        {
            'url': 'http://my_galaxy_ng:8000/api/automation-hub/',
            'auth_url': 'http://my_keycloak:8080/auth/realms/myco/protocol/openid-connect/token',
            'client_id': 'galaxy-ng',
            'token': 'access_token',
        }
    )

    test_server_default = {option[0]: None for option in SERVER_DEF}
    test_server_default.update(
        {
            'url': 'https://cloud.redhat.com/api/automation-hub/',
            'auth_url': 'https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token',
            'token': 'access_token',
        }
    )

    get_plugin_options = mocker.MagicMock(side_effect=[test_server_config, test_server_default])
    monkeypatch.setattr(C.config, 'get_plugin_options', get_plugin_options)

    cli_args = [
        'ansible-galaxy',
        'collection',
        'install',
        'namespace.collection:1.0.0',
    ]

    galaxy_cli = GalaxyCLI(args=cli_args)
    mock_execute_install = mocker.MagicMock()
    monkeypatch.setattr(galaxy_cli, '_execute_install_collection', mock_execute_install)
    galaxy_cli.run()

    assert galaxy_cli.api_servers[0].token.client_id == 'galaxy-ng'
    assert galaxy_cli.api_servers[1].token.client_id == 'cloud-services'


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


def test_parse_bearer_token(monkeypatch, mocker):
    monkeypatch.setattr(token_lib, 'REQUIRED_JWT_HEADER_KEYS', {'alg'})
    monkeypatch.setattr(token_lib, 'REQUIRED_JWT_HEADER_VALUES', {'alg': ['RS256']})

    # result from https://www.rfc-editor.org/rfc/rfc7515#appendix-A.2.1 to test validating A.2.2
    token_info = (
        "eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0"
        "dHA6Ly9leGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ.cC4hiUPoj9Eetdgtv3hF80EGrhuB__"
        "dzERat0XF9g2VtQgr9PJbu3XOiZj5RZmh7AAuHIm4Bh-0Qc_lF5YKt_O8W2Fp5jujGbds9uJd"
        "bF9CUAr7t1dnZcAcQjbKBYNX4BAynRFdiuB--f_nZLgrnbyTyWzO75vRK5h6xBArLIARNPvkS"
        "jtQBMHlb1L07Qe7K0GarZRmB_eSN9383LcOLn6_dO--xi12jzDwusC-eOkHWEsqtFZESc6BfI"
        "7noOPqvhJ1phCnvWh6IeYI2w9QOYEUipUTI8np6LbgGY9Fs98rqVt5AXLIhWkWywlVmtVrBp0"
        "igcN_IoypGlUPQGe77Rw"
    )

    e = "AQAB"
    n = (
        "ofgWCuLjybRlzo0tZWJjNiuSfb4p4fAkd_wWJcyQoTbji9k0l8W26mPddxHmfHQp-Vaw-4qPC"
        "JrcS2mJPMEzP1Pt0Bm4d4QlL-yRT-SFd2lZS-pCgNMsD1W_YpRPEwOWvG6b32690r2jZ47soM"
        "Zo9wGzjb_7OMg0LOL-bSf63kpaSHSXndS5z5rexMdbBYUsLA9e-KXBdQOS-UTo7WTBEMa2R2C"
        "apHg665xsmtdVMTBQY4uDZlxvb3qCo5ZwKh9kG4LT6_I5IhlJH7aGhyxXFvUK-DWNmoudF8NA"
        "co9_h9iaGNj8q2ethFkMLs91kzk2PAcDTW9gb54h4FRWyuXpoQ"
    )
    public_numbers = RSAPublicNumbers(b64urlsafe_to_long(e), b64urlsafe_to_long(n))
    monkeypatch.setattr(token_lib, 'get_public_numbers', mocker.MagicMock(return_value=(e, n)))
    token_lib.parse_bearer_token(token_info)

    with pytest.raises(token_lib.InvalidSignature):
        token_lib.parse_bearer_token(token_info + 'wrongsig')


@pytest.mark.parametrize(('exp_delta', 'expired'), [(1, True), (-15, True), (15, False)])
def test_keycloak_expiration(exp_delta, expired, monkeypatch, private_key, public_key_numbers, mocker):
    exp_timestamp = int((datetime.now(tz=timezone.utc) + timedelta(minutes=exp_delta)).timestamp())
    signed_payload = create_token_payload(private_key, exp_timestamp)

    token = KeycloakToken(access_token='', auth_url='')
    token.jwks = [{'kid': 'key_id', 'e': public_key_numbers['e'], 'n': public_key_numbers['n']}]

    mock_response = json.dumps({"access_token": "token", "id_token": signed_payload})
    with StringIO(mock_response) as response:
        monkeypatch.setattr(token_lib, 'open_url', mocker.MagicMock(return_value=response))
        token.get()

    assert token.expired == expired
