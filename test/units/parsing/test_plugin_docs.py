# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

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

MULTI_LINE = '''
DOCUMENTATION = r"""
module: sample
short_description: The real short
  description
options: {}
"""
'''


@pytest.mark.parametrize('source', [NESTED_OPTION_FIRST, TOP_LEVEL_FIRST, INDENTED_BLOCK, QUOTE_ON_OWN_LINE, MULTI_LINE],
                         ids=['nested-option-first', 'top-level-first', 'indented-block', 'quote-on-own-line', 'multi-line'])
def test_read_docstub_top_level_short_description(tmp_path, source):
    plugin = tmp_path / 'sample.py'
    plugin.write_text(source)

    assert read_docstub(str(plugin)) == {'short_description': 'The real short description'}
