#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_iis_webapppool
version_added: "2.0"
short_description: Configure IIS Web Application Pools
description:
  - Creates, removes and configures an IIS Web Application Pool.
options:
  attributes:
    description:
      - This field is a free form dictionary value for the application pool
        attributes.
      - These attributes are based on the naming standard at
        U(https://www.iis.net/configreference/system.applicationhost/applicationpools/add#005),
        see the examples section for more details on how to set this.
      - You can also set the attributes of child elements like cpu and
        processModel, see the examples to see how it is done.
      - While you can use the numeric values for enums it is recommended to use
        the enum name itself, e.g. use SpecificUser instead of 3 for
        processModel.identityType.
      - managedPipelineMode may be either "Integrated" or "Classic".
      - startMode may be either "OnDemand" or "AlwaysRunning".
      - Use C(state) module parameter to modify the state of the app pool.
      - When trying to set 'processModel.password' and you receive a 'Value
        does fall within the expected range' error, you have a corrupted
        keystore. Please follow
        U(http://structuredsight.com/2014/10/26/im-out-of-range-youre-out-of-range/)
        to help fix your host.
  name:
    description:
      - Name of the application pool.
    type: str
    required: yes
  state:
    description:
      - The state of the application pool.
      - If C(absent) will ensure the app pool is removed.
      - If C(present) will ensure the app pool is configured and exists.
      - If C(restarted) will ensure the app pool exists and will restart, this
        is never idempotent.
      - If C(started) will ensure the app pool exists and is started.
      - If C(stopped) will ensure the app pool exists and is stopped.
    type: str
    choices: [ absent, present, restarted, started, stopped ]
    default: present
seealso:
- module: win_iis_virtualdirectory
- module: win_iis_webapplication
- module: win_iis_webbinding
- module: win_iis_website
author:
- Henrik Wallström (@henrikwallstrom)
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Return information about an existing application pool
  win_iis_webapppool:
    name: DefaultAppPool
    state: present

- name: Create a new application pool in 'Started' state
  win_iis_webapppool:
    name: AppPool
    state: started

- name: Stop an application pool
  win_iis_webapppool:
    name: AppPool
    state: stopped

- name: Restart an application pool (non-idempotent)
  win_iis_webapppool:
    name: AppPool
    state: restart

- name: Change application pool attributes using new dict style
  win_iis_webapppool:
    name: AppPool
    attributes:
      managedRuntimeVersion: v4.0
      autoStart: no

- name: Creates an application pool, sets attributes and starts it
  win_iis_webapppool:
    name: AnotherAppPool
    state: started
    attributes:
      managedRuntimeVersion: v4.0
      autoStart: no

# In the below example we are setting attributes in child element processModel
# https://www.iis.net/configreference/system.applicationhost/applicationpools/add/processmodel
- name: Manage child element and set identity of application pool
  win_iis_webapppool:
    name: IdentitiyAppPool
    state: started
    attributes:
      managedPipelineMode: Classic
      processModel.identityType: SpecificUser
      processModel.userName: '{{ansible_user}}'
      processModel.password: '{{ansible_password}}'
      processModel.loadUserProfile: true

- name: Manage a timespan attribute
  win_iis_webapppool:
    name: TimespanAppPool
    state: started
    attributes:
      # Timespan with full string "day:hour:minute:second.millisecond"
      recycling.periodicRestart.time: "00:00:05:00.000000"
      recycling.periodicRestart.schedule: ["00:10:00", "05:30:00"]
      # Shortened timespan "hour:minute:second"
      processModel.pingResponseTime: "00:03:00"
'''

RETURN = r'''
attributes:
  description: Application Pool attributes that were set and processed by this
    module invocation.
  returned: success
  type: dict
  sample:
    enable32BitAppOnWin64: "true"
    managedRuntimeVersion: "v4.0"
    managedPipelineMode: "Classic"
info:
  description: Information on current state of the Application Pool. See
    https://www.iis.net/configreference/system.applicationhost/applicationpools/add#005
    for the full list of return attributes based on your IIS version.
  returned: success
  type: complex
  sample:
  contains:
    attributes:
      description: Key value pairs showing the current Application Pool attributes.
      returned: success
      type: dict
      sample:
        autoStart: true
        managedRuntimeLoader: "webengine4.dll"
        managedPipelineMode: "Classic"
        name: "DefaultAppPool"
        CLRConfigFile: ""
        passAnonymousToken: true
        applicationPoolSid: "S-1-5-82-1352790163-598702362-1775843902-1923651883-1762956711"
        queueLength: 1000
        managedRuntimeVersion: "v4.0"
        state: "Started"
        enableConfigurationOverride: true
        startMode: "OnDemand"
        enable32BitAppOnWin64: true
    cpu:
      description: Key value pairs showing the current Application Pool cpu attributes.
      returned: success
      type: dict
      sample:
        action: "NoAction"
        limit: 0
        resetInterval:
          Days: 0
          Hours: 0
    failure:
      description: Key value pairs showing the current Application Pool failure attributes.
      returned: success
      type: dict
      sample:
        autoShutdownExe: ""
        orphanActionExe: ""
        rapidFailProtextionInterval:
          Days: 0
          Hours: 0
    name:
      description: Name of Application Pool that was processed by this module invocation.
      returned: success
      type: str
      sample: "DefaultAppPool"
    processModel:
      description: Key value pairs showing the current Application Pool processModel attributes.
      returned: success
      type: dict
      sample:
        identityType: "ApplicationPoolIdentity"
        logonType: "LogonBatch"
        pingInterval:
          Days: 0
          Hours: 0
    recycling:
      description: Key value pairs showing the current Application Pool recycling attributes.
      returned: success
      type: dict
      sample:
        disallowOverlappingRotation: false
        disallowRotationOnConfigChange: false
        logEventOnRecycle: "Time,Requests,Schedule,Memory,IsapiUnhealthy,OnDemand,ConfigChange,PrivateMemory"
    state:
      description: Current runtime state of the pool as the module completed.
      returned: success
      type: str
      sample: "Started"
'''
