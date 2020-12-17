# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Brian Coca <bcoca@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  decrypt:
    description:
      - This option controls the autodecryption of source files using vault.
    type: bool
    default: yes
    version_added: '2.4'
'''
