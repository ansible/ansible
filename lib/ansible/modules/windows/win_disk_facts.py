#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Marc Tschapek <marc.tschapek@itelligence.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_disk_facts
version_added: '2.5'
short_description: Show disks and disks information of the target host
description:
   - With the module you can retrieve and output detailed information about the attached disks on the target.
requirements:
    - Windows 8.1 / Windows 2012R2 (NT 6.3) or newer
author:
    - Marc Tschapek (@marqelme)
notes:
  - You can use this module in combination with the win_disk_management module in order to retrieve the disks status
    on the target.
'''

EXAMPLES = r'''
- name: get disk facts
   win_disk_facts:
- name: output first disk size
   debug:
       var: ansible_facts.ansible_disk.disk_0.size

- name: get disk facts
   win_disk_facts:
- name: output second disk serial number
   debug:
       var: ansible_facts.ansible_disk.disk_1.serial_number
'''

RETURN = r'''
changed:
    description: Whether anything was changed.
    returned: always
    type: boolean
    sample: true
msg:
    description: Possible error message on failure.
    returned: failed
    type: string
    sample: "No disks could be found on the target"
ansible_facts:
    description: Dictionary containing all the detailed information about the disks of the target.
    returned: always
    type: complex
    contains:
        ansible_disk:
            description: Detailed information about found disks on the target.
            returned: always
            type: complex
            contains:
                total_disks_found:
                    description: Count of found disks on the target.
                    returned: success or failed
                    type: string
                    sample: "3"
                disk_number:
                    description: Detailed information about one particular disk.
                    returned: success or failed
                    type: complex
                    contains:
                        number:
                            description: Number of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "0"
                        size:
                            description: Size in gb of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "100gb"
                        location:
                            description: Location of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "PCIROOT(0)#PCI(0400)#SCSI(P00T00L00)"
                        serial_number:
                            description: Serial number of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "b62beac80c3645e5877f"
                        unique_id:
                            description: Unique ID of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "3141463431303031"
                        operational_status:
                            description: Operational status of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "Online"
                        partition_style:
                            description: Partition style of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "MBR"
                        read_only:
                            description: Read only status of the particular disk on the target.
                            returned: always
                            type: string
                            sample: "False"
'''
