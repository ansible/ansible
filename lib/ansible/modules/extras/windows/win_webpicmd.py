#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Peter Mounce <public@neverrunwithscissors.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_webpicmd
version_added: "2.0"
short_description: Installs packages using Web Platform Installer command-line
description:
    - Installs packages using Web Platform Installer command-line (http://www.iis.net/learn/install/web-platform-installer/web-platform-installer-v4-command-line-webpicmdexe-rtw-release).
    - Must be installed and present in PATH (see win_chocolatey module; 'webpicmd' is the package name, and you must install 'lessmsi' first too)
    - Install IIS first (see win_feature module)
notes:
    - accepts EULAs and suppresses reboot - you will need to check manage reboots yourself (see win_reboot module)
options:
  name:
    description:
      - Name of the package to be installed
    required: true
author: Peter Mounce
'''

EXAMPLES = '''
  # Install URLRewrite2.
  win_webpicmd:
    name: URLRewrite2
'''
