# Copyright 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import json

from decimal import Decimal

from ansible.module_utils._text import to_native
from ansible.parsing.ajson import AnsibleJSONDecoder, AnsibleJSONEncoder
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


def test_AnsibleJSONDecoder_vault():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/ajson.json')) as f:
        data = json.load(f, cls=AnsibleJSONDecoder)

    assert isinstance(data['password'], AnsibleVaultEncryptedUnicode)
    assert isinstance(data['bar']['baz'][0]['password'], AnsibleVaultEncryptedUnicode)
    assert isinstance(data['foo']['password'], AnsibleVaultEncryptedUnicode)


def test_AnsibleJSONEncoder_decimal():
    test_numbers = (
        (1, 1.0),
        (1.0, 1.0),
        (1.155789, 1.155789),
    )

    for test in test_numbers:
        value = Decimal(test[0])
        test_data = {'number': value}
        data = json.dumps(test_data, cls=AnsibleJSONEncoder)
        assert '{{"number": {0}}}'.format(to_native(test[1])) == data
