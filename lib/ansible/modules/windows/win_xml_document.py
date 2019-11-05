#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Micah Hunsberger (@mhunsber)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_xml_document
short_description: Manage an XML Document file or string.
description:
- A CRUD-like interface to managing XML documents.
version_added: '2.10'
options:
  path:
    description:
    - Path to the file to operate on.
    - This file must exist ahead of time.
    - This parameter is required, unless C(xmlstring) is given.
    type: path
    required: yes
    aliases: [ dest, file ]
  xmlstring:
    description:
    - A string containing XML on which to operate.
    - This parameter is required, unless C(path) is given.
    type: str
    required: yes
  xpath:
    description:
    - A valid XPath expression describing the item(s) you want to manipulate.
    - Differs slightly from the XPath expression in M(xml), see notes for details.
    type: str
  namespaces:
    description:
    - A dictionary maping of namespaces C(prefix:uri) XPath expression.
    - Needs to be a C(dict), not a C(list) of items.
    type: dict
  state:
    description:
    - Set or remove an xpath selection (node(s), attribute(s)).
    type: str
    choices: [ absent, present ]
    default: present
    aliases: [ ensure ]
  value:
    description:
    - Desired value of the selected node(s) from C(xpath).
    - Must be a C(str), this is different from the M(xml) module.
    - To unset an attribute or element text, set to an empty string.
    - If not set, only element or attribute presence is checked.
    type: str
  add_children:
    description:
    - Add additional child-element(s) to a selected element for a given C(xpath).
    - Child elements must be given in a list and each item may be either a string
      (eg. C(children=ansible) to add an empty C(<ansible/>) child element),
      or a hash where the key is an element name and the value is the element value.
    - This parameter requires C(xpath) to be set.
    - This parameter always adds the children, so it is never idempotent.
    type: list
  set_children:
    description:
    - Set the child-element(s) of a selected element for a given C(xpath).
    - Removes any existing children.
    - Child elements must be specified as in C(add_children).
    - This parameter requires C(xpath) to be set.
    type: list
  count:
    description:
    - Search for a given C(xpath) and provide the count of any matches.
    - This parameter requires C(xpath) to be set.
    type: bool
    default: no
  print_match:
    description:
    - Search for a given C(xpath) and print out any matches.
    - This parameter requires C(xpath) to be set.
    type: bool
    default: no
  indent:
    description:
    - Whether or not to use the indent formatting for the XML document.
    - If this is set to I(False), then the document will be printed on a single line.
    type: bool
    default: yes
  indent_spaces:
    description:
    - When C(indent=true), this controls how many spaces to use for indentation when formatting the document.
    type: int
    default: 2
  content:
    description:
    - Search for a given C(xpath) and get content.
    - This parameter requires C(xpath) to be set.
    type: str
    choices: [ attribute, text ]
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  insertbefore:
    description:
      - Add additional child-element(s) before the first selected element for a given C(xpath).
      - Child elements must be given in a list and each item may be either a string
        (eg. C(children=ansible) to add an empty C(<ansible/>) child element),
        or a hash where the key is an element name and the value is the element value.
      - This parameter requires C(xpath) to be set.
    type: bool
    default: no
  insertafter:
    description:
      - Add additional child-element(s) after the last selected element for a given C(xpath).
      - Child elements must be given in a list and each item may be either a string
        (eg. C(children=ansible) to add an empty C(<ansible/>) child element),
        or a hash where the key is an element name and the value is the element value.
      - This parameter requires C(xpath) to be set.
    type: bool
    default: no
notes:
- Use the C(--check) and C(--diff) options when testing your expressions.
- The diff output is automatically formatted based on the input parameters, so may not reflect the actual file content, only the file structure.
- If you only set C(indent) and C(indent_spaces), the diff output will reflect the original file content, since formatting is the only thing changing.
- This module does not handle complicated xpath expressions, so limit xpath selectors to simple expressions.
- In M(xml), an xpath xpression of '/business/beers/beer/@alcohol = 0.3' will set the @alcohol attribute to 0.3.
  In the .NET XPathExpression object, this resolves to a boolean expression, and can't be used to select attribute node(s).
  Instead, use C(xpath='/business/beers/beer/@alcohol',state='present',value='0.3'), which will set all 'beer/@alcohol' attributes to 0.3.
  To only set a specific beer alcohol attribute, limit your xpath expression to a single node, such as '//beer[text()="Old Rasputin"]/@alcohol'
