#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>, and others
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_package
version_added: "1.7"
short_description: Installs/uninstalls an installable package
description:
- Installs or uninstalls software packages for Windows.
- Supports C(.exe), C(.msi), C(.msp), C(.appx), C(.appxbundle), C(.msix),
  and C(.msixbundle).
- These packages can be sourced from the local file system, network file share
  or a url.
- See I(provider) for more info on each package type that is supported.
options:
  arguments:
    description:
    - Any arguments the installer needs to either install or uninstall the
      package.
    - If the package is an MSI do not supply the C(/qn), C(/log) or
      C(/norestart) arguments.
    - This is only used for the C(msi), C(msp), and C(registry) providers.
    - As of Ansible 2.5, this parameter can be a list of arguments and the
      module will escape the arguments as necessary, it is recommended to use a
      string when dealing with MSI packages due to the unique escaping issues
      with msiexec.
    type: raw
  chdir:
    description:
    - Set the specified path as the current working directory before installing
      or uninstalling a package.
    - This is only used for the C(msi), C(msp), and C(registry) providers.
    type: path
    version_added: '2.8'
  creates_path:
    description:
    - Will check the existence of the path specified and use the result to
      determine whether the package is already installed.
    - You can use this in conjunction with C(product_id) and other C(creates_*).
    type: path
    version_added: '2.4'
  creates_service:
    description:
    - Will check the existing of the service specified and use the result to
      determine whether the package is already installed.
    - You can use this in conjunction with C(product_id) and other C(creates_*).
    type: str
    version_added: '2.4'
  creates_version:
    description:
    - Will check the file version property of the file at C(creates_path) and
      use the result to determine whether the package is already installed.
    - C(creates_path) MUST be set and is a file.
    - You can use this in conjunction with C(product_id) and other C(creates_*).
    type: str
    version_added: '2.4'
  expected_return_code:
    description:
    - One or more return codes from the package installation that indicates
      success.
    - Before Ansible 2.4 this was just 0 but since Ansible 2.4 this is both C(0) and
      C(3010).
    - A return code of C(3010) usually means that a reboot is required, the
      C(reboot_required) return value is set if the return code is C(3010).
    - This is only used for the C(msi), C(msp), and C(registry) providers.
    type: list
    elements: int
    default: [0, 3010]
  log_path:
    description:
    - Specifies the path to a log file that is persisted after a package is
      installed or uninstalled.
    - This is only used for the C(msi) or C(msp) provider.
    - When omitted, a temporary log file is used instead for those providers.
    - This is only valid for MSI files, use C(arguments) for the C(registry)
      provider.
    type: path
    version_added: '2.8'
  password:
    description:
    - The password for C(user_name), must be set when C(user_name) is.
    - This option is deprecated in favour of using become, see examples for
      more information.
    type: str
    aliases: [ user_password ]
  path:
    description:
    - Location of the package to be installed or uninstalled.
    - This package can either be on the local file system, network share or a
      url.
    - When C(state=present), C(product_id) is not set and the path is a URL,
      this file will always be downloaded to a temporary directory for
      idempotency checks, otherwise the file will only be downloaded if the
      package has not been installed based on the C(product_id) checks.
    - If C(state=present) then this value MUST be set.
    - If C(state=absent) then this value does not need to be set if
      C(product_id) is.
    type: str
  product_id:
    description:
    - The product id of the installed packaged.
    - This is used for checking whether the product is already installed and
      getting the uninstall information if C(state=absent).
    - For msi packages, this is the C(ProductCode) (GUID) of the package. This
      can be found under the same registry paths as the C(registry) provider.
    - For msp packages, this is the C(PatchCode) (GUID) of the package which
      can found under the C(Details -> Revision number) of the file's properties.
    - For msix packages, this is the C(Name) or C(PackageFullName) of the
      package found under the C(Get-AppxPackage) cmdlet.
    - For registry (exe) packages, this is the registry key name under the
      registry paths specified in I(provider).
    - This value is ignored if C(path) is set to a local accesible file path
      and the package is not an C(exe).
    - This SHOULD be set when the package is an C(exe), or the path is a url
      or a network share and credential delegation is not being used. The
      C(creates_*) options can be used instead but is not recommended.
    - The C(productid) alias will be removed in Ansible 2.14.
    type: str
    aliases: [ productid ]
  provider:
    description:
    - Set the package provider to use when searching for a package.
    - The C(auto) provider will select the proper provider if I(path)
      otherwise it scans all the other providers based on the I(product_id).
    - The C(msi) provider scans for MSI packages installed on a machine wide
      and current user context based on the C(ProductCode) of the MSI. Before
      Ansible 2.10 only the machine wide context was searched.
    - The C(msix) provider is used to install C(.appx), C(.msix),
      C(.appxbundle), or C(.msixbundle) packages. These packages are only
      installed or removed on the current use. The host must be set to allow
      sideloaded apps or in developer mode. See the examples for how to enable
      this. If a package is already installed but C(path) points to an updated
      package, this will be installed over the top of the existing one.
    - The C(msp) provider scans for all MSP patches installed on a machine wide
      and current user context based on the C(PatchCode) of the MSP. A C(msp)
      will be applied or removed on all C(msi) products that it applies to and
      is installed. If the patch is obsoleted or superseded then no action will
      be taken.
    - The C(registry) provider is used for traditional C(exe) installers and
      uses the following registry path to determine if a product was installed;
      C(HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall),
      C(HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall),
      C(HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall), and
      C(HKCU:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall).
      Before Ansible 2.10 only the C(HKLM) hive was searched.
    - Before Ansible 2.10 only the C(msi) and C(registry) providers were used.
    choices:
    - auto
    - msi
    - msix
    - msp
    - registry
    default: auto
    type: str
    version_added: '2.10'
  state:
    description:
    - Whether to install or uninstall the package.
    - The module uses I(product_id) to determine whether the package is
      installed or not.
    - For all providers but C(auto), the I(path) can be used for idempotency
      checks if it is locally accesible filesystem path.
    - The C(ensure) alias will be removed in Ansible 2.14.
    type: str
    choices: [ absent, present ]
    default: present
    aliases: [ ensure ]
  username:
    description:
    - Username of an account with access to the package if it is located on a
      file share.
    - This is only needed if the WinRM transport is over an auth method that
      does not support credential delegation like Basic or NTLM or become is
      not used.
    - This option is deprecated in favour of using become, see examples for
      more information.
    type: str
    aliases: [ user_name ]

  # Overrides the options in url_windows
  client_cert:
    version_added: '2.10'
  client_cert_password:
    version_added: '2.10'
  follow_redirects:
    version_added: '2.10'
  force_basic_auth:
    version_added: '2.10'
  headers:
    version_added: '2.10'
  http_agent:
    version_added: '2.10'
  maximum_redirection:
    version_added: '2.10'
  method:
    version_added: '2.10'
  proxy_password:
    version_added: '2.10'
  proxy_url:
    version_added: '2.10'
  proxy_use_default_credential:
    version_added: '2.10'
  proxy_username:
    version_added: '2.10'
  timeout:
    description:
    - Specifies how long the web download request can be pending before it
      times out in seconds.
    - Set to C(0) to specify an infinite timeout.
    version_added: '2.10'
  url_password:
    version_added: '2.10'
  url_username:
    version_added: '2.10'
  use_default_credential:
    version_added: '2.10'
  use_proxy:
    version_added: '2.10'
