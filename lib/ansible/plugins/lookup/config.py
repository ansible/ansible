# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: config
    author: Ansible Core
    version_added: "2.5"
    short_description: Lookup current Ansilbe configuration values
    description:
      - Retrieves the value of an Ansible configuration setting.
      - You can use ``ansible-config list`` to see all available settings.
    options:
      _terms:
        description: they key(s) too look up
        required: True
"""

EXAMPLES = """
    - name: Show configured default become user
      debug: msg="{{ lookup('config', 'DEFAULT_BECOME_USER')}}"

    - name: print out role paths
      debug: msg="This is a role path {{item}}"
      loop: "{{ lookup('config', 'DEFAULT_ROLES_PATH')}}"

    - name: find retry files
      find:
        paths: "{{lookup('config', 'RETRY_FILES_SAVE_PATH')|default(playbook_dir, True)}}"
        patterns: "*.retry"
"""

RETURN = """
_raw:
  description:
    - value(s) of the key(s) in the config
"""

from ansible import constants as C
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []
        for term in terms:
            ret.append(getattr(C, term, None))
        return ret
