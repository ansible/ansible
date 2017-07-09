# coding: utf-8
# (c) 2017, Toshio Kuratomi <tkuratomi@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ast

import pytest

from ansible.parsing import metadata as md


LICENSE = b"""# some license text boilerplate
# That we have at the top of files
"""

FUTURE_IMPORTS = b"""
from __future__ import (absolute_import, division, print_function)
"""

REGULAR_IMPORTS = b"""
import test
from foo import bar
"""

STANDARD_METADATA = b"""
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}
"""

TEXT_STD_METADATA = b"""
ANSIBLE_METADATA = u'''
metadata_version: '1.0'
status:
  - 'stableinterface'
supported_by: 'core'
'''
"""

BYTES_STD_METADATA = b"""
ANSIBLE_METADATA = b'''
metadata_version: '1.0'
status:
  - 'stableinterface'
supported_by: 'core'
'''
"""

TRAILING_COMMENT_METADATA = b"""
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'} # { Testing }
"""

MULTIPLE_STATEMENTS_METADATA = b"""
DOCUMENTATION = "" ; ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'} ; RETURNS = ""
"""

EMBEDDED_COMMENT_METADATA = b"""
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    # { Testing }
                    'supported_by': 'core'}
"""

HASH_SYMBOL_METADATA = b"""
ANSIBLE_METADATA = {'metadata_version': '1.0 # 4',
                    'status': ['stableinterface'],
                    'supported_by': 'core # Testing '}
"""

HASH_SYMBOL_METADATA = b"""
ANSIBLE_METADATA = {'metadata_version': '1.0 # 4',
                    'status': ['stableinterface'],
                    'supported_by': 'core # Testing '}
"""

HASH_COMBO_METADATA = b"""
ANSIBLE_METADATA = {'metadata_version': '1.0 # 4',
                    'status': ['stableinterface'],
                    # { Testing }
                    'supported_by': 'core'} # { Testing }
"""

METADATA = {'metadata_version': '1.0', 'status': ['stableinterface'], 'supported_by': 'core'}
HASH_SYMBOL_METADATA = {'metadata_version': '1.0 # 4', 'status': ['stableinterface'], 'supported_by': 'core'}

METADATA_EXAMPLES = (
    # Standard import
    (LICENSE + FUTURE_IMPORTS + STANDARD_METADATA + REGULAR_IMPORTS,
     (METADATA, 5, 0, 7, 42, ['ANSIBLE_METADATA'])),
    # Metadata at end of file
    (LICENSE + FUTURE_IMPORTS + REGULAR_IMPORTS + STANDARD_METADATA.rstrip(),
     (METADATA, 8, 0, 10, 42, ['ANSIBLE_METADATA'])),
    # Metadata at beginning of file
    (STANDARD_METADATA + LICENSE + REGULAR_IMPORTS,
     (METADATA, 1, 0, 3, 42, ['ANSIBLE_METADATA'])),

    # Standard import with a trailing comment
    (LICENSE + FUTURE_IMPORTS + TRAILING_COMMENT_METADATA + REGULAR_IMPORTS,
     (METADATA, 5, 0, 7, 42, ['ANSIBLE_METADATA'])),
    # Metadata at end of file with a trailing comment
    (LICENSE + FUTURE_IMPORTS + REGULAR_IMPORTS + TRAILING_COMMENT_METADATA.rstrip(),
     (METADATA, 8, 0, 10, 42, ['ANSIBLE_METADATA'])),
    # Metadata at beginning of file with a trailing comment
    (TRAILING_COMMENT_METADATA + LICENSE + REGULAR_IMPORTS,
     (METADATA, 1, 0, 3, 42, ['ANSIBLE_METADATA'])),

    # FIXME: Current code cannot handle multiple statements on the same line.
    # This is bad style so we're just going to ignore it for now
    # Standard import with other statements on the same line
    # (LICENSE + FUTURE_IMPORTS + MULTIPLE_STATEMENTS_METADATA + REGULAR_IMPORTS,
    #  (METADATA, 5, 0, 7, 42, ['ANSIBLE_METADATA'])),
    # Metadata at end of file with other statements on the same line
    # (LICENSE + FUTURE_IMPORTS + REGULAR_IMPORTS + MULTIPLE_STATEMENTS_METADATA.rstrip(),
    #  (METADATA, 8, 0, 10, 42, ['ANSIBLE_METADATA'])),
    # Metadata at beginning of file with other statements on the same line
    # (MULTIPLE_STATEMENTS_METADATA + LICENSE + REGULAR_IMPORTS,
    #  (METADATA, 1, 0, 3, 42, ['ANSIBLE_METADATA'])),

    # Standard import with comment inside the metadata
    (LICENSE + FUTURE_IMPORTS + EMBEDDED_COMMENT_METADATA + REGULAR_IMPORTS,
     (METADATA, 5, 0, 8, 42, ['ANSIBLE_METADATA'])),
    # Metadata at end of file with comment inside the metadata
    (LICENSE + FUTURE_IMPORTS + REGULAR_IMPORTS + EMBEDDED_COMMENT_METADATA.rstrip(),
     (METADATA, 8, 0, 11, 42, ['ANSIBLE_METADATA'])),
    # Metadata at beginning of file with comment inside the metadata
    (EMBEDDED_COMMENT_METADATA + LICENSE + REGULAR_IMPORTS,
     (METADATA, 1, 0, 4, 42, ['ANSIBLE_METADATA'])),

    # FIXME: Current code cannot handle hash symbols in the last element of
    # the metadata.  Fortunately, the metadata currently fully specifies all
    # the strings inside of metadata and none of them can contain a hash.
    # Need to fix this to future-proof it against strings containing hashes
    # Standard import with hash symbol in metadata
    # (LICENSE + FUTURE_IMPORTS + HASH_SYMBOL_METADATA + REGULAR_IMPORTS,
    #  (HASH_SYMBOL_METADATA, 5, 0, 7, 53, ['ANSIBLE_METADATA'])),
    # Metadata at end of file with hash symbol in metadata
    # (LICENSE + FUTURE_IMPORTS + REGULAR_IMPORTS + HASH_SYMBOL_HASH_SYMBOL_METADATA.rstrip(),
    #  (HASH_SYMBOL_METADATA, 8, 0, 10, 53, ['ANSIBLE_METADATA'])),
    # Metadata at beginning of file with hash symbol in metadata
    # (HASH_SYMBOL_HASH_SYMBOL_METADATA + LICENSE + REGULAR_IMPORTS,
    #  (HASH_SYMBOL_METADATA, 1, 0, 3, 53, ['ANSIBLE_METADATA'])),

    # Standard import with a bunch of hashes everywhere
    (LICENSE + FUTURE_IMPORTS + HASH_COMBO_METADATA + REGULAR_IMPORTS,
     (HASH_SYMBOL_METADATA, 5, 0, 8, 42, ['ANSIBLE_METADATA'])),
    # Metadata at end of file with a bunch of hashes everywhere
    (LICENSE + FUTURE_IMPORTS + REGULAR_IMPORTS + HASH_COMBO_METADATA.rstrip(),
     (HASH_SYMBOL_METADATA, 8, 0, 11, 42, ['ANSIBLE_METADATA'])),
    # Metadata at beginning of file with a bunch of hashes everywhere
    (HASH_COMBO_METADATA + LICENSE + REGULAR_IMPORTS,
     (HASH_SYMBOL_METADATA, 1, 0, 4, 42, ['ANSIBLE_METADATA'])),

    # Standard import with a junk ANSIBLE_METADATA as well
    (LICENSE + FUTURE_IMPORTS + b"\nANSIBLE_METADATA = 10\n" + HASH_COMBO_METADATA + REGULAR_IMPORTS,
     (HASH_SYMBOL_METADATA, 7, 0, 10, 42, ['ANSIBLE_METADATA'])),
)

