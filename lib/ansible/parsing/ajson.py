# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.utils.display import Display

Display().deprecated(msg='The ansible.parsing.ajson module has moved to ansible.module_utils.common.json', version='2.18')

# Imported for backwards compat
from ansible.module_utils.common.json import AnsibleJSONEncoder, AnsibleJSONDecoder  # pylint: disable=unused-import
