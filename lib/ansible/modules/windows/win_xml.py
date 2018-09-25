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
options:
    path:
        description:
        - The path of remote servers XML.
        required: true
        aliases: [ dest, file ]
    fragment:
        description:
        - The string representation of the XML fragment to be added.
        required: true
        aliases: [ xmlstring ]
    xpath:
        description:
        - The node of the remote server XML where the fragment will go.
        required: true
    backup:
        description:
        - Whether to backup the remote server's XML before applying the change.
        type: bool
        default: 'no'
    type:
        description:
        - The type of XML you are working with.
        required: yes
        default: element
        choices:
        - element
        - attribute
        - text
    attribute:
        description:
        - The attribute name if the type is 'attribute'. Required if C(type=attribute).

author:
    - Richard Levenberg (@richardcs)
'''

EXAMPLES = r'''
# Apply our filter to Tomcat web.xml
- win_xml:
   path: C:\apache-tomcat\webapps\myapp\WEB-INF\web.xml
   fragment: '<filter><filter-name>MyFilter</filter-name><filter-class>com.example.MyFilter</filter-class></filter>'
   xpath: '/*'

# Apply sslEnabledProtocols to Tomcat's server.xml
- win_xml:
   path: C:\Tomcat\conf\server.xml
   xpath: '//Server/Service[@name="Catalina"]/Connector[@port="9443"]'
   attribute: 'sslEnabledProtocols'
   fragment: 'TLSv1,TLSv1.1,TLSv1.2'
   type: attribute
'''

RETURN = r'''
msg:
    description: what was done
    returned: always
    type: string
    sample: "xml added"
err:
    description: xml comparison exceptions
    returned: always, for type element and -vvv or more
    type: list
    sample: attribute mismatch for actual=string
backup:
    description: name of the backup file, if created
    returned: changed
    type: string
    sample: C:\config.xml.19700101-000000
'''
