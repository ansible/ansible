#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_chocolatey
version_added: '1.9'
short_description: Manage packages using chocolatey
description:
- Manage packages using Chocolatey.
- If Chocolatey is missing from the system, the module will install it.
requirements:
- chocolatey >= 0.10.5 (will be upgraded if older)
options:
  allow_empty_checksums:
    description:
    - Allow empty checksums to be used for downloaded resource from non-secure
      locations.
    - Use M(win_chocolatey_feature) with the name C(allowEmptyChecksums) to
      control this option globally.
    type: bool
    default: no
    version_added: '2.2'
  allow_multiple:
    description:
    - Allow the installation of multiple packages when I(version) is specified.
    - Having multiple packages at different versions can cause issues if the
      package doesn't support this. Use at your own risk.
    type: bool
    default: no
    version_added: '2.8'
  allow_prerelease:
    description:
    - Allow the installation of pre-release packages.
    - If I(state) is C(latest), the latest pre-release package will be
      installed.
    type: bool
    default: no
    version_added: '2.6'
  architecture:
    description:
    - Force Chocolatey to install the package of a specific process
      architecture.
    - When setting C(x86), will ensure Chocolatey installs the x86 package
      even when on an x64 bit OS.
    type: str
    choices: [ default, x86 ]
    default: default
    version_added: '2.7'
  force:
    description:
    - Forces the install of a package, even if it already is installed.
    - Using I(force) will cause Ansible to always report that a change was
      made.
    type: bool
    default: no
  install_args:
    description:
    - Arguments to pass to the native installer.
    - These are arguments that are passed directly to the installer the
      Chocolatey package runs, this is generally an advanced option.
    type: str
    version_added: '2.1'
  ignore_checksums:
    description:
    - Ignore the checksums provided by the package.
    - Use M(win_chocolatey_feature) with the name C(checksumFiles) to control
      this option globally.
    type: bool
    default: no
    version_added: '2.2'
  ignore_dependencies:
    description:
    - Ignore dependencies, only install/upgrade the package itself.
    type: bool
    default: no
    version_added: '2.1'
  name:
    description:
    - Name of the package(s) to be installed.
    - Set to C(all) to run the action on all the installed packages.
    type: list
    required: yes
  package_params:
    description:
    - Parameters to pass to the package.
    - These are parameters specific to the Chocolatey package and are generally
      documented by the package itself.
    - Before Ansible 2.7, this option was just I(params).
    type: str
    version_added: '2.1'
    aliases: [ params ]
  pinned:
    description:
    - Whether to pin the Chocolatey package or not.
    - If omitted then no checks on package pins are done.
    - Will pin/unpin the specific version if I(version) is set.
    - Will pin the latest version of a package if C(yes), I(version) is not set
      and and no pin already exists.
    - Will unpin all versions of a package if C(no) and I(version) is not set.
    - This is ignored when C(state=absent).
    type: bool
    version_added: '2.8'
  proxy_url:
    description:
    - Proxy URL used to install chocolatey and the package.
    - Use M(win_chocolatey_config) with the name C(proxy) to control this
      option globally.
    type: str
    version_added: '2.4'
  proxy_username:
    description:
    - Proxy username used to install Chocolatey and the package.
    - Before Ansible 2.7, users with double quote characters C(") would need to
      be escaped with C(\) beforehand. This is no longer necessary.
    - Use M(win_chocolatey_config) with the name C(proxyUser) to control this
      option globally.
    type: str
    version_added: '2.4'
  proxy_password:
    description:
    - Proxy password used to install Chocolatey and the package.
    - This value is exposed as a command argument and any privileged account
      can see this value when the module is running Chocolatey, define the
      password on the global config level with M(win_chocolatey_config) with
      name C(proxyPassword) to avoid this.
    type: str
    version_added: '2.4'
  skip_scripts:
    description:
    - Do not run I(chocolateyInstall.ps1) or I(chocolateyUninstall.ps1) scripts
      when installing a package.
    type: bool
    default: no
    version_added: '2.4'
  source:
    description:
    - Specify the source to retrieve the package from.
    - Use M(win_chocolatey_source) to manage global sources.
    - This value can either be the URL to a Chocolatey feed, a path to a folder
      containing C(.nupkg) packages or the name of a source defined by
      M(win_chocolatey_source).
    - This value is also used when Chocolatey is not installed as the location
      of the install.ps1 script and only supports URLs for this case.
    type: str
  source_username:
    description:
    - A username to use with I(source) when accessing a feed that requires
      authentication.
    - It is recommended you define the credentials on a source with
      M(win_chocolatey_source) instead of passing it per task.
    type: str
    version_added: '2.7'
  source_password:
    description:
    - The password for I(source_username).
    - This value is exposed as a command argument and any privileged account
      can see this value when the module is running Chocolatey, define the
      credentials with a source with M(win_chocolatey_source) to avoid this.
    type: str
    version_added: '2.7'
  state:
    description:
    - State of the package on the system.
    - When C(absent), will ensure the package is not installed.
    - When C(present), will ensure the package is installed.
    - When C(downgrade), will allow Chocolatey to downgrade a package if
      I(version) is older than the installed version.
    - When C(latest), will ensure the package is installed to the latest
      available version.
    - When C(reinstalled), will uninstall and reinstall the package.
    type: str
    choices: [ absent, downgrade, latest, present, reinstalled ]
    default: present
  timeout:
    description:
    - The time to allow chocolatey to finish before timing out.
    type: int
    default: 2700
    version_added: '2.3'
    aliases: [ execution_timeout ]
  validate_certs:
    description:
    - Used when downloading the Chocolatey install script if Chocolatey is not
      already installed, this does not affect the Chocolatey package install
      process.
    - When C(no), no SSL certificates will be validated.
    - This should only be used on personally controlled sites using self-signed
      certificate.
    type: bool
    default: yes
    version_added: '2.7'
  version:
    description:
    - Specific version of the package to be installed.
    - When I(state) is set to C(absent), will uninstall the specific version
      otherwise all versions of that package will be removed.
    - If a different version of package is installed, I(state) must be C(latest)
      or I(force) set to C(yes) to install the desired version.
    - Provide as a string (e.g. C('6.1')), otherwise it is considered to be
      a floating-point number and depending on the locale could become C(6,1),
      which will cause a failure.
    type: str
notes:
- This module will install or upgrade Chocolatey when needed.
- When using verbosity 2 or less (C(-vv)) the C(stdout) output will be restricted.
  When using verbosity 4 (C(-vvvv)) the C(stdout) output will be more verbose.
  When using verbosity 5 (C(-vvvvv)) the C(stdout) output will include debug output.
- Some packages, like hotfixes or updates need an interactive user logon in
  order to install. You can use C(become) to achieve this, see
  :ref:`become_windows`.
  Even if you are connecting as local Administrator, using C(become) to
  become Administrator will give you an interactive user logon, see examples
  below.
- If C(become) is unavailable, use M(win_hotfix) to install hotfixes instead
  of M(win_chocolatey) as M(win_hotfix) avoids using C(wusa.exe) which cannot
  be run without C(become).
seealso:
- module: win_chocolatey_config
- module: win_chocolatey_facts
- module: win_chocolatey_feature
- module: win_chocolatey_source
- module: win_feature
- module: win_hotfix
  description: Use when C(become) is unavailable, to avoid using C(wusa.exe).
- module: win_package
- module: win_updates
- name: Chocolatey website
  description: More information about the Chocolatey tool.
  link: http://chocolatey.org/
- name: Chocolatey packages
  description: An overview of the available Chocolatey packages.
  link: http://chocolatey.org/packages
- ref: become_windows
  description: Some packages, like hotfixes or updates need an interactive user logon
    in order to install. You can use C(become) to achieve this.
author:
- Trond Hindenes (@trondhindenes)
- Peter Mounce (@petemounce)
- Pepe Barbe (@elventear)
- Adam Keech (@smadam813)
- Pierre Templier (@ptemplier)
- Jordan Borean (@jborean93)
'''

# TODO:
# * Better parsing when a package has dependencies - currently fails
# * Time each item that is run
# * Support 'changed' with gems - would require shelling out to `gem list` first and parsing, kinda defeating the point of using chocolatey.
# * Version provided not as string might be translated to 6,6 depending on Locale (results in errors)

EXAMPLES = r'''
- name: Install git
  win_chocolatey:
    name: git
    state: present

- name: Upgrade installed packages
  win_chocolatey:
    name: all
    state: latest

- name: Install notepadplusplus version 6.6
  win_chocolatey:
    name: notepadplusplus
    version: '6.6'

- name: Install notepadplusplus 32 bit version
  win_chocolatey:
    name: notepadplusplus
    architecture: x86

- name: Install git from specified repository
  win_chocolatey:
    name: git
    source: https://someserver/api/v2/

- name: Install git from a pre configured source (win_chocolatey_source)
  win_chocolatey:
    name: git
    source: internal_repo

- name: Ensure Chocolatey itself is installed and use internal repo as source
  win_chocolatey:
    name: chocolatey
    source: http://someserver/chocolatey

- name: Uninstall git
  win_chocolatey:
    name: git
    state: absent

- name: Install multiple packages
  win_chocolatey:
    name:
    - procexp
    - putty
    - windirstat
    state: present

- name: Install multiple packages sequentially
  win_chocolatey:
    name: '{{ item }}'
    state: present
  loop:
  - procexp
  - putty
  - windirstat

- name: Uninstall multiple packages
  win_chocolatey:
    name:
    - procexp
    - putty
    - windirstat
    state: absent

- name: Install curl using proxy
  win_chocolatey:
    name: curl
    proxy_url: http://proxy-server:8080/
    proxy_username: joe
    proxy_password: p@ssw0rd

- name: Install a package that requires 'become'
  win_chocolatey:
    name: officepro2013
  become: yes
  become_user: Administrator
  become_method: runas

- name: install and pin Notepad++ at 7.6.3
  win_chocolatey:
    name: notepadplusplus
    version: 7.6.3
    pinned: yes
    state: present

- name: remove all pins for Notepad++ on all versions
  win_chocolatey:
    name: notepadplusplus
    pinned: no
    state: present
'''

RETURN = r'''
command:
  description: The full command used in the chocolatey task.
  returned: changed
  type: str
  sample: choco.exe install -r --no-progress -y sysinternals --timeout 2700 --failonunfound
rc:
  description: The return code from the chocolatey task.
  returned: always
  type: int
  sample: 0
stdout:
  description: The stdout from the chocolatey task. The verbosity level of the
    messages are affected by Ansible verbosity setting, see notes for more
    details.
  returned: changed
  type: str
  sample: Chocolatey upgraded 1/1 packages.
'''
