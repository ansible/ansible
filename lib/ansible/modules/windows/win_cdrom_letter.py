#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, RusoSova
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: win_cdrom_letter
short_description: Change drive letter of CDROMs

description:
 - Change drive letter of CDROMs present on the system. The amount of CDROMs that will be affected is determinated
   by the number of CDROMs or the number of drive_letter provided, whichever is smaller.
 - Module can also dismount Windows virtual CDROMs.
 - On changed, a summary of CDROM's state is provided.

options:
 drive_letter:
   description:
     - List of the drive letters to assign to the CDROMs separated by comma.
     - The letters in the list are of equal cost. If CDROM is already mapped to one of the letter provided no change will happen to this device.
     - If less drive letters than CDROMs are avaliable, the module will only change the number of CDROMs equal to drive letters.
     - Accepted characters C-Z
     - Example O,S,U,R
   required: false
   type: str
 change_single:
   description:
     - Specify the drive letter of a single CDROM to change or dismount.
     - Usefull when multiple CDROMs are present on the system but you need to change or dismount only one of them
     - Note, it's not advisable to use change_single in conjunction with both dismount_virtual and drive_letter simultaneously.
   required: false
   type: str
 dismount_virtual:
   description:
     - Dismount all Windows virtual CDROMs before changing any letters. Unless change_single is provided, which will only affect one drive.
     - Yes|No or True|False
   required: false
   default: false
   type: bool
 dismount_only:
   description:
     - Only dismount Windows virtual CDROMs, do not change any drive letters
     - Mutually exclusive with drive_letter parameter
     - Yes|No or True|False
   required: false
   default: false
   type: bool

version_added: 2.9

author: 
- RusoSova
'''

EXAMPLES = r'''
- name: Change CDROM letter to Z
  win_cdrom_letter:
   drive_letter: Z
  register: result

#If single CDROM present, the letter will be changed to one from the list
#If multiple CDROM are present, up to 3 CDROM's will be updated
- name: Change CDROM letter to Z or Y if Z is in use or to K if Z and Y are in use
  win_cdrom_letter:
   drive_letter: Z,Y,K
  register: result

- name: Change CDROM letter for up to 4 CDROMs and dismount any Windows virtual ones
  win_cdrom_letter:
   drive_letter: O,S,U,R
   dismount_virtual: yes
  register: result

- name: Change single CDROM from letter D to the first avaliable from the list Z,Y,X
  win_cdrom_letter:
   drive_letter: Z,Y,X
   change_single: D
  register: result

- name: Dismount all Windows virtual CDROMs
  win_cdrom_letter:
   dismount_only: yes
  register: result
'''

RETURN = r'''
before_change:
  description: List the initial state of CDROMs
  returned: When at least one CDROM is present on the system
  type: list
  sample: ["O:","P:","E:"]
dismounted:
  description: List of the Windows virtual CDROMs that were dismounted
  returned: When dismount_virtual = yes or dismount_only = yes
  type: str
  sample: "G:,V:"
number_of_cdroms:
  description: Total number of CDROMs thats are susceptible to the change
  returned: When dismount_only = no
  type: int
  sample: 3
number_of_changes:
  description: How many drive letters were changed
  returned: When dismount_only = no
  type: int
  sample: 3
post_change:
  description: List the state of CDROMs after the module had run
  returned: On success
  type: list
  sample: ["Z:","X:","T:"]
remap[n]:
  description: Show the change that was performed. There will be an entry for each change. remap[n] remap[n++] remap[n++] etc..
  returned: When any drive letters were successfully changed
  type: str
  sample:
    - "remap[0]": "O: --> Z:"
    - "remap[1]": "P: --> X:"
    - "remap[2]": "E: --> T:"

'''
