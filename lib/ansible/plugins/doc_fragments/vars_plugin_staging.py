# -*- coding: utf-8 -*-

# Copyright: (c) 2019,  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  stage:
    description: Control when this vars plugin may be executed.
    choices: ['all', 'task', 'inventory']
    default: 'all'
    version_added: "2.9"
    type: str
'''
