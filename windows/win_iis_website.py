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

DOCUMENTATION = '''
---
module: win_iis_website
version_added: "2.0"
short_description: Configures a IIS Web site.
description:
     - Creates, Removes and configures a IIS Web site
options:
  name:
    description:
      - Names of web site
    required: true
    default: null
    aliases: []
  site_id:
    description:
      - Explicitly set the IIS numeric ID for a site. Note that this value cannot be changed after the website has been created.
    required: false
    version_added: "2.1"
    default: null
  state:
    description:
      - State of the web site
    choices:
      - started
      - restarted
      - stopped
      - absent
    required: false
    default: null
    aliases: []
  physical_path:
    description:
      - The physical path on the remote host to use for the new site. The specified folder must already exist.
    required: false
    default: null
    aliases: []
  application_pool:
    description:
      - The application pool in which the new site executes.
    required: false
    default: null
    aliases: []
  port:
    description:
      - The port to bind to / use for the new site.
    required: false
    default: null
    aliases: []
  ip:
    description:
      - The IP address to bind to / use for the new site.
    required: false
    default: null
    aliases: []
  hostname:
    description:
      - The host header to bind to / use for the new site.
    required: false
    default: null
    aliases: []
  ssl:
    description:
      - Enables HTTPS binding on the site..
    required: false
    default: null
    aliases: []
  parameters:
    description:
      - Custom site Parameters from string where properties are seperated by a pipe and property name/values by colon Ex. "foo:1|bar:2"
    required: false
    default: null
    aliases: []
author: Henrik Wallström
'''

EXAMPLES = '''
# This return information about an existing host
$ ansible -i vagrant-inventory -m win_iis_website -a "name='Default Web Site'" window
host | success >> {
    "changed": false,
    "site": {
        "ApplicationPool": "DefaultAppPool",
        "Bindings": [
            "*:80:"
        ],
        "ID": 1,
        "Name": "Default Web Site",
        "PhysicalPath": "%SystemDrive%\\inetpub\\wwwroot",
        "State": "Stopped"
    }
}

# This stops an existing site.
$ ansible -i hosts -m win_iis_website -a "name='Default Web Site' state=stopped" host

# This creates a new site.
$ ansible -i hosts -m win_iis_website -a "name=acme physical_path=c:\\sites\\acme" host

# Change logfile .
$ ansible -i hosts -m win_iis_website -a "name=acme physical_path=c:\\sites\\acme" host


# Playbook example
---

- name: Acme IIS site
  win_iis_website:
    name: "Acme"
    state: started
    port: 80
    ip: 127.0.0.1
    hostname: acme.local
    application_pool: "acme"
    physical_path: 'c:\\sites\\acme'
    parameters: 'logfile.directory:c:\\sites\\logs'
  register: website

'''
