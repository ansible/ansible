# Copyright 2018, Matt Martz <matt@sivel.net>
# Copyright 2019, Andrew Klychkov @Andersson007 <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import json

import pytest

from datetime import date, datetime

from ansible.module_utils.common._collections_compat import Mapping
from ansible.parsing.ajson import AnsibleJSONEncoder, AnsibleJSONDecoder
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


def test_AnsibleJSONDecoder_vault():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/ajson.json')) as f:
        data = json.load(f, cls=AnsibleJSONDecoder)

    assert isinstance(data['password'], AnsibleVaultEncryptedUnicode)
    assert isinstance(data['bar']['baz'][0]['password'], AnsibleVaultEncryptedUnicode)
    assert isinstance(data['foo']['password'], AnsibleVaultEncryptedUnicode)


class TestAnsibleJSONEncoder():
    """
    Class for testing AnsibleJSONEncoder
    """

    #################
    # Fixture section

    @pytest.fixture
    def mapping(self, request):
        """
        Returns object of Mapping mock class.
        The object is used for testing handling of Mapping objects
        in AnsibleJSONEncoder.default().
        Using a plain dictionary instead is not suitable because
        it is handled by default encoder of the superclass (json.JSONEncoder).
        """
        class M(Mapping):
            def __init__(self, *args, **kwargs):
                self.__dict__.update(*args, **kwargs)

            def __getitem__(self, key):
                return self.__dict__[key]

            def __iter__(self):
                return iter(self.__dict__)

            def __len__(self):
                return len(self.__dict__)

        return M(request.param)

    @pytest.fixture
    def ansible_json_encoder(self):
        return AnsibleJSONEncoder()

    @pytest.fixture
    def vault_data(self):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures/ajson.json')) as f:
            data = json.load(f, cls=AnsibleJSONDecoder)
        return (data['password'], data['bar']['baz'][0]['password'])

    # The end of the fixture section
    ################################

    @pytest.mark.parametrize(
        'test_input,expected',
        [
            (datetime(2019, 5, 14, 13, 39, 38, 569047), '2019-05-14T13:39:38.569047'),
            (datetime(2019, 5, 14, 13, 47, 16, 923866), '2019-05-14T13:47:16.923866'),
            (date(2019, 5, 14), '2019-05-14'),
            (date(2020, 5, 14), '2020-05-14'),
        ]
    )
    def test_date_datetime(self, ansible_json_encoder, test_input, expected):
        """
        Test for passing datetime.date or datetime.datetime objects
        to AnsibleJSONEncoder.default()
        """
        assert(ansible_json_encoder.default(test_input) == expected)

    @pytest.mark.parametrize(
        'mapping,expected',
        [
            ({1: 1}, {1: 1}),
            ({2: 2}, {2: 2}),
            ({1: 2}, {1: 2}),
            ({2: 1}, {2: 1}),
        ], indirect=['mapping']
    )
    def test_mapping(self, ansible_json_encoder, mapping, expected):
        """
        Test for passing Mapping object to AnsibleJSONEncoder.default()
        """
        m = mapping
        assert(isinstance(m, Mapping))
        assert(ansible_json_encoder.default(m) == expected)

    # The pytest.mark.parametrize decorator is not used for this function
    # because, at least, it's difficult to read it in this particular case.
    def test_ansible_json_decoder_vault(self, ansible_json_encoder, vault_data):
        """
        Test for passing AnsibleVaultEncryptedUnicode to AnsibleJSONEncoder.default()
        """

        # prepare test data and expected results:
        data_0, data_1 = vault_data[0], vault_data[1]

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

        # previously check that test data is a suitable type:
        assert(isinstance(data_0, AnsibleVaultEncryptedUnicode))
        assert(isinstance(data_1, AnsibleVaultEncryptedUnicode))

        # main assertions:
        assert(ansible_json_encoder.default(data_0) == {'__ansible_vault': expected_0})
        assert(ansible_json_encoder.default(data_1) == {'__ansible_vault': expected_1})

    @pytest.mark.parametrize(
        'test_input,expected',
        [
            ({1: 'first'}, {1: 'first'}),
            ({2: 'second'}, {2: 'second'}),
        ]
    )
    def test_default_encoder(self, ansible_json_encoder, test_input, expected):
        """
        Test for the default encoder of json.JSONEncoder superclass
        by passing objects of different classes that are not tested above
        """
        assert(ansible_json_encoder.default(test_input) == expected)

    @pytest.mark.xfail(raises=TypeError)
    @pytest.mark.parametrize(
        'test_input,expected',
        [
            (1, 1),
            (1.1, 1.1),
            ('string', 'string'),
            ([1, 2], [1, 2]),
            (True, True),
            (None, None),
            (set('set'), ''),
        ]
    )
    def test_default_encoder_unserializable(self, ansible_json_encoder, test_input, expected):
        """
        Test for the default encoder of json.JSONEncoder superclass
        by passing unserializable objects of different classes.
        It must fail with TypeError 'object is not serializable'
        """
        assert(ansible_json_encoder.default(test_input) == expected)
