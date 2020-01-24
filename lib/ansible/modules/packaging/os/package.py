#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: package
version_added: 2.0
author:
    - Ansible Core Team
short_description: Generic OS package manager
description:
     - Installs, upgrade and removes packages using the underlying OS package manager.
     - For Windows targets, use the M(win_package) module instead.
options:
  name:
    description:
      - Package name, or package specifier with version.
      - Syntax varies with package manager. For example C(name-1.0) or C(name=1.0).
      - Package names also vary with package manager; this module will not "translate" them per distro. For example C(libyaml-dev), C(libyaml-devel).
    required: true
  state:
    description:
      - Whether to install (C(present)), or remove (C(absent)) a package.
      - You can use other states like C(latest) ONLY if they are supported by the underlying package module(s) executed.
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
- name: install ntpdate
  package:
    name: ntpdate
    state: present

# This uses a variable as this changes per distribution.
- name: remove the apache package
  package:
    name: "{{ apache }}"
    state: absent

- name: install the latest version of Apache and MariaDB
  package:
    name:
      - httpd
      - mariadb-server
    state: latest
'''
