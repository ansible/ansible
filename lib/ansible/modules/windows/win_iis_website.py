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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_iis_website
version_added: "2.0"
short_description: Configures an IIS Web site.
description:
  - Creates, removes and configures an IIS Web site.
  - If you wish to modify the bindings for a site, please use
    M(win_iis_webbinding) to perform these tasks.
options:
  name:
    description: The name of the web site.
    required: true
  site_id:
    description:
      - Explicitly set the IIS numeric ID for a site. Note that if this ID does
        not match a site.
      - If the site ID does not match then the site will be deleted and
        recreated with the new ID set.
      - The module will throw an error if the ID is already used by another
        site that is not called C(name).
    version_added: "2.1"
  state:
    description: The state of the web site.
    choices:
      - started
      - restarted
      - stopped
      - absent
    default: started
  physical_path:
    description:
      - The physical path on the remote host to use for the new site.
      - The specified folder must already exist.
      - This must be set when creating a new web site.
  application_pool:
    description:
      - The application pool in which the site executes.
      - If a new site is created and this is not set, the app pool used will
        be the default on the server.
  port:
    description:
      - The port to bind to.
      - This is only set if the site does not exist and will be created by
        the module execution.
      - DEPRECATED as of Ansible 2.4, will be removed in Ansible 2.6.
      - Use M(win_iis_webbinding) instead to modify the bindings of a site.
  ip:
    description:
      - The IP address to bind to.
      - This is only set if the site does not exist and will be created by
        the module execution.
      - DEPRECATED as of Ansible 2.4, will be removed in Ansible 2.6.
      - Use M(win_iis_webbinding) instead to modify the bindings of a site.
  hostname:
    description:
      - The host header to bind to.
      - This is only set if the site does not exist and will be created by
        the module execution.
      - DEPRECATED as of Ansible 2.4, will be removed in Ansible 2.6.
      - Use M(win_iis_webbinding) instead to modify the bindings of a site.
  ssl:
    description:
      - Enables HTTPS binding on the site.
      - This is only set if the site does not exist and will be created by
        the module execution.
      - DEPRECATED as of Ansible 2.4, will be removed in Ansible 2.6.
      - Use M(win_iis_webbinding) instead to modify the bindings of a site.
  attributes:
    description:
      - Custom site attributes to set in a dict form.
      - These attributes are based on the naming standard at
        U(https://www.iis.net/configreference/system.applicationhost/sites/site#005).
      - You can also set attributes of child elements like application, limits
        and other by setting the full path like 'limits.maxBandwidth'.
      - If setting an enum value, this can be either the enum value or the enum
        name itself.
    version_added: "2.4"
  parameters:
    description:
      - DEPRECATED as of Ansible 2.4, use C(attributes) instead, this will be
        removed in Ansible 2.6.
      - Custom site parameters in a string where each parameter is separated by
        a pip and property name/values by colon, e.g. "foo:1|bar:2"
author:
  - "Henrik Wallström (@henrikwallstrom)"
  - "Jordan Borean (@jborean93)"
'''

EXAMPLES = r'''
- name: create and start a website with defaults
  win_iis_website:
    name: Acme
    state: started

- name: create and start a website with custom attributes
  win_iis_website:
    name: Acme
    state: started
    application_pool: acme
    physical_path: C:\sites\acme
    attributes:
      serverAutoStart: True
      # timespan format is "days:hours:minutes:seconds.milliseconds" or "hours:minutes:seconds"
      limits.connectionTimeout: "00:02:00"
      logFile.directory: C:\sites\logs
      logFile.logFormat: IIS

# Note the below is the older format for setting attributes
# this is only set as a reference for older users and should
# not be followed for future implementations
- name: create and start a website with custom attributes
  win_iis_website:
    name: Acme
    state: started
    application_pool: acme
    physical_path: C:\sites\acme
    parameters: "logFile.directory:C:\\sites\\logs"

- name: remove the Default Web Site
  win_iis_website:
    name: Default Web Site
    state: absent
'''

RETURN = r'''
attributes:
  description: The attributes that are set when calling the module and parsed
    during execution.
  returned: success
  type: dictionary
  sample:
    "serverAutoStart": True
    "limits.connectionTimeout": "00:02:00"
    "logFile.directory": "C:\\sites\\logs"
    "logFile.logFormat": IIS
info:
  description: Information about the web site, these are all the attributes
    that are set and retrieved from the Site. See
    "https://www.iis.net/configreference/system.applicationhost/sites/site#005"
    for a full list of attributes that are returned, the below is just a
    sample.
  returned: success
  type: complex
  contains:
    applicationDefaults:
      description: Attributes of the default configuration settings for
        applications in the site.
      returned: success
      type: dictionary
      sample:
        applicationPool: ""
        enabledProtocols: http
        path: ""
        preloadEnabled: False
        serviceAutoStartEnabled: False
        serviceAutoStartProvider: ""
    attributes:
      description: Attributes for the basic site settings.
      returned: success
      type: dictionary
      sample:
        applicationPool: "AppPool"
        id: 1
        name: Acme
        physicalPath: C:\ansible\win_iis_website
        serverAutoStart: True
        state: Started
    bindings:
      description: A list of bindings to access the site.
      returned: success
      type: list
      sample: [
        {
          "bindingInformation": "*:80:", "certificateHash": "",
           "certificateStoreName": "", "isDsMapperEnabled": False,
           "protocol": "http", "sslFlags": 0
        }
      ]
    limits:
      description: Attributes to limit the amount of bandwidth, the number of
        connections, or the amount of time for connections to a site.
      returned: success
      type: dictionary
      sample:
        connectionTimeout: { "TotalSeconds": 120 }
        maxBandwidth: 2048
        maxConnections: 1000
        maxUrlSegments: 32
    logFile:
      description: Attributes for handling and storage of log files for the
        site.
      returned: success
      type: dictionary
      sample:
        directory: "%SystemDrive%\\inetpub\\logs\\LogFiles"
        enabled: true
    traceFailedRequestsLogging:
      description: Attributes for logging failed-request traces for the site.
      returned: success
      type: dictionary
      sample:
        directory: "%SystemDrive%\\inetpub\\logs\\FailedReqLogFiles"
        enabled: False
    virtualDirectoryDefaults:
      description: Attributes for all virtual directories in the site.
      returned: success
      type: dictionary
      sample:
        logonMethod: "Batch"
        path: ""
        userName: "User"
site:
  description: Basic information about the web site, this is deprecated and
    kept for backwards compatibility, use the info key as it contains more
    info of the site.
  returned: success
  type: dictionary
  sample:
    ApplicationPool: "AppPool"
    Bindings: "*:80:"
    ID: 1
    PhysicalPath: "C:\\ansible\\win_iis_website"
    State: "Started"
'''
