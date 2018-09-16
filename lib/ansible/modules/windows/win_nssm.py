#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Heyo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_nssm
version_added: "2.0"
short_description: NSSM - the Non-Sucking Service Manager
description:
    - nssm is a service helper which doesn't suck. See U(https://nssm.cc/) for more information.
requirements:
    - "nssm >= 2.24.0 # (install via M(win_chocolatey)) C(win_chocolatey: name=nssm)"
options:
  name:
    description:
      - Name of the service to operate on.
    type: str
    required: true
  state:
    description:
      - State of the service on the system.
      - Note that NSSM actions like "pause", "continue", "rotate" do not fit the declarative style of ansible, so these should be implemented via the
        ansible command module.
    type: str
    choices: [ absent, present, started, stopped, restarted ]
    default: started
  application:
    description:
      - The application binary to run as a service
      - "Specify this whenever the service may need to be installed (state: present, started, stopped, restarted)"
      - "Note that the application name must look like the following, if the directory includes spaces:"
      - 'nssm install service "C:\\Program Files\\app.exe\\" "C:\\Path with spaces\\"'
      - >
        See commit 0b386fc1984ab74ee59b7bed14b7e8f57212c22b in the nssm.git project for more info:
        U(https://git.nssm.cc/?p=nssm.git;a=commit;h=0b386fc1984ab74ee59b7bed14b7e8f57212c22b)
    type: path
  working_directory:
    version_added: "2.8.0"
    description:
      - The working directory to run the service executable from (defaults to the directory containing the application binary)
    aliases: [ app_directory, chdir ]
  stdout_file:
    description:
      - Path to receive output.
    type: path
  stderr_file:
    description:
      - Path to receive error output.
    type: path
  app_parameters:
    description:
      - A string representing a dictionary of parameters to be passed to the application when it starts.
      - DEPRECATED since v2.8, please use C(arguments) instead.
      - Use either this or C(arguments), not both.
    type: str
  arguments:
    description:
      - Parameters to be passed to the application when it starts.
      - This can be either a simple string or a list.
      - Use either this or C(app_parameters), not both.
    aliases: [ app_parameters_free_form ]
    type: str
    version_added: "2.3"
  dependencies:
    description:
      - Service dependencies that has to be started to trigger startup, separated by comma.
    type: list
  user:
    description:
      - User to be used for service startup.
    type: str
  password:
    description:
      - Password to be used for service startup.
    type: str
  start_mode:
    description:
      - If C(auto) is selected, the service will start at bootup.
      - C(delayed) causes a delayed but automatic start after boot (added in version 2.5).
      - C(manual) means that the service will start only when another service needs it.
      - C(disabled) means that the service will stay off, regardless if it is needed or not.
    type: str
    choices: [ auto, delayed, disabled, manual ]
    default: auto
seealso:
- module: win_service
author:
  - Adam Keech (@smadam813)
  - George Frank (@georgefrank)
  - Hans-Joachim Kliemeck (@h0nIg)
  - Michael Wild (@themiwi)
  - Kevin Subileau (@ksubileau)
'''

EXAMPLES = r'''
# Install and start the foo service
- win_nssm:
    name: foo
    application: C:\windows\foo.exe

# Install and start the consul service with a list of parameters
# This will yield the following command: C:\windows\foo.exe bar "true"
- win_nssm:
    name: consul
    application: C:\consul\consul.exe
    arguments:
      - agent
      - -config-dir=C:\consul\config

# Install and start the consul service with an arbitrary string of parameters
# This is strictly equivalent to the previous example
- name: Make sure the Consul service runs
  win_nssm:
    name: consul
    application: C:\consul\consul.exe
    arguments: agent -config-dir=C:\consul\config

# Install and start the foo service, redirecting stdout and stderr to the same file
- win_nssm:
    name: foo
    application: C:\windows\foo.exe
    stdout_file: C:\windows\foo.log
    stderr_file: C:\windows\foo.log

# Install and start the foo service, but wait for dependencies tcpip and adf
- win_nssm:
    name: foo
    application: C:\windows\foo.exe
    dependencies: 'adf,tcpip'

# Install and start the foo service with dedicated user
- win_nssm:
    name: foo
    application: C:\windows\foo.exe
    user: foouser
    password: secret

# Install the foo service but do not start it automatically
- win_nssm:
    name: foo
    application: C:\windows\foo.exe
    state: present
    start_mode: manual

# Remove the foo service
- win_nssm:
    name: foo
    state: absent
'''
