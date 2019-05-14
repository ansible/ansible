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

    @pytest.yield_fixture
    def mapping(self, request):
        """
        Returns object of Mapping mock class
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

        yield M(request.param)

    @pytest.yield_fixture
    def ansible_json_encoder(self):
        yield AnsibleJSONEncoder()

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