- Beware that in case your XML elements are namespaced, you need to use the C(namespaces) parameter, see the examples.
- Namespaces prefix should be used for all children of an element where namespace is defined, unless another namespace is defined for them.
seealso:
- module: win_xml
- module: xml
- name: Introduction to XPath
  description: A brief tutorial on XPath (w3schools.com).
  link: https://www.w3schools.com/xml/xpath_intro.asp
- name: XPath Reference document
  description: The reference documentation on XSLT/XPath (developer.mozilla.org).
  link: https://developer.mozilla.org/en-US/docs/Web/XPath
author:
- Micah Hunsberger (@mhunsber)
'''

EXAMPLES = r'''
# Consider the following XML file:
#
# <business type="bar">
#   <name>Tasty Beverage Co.</name>
#     <beers>
#       <beer>Rochefort 10</beer>
#       <beer>St. Bernardus Abbot 12</beer>
#       <beer>Schlitz</beer>
#    </beers>
#   <rating subjective="true">10</rating>
#   <website>
#     <mobilefriendly/>
#     <address>http://tastybeverageco.com</address>
#   </website>
# </business>

- name: Remove the 'subjective' attribute of the 'rating' element
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/rating/@subjective
    state: absent

- name: Set the rating to '11'
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/rating
    value: 11

# Retrieve and display the number of nodes
- name: Get count of 'beers' nodes
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/beers/beer
    count: yes
  register: hits

- debug:
    var: hits.count

# Example where parent XML nodes are created automatically
- name: Add a 'phonenumber' element to the 'business' element
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/phonenumber
    value: 555-555-1234

- name: Add several more beers to the 'beers' element
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/beers
    add_children:
    - beer: Old Rasputin
    - beer: Old Motor Oil
    - beer: Old Curmudgeon

- name: Add several more beers to the 'beers' element and add them before the 'Rochefort 10' element
  win_xml_document:
    path: \foo\bar.xml
    xpath: '/business/beers/beer[text()="Rochefort 10"]'
    insertbefore: yes
    add_children:
    - beer: Old Rasputin
    - beer: Old Motor Oil
    - beer: Old Curmudgeon

# NOTE: The 'state' defaults to 'present' and 'value' defaults to 'null' for elements
- name: Add a 'validxhtml' element to the 'website' element
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/website/validxhtml

- name: Add an empty 'validatedon' attribute to the 'validxhtml' element
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/website/validxhtml/@validatedon

- name: Add or modify an attribute, add element if needed
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/website/validxhtml/@validatedon
    value: 1976-08-05

# How to read an attribute value and access it in Ansible
- name: Read an element's attribute values
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/website/validxhtml
    content: attribute
  register: xmlresp

- name: Show an attribute value
  debug:
    var: xmlresp.matches[0].validxhtml.validatedon

- name: Remove all children from the 'website' element
  win_xml_document:
    path: \foo\bar.xml
    xpath: /business/website/*
    state: absent

# In case of namespaces, like in below XML, they have to be explicitly stated.
#
# <foo xmlns="http://x.test" xmlns:attr="http://z.test">
#   <bar>
#     <baz xmlns="http://y.test" attr:my_namespaced_attribute="true" />
#   </bar>
# </foo>

# NOTE: There is the prefix 'x' in front of the 'bar' element, too.
- name: Set namespaced '/x:foo/x:bar/y:baz/@z:my_namespaced_attribute' to 'false'
  win_xml_document:
    path: foo.xml
    xpath: /x:foo/x:bar/y:baz
    namespaces:
      x: http://x.test
      y: http://y.test
      z: http://z.test
    attribute: z:my_namespaced_attribute
    value: 'false'
'''

RETURN = r'''
actions:
    description: A dictionary with the original xpath, namespaces and state.
    type: dict
    returned: success
    sample: {xpath: xpath, namespaces: [namespace1, namespace2], state=present}
backup_file:
    description: The name of the backup file that was created
    type: str
    returned: when backup=yes
    sample: /path/to/file.xml.1942.2017-08-24@14:16:01~
count:
    description: The count of xpath matches.
    type: int
    returned: when parameter 'count' is set
    sample: 2
matches:
    description: The xpath matches found.
    type: list
    returned: when parameter 'print_match', or 'content' is set
xmlstring:
    description: An XML string of the resulting output.
    type: str
    returned: when parameter 'xmlstring' is set
'''
