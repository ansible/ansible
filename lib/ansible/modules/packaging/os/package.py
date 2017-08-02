#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: package
version_added: 2.0
author:
    - Ansible Inc
short_description: Generic OS package manager
description:
     - Installs, upgrade and removes packages using the underlying OS package manager.
     - For Windows targets, use the M(win_package) module instead.
options:
  name:
    description:
      - "Package name, or package specifier with version, like C(name-1.0)."
      - "Be aware that packages are not always named the same and this module will not 'translate' them per distro."
    required: true
  state:
    description:
      - Whether to install (C(present), C(latest)), or remove (C(absent)) a package.
    required: true
  use:
    description:
      - The required package manager module to use (yum, apt, etc). The default 'auto' will use existing facts or try to autodetect it.
      - You should only use this field if the automatic selection is not working for some reason.
    required: false
    default: auto
requirements:
    - Whatever is required for the package plugins specific for each system.
notes:
    - This module actually calls the pertinent package modules for each system (apt, yum, etc).
    - For Windows targets, use the M(win_package) module instead.
'''
EXAMPLES = '''
- name: install the latest version of ntpdate
  package:
    name: ntpdate
    state: latest

# This uses a variable as this changes per distribution.
- name: remove the apache package
  package:
    name: "{{ apache }}"
    state: absent
'''
