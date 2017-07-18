#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Dag Wieers <dag@wieers.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: win_shortcut
version_added: '2.3'
short_description: Manage shortcuts on Windows
description:
- Create, manage and delete Windows shortcuts
options:
  src:
    description:
    - Executable or URL the shortcut points to.
    - The executable needs to be in your PATH, or has to be an absolute
      path to the executable.
  description:
    description:
    - Description for the shortcut.
    - This is usually shown when hoovering the icon.
  dest:
    description:
    - Destination file for the shortcuting file.
    - File name should have a C(.lnk) or C(.url) extension.
    required: yes
  args:
    description:
    - Additional arguments for the executable defined in C(src).
  directory:
    description:
    - Working directory for executable defined in C(src).
  icon:
    description:
    - Icon used for the shortcut.
    - File name should have a C(.ico) extension.
    - The file name is followed by a comma and the number in the library file (.dll) or use 0 for an image file.
  hotkey:
    description:
    - Key combination for the shortcut.
  windowstyle:
    description:
    - Influences how the application is displayed when it is launched.
    choices:
    - maximized
    - minimized
    - normal
  state:
    description:
    - When C(present), creates or updates the shortcut.  When C(absent),
      removes the shortcut if it exists.
    choices:
    - absent
    - present
    default: present
author:
- Dag Wieers (@dagwieers)
notes:
- 'The following options can include Windows environment variables: C(dest), C(args), C(description), C(dest), C(directory), C(icon) C(src)'
- 'Windows has two types of shortcuts: Application and URL shortcuts. URL shortcuts only consists of C(dest) and C(src)'
'''

EXAMPLES = r'''
- name: Create an application shortcut on the desktop
  win_shortcut:
    src: C:\Program Files\Mozilla Firefox\Firefox.exe
    dest: C:\Users\Public\Desktop\Mozilla Firefox.lnk
    icon: C:\Program Files\Mozilla Firefox\Firefox.exe,0

- name: Create the same shortcut using environment variables
  win_shortcut:
    description: The Mozilla Firefox web browser
    src: '%ProgramFiles%\Mozilla Firefox\Firefox.exe'
    dest: '%Public%\Desktop\Mozilla Firefox.lnk'
    icon: '%ProgramFiles\Mozilla Firefox\Firefox.exe,0'
    directory: '%ProgramFiles%\Mozilla Firefox'

- name: Create an application shortcut for an executable in PATH to your desktop
  win_shortcut:
    src: cmd.exe
    dest: Desktop\Command prompt.lnk

- name: Create an application shortcut for the Ansible website
  win_shortcut:
    src: '%ProgramFiles%\Google\Chrome\Application\chrome.exe'
    dest: '%UserProfile%\Desktop\Ansible website.lnk'
    args: --new-window https://ansible.com/
    directory: '%ProgramFiles%\Google\Chrome\Application'
    icon: '%ProgramFiles%\Google\Chrome\Application\chrome.exe,0'

- name: Create a URL shortcut for the Ansible website
  win_shortcut:
    src: https://ansible.com/
    dest: '%Public%\Desktop\Ansible website.url'
'''

RETURN = '''
'''
