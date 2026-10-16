# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pathlib

import pytest

from ansible.parsing.plugin_docs import read_docstub

NESTED_OPTION_FIRST = '''
DOCUMENTATION = r"""
module: sample
options:
  short_description:
    description:
      - An option that shares its name with the top-level key.
    type: str
short_description: The real short description
"""
'''

TOP_LEVEL_FIRST = '''
DOCUMENTATION = r"""
module: sample
short_description: The real short description
options:
  short_description:
    description:
      - An option that shares its name with the top-level key.
    type: str
"""
'''

INDENTED_BLOCK = '''
DOCUMENTATION = """
    module: sample
    options:
      short_description:
        description: An option.
    short_description: The real short description
"""
'''

QUOTE_ON_OWN_LINE = """
DOCUMENTATION = \\
    '''
---
module: sample
options:
  short_description:
    description: An option.
short_description: The real short description
'''
"""

MULTI_LINE = '''
DOCUMENTATION = r"""
module: sample
short_description: The real short
  description
options: {}
"""
'''

YAML_FILE = '''
DOCUMENTATION:
  name: sample
  options:
    short_description:
      description: An option.
  short_description: The real short description
RETURN:
  short_description:
    description: A return value.
'''

RETURN_AFTER_DOCUMENTATION = '''
DOCUMENTATION = r"""
module: sample
"""

RETURN = r"""
short_description:
  description: A return value that shares its name with the top-level key.
  returned: always
  type: str
"""
'''

EXAMPLES_AFTER_DOCUMENTATION = '''
DOCUMENTATION = """
    module: sample
"""

EXAMPLES = """
- name: Run sample
  sample:
    short_description: An option value
"""
'''

YAML_RETURN_AFTER_DOCUMENTATION = '''
DOCUMENTATION:
  name: sample
RETURN:
  short_description:
    description: A return value.
'''


@pytest.mark.parametrize(('filename', 'source'), [
    pytest.param('sample.py', NESTED_OPTION_FIRST, id='nested-option-first'),
    pytest.param('sample.py', TOP_LEVEL_FIRST, id='top-level-first'),
    pytest.param('sample.py', INDENTED_BLOCK, id='indented-block'),
    pytest.param('sample.py', QUOTE_ON_OWN_LINE, id='quote-on-own-line'),
    pytest.param('sample.py', MULTI_LINE, id='multi-line'),
    pytest.param('sample.yml', YAML_FILE, id='yaml-file'),
])
def test_read_docstub_top_level_short_description(tmp_path: pathlib.Path, filename: str, source: str) -> None:
    plugin = tmp_path / filename
    plugin.write_text(source)

    assert read_docstub(str(plugin)) == {'short_description': 'The real short description'}


@pytest.mark.parametrize(('filename', 'source'), [
    pytest.param('sample.py', RETURN_AFTER_DOCUMENTATION, id='return'),
    pytest.param('sample.py', EXAMPLES_AFTER_DOCUMENTATION, id='examples'),
    pytest.param('sample.yml', YAML_RETURN_AFTER_DOCUMENTATION, id='yaml-return'),
])
def test_read_docstub_ignores_short_description_after_documentation(tmp_path: pathlib.Path, filename: str, source: str) -> None:
    plugin = tmp_path / filename
    plugin.write_text(source)

    assert read_docstub(str(plugin)) is None
