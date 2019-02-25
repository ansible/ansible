#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_xml
version_added: "2.7"
short_description: Add XML fragment to an XML parent
description:
    - Adds XML fragments formatted as strings to existing XML on remote servers.
    - For non-Windows targets, use the M(xml) module instead.
options:
    path:
        description:
        - The path of remote servers XML.
        type: path
        required: true
        aliases: [ dest, file ]
    fragment:
        description:
        - The string representation of the XML fragment to be added.
        type: str
        required: true
        aliases: [ xmlstring ]
    xpath:
        description:
        - The node of the remote server XML where the fragment will go.
        type: str
        required: true
    backup:
        description:
        - Determine whether a backup should be created.
        - When set to C(yes), create a backup file including the timestamp information
          so you can get the original file back if you somehow clobbered it incorrectly.
        type: bool
        default: no
    type:
        description:
        - The type of XML you are working with.
        type: str
        required: yes
        default: element
        choices: [ attribute, element, text ]
    attribute:
        description:
        - The attribute name if the type is 'attribute'.
        - Required if C(type=attribute).
        type: str
author:
    - Richard Levenberg (@richardcs)
'''

EXAMPLES = r'''
- name: Apply our filter to Tomcat web.xml
  win_xml:
   path: C:\apache-tomcat\webapps\myapp\WEB-INF\web.xml
   fragment: '<filter><filter-name>MyFilter</filter-name><filter-class>com.example.MyFilter</filter-class></filter>'
   xpath: '/*'

- name: Apply sslEnabledProtocols to Tomcat's server.xml
  win_xml:
   path: C:\Tomcat\conf\server.xml
   xpath: '//Server/Service[@name="Catalina"]/Connector[@port="9443"]'
   attribute: 'sslEnabledProtocols'
   fragment: 'TLSv1,TLSv1.1,TLSv1.2'
   type: attribute
'''

RETURN = r'''
backup_file:
    description: Name of the backup file that was created.
    returned: if backup=yes
    type: str
    sample: C:\Path\To\File.txt.11540.20150212-220915.bak
msg:
    description: What was done.
    returned: always
    type: str
    sample: "xml added"
err:
    description: XML comparison exceptions.
    returned: always, for type element and -vvv or more
    type: list
    sample: attribute mismatch for actual=string
'''
