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
    required: false
    default: null
  description:
    description:
    - Description for the shortcut.
    - This is usually shown when hoovering the icon.
    required: false
    default: null
  dest:
    description:
    - Destination file for the shortcuting file.
    - File name should have a C(.lnk) or C(.url) extension.
    required: true
    default: null
  args:
    description:
    - Additional arguments for the executable defined in C(src).
    required: false
    default: null
  directory:
    description:
    - Working directory for executable defined in C(src).
    required: false
    default: null
  icon:
    description:
    - Icon used for the shortcut
    - File name should have a C(.ico) extension.
    - The file name is followed by a comma and the number in the library file (.dll) or use 0 for an image file.
    required: false
    default: null
  hotkey:
    description:
    - Key combination for the shortcut.
    required: false
    default: null
  windowstyle:
    description:
    - Influences how the application is displayed when it is launched.
        C(1) for default location and size
        C(3) for maximized
        C(7) minimized
  state:
    description:
    - When C(present), creates or updates the shortcut.  When C(absent),
      removes the shortcut if it exists.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
author: Dag Wieers (@dagwieers)
notes:
- 'The following options can include Windows environment variables: C(dest), C(args), C(description), C(dest), C(directory), C(icon) C(src)'
'''

EXAMPLES = '''
# Create a desktop shortcut for an application
- win_shortcut:
    src: C:\Program Files\Mozilla Firefox\Firefox.exe
    dest: '%PUBLIC%\Desktop\Mozilla Firefox.lnk'
    icon: C:\Program Files\Mozilla Firefox\Firefox.exe,0

# The same desktop shortcut using environment variables
- win_shortcut:
    description: The Mozilla Firefox web browser
    src: '%PROGRAMFILES%\Mozilla Firefox\Firefox.exe'
    dest: '%PUBLIC%\Desktop\Mozilla Firefox.lnk'
    icon: '%PROGRAMFILES\Mozilla Firefox\Firefox.exe,0'
    directory: '%PROGRAMFILES%\Mozilla Firefox\'

# Create a link to the Ansible website
- win_shortcut:
    dest: '%PUBLIC%\Desktop\Ansible website.url'
    src: 'https://ansible.com/'
'''

RETURN = '''
'''