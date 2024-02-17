# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Brian Coca <bcoca@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  decrypt:
    description:
      - This option controls the auto-decryption of source files using vault.
    type: bool
    default: yes
    version_added: '2.4'
'''
