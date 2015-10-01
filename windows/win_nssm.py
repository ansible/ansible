#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Heyo
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

DOCUMENTATION = '''
---
module: win_nssm
version_added: "2.0"
short_description: NSSM - the Non-Sucking Service Manager
description:
    - nssm is a service helper which doesn't suck. See https://nssm.cc/ for more information.
requirements:
  - "nssm >= 2.24.0 # (install via win_chocolatey) win_chocolatey: name=nssm"
options:
  name:
    description:
      - Name of the service to operate on
    required: true
  state:
    description:
      - State of the service on the system
      - Note that NSSM actions like "pause", "continue", "rotate" do not fit the declarative style of ansible, so these should be implemented via the ansible command module
    required: false
    choices:
      - present
      - started
      - stopped
      - restarted
      - absent
    default: started
  application:
    description:
      - The application binary to run as a service
      - "Specify this whenever the service may need to be installed (state: present, started, stopped, restarted)"
      - "Note that the application name must look like the following, if the directory includes spaces:"
      - "nssm install service \\"c:\\Program Files\\app.exe\\" \\"\\"\\"C:\\Path with spaces\\"\\"\\""
      - "See commit 0b386fc1984ab74ee59b7bed14b7e8f57212c22b in the nssm.git project for more info (https://git.nssm.cc/?p=nssm.git;a=commit;h=0b386fc1984ab74ee59b7bed14b7e8f57212c22b)"
    required: false
    default: null
  stdout_file:
    description:
      - Path to receive output
    required: false
    default: null
  stderr_file:
    description:
      - Path to receive error output
    required: false
    default: null
  app_parameters:
    description:
      - Parameters to be passed to the application when it starts
    required: false
    default: null
author:
  - "Adam Keech (@smadam813)"
  - "George Frank (@georgefrank)"
'''

EXAMPLES = '''
  # Install and start the foo service
  win_nssm:
    name: foo
    application: C:\windows\foo.exe

  # Install and start the foo service with a key-value pair argument
  # This will yield the following command: C:\windows\foo.exe bar "true"
  win_nssm:
    name: foo
    application: C:\windows\foo.exe
    app_parameters:
        bar: true

  # Install and start the foo service with a key-value pair argument, where the argument needs to start with a dash
  # This will yield the following command: C:\windows\foo.exe -bar "true"
  win_nssm:
    name: foo
    application: C:\windows\foo.exe
    app_parameters:
        "-bar": true

  # Install and start the foo service with a single parameter
  # This will yield the following command: C:\windows\foo.exe bar
  win_nssm:
    name: foo
    application: C:\windows\foo.exe
    app_parameters:
        _: bar

  # Install and start the foo service with a mix of single params, and key value pairs
  # This will yield the following command: C:\windows\foo.exe bar -file output.bat
  win_nssm:
    name: foo
    application: C:\windows\foo.exe
    app_parameters:
        _: bar
        "-file": "output.bat"

  # Install and start the foo service, redirecting stdout and stderr to the same file
  win_nssm:
    name: foo
    application: C:\windows\foo.exe
    stdout_file: C:\windows\foo.log
    stderr_file: C:\windows\foo.log

  # Remove the foo service
  win_nssm:
    name: foo
    state: absent
'''
