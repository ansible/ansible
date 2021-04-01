#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: package
version_added: 2.0
author:
    - Ansible Core Team
short_description: Generic OS package manager
description:
    - This modules manages packages on a target without specifying a package manager module (like M(ansible.builtin.yum), M(ansible.builtin.apt), ...).
      It is convenient to use in an heterogeneous environment of machines without having to create a specific task for
      each package manager. `package` calls behind the module for the package manager used by the operating system
      discovered by the module M(ansible.builtin.setup).  If `setup` was not yet run, `package` will run it.
    - This module acts as a proxy to the underlying package manager module. While all arguments will be passed to the
      underlying module, not all modules support the same arguments. This documentation only covers the minimum intersection
      of module arguments that all packaging modules support.
    - For Windows targets, use the M(ansible.windows.win_package) module instead.
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
      - The required package manager module to use (`yum`, `apt`, and so on). The default 'auto' will use existing facts or try to autodetect it.
      - You should only use this field if the automatic selection is not working for some reason.
    default: auto
requirements:
    - Whatever is required for the package plugins specific for each system.
notes:
    - While `package` abstracts package managers to ease dealing with multiple distributions, package name often differs for the same software.

'''
EXAMPLES = '''
- name: Install ntpdate
  ansible.builtin.package:
    name: ntpdate
    state: present

# This uses a variable as this changes per distribution.
- name: Remove the apache package
  ansible.builtin.package:
    name: "{{ apache }}"
    state: absent

- name: Install the latest version of Apache and MariaDB
  ansible.builtin.package:
    name:
      - httpd
      - mariadb-server
    state: latest
'''