# FIXME: String/yaml metadata is not implemented yet.  Need more test cases once it is implemented
STRING_METADATA_EXAMPLES = (
    # Standard import
    (LICENSE + FUTURE_IMPORTS + TEXT_STD_METADATA + REGULAR_IMPORTS,
     (METADATA, 5, 0, 10, 3, ['ANSIBLE_METADATA'])),
    # Metadata at end of file
    (LICENSE + FUTURE_IMPORTS + REGULAR_IMPORTS + TEXT_STD_METADATA.rstrip(),
     (METADATA, 8, 0, 13, 3, ['ANSIBLE_METADATA'])),
    # Metadata at beginning of file
    (TEXT_STD_METADATA + LICENSE + REGULAR_IMPORTS,
     (METADATA, 1, 0, 6, 3, ['ANSIBLE_METADATA'])),

    # Standard import
    (LICENSE + FUTURE_IMPORTS + BYTES_STD_METADATA + REGULAR_IMPORTS,
     (METADATA, 5, 0, 10, 3, ['ANSIBLE_METADATA'])),
    # Metadata at end of file
    (LICENSE + FUTURE_IMPORTS + REGULAR_IMPORTS + BYTES_STD_METADATA.rstrip(),
     (METADATA, 8, 0, 13, 3, ['ANSIBLE_METADATA'])),
    # Metadata at beginning of file
    (BYTES_STD_METADATA + LICENSE + REGULAR_IMPORTS,
     (METADATA, 1, 0, 6, 3, ['ANSIBLE_METADATA'])),
)


@pytest.mark.parametrize("code, expected", METADATA_EXAMPLES)
def test_dict_metadata(code, expected):
    assert md.extract_metadata(module_data=code, offsets=True) == expected


@pytest.mark.parametrize("code, expected", STRING_METADATA_EXAMPLES)
def test_string_metadata(code, expected):
    # FIXME: String/yaml metadata is not implemented yet.
    with pytest.raises(NotImplementedError):
        assert md.extract_metadata(module_data=code, offsets=True) == expected


def test_required_params():
    with pytest.raises(TypeError, message='One of module_ast or module_data must be given'):
        assert md.extract_metadata()


def test_module_data_param_given_with_offset():
    with pytest.raises(TypeError, message='If offsets is True then module_data must also be given'):
        assert md.extract_metadata(module_ast='something', offsets=True)


def test_invalid_dict_metadata():
    with pytest.raises(SyntaxError):
        assert md.extract_metadata(module_data=LICENSE + FUTURE_IMPORTS + b'ANSIBLE_METADATA={"metadata_version": "1.0",\n' + REGULAR_IMPORTS)

    with pytest.raises(md.ParseError, message='Unable to find the end of dictionary'):
        assert md.extract_metadata(module_ast=ast.parse(LICENSE + FUTURE_IMPORTS + b'ANSIBLE_METADATA={"metadata_version": "1.0"}\n' + REGULAR_IMPORTS),
                                   module_data=LICENSE + FUTURE_IMPORTS + b'ANSIBLE_METADATA={"metadata_version": "1.0",\n' + REGULAR_IMPORTS,
                                   offsets=True)


def test_multiple_statements_limitation():
    with pytest.raises(md.ParseError, message='Multiple statements per line confuses the module metadata parser.'):
        assert md.extract_metadata(module_data=LICENSE + FUTURE_IMPORTS + b'ANSIBLE_METADATA={"metadata_version": "1.0"}; a=b\n' + REGULAR_IMPORTS,
                                   offsets=True)
