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
short_description: Install a service using NSSM
description:
    - Install a Windows service using the NSSM wrapper.
    - NSSM is a service helper which doesn't suck. See U(https://nssm.cc/) for more information.
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
      - Values C(started), C(stopped), and C(restarted) are deprecated since v2.8,
        please use the M(win_service) module instead to start, stop or restart the service.
    type: str
    choices: [ absent, present, started, stopped, restarted ]
    default: present
  application:
    description:
      - The application binary to run as a service
      - Required when I(state) is C(present), C(started), C(stopped), or C(restarted).
    type: path
  executable:
    description:
    - The location of the NSSM utility (in case it is not located in your PATH).
    type: path
    default: nssm.exe
    version_added: "2.8.0"
  description:
    description:
      - The description to set for the service.
    type: str
    version_added: "2.8.0"
  display_name:
    description:
      - The display name to set for the service.
    type: str
    version_added: "2.8.0"
  working_directory:
    version_added: "2.8.0"
    description:
      - The working directory to run the service executable from (defaults to the directory containing the application binary)
    type: path
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
      - DEPRECATED since v2.8, please use I(arguments) instead.
      - This is mutually exclusive with I(arguments).
    type: str
  arguments:
    description:
      - Parameters to be passed to the application when it starts.
      - This can be either a simple string or a list.
      - This parameter was renamed from I(app_parameters_free_form) in 2.8.
      - This is mutually exclusive with I(app_parameters).
    aliases: [ app_parameters_free_form ]
    type: str
    version_added: "2.3"
  dependencies:
    description:
      - Service dependencies that has to be started to trigger startup, separated by comma.
      - DEPRECATED since v2.8, please use the M(win_service) module instead.
    type: list
  user:
    description:
      - User to be used for service startup.
      - DEPRECATED since v2.8, please use the M(win_service) module instead.
    type: str
  password:
    description:
      - Password to be used for service startup.
      - DEPRECATED since v2.8, please use the M(win_service) module instead.
    type: str
  start_mode:
    description:
      - If C(auto) is selected, the service will start at bootup.
      - C(delayed) causes a delayed but automatic start after boot (added in version 2.5).
      - C(manual) means that the service will start only when another service needs it.
      - C(disabled) means that the service will stay off, regardless if it is needed or not.
      - DEPRECATED since v2.8, please use the M(win_service) module instead.
    type: str
    choices: [ auto, delayed, disabled, manual ]
    default: auto
seealso:
  - module: win_service
notes:
  - The service will NOT be started after its creation when C(state=present).
  - Once the service is created, you can use the M(win_service) module to start it or configure
    some additionals properties, such as its startup type, dependencies, service account, and so on.
author:
  - Adam Keech (@smadam813)
  - George Frank (@georgefrank)
  - Hans-Joachim Kliemeck (@h0nIg)
  - Michael Wild (@themiwi)
  - Kevin Subileau (@ksubileau)
'''

EXAMPLES = r'''
- name: Install the foo service
  win_nssm:
    name: foo
    application: C:\windows\foo.exe

# This will yield the following command: C:\windows\foo.exe bar "true"
- name: Install the Consul service with a list of parameters
  win_nssm:
    name: Consul
    application: C:\consul\consul.exe
    arguments:
      - agent
      - -config-dir=C:\consul\config

# This is strictly equivalent to the previous example
- name: Install the Consul service with an arbitrary string of parameters
  win_nssm:
    name: Consul
    application: C:\consul\consul.exe
    arguments: agent -config-dir=C:\consul\config


# Install the foo service, and then configure and start it with win_service
- name: Install the foo service, redirecting stdout and stderr to the same file
  win_nssm:
    name: foo
    application: C:\windows\foo.exe
    stdout_file: C:\windows\foo.log
    stderr_file: C:\windows\foo.log

- name: Configure and start the foo service using win_service
  win_service:
    name: foo
    dependencies: [ adf, tcpip ]
    user: foouser
    password: secret
    start_mode: manual
    state: started

- name: Remove the foo service
  win_nssm:
    name: foo
    state: absent
'''
