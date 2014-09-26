#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Matt Martz <matt@sivel.net>, and others
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
module: win_msi
version_added: "1.7"
short_description: Installs and uninstalls Windows MSI files
description:
    - Installs or uninstalls a Windows MSI file that is already located on the
      target server
options:
    path:
        description:
            - File system path to the MSI file to install
        required: true
    state:
        description:
            - Whether the MSI file should be installed or uninstalled
        choices:
            - present
            - absent
        default: present
    creates:
        description:
            - Path to a file created by installing the MSI to prevent from
              attempting to reinstall the package on every run
author: Matt Martz
'''

EXAMPLES = '''
# Install an MSI file
- win_msi: path=C:\\\\7z920-x64.msi

# Uninstall an MSI file
- win_msi: path=C:\\\\7z920-x64.msi state=absent
'''

