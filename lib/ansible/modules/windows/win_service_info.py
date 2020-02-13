#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_service_info
version_added: '2.10'
short_description: Gather information about Windows services
description:
- Gather information about all or a specific installed Windows service(s).
options:
  name:
    description:
    - If specified, this is used to match the C(name) or C(display_name) of the Windows service to get the info for.
    - Can be a wildcard to match multiple services but the wildcard will only be matched on the C(name) of the service
      and not C(display_name).
    - If omitted then all services will returned.
    type: str
seealso:
- module: win_service
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Get info for all installed services
  win_service_info:
  register: service_info

- name: Get info for a single service
  win_service_info:
    name: WinRM
  register: service_info

- name: Get info for a service using its display name
  win_service_info:
    name: Windows Remote Management (WS-Management)

- name: Find all services that start with 'win'
  win_service_info:
    name: win*
'''

RETURN = r'''
exists:
  description: Whether any services were found based on the criteria specified.
  returned: always
  type: bool
  sample: true
services:
  description:
  - A list of service(s) that were found based on the criteria.
  - Will be an empty list if no services were found.
  returned: always
  type: list
  elements: dict
  contains:
    checkpoint:
      description:
      - A check-point value that the service increments periodically to report its progress.
      type: int
      sample: 0
    controls_accepted:
      description:
      - A list of controls that the service can accept.
      - Common controls are C(stop), C(pause_continue), C(shutdown).
      type: list
      elements: str
      sample: ['stop', 'shutdown']
    dependencies:
      description:
      - A list of services by their C(name) that this service is dependent on.
      type: list
      elements: str
      sample: ['HTTP', 'RPCSS']
    dependency_of:
      description:
      - A list of services by their C(name) that depend on this service.
      type: list
      elements: str
      sample: ['upnphost', 'WMPNetworkSvc']
    description:
      description:
      - The description of the service.
      type: str
      sample: Example description of the Windows service.
    desktop_interact:
      description:
      - Whether the service can interact with the desktop, only valid for services running as C(SYSTEM).
      type: bool
      sample: false
    display_name:
      description:
      - The display name to be used by SCM to identify the service.
      type: str
      sample: Windows Remote Management (WS-Management)
    error_control:
      description:
      - The action to take if a service fails to start.
      - Common values are C(critical), C(ignore), C(normal), C(severe).
      type: str
      sample: normal
    failure_actions:
      description:
      - A list of failure actions to run in the event of a failure.
      type: list
      elements: dict
      contains:
        delay_ms:
          description:
          - The time to wait, in milliseconds, before performing the specified action.
          type: int
          sample: 120000
        type:
          description:
          - The action that will be performed.
          - Common values are C(none), C(reboot), C(restart), C(run_command).
          type: str
          sample: run_command
    failure_action_on_non_crash_failure:
      description:
      - Controls when failure actions are fired based on how the service was stopped.
      type: bool
      sample: false
    failure_command:
      description:
      - The command line that will be run when a C(run_command) failure action is fired.
      type: str
      sample: runme.exe
    failure_reboot_msg:
      description:
      - The message to be broadcast to server users before rebooting when a C(reboot) failure action is fired.
      type: str
      sample: Service failed, rebooting host.
    failure_reset_period_sec:
      description:
      - The time, in seconds, after which to reset the failure count to zero.
      type: int
      sample: 86400
    launch_protection:
      description:
      - The protection type of the service.
      - Common values are C(none), C(windows), C(windows_light), or C(antimalware_light).
      type: str
      sample: none
    load_order_group:
      description:
      - The name of the load ordering group to which the service belongs.
      - Will be an empty string if it does not belong to any group.
      type: str
      sample: My group
    name:
      description:
      - The name of the service.
      type: str
      sample: WinRM
    path:
      description:
      - The path to the service binary and any arguments used when starting the service.
      - The binary part can be quoted to ensure any spaces in path are not treated as arguments.
      type: str
      sample: 'C:\Windows\System32\svchost.exe -k netsvcs -p'
    pre_shutdown_timeout_ms:
      description:
      - The preshutdown timeout out value in milliseconds.
      type: int
      sample: 10000
    preferred_node:
      description:
      - The node number for the preferred node.
      - This will be C(null) if the Windows host has no NUMA configuration.
      type: int
      sample: 0
    process_id:
      description:
      - The process identifier of the running service.
      type: int
      sample: 5135
    required_privileges:
      description:
      - A list of privileges that the service requires and will run with
      type: list
      elements: str
      sample: ['SeBackupPrivilege', 'SeRestorePrivilege']
    service_exit_code:
      description:
      - A service-specific error code that is set while the service is starting or stopping.
      type: int
      sample: 0
    service_flags:
      description:
      - Shows more information about the behaviour of a running service.
      - Currently the only flag that can be set is C(runs_in_system_process).
      type: list
      elements: str
      sample: [ 'runs_in_system_process' ]
    service_type:
      description:
      - The type of service.
      - Common types are C(win32_own_process), C(win32_share_process), C(user_own_process), C(user_share_process),
        C(kernel_driver).
      type: str
      sample: win32_own_process
    sid_info:
      description:
      - The behavior of how the service's access token is generated and how to add the service SID to the token.
      - Common values are C(none), C(restricted), or C(unrestricted).
      type: str
      sample: none
    start_mode:
      description:
      - When the service is set to start.
      - Common values are C(auto), C(manual), C(disabled), C(delayed).
      type: str
      sample: auto
    state:
      description:
      - The current running state of the service.
      - Common values are C(stopped), C(start_pending), C(stop_pending), C(started), C(continue_pending),
        C(pause_pending), C(paused).
      type: str
      sample: started
    triggers:
      description:
      - A list of triggers defined for the service.
      type: list
      elements: dict
      contains:
        action:
          description:
          - The action to perform once triggered, can be C(start_service) or C(stop_service).
          type: str
          sample: start_service
        data_items:
          description:
          - A list of trigger data items that contain trigger specific data.
          - A trigger can contain 0 or multiple data items.
          type: list
          elements: dict
          contains:
            data:
              description:
              - The trigger data item value.
              - Can be a string, list of string, int, or base64 string of binary data.
              type: complex
              sample: named pipe
            type:
              description:
              - The type of C(data) for the trigger.
              - Common values are C(string), C(binary), C(level), C(keyword_any), or C(keyword_all).
              type: str
              sample: string
        sub_type:
          description:
          - The trigger event sub type that is specific to each C(type).
          - Common values are C(named_pipe_event), C(domain_join), C(domain_leave), C(firewall_port_open), and others.
          type: str
          sample:
        sub_type_guid:
          description:
          - The guid which represents the trigger sub type.
          type: str
          sample: 1ce20aba-9851-4421-9430-1ddeb766e809
        type:
          description:
          - The trigger event type.
          - Common values are C(custom), C(rpc_interface_event), C(domain_join), C(group_policy), and others.
          type: str
          sample: domain_join
    username:
      description:
      - The username used to run the service.
      - Can be null for user services and certain driver services.
      type: str
      sample: NT AUTHORITY\SYSTEM
    wait_hint_ms:
      description:
      - The estimated time in milliseconds required for a pending start, stop, pause,or continue operations.
      type: int
      sample: 0
    win32_exitcode:
      description:
      - The error code returned from the service binary once it has stopped.
      - When set to C(1066) then a service specific error is returned on C(service_exit_code).
      type: int
      sample: 0
'''
