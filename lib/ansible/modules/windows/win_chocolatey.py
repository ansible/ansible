#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_chocolatey
version_added: "1.9"
short_description: Manage packages using chocolatey
description:
    - Manage packages using Chocolatey (U(http://chocolatey.org/)).
    - If Chocolatey is missing from the system, the module will install it.
    - List of packages can be found at U(http://chocolatey.org/packages).
requirements:
- chocolatey >= 0.10.5 (will be upgraded if older)
options:
  name:
    description:
      - Name of the package to be installed.
      - This must be a single package name.
    required: yes
  state:
    description:
      - State of the package on the system.
    choices:
      - absent
      - downgrade
      - latest
      - present
      - reinstalled
    default: present
  force:
    description:
      - Forces install of the package (even if it already exists).
      - Using C(force) will cause ansible to always report that a change was made.
    type: bool
    default: 'no'
  version:
    description:
      - Specific version of the package to be installed.
      - Ignored when C(state) is set to C(absent).
  source:
    description:
      - Specify source rather than using default chocolatey repository.
  install_args:
    description:
      - Arguments to pass to the native installer.
    version_added: '2.1'
  params:
    description:
      - Parameters to pass to the package
    version_added: '2.1'
  allow_empty_checksums:
    description:
      - Allow empty checksums to be used.
    type: bool
    default: 'no'
    version_added: '2.2'
  ignore_checksums:
    description:
      - Ignore checksums altogether.
    type: bool
    default: 'no'
    version_added: '2.2'
  ignore_dependencies:
    description:
      - Ignore dependencies, only install/upgrade the package itself.
    type: bool
    default: 'no'
    version_added: '2.1'
  timeout:
    description:
      - The time to allow chocolatey to finish before timing out.
    default: 2700
    version_added: '2.3'
    aliases: [ execution_timeout ]
  skip_scripts:
    description:
    - Do not run I(chocolateyInstall.ps1) or I(chocolateyUninstall.ps1) scripts.
    type: bool
    default: 'no'
    version_added: '2.4'
  proxy_url:
    description:
      - Proxy url used to install chocolatey and the package.
    version_added: '2.4'
  proxy_username:
    description:
      - Proxy username used to install chocolatey and the package.
      - When dealing with a username with double quote characters C("), they
        need to be escaped with C(\) beforehand. See examples for more details.
    version_added: '2.4'
  proxy_password:
    description:
      - Proxy password used to install chocolatey and the package.
      - See notes in C(proxy_username) when dealing with double quotes in a
        password.
    version_added: '2.4'
  allow_prerelease:
    description:
      - Allow install of prerelease packages.
      - If state C(state) is C(latest) the highest prerelease package will be installed.
    type: bool
    default: 'no'
    version_added: '2.6'
notes:
- Provide the C(version) parameter value as a string (e.g. C('6.1')), otherwise it
  is considered to be a floating-point number and depending on the locale could
  become C(6,1), which will cause a failure.
- When using verbosity 2 or less (C(-vv)) the C(stdout) output will be restricted.
- When using verbosity 4 (C(-vvvv)) the C(stdout) output will be more verbose.
- When using verbosity 5 (C(-vvvvv)) the C(stdout) output will include debug output.
- This module will install or upgrade Chocolatey when needed.
- Some packages need an interactive user logon in order to install.  You can use (C(become)) to achieve this.
- Even if you are connecting as local Administrator, using (C(become)) to become Administrator will give you an interactive user logon, see examples below.
- Use (M(win_hotfix) to install hotfixes instead of (M(win_chocolatey)) as (M(win_hotfix)) avoids using wusa.exe which cannot be run remotely.
author:
- Trond Hindenes (@trondhindenes)
- Peter Mounce (@petemounce)
- Pepe Barbe (@elventear)
- Adam Keech (@smadam813)
- Pierre Templier (@ptemplier)
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

- name: Install git from specified repository
  win_chocolatey:
    name: git
    source: https://someserver/api/v2/

- name: Uninstall git
  win_chocolatey:
    name: git
    state: absent

- name: Install multiple packages
  win_chocolatey:
    name: '{{ item }}'
    state: present
  with_items:
  - procexp
  - putty
  - windirstat

- name: uninstall multiple packages
  win_chocolatey:
    name: '{{ item }}'
    state: absent
  with_items:
  - procexp
  - putty
  - windirstat

- name: Install curl using proxy
  win_chocolatey:
    name: curl
    proxy_url: http://proxy-server:8080/
    proxy_username: joe
    proxy_password: p@ssw0rd

- name: Install curl with proxy credentials that contain quotes
  win_chocolatey:
    name: curl
    proxy_url: http://proxy-server:8080/
    proxy_username: user with \"escaped\" double quotes
    proxy_password: pass with \"escaped\" double quotes

- name: Install a package that requires 'become'
  win_chocolatey:
    name: officepro2013
  become: yes
  become_user: Administrator
  become_method: runas
'''

RETURN = r'''
command:
  description: The full command used in the chocolatey task.
  returned: changed
  type: str
  sample: choco.exe install -r --no-progress -y sysinternals --timeout 2700 --failonunfound
rc:
  description: The return code from the chocolatey task.
  returned: changed
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
