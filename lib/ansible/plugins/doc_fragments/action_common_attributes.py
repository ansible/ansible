# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


# NOTE: this file is here to allow modules using the new attributes feature to
#       work w/o errors in this version of ansible, it does NOT provide the full
#       attributes feature, just a shim to avoid the fragment not being found.

class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = r'''
options: {}
'''
