#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Chris Hoffman <choffman@chathamfinancial.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_service
version_added: "1.7"
short_description: Manage and query Windows services
description:
    - Manage and query Windows services.
    - For non-Windows targets, use the M(service) module instead.
options:
  dependencies:
    description:
    - A list of service dependencies to set for this particular service.
    - This should be a list of service names and not the display name of the
      service.
    - This works by C(dependency_action) to either add/remove or set the
      services in this list.
    type: list
    version_added: "2.3"
  dependency_action:
    description:
    - Used in conjunction with C(dependency) to either add the dependencies to
      the existing service dependencies.
    - Remove the dependencies to the existing dependencies.
    - Set the dependencies to only the values in the list replacing the
      existing dependencies.
    choices: [ add, remove, set ]
    default: set
    version_added: "2.3"
  desktop_interact:
    description:
      - Whether to allow the service user to interact with the desktop.
      - This should only be set to C(yes) when using the LocalSystem username.
    type: bool
    default: 'no'
    version_added: "2.3"
  description:
    description:
      - The description to set for the service.
    version_added: "2.3"
  display_name:
    description:
      - The display name to set for the service.
    version_added: "2.3"
  force_dependent_services:
    description:
    - If C(yes), stopping or restarting a service with dependent services will
      force the dependent services to stop or restart also.
    - If C(no), stopping or restarting a service with dependent services may
      fail.
    type: bool
    default: 'no'
    version_added: "2.3"
  name:
    description:
      - Name of the service.
      - If only the name parameter is specified, the module will report
        on whether the service exists or not without making any changes.
    required: yes
  path:
    description:
      - The path to the executable to set for the service.
    version_added: "2.3"
  password:
    description:
      - The password to set the service to start as.
      - This and the C(username) argument must be supplied together.
      - If specifying LocalSystem, NetworkService or LocalService this field
        must be an empty string and not null.
    version_added: "2.3"
  start_mode:
    description:
      - Set the startup type for the service.
      - C(delayed) added in Ansible 2.3
    choices: [ auto, delayed, disabled, manual ]
  state:
    description:
      - C(started)/C(stopped)/C(absent)/C(pause) are idempotent actions that will not run
        commands unless necessary.
      - C(restarted) will always bounce the service.
      - C(absent) added in Ansible 2.3
      - C(pause) was added in Ansible 2.4
      - Only services that support the paused state can be paused, you can
        check the return value C(can_pause_and_continue).
      - You can only pause a service that is already started.
    choices: [ absent, paused, started, stopped, restarted ]
  username:
    description:
      - The username to set the service to start as.
      - This and the C(password) argument must be supplied together when using
        a local or domain account.
      - Set to C(LocalSystem) to use the SYSTEM account.
    version_added: "2.3"
notes:
    - For non-Windows targets, use the M(service) module instead.
author:
- Chris Hoffman (@chrishoffman)
'''

EXAMPLES = r'''
- name: Restart a service
  win_service:
    name: spooler
    state: restarted

- name: Set service startup mode to auto and ensure it is started
  win_service:
    name: spooler
    start_mode: auto
    state: started

- name: Pause a service
  win_service:
    name: Netlogon
    state: paused

# a new service will also default to the following values:
# - username: LocalSystem
# - state: stopped
# - start_mode: auto
- name: Create a new service
  win_service:
    name: service name
    path: C:\temp\test.exe

- name: Create a new service with extra details
  win_service:
    name: service name
    path: C:\temp\test.exe
    display_name: Service Name
    description: A test service description

- name: Remove a service
  win_service:
    name: service name
    state: absent

- name: Check if a service is installed
  win_service:
    name: service name
  register: service_info

- name: Set the log on user to a domain account
  win_service:
    name: service name
    state: restarted
    username: DOMAIN\User
    password: Password

- name: Set the log on user to a local account
  win_service:
    name: service name
    state: restarted
    username: .\Administrator
    password: Password

- name: Set the log on user to Local System
  win_service:
    name: service name
    state: restarted
    username: LocalSystem
    password: ""

- name: Set the log on user to Local System and allow it to interact with the desktop
  win_service:
    name: service name
    state: restarted
    username: LocalSystem
    password: ""
    desktop_interact: yes

- name: Set the log on user to Network Service
  win_service:
    name: service name
    state: restarted
    username: NT AUTHORITY\NetworkService
    password: ""

- name: Set the log on user to Local Service
  win_service:
    name: service name
    state: restarted
    username: NT AUTHORITY\LocalService
    password: ""

- name: Set dependencies to ones only in the list
  win_service:
    name: service name
    dependencies: ['service1', 'service2']

- name: Add dependencies to existing dependencies
  win_service:
    name: service name
    dependencies: ['service1', 'service2']
    dependency_action: add

- name: Remove dependencies from existing dependencies
  win_service:
    name: service name
    dependencies: ['service1', 'service2']
    dependency_action: remove
'''

RETURN = r'''
exists:
    description: Whether the service exists or not.
    returned: success
    type: boolean
    sample: true
name:
    description: The service name or id of the service.
    returned: success and service exists
    type: string
    sample: CoreMessagingRegistrar
display_name:
    description: The display name of the installed service.
    returned: success and service exists
    type: string
    sample: CoreMessaging
state:
    description: The current running status of the service.
    returned: success and service exists
    type: string
    sample: stopped
start_mode:
    description: The startup type of the service.
    returned: success and service exists
    type: string
    sample: manual
path:
    description: The path to the service executable.
    returned: success and service exists
    type: string
    sample: C:\Windows\system32\svchost.exe -k LocalServiceNoNetwork
can_pause_and_continue:
    description: Whether the service can be paused and unpaused.
    returned: success and service exists
    type: bool
    sample: True
description:
    description: The description of the service.
    returned: success and service exists
    type: string
    sample: Manages communication between system components.
username:
    description: The username that runs the service.
    returned: success and service exists
    type: string
    sample: LocalSystem
desktop_interact:
    description: Whether the current user is allowed to interact with the desktop.
    returned: success and service exists
    type: boolean
    sample: False
dependencies:
    description: A list of services that is depended by this service.
    returned: success and service exists
    type: list
    sample: False
depended_by:
    description: A list of services that depend on this service.
    returned: success and service exists
    type: list
    sample: False
'''
