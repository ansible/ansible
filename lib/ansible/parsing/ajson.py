# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations as _annotations

# from ansible.utils.display import Display as _Display


# DTFIX-RELEASE: The pylint deprecated checker does not detect `Display().deprecated` calls, of which we have many.

# deprecated: description='deprecate ajson' core_version='2.23'
# _Display().deprecated(
#     msg='The `ansible.parsing.ajson` module is deprecated.',
#     version='2.27',
#     help_text="",  # DTFIX-RELEASE: complete this help text
# )

# Imported for backward compat
from ansible.module_utils.common.json import (  # pylint: disable=unused-import
    _AnsibleJSONEncoder as AnsibleJSONEncoder,
    _AnsibleJSONDecoder as AnsibleJSONDecoder,
)
