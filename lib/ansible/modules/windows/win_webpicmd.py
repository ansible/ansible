#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Peter Mounce <public@neverrunwithscissors.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_webpicmd
version_added: "2.0"
short_description: Installs packages using Web Platform Installer command-line
description:
    - Installs packages using Web Platform Installer command-line
      (U(http://www.iis.net/learn/install/web-platform-installer/web-platform-installer-v4-command-line-webpicmdexe-rtw-release)).
    - Must be installed and present in PATH (see M(win_chocolatey) module; 'webpicmd' is the package name, and you must install 'lessmsi' first too)?
    - Install IIS first (see M(win_feature) module).
notes:
    - Accepts EULAs and suppresses reboot - you will need to check manage reboots yourself (see M(win_reboot) module)
options:
  name:
    description:
      - Name of the package to be installed.
    type: str
    required: yes
seealso:
- module: win_package
author:
- Peter Mounce (@petemounce)
'''

EXAMPLES = r'''
- name: Install URLRewrite2.
  win_webpicmd:
    name: URLRewrite2
'''
