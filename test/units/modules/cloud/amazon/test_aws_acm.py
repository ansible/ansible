# (c) 2019 Telstra Corporation Limited
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible.modules.cloud.amazon.aws_acm import pem_chain_split, chain_compare
from ansible.module_utils._text import to_bytes, to_text
from pprint import pprint


def test_chain_compare():

    # The functions we're testing take module as an argument
    # Just so they can call module.fail_json
    # Let's just use None for the unit tests,
    # Because they shouldn't fail
    # And if they do, fail_json is not applicable
    module = None

    fixture_suffix = 'test/units/modules/cloud/amazon/fixtures/certs'

    # Test chain split function on super simple (invalid) certs
    expected = ['aaa', 'bbb', 'ccc']

    for fname in ['simple-chain-a.cert', 'simple-chain-b.cert']:
        path = fixture_suffix + '/' + fname
        with open(path, 'r') as f:
            pem = to_text(f.read())
        actual = pem_chain_split(module, pem)
        actual = [a.strip() for a in actual]
        if actual != expected:
            print("Expected:")
            pprint(expected)
            print("Actual:")
            pprint(actual)
            raise AssertionError("Failed to properly split %s" % fname)

    # Now test real chains
    # chains with same same_as should be considered equal
    test_chains = [
        {  # Original Cert chain
            'path': fixture_suffix + '/chain-1.0.cert',
            'same_as': 1,
            'length': 3
        },
        {  # Same as 1.0, but longer PEM lines
            'path': fixture_suffix + '/chain-1.1.cert',
            'same_as': 1,
            'length': 3
        },
        {  # Same as 1.0, but without the stuff before each --------
            'path': fixture_suffix + '/chain-1.2.cert',
            'same_as': 1,
            'length': 3
        },
        {  # Same as 1.0, but in a different order, so should be considered different
            'path': fixture_suffix + '/chain-1.3.cert',
            'same_as': 2,
            'length': 3
        },
        {  # Same as 1.0, but with last link missing
            'path': fixture_suffix + '/chain-1.4.cert',
            'same_as': 3,
            'length': 2
        },
        {  # Completely different cert chain to all the others
            'path': fixture_suffix + '/chain-4.cert',
            'same_as': 4,
            'length': 3
        },
        {  # Single cert
            'path': fixture_suffix + '/a.pem',
            'same_as': 5,
            'length': 1
        },
        {  # a different, single cert
            'path': fixture_suffix + '/b.pem',
            'same_as': 6,
            'length': 1
        }
    ]

    for chain in test_chains:
        with open(chain['path'], 'r') as f:
            chain['pem_text'] = to_text(f.read())

        # Test to make sure our regex isn't too greedy
        chain['split'] = pem_chain_split(module, chain['pem_text'])
        if len(chain['split']) != chain['length']:
            print("Cert before split")
            print(chain['pem_text'])
            print("Cert after split")
            pprint(chain['split'])
            print("path: %s" % chain['path'])
            print("Expected chain length: %d" % chain['length'])
            print("Actual chain length: %d" % len(chain['split']))
            raise AssertionError("Chain %s was not split properly" % chain['path'])

    for chain_a in test_chains:
        for chain_b in test_chains:
            expected = (chain_a['same_as'] == chain_b['same_as'])

            # Now test the comparison function
            actual = chain_compare(module, chain_a['pem_text'], chain_b['pem_text'])
            if expected != actual:
                print("Error, unexpected comparison result between \n%s\nand\n%s" % (chain_a['path'], chain_b['path']))
                print("Expected %s got %s" % (str(expected), str(actual)))
            assert(expected == actual)
