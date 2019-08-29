from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from itertools import count

from ansible.module_utils.identity.keycloak.keycloak import (
    get_token,
    KeycloakError,
)
from ansible.module_utils.six import StringIO
from ansible.module_utils.six.moves.urllib.error import HTTPError


def build_mocked_request(get_id_user_count, response_dict):
    def _mocked_requests(*args, **kwargs):
        url = args[0]
        method = kwargs['method']
        future_response = response_dict.get(url, None)
        return get_response(future_response, method, get_id_user_count)
    return _mocked_requests


def get_response(object_with_future_response, method, get_id_call_count):
    if callable(object_with_future_response):
        return object_with_future_response()
    if isinstance(object_with_future_response, dict):
        return get_response(
            object_with_future_response[method], method, get_id_call_count)
    if isinstance(object_with_future_response, list):
        try:
            call_number = get_id_call_count.__next__()
        except AttributeError:
            # manage python 2 versions.
            call_number = get_id_call_count.next()
        return get_response(
            object_with_future_response[call_number], method, get_id_call_count)
    return object_with_future_response


def create_wrapper(text_as_string):
    """Allow to mock many times a call to one address.
    Without this function, the StringIO is empty for the second call.
    """
    def _create_wrapper():
        return StringIO(text_as_string)
    return _create_wrapper


@pytest.fixture()
def mock_good_connection(mocker):
    token_response = {
        'http://keycloak.url/auth/realms/master/protocol/openid-connect/token': create_wrapper('{"access_token": "alongtoken"}'), }
    return mocker.patch(
        'ansible.module_utils.identity.keycloak.keycloak.open_url',
        side_effect=build_mocked_request(count(), token_response),
        autospec=True
    )


def test_connect_to_keycloak(mock_good_connection):
    keycloak_header = get_token(
        base_url='http://keycloak.url/auth',
        validate_certs=True,
        auth_realm='master',
        client_id='admin-cli',
        auth_username='admin',
        auth_password='admin',
        client_secret=None
    )
    assert keycloak_header == {
        'Authorization': 'Bearer alongtoken',
        'Content-Type': 'application/json'
    }


@pytest.fixture()
def mock_bad_json_returned(mocker):
    token_response = {
        'http://keycloak.url/auth/realms/master/protocol/openid-connect/token': create_wrapper('{"access_token":'), }
    return mocker.patch(
        'ansible.module_utils.identity.keycloak.keycloak.open_url',
        side_effect=build_mocked_request(count(), token_response),
        autospec=True
    )


def test_bad_json_returned(mock_bad_json_returned):
    with pytest.raises(KeycloakError) as raised_error:
        get_token(
            base_url='http://keycloak.url/auth',
            validate_certs=True,
            auth_realm='master',
            client_id='admin-cli',
            auth_username='admin',
            auth_password='admin',
            client_secret=None
        )
    # cannot check all the message, different errors message for the value
    # error in python 2.6, 2.7 and 3.*.
    assert (
        'API returned invalid JSON when trying to obtain access token from '
        'http://keycloak.url/auth/realms/master/protocol/openid-connect/token: '
    ) in str(raised_error.value)


def raise_401(url):
    def _raise_401():
        raise HTTPError(url=url, code=401, msg='Unauthorized', hdrs='', fp=StringIO(''))
    return _raise_401


@pytest.fixture()
def mock_401_returned(mocker):
    token_response = {
        'http://keycloak.url/auth/realms/master/protocol/openid-connect/token': raise_401(
            'http://keycloak.url/auth/realms/master/protocol/openid-connect/token'),
    }
    return mocker.patch(
        'ansible.module_utils.identity.keycloak.keycloak.open_url',
        side_effect=build_mocked_request(count(), token_response),
        autospec=True
    )


def test_error_returned(mock_401_returned):
    with pytest.raises(KeycloakError) as raised_error:
        get_token(
            base_url='http://keycloak.url/auth',
            validate_certs=True,
            auth_realm='master',
            client_id='admin-cli',
            auth_username='notadminuser',
            auth_password='notadminpassword',
            client_secret=None
        )
    assert str(raised_error.value) == (
        'Could not obtain access token from http://keycloak.url'
        '/auth/realms/master/protocol/openid-connect/token: '
        'HTTP Error 401: Unauthorized'
    )


@pytest.fixture()
def mock_json_without_token_returned(mocker):
    token_response = {
        'http://keycloak.url/auth/realms/master/protocol/openid-connect/token': create_wrapper('{"not_token": "It is not a token"}'), }
    return mocker.patch(
        'ansible.module_utils.identity.keycloak.keycloak.open_url',
        side_effect=build_mocked_request(count(), token_response),
        autospec=True
    )


def test_json_without_token_returned(mock_json_without_token_returned):
    with pytest.raises(KeycloakError) as raised_error:
        get_token(
            base_url='http://keycloak.url/auth',
            validate_certs=True,
            auth_realm='master',
            client_id='admin-cli',
            auth_username='admin',
            auth_password='admin',
            client_secret=None
        )
    assert str(raised_error.value) == (
        'Could not obtain access token from http://keycloak.url'
        '/auth/realms/master/protocol/openid-connect/token'
    )
