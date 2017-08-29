#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Ansible, inc
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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
module: win_region
version_added: "2.3"
short_description: Set the region and format settings
description:
    - Set the location settings of a Windows Server.
    - Set the format settings of a Windows Server.
    - Set the unicode language settings of a Windows Server.
    - Copy across these settings to the default profile.
options:
    location:
        description:
            - The location to set for the current user, see
              U(https://msdn.microsoft.com/en-us/library/dd374073.aspx)
              for a list of GeoIDs you can use and what location it relates to.
              This needs to be set if C(format) or C(unicode_language) is not
              set.
    format:
        description:
            - The language format to set for the current user, see
              U(https://msdn.microsoft.com/en-us/library/system.globalization.cultureinfo.aspx)
              for a list of culture names to use. This needs to be set if
              C(location) or C(unicode_language) is not set.
    unicode_language:
        description:
            - The unicode language format to set for all users, see
              U(https://msdn.microsoft.com/en-us/library/system.globalization.cultureinfo.aspx)
              for a list of culture names to use. This needs to be set if
              C(location) or C(format) is not set. After setting this
              value a reboot is required for it to take effect.
    copy_settings:
        description:
            - This will copy the current format and location values to new user
              profiles and the welcome screen. This will only run if
              C(location), C(format) or C(unicode_language) has resulted in a
              change. If this process runs then it will always result in a
              change.
        default: false
        choices: ['true', 'false']
author: "Jordan Borean (@jborean93)"
'''

EXAMPLES = r'''
# Set the region format to English United States
- win_region:
    format: en-US

# Set the region format to English Australia and copy settings to new profiles
- win_region:
    format: en-AU
    copy_settings: True

# Set the unicode language to English Great Britain, reboot if required
- win_region:
    unicode_language: en-GB
  register: result

- win_reboot:
  when: result.restart_required

# Set the location to United States
- win_region:
    location: 244

# Set format, location and unicode to English Australia and copy settings, reboot if required
- win_region:
    location: 12
    format: en-AU
    unicode_language: en-AU
  register: result

- win_reboot:
  when: result.restart_required
'''

RETURN = r'''
changed:
    description: Whether anything was changed
    returned: always
    type: boolean
    sample: True
restart_required:
    description: Whether a reboot is required for the change to take effect
    returned: success
    type: boolean
    sample: True
'''
