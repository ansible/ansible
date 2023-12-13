# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
    module: module2
    short_description: Hello test module
    description: Hello test module.
    options:
        plugin:
            required: true
            description: name of the plugin (cache_host)
    author:
      - Ansible Core Team
"""

EXAMPLES = r"""
---

first_doc:
some_key:

---

second_doc:
some_key:

"""

RETURN = r"""
---
---
"""

from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):

    NAME = 'inventory1'
