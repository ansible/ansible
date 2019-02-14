#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Rodric Vos <rodric@vosenterprises.eu>, and others
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub. Actual code lives in the .ps1
# file of the same name.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_msp
short_description: Installs/uninstalls a Microsoft Installer Patch file (*.msp).
description:
- Installs or uninstalls a package in MSP format.
- These packages can be sources from the local file system, network file share
  or a url.
author:
- Rodric Vos (@finzzownt)
options:
  expected_return_code:
    description:
    - One or more return codes from the package installation that indicates
      success.
    - A return code of C(3010) usually means that a reboot is required, the
      I(reboot_required) return value is set if the return code is C(3010).
    type: list
    default: [0, 3010]
  path:
    description:
    - Location of the MSP to be installed, e.g. I(state=present).
    - This package can either be on the local file system, network share or a
      url.
    - If the path is on a network share and the current WinRM transport
      doesn't support credential delegation, then I(user_name) and I(user_password)
      must be set to access the file.
    - There are cases where this file will be copied locally to the server so
      it can access it, see the notes for more info.
    - Required when I(state=present).
  product_id:
    description:
    - The product id of the installed package (MSI). This parameter is
      typically specified as a GUID including curly braces.
    - You can find product ids for installed programs in the Windows registry
      either at
      C(HKLM:Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall) or for 32 bit
      programs at
      C(HKLM:Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall).
    - Required when uninstalling an MSP, e.g. I(state=absent).
    aliases: [ productid ]
  patch_id:
    description:
    - The patch id of the installed MSP. This parameter is typically specified
      as a hexadecimal string without curly braces.
    - You can find patch id for installed patches in the Windows registry at
      C(HKCR:Installer\\Patches\\GUID).
    - Required when uninstalling an MSP, e.g. I(state=absent).
    aliases: [ patchid ]
  patch_guid:
    description:
    - The patch guid of the installed MSP. This parameter is typically specified
      as a GUID including curly braces.
    - To find the patch id for a given .MSP file, open the file properties in
      Windows Explorer, select the Details tab and search for Revision Number.
      Alternatively, use the psmsi package (https://github.com/heaths/psmsi) to
      obtain information from the .MSP package.
    - Required when uninstalling an MSP, e.g. C(state=absent).
    aliases: [ patchguid ]
  state:
    description:
    - Whether to install or uninstall the MSP.
    default: present
  username:
    description:
    - Username of an account with access to the package if it is located on a
      file share.
    - This is only needed if the WinRM transport is over an auth method that
      does not support credential delegation like Basic or NTLM.
    aliases: [ user_name ]
  password:
    description:
    - The password for C(user_name), must be set when C(user_name) is.
    aliases: [ user_password ]
  validate_certs:
    description:
    - SSL certification check can be disabled, when the MSP file should be
      obtained from a https location.
    - If C(no), SSL certificates will not be validated. This should only be
      used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
notes:
- By default all MSP installs and uninstalls will be run with the options
  C(/L*V /log, /qn, /norestart).
- Packages will be temporarily downloaded or copied locally when path is a
  network location and credential delegation is not set, or path is a URL.
author:
- Rodric Vos (@finzzownt)
'''

EXAMPLES = r'''
- name: Install SCOM 2016 UR4 over https
  win_msp:
    path: http://nexusrepo.domain.local/repository/MyRepo/Microsoft/OperationsManager/KB4024941-AMD64-ENU-Console.msp
    patch_id: 4E6A3C97C54C78E478CDDF6B3268A6FC
    state: present

- name: Install SCOM 2016 UR4 over fs
  win_msp:
    path: D:\\Staging\\KB4024941-AMD64-ENU-Console.msp
    patch_id: 4E6A3C97C54C78E478CDDF6B3268A6FC
    state: present

- name: Install SCOM 2016 UR4 over unc
  win_msp:
    path: \\\\packagesrv\data\\KB4024941-AMD64-ENU-Console.msp
    patch_id: 4E6A3C97C54C78E478CDDF6B3268A6FC
    username: DOMAIN\\userID
    password: Secret
    state: present

- name: Uninstall SCOM 2016 UR4
  win_msp:
    patch_id: 4E6A3C97C54C78E478CDDF6B3268A6FC
    patch_guid: '{79C3A6E4-C45C-4E87-87DC-FDB623866ACF}'
    product_id: '{E072D8FC-CD31-4ABE-BD65-606965965426}'
    state: absent
'''

RETURN = r'''
rc:
    description: msiexec.exe return code
    returned: changed
    type: int
    sample: 0
exit_code:
    description: msiexec.exe return code
    returned: changed
    type: int
    sample: 0
log:
    description: msiexec.exe log
    returned: changed
    type: string
reboot_required:
    description: Indicates if a reboot is required after change
    returned: changed
    type: bool
    sample: true
'''