extends_documentation_fragment:
- url_windows
notes:
- When C(state=absent) and the product is an exe, the path may be different
  from what was used to install the package originally. If path is not set then
  the path used will be what is set under C(QuietUninstallString) or
  C(UninstallString) in the registry for that I(product_id).
- By default all msi installs and uninstalls will be run with the arguments
  C(/log, /qn, /norestart).
- All the installation checks under C(product_id) and C(creates_*) add
  together, if one fails then the program is considered to be absent.
seealso:
- module: win_chocolatey
- module: win_hotfix
- module: win_updates
author:
- Trond Hindenes (@trondhindenes)
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Install the Visual C thingy
  win_package:
    path: http://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe
    product_id: '{CF2BEA3C-26EA-32F8-AA9B-331F7E34BA97}'
    arguments: /install /passive /norestart

- name: Install Visual C thingy with list of arguments instead of a string
  win_package:
    path: http://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe
    product_id: '{CF2BEA3C-26EA-32F8-AA9B-331F7E34BA97}'
    arguments:
    - /install
    - /passive
    - /norestart

- name: Install Remote Desktop Connection Manager from msi with a permanent log
  win_package:
    path: https://download.microsoft.com/download/A/F/0/AF0071F3-B198-4A35-AA90-C68D103BDCCF/rdcman.msi
    product_id: '{0240359E-6A4C-4884-9E94-B397A02D893C}'
    state: present
    log_path: D:\logs\vcredist_x64-exe-{{lookup('pipe', 'date +%Y%m%dT%H%M%S')}}.log

