# Copyright 2018, Matt Martz <matt@sivel.net>
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import json
import pathlib

import pytest

from collections.abc import Mapping
from datetime import date, datetime, timezone, timedelta

from ansible._internal._json._legacy_encoder import LegacyControllerJSONEncoder
from ansible.module_utils.common.json import get_encoder, get_decoder
from ansible.parsing.vault import EncryptedString, AnsibleVaultError
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible._internal._json._profiles import _legacy


def test_AnsibleJSONDecoder_vault(_empty_vault_secrets_context):
    profile = _legacy

    with open(os.path.join(os.path.dirname(__file__), 'fixtures/ajson.json')) as f:
        data = json.load(f, cls=get_decoder(profile))

    assert isinstance(data['password'], EncryptedString)
    with pytest.raises(AnsibleVaultError):
        str(data['password'])

    assert isinstance(data['bar']['baz'][0]['password'], EncryptedString)
    with pytest.raises(AnsibleVaultError):
        str(data['bar']['baz'][0]['password'])

    assert isinstance(data['foo']['password'], EncryptedString)
    with pytest.raises(AnsibleVaultError):
        str(data['foo']['password'])


def vault_data():
    """
    Prepare vault test data for AnsibleJSONEncoder.default().

    Return a list of tuples (input, expected).
    """

    profile = _legacy

    raw_data = TrustedAsTemplate().tag((pathlib.Path(__file__).parent / 'fixtures/ajson.json').read_text())
    data = json.loads(raw_data, cls=get_decoder(profile))

    data_0 = data['password']
    data_1 = data['bar']['baz'][0]['password']

    expected_0 = (u'$ANSIBLE_VAULT;1.1;AES256\n34646264306632313333393636316'
                  '562356435376162633631326264383934326565333633366238\n3863'
                  '373264326461623132613931346165636465346337310a32643431383'
                  '0316337393263616439\n646539373134633963666338613632666334'
                  '65663730303633323534363331316164623237363831\n35363335613'
                  '93238370a313330316263373938326162386433313336613532653538'
                  '376662306435\n3339\n')

    expected_1 = (u'$ANSIBLE_VAULT;1.1;AES256\n34646264306632313333393636316'
                  '562356435376162633631326264383934326565333633366238\n3863'
                  '373264326461623132613931346165636465346337310a32643431383'
                  '0316337393263616439\n646539373134633963666338613632666334'
                  '65663730303633323534363331316164623237363831\n35363335613'
                  '93238370a313330316263373938326162386433313336613532653538'
                  '376662306435\n3338\n')

    return [
        (data_0, expected_0),
        (data_1, expected_1),
    ]


class TestAnsibleJSONEncoder:

    """
    Namespace for testing AnsibleJSONEncoder.
    """

    @pytest.fixture(scope='class')
    def mapping(self, request):
        """
        Returns object of Mapping mock class.

        The object is used for testing handling of Mapping objects
        in AnsibleJSONEncoder.default().
        Using a plain dictionary instead is not suitable because
        it is handled by default encoder of the superclass (json.JSONEncoder).
        """

        class M(Mapping):

            """Mock mapping class."""

            def __init__(self, *args, **kwargs):
                self.__dict__.update(*args, **kwargs)

            def __getitem__(self, key):
                return self.__dict__[key]

            def __iter__(self):
                return iter(self.__dict__)

            def __len__(self):
                return len(self.__dict__)

        mapping = M(request.param)

        assert isinstance(len(mapping), int)   # ensure coverage of __len__

        return mapping

    @pytest.fixture
    def ansible_json_encoder(self):
        """Return AnsibleJSONEncoder object."""
        return LegacyControllerJSONEncoder()

    ###############
    # Test methods:

    @pytest.mark.parametrize(
        'test_input,expected',
        [
            (datetime(2019, 5, 14, 13, 39, 38, 569047), '2019-05-14T13:39:38.569047'),
            (datetime(2019, 5, 14, 13, 47, 16, 923866), '2019-05-14T13:47:16.923866'),
            (date(2019, 5, 14), '2019-05-14'),
            (date(2020, 5, 14), '2020-05-14'),
            (datetime(2019, 6, 15, 14, 45, tzinfo=timezone.utc), '2019-06-15T14:45:00+00:00'),
            (datetime(2019, 6, 15, 14, 45, tzinfo=timezone(timedelta(hours=1, minutes=40))), '2019-06-15T14:45:00+01:40'),
        ]
    )
    def test_date_datetime(self, ansible_json_encoder, test_input, expected):
        """
        Test for passing datetime.date or datetime.datetime objects to AnsibleJSONEncoder.default().
        """
        assert ansible_json_encoder.default(test_input) == expected

    @pytest.mark.parametrize(
        'mapping,expected',
        [
            ({'1': 1}, {'1': 1}),
            ({'2': 2}, {'2': 2}),
            ({'1': 2}, {'1': 2}),
            ({'2': 1}, {'2': 1}),
        ], indirect=['mapping'],
    )
    def test_mapping(self, ansible_json_encoder, mapping, expected):
        """
        Test for passing Mapping object to AnsibleJSONEncoder.default().
        """
        assert ansible_json_encoder.default(mapping) == expected

    @pytest.mark.parametrize('test_input,expected', vault_data())
    def test_ansible_json_encoder_vault(self, test_input, expected):
        """
        Test for passing vaulted values to AnsibleJSONEncoder.default().
        """
        profile = _legacy
        assert json.dumps(test_input, cls=get_encoder(profile)) == '{"__ansible_vault": "%s"}' % expected.replace('\n', '\\n')

    @pytest.mark.parametrize(
        'test_input,expected',
        [
            ({'1': 'first'}, {'1': 'first'}),
            ({'2': 'second'}, {'2': 'second'}),
        ]
    )
    def test_default_encoder(self, ansible_json_encoder, test_input, expected):
        """
        Test for the default encoder of AnsibleJSONEncoder.default().

        If objects of different classes that are not tested above were passed,
        AnsibleJSONEncoder.default() invokes 'default()' method of json.JSONEncoder superclass.
        """
        assert ansible_json_encoder.default(test_input) == expected


@pytest.mark.parametrize("trust_input_str", (
    True,
    False
))
def test_string_trust_propagation(trust_input_str: bool) -> None:
    """Verify that input trust propagation behaves as expected. The presence of trust on the input string determines if trust is applied to outputs."""
    data = '{"foo": "bar"}'

    if trust_input_str:
        data = TrustedAsTemplate().tag(data)

    res = json.loads(data, cls=_legacy.Decoder)

    assert trust_input_str == TrustedAsTemplate.is_tagged_on(res['foo'])
