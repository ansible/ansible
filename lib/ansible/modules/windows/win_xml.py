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
short_description: Manages XML file content on Windows hosts
description:
    - Manages XML nodes, attributes and text, using xpath to select which xml nodes need to be managed.
    - XML fragments, formatted as strings, are used to specify the desired state of a part or parts of XML files on remote Windows servers.
    - For non-Windows targets, use the M(xml) module instead.
options:
    attribute:
        description:
        - The attribute name if the type is 'attribute'.
        - Required if C(type=attribute).
        type: str
    count:
        description:
        - When set to C(yes), return the number of nodes matched by I(xpath).
        type: bool
        default: false
        version_added: 2.9
    backup:
        description:
        - Determine whether a backup should be created.
        - When set to C(yes), create a backup file including the timestamp information
          so you can get the original file back if you somehow clobbered it incorrectly.
        type: bool
        default: no
    fragment:
        description:
        - The string representation of the XML fragment expected at xpath.  Since ansible 2.9 not required when I(state=absent), or when I(count=yes).
        type: str
        required: false
        aliases: [ xmlstring ]
    path:
        description:
        - Path to the file to operate on.
        type: path
        required: true
        aliases: [ dest, file ]
    state:
        description:
        - Set or remove the nodes (or attributes) matched by I(xpath).
        type: str
        default: present
        choices: [ present, absent ]
        version_added: 2.9
    type:
        description:
        - The type of XML node you are working with.
        type: str
        required: yes
        default: element
        choices: [ attribute, element, text ]
    xpath:
        description:
        - Xpath to select the node or nodes to operate on.
        type: str
        required: true
author:
    - Richard Levenberg (@richardcs)
    - Jon Hawkesworth (@jhawkesworth)
notes:
    - Only supports operating on xml elements, attributes and text.
    - Namespace, processing-instruction, command and document node types cannot be modified with this module.
seealso:
    - module: xml
      description: XML manipulation for Posix hosts.
    - name: w3shools XPath tutorial
      description: A useful tutorial on XPath
      link: https://www.w3schools.com/xml/xpath_intro.asp
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

- name: remove debug configuration nodes from nlog.conf
  win_xml:
   path: C:\IISApplication\nlog.conf
   xpath: /nlog/rules/logger[@name="debug"]/descendant::*
   state: absent

- name: count configured connectors in Tomcat's server.xml
  win_xml:
   path: C:\Tomcat\conf\server.xml
   xpath: //Server/Service/Connector
   count: yes
  register: connector_count

- name: show connector count
  debug:
    msg="Connector count is {{connector_count.count}}"

- name: ensure all lang=en attributes to lang=nl
  win_xml:
   path: C:\Data\Books.xml
   xpath: //@[lang="en"]
   attribute: lang
   fragment: nl
   type: attribute

'''

RETURN = r'''
backup_file:
    description: Name of the backup file that was created.
    returned: if backup=yes
    type: str
    sample: C:\Path\To\File.txt.11540.20150212-220915.bak
count:
    description: Number of nodes matched by xpath.
    returned: if count=yes
    type: int
    sample: 33
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