- name: Uninstall Remote Desktop Connection Manager
  win_package:
    product_id: '{0240359E-6A4C-4884-9E94-B397A02D893C}'
    state: absent

- name: Install Remote Desktop Connection Manager locally omitting the product_id
  win_package:
    path: C:\temp\rdcman.msi
    state: present

- name: Uninstall Remote Desktop Connection Manager from local MSI omitting the product_id
  win_package:
    path: C:\temp\rdcman.msi
    state: absent

# 7-Zip exe doesn't use a guid for the Product ID
- name: Install 7zip from a network share with specific credentials
  win_package:
    path: \\domain\programs\7z.exe
    product_id: 7-Zip
    arguments: /S
    state: present
  become: yes
  become_method: runas
  become_flags: logon_type=new_credential logon_flags=netcredentials_only
  vars:
    ansible_become_user: DOMAIN\User
    ansible_become_password: Password

- name: Install 7zip and use a file version for the installation check
  win_package:
    path: C:\temp\7z.exe
    creates_path: C:\Program Files\7-Zip\7z.exe
    creates_version: 16.04
    state: present

- name: Uninstall 7zip from the exe
  win_package:
    path: C:\Program Files\7-Zip\Uninstall.exe
    product_id: 7-Zip
    arguments: /S
    state: absent

- name: Uninstall 7zip without specifying the path
  win_package:
    product_id: 7-Zip
    arguments: /S
    state: absent

- name: Install application and override expected return codes
  win_package:
    path: https://download.microsoft.com/download/1/6/7/167F0D79-9317-48AE-AEDB-17120579F8E2/NDP451-KB2858728-x86-x64-AllOS-ENU.exe
    product_id: '{7DEBE4EB-6B40-3766-BB35-5CBBC385DA37}'
    arguments: '/q /norestart'
    state: present
    expected_return_code: [0, 666, 3010]

- name: Install a .msp patch
  win_package:
    path: C:\Patches\Product.msp
    state: present

- name: Remove a .msp patch
  win_package:
    product_id: '{AC76BA86-A440-FFFF-A440-0C13154E5D00}'
    state: absent

- name: Enable installation of 3rd party MSIX packages
  win_regedit:
    path: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock
    name: AllowAllTrustedApps
    data: 1
    type: dword
    state: present

- name: Install an MSIX package for the current user
  win_package:
    path: C:\Installers\Calculator.msix  # Can be .appx, .msixbundle, or .appxbundle
    state: present

- name: Uninstall an MSIX package using the product_id
  win_package:
    product_id: InputApp
    state: absent
'''

RETURN = r'''
log:
  description: The contents of the MSI or MSP log.
  returned: installation/uninstallation failure for MSI or MSP packages
  type: str
  sample: Installation completed successfully
rc:
  description: The return code of the package process.
  returned: change occurred
  type: int
  sample: 0
reboot_required:
  description: Whether a reboot is required to finalise package. This is set
    to true if the executable return code is 3010.
  returned: always
  type: bool
  sample: true
stdout:
  description: The stdout stream of the package process.
  returned: failure during install or uninstall
  type: str
  sample: Installing program
stderr:
  description: The stderr stream of the package process.
  returned: failure during install or uninstall
  type: str
  sample: Failed to install program
'''
