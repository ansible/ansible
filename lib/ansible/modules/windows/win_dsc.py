#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Trond Hindenes <trond@hindenes.com>, and others
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_dsc
version_added: "2.4"
short_description: Invokes a PowerShell DSC configuration
description:
    - Invokes a PowerShell DSC Configuration. Requires PowerShell version 5 (February release or newer).
    - Most of the parameters for this module are dynamic and will vary depending on the DSC Resource.
options:
  resource_name:
    description:
      - The DSC Resource to use. Must be accessible to PowerShell using any of the default paths.
    required: true
  module_version:
    description:
      - Can be used to configure the exact version of the dsc resource to be invoked.
      - Useful if the target node has multiple versions installed of the module containing the DSC resource.
      - If not specified, the module will follow standard Powershell convention and use the highest version available.
    default: latest
author: Trond Hindenes
'''

EXAMPLES = r'''
# Playbook example
  - name: Extract zip file
    win_dsc:
      resource_name: archive
      ensure: Present
      path: "C:\\Temp\\zipfile.zip"
      destination: "C:\\Temp\\Temp2"

  - name: Invoke DSC with check mode
    win_dsc:
      resource_name: windowsfeature
      name: telnet-client
'''

RETURN = r'''
resource_name:
    description: The name of the invoked resource
    returned: always
    type: string
    sample: windowsfeature
module_version:
    description: The version of the dsc resource/module used.
    returned: success
    type: string
    sample: "1.0.1"
attributes:
    description: The attributes/parameters passed in to the DSC resource as key/value pairs
    returned: always
    type: complex
    sample:
    contains:
      Key:
          description: Attribute key
      Value:
          description: Attribute value
dsc_attributes:
    description: The attributes/parameters as returned from the DSC engine in dict format
    returned: always
    type: complex
    contains:
      Key:
          description: Attribute key
      Value:
          description: Attribute value
reboot_required:
    description: flag returned from the DSC engine indicating whether or not the machine requires a reboot for the invoked changes to take effect
    returned: always
    type: boolean
    sample: True
message:
    description: any error message from invoking the DSC resource
    returned: error
    type: string
    sample: Multiple DSC modules found with resource name xyz
'''
