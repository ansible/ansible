#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_iis_webapppool
version_added: "2.0"
short_description: configures an IIS Web Application Pool
description:
  - Creates, removes and configures an IIS Web Application Pool.
options:
  attributes:
    description:
      - As of Ansible 2.4, this field can take in dict entries to set the
        application pool attributes.
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
      - DEPRECATED As of Ansible 2.4 this field should be set using a dict
        form, in older versions of Ansible this field used to be a string.
      - This string has attributes that are separated by a pipe '|' and
        attribute name/values by colon ':'
        Ex. "startMode:OnDemand|managedPipelineMode:Classic".
  name:
    description:
      - Name of the application pool.
    required: true
  state:
    choices:
      - present
      - absent
      - stopped
      - started
      - restarted
    default: present
    description:
      - The state of the application pool.
      - If C(present) will ensure the app pool is configured and exists.
      - If C(absent) will ensure the app pool is removed.
      - If C(stopped) will ensure the app pool exists and is stopped.
      - If C(started) will ensure the app pool exists and is started.
      - If C(restarted) will ensure the app pool exists and will restart, this
        is never idempotent.
author:
  - "Henrik Wallström (@henrikwallstrom)"
  - "Jordan Borean (@jborean93)"
'''

EXAMPLES = r'''
- name: return information about an existing application pool
  win_iis_webapppool:
    name: DefaultAppPool
    state: present

- name: create a new application pool in 'Started' state
  win_iis_webapppool:
    name: AppPool
    state: started

- name: stop an application pool
  win_iis_webapppool:
    name: AppPool
    state: stopped

- name: restart an application pool (non-idempotent)
  win_iis_webapppool:
    name: AppPool
    state: restart

- name: change application pool attributes using new dict style
  win_iis_webapppool:
    name: AppPool
    attributes:
      managedRuntimeVersion: v4.0
      autoStart: false

# Note this format style has been deprecated, please use the newer dict style instead
- name: change application pool attributes using older string style
  win_iis_webapppool:
    name: AppPool
    attributes: 'managedRuntimeVersion:v4.0|autoStart:false'

# This is the preferred style to use when setting attributes
- name: creates an application pool, sets attributes and starts it
  win_iis_webapppool:
    name: AnotherAppPool
    state: started
    attributes:
      managedRuntimeVersion: v4.0
      autoStart: false

# In the below example we are setting attributes in child element processModel
# https://www.iis.net/configreference/system.applicationhost/applicationpools/add/processmodel
- name: manage child element and set identity of application pool
  win_iis_webapppool:
    name: IdentitiyAppPool
    state: started
    attributes:
      managedPipelineMode: Classic
      processModel.identityType: SpecificUser
      processModel.userName: '{{ansible_user}}'
      processModel.password: '{{ansible_password}}'
      processModel.loadUserProfile: True

- name: manage a timespan attribute
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
  type: dictionary
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
      type: dictionary
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
      type: dictionary
      sample:
        action: "NoAction"
        limit: 0
        resetInterval:
          Days: 0
          Hours: 0
    failure:
      description: Key value pairs showing the current Application Pool failure attributes.
      returned: success
      type: dictionary
      sample:
        autoShutdownExe: ""
        orphanActionExe: ""
        rapidFailProtextionInterval:
          Days: 0
          Hours: 0
    name:
      description: Name of Application Pool that was processed by this module invocation.
      returned: success
      type: string
      sample: "DefaultAppPool"
    processModel:
      description: Key value pairs showing the current Application Pool processModel attributes.
      returned: success
      type: dictionary
      sample:
        identityType: "ApplicationPoolIdentity"
        logonType: "LogonBatch"
        pingInterval:
          Days: 0
          Hours: 0
    recycling:
      description: Key value pairs showing the current Application Pool recycling attributes.
      returned: success
      type: dictionary
      sample:
        disallowOverlappingRotation: false
        disallowRotationOnConfigChange: false
        logEventOnRecycle: "Time,Requests,Schedule,Memory,IsapiUnhealthy,OnDemand,ConfigChange,PrivateMemory"
    state:
      description: Current runtime state of the pool as the module completed.
      returned: success
      type: string
      sample: "Started"
'''
