#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Corwin Brown <corwin@corwinbrown.com>
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = """
---
module: win_uri
version_added: "2.1"
short_description: Interacts with webservices.
description:
  - Interacts with HTTP and HTTPS web services and supports Digest, Basic and WSSE HTTP authentication mechanisms.
options:
  url:
    description:
      - HTTP or HTTPS URL in the form of (http|https)://host.domain:port/path
  method:
    description:
      - The HTTP Method of the request or response.
    default: GET
    choices:
      - GET
      - POST
      - PUT
      - HEAD
      - DELETE
      - OPTIONS
      - PATCH
      - TRACE
      - CONNECT
      - REFRESH
  content_type:
    description:
      - Sets the "Content-Type" header.
  body:
    description:
      - The body of the HTTP request/response to the web service.
  headers:
    description:
      - 'Key Value pairs for headers. Example "Host: www.somesite.com"'
  use_basic_parsing:
    description:
      - This module relies upon 'Invoke-WebRequest', which by default uses the Internet Explorer Engine to parse a webpage. There's an edge-case where if a user hasn't run IE before, this will fail. The only advantage to using the Internet Explorer praser is that you can traverse the DOM in a powershell script. That isn't useful for Ansible, so by default we toggle 'UseBasicParsing'. However, you can toggle that off here.
    choices:
      - True
      - False
    default: True
author: Corwin Brown (@blakfeld)
"""

EXAMPLES = """
# Send a GET request and store the output:
---
- name: Perform a GET and Store Output
  win_uri:
    url: http://www.somesite.com/myendpoint
  register: http_output

# Set a HOST header to hit an internal webserver:
---
- name: Hit a Specific Host on the Server
  win_uri:
    url: http://my.internal.server.com
    method: GET
    headers:
      host: "www.somesite.com"

# Do a HEAD request on an endpoint
---
- name: Perform a HEAD on an Endpoint
  win_uri:
    url: http://www.somesite.com
    method: HEAD

# Post a body to an endpoint
---
- name: POST a Body to an Endpoint
  win_uri:
    url: http://www.somesite.com
    method: POST
    body: "{ 'some': 'json' }"
"""

RETURN = """
url:
  description: The Target URL
  returned: always
  type: string
  sample: "http://www.ansible.com"
method:
  description: The HTTP method used.
  returned: always
  type: string
  sample: "GET"
content_type:
  description: The "content-type" header used.
  returned: always
  type: string
  sample: "application/json"
use_basic_parsing:
  description: The state of the "use_basic_parsing" flag.
  returned: always
  type: bool
  sample: True
status_code:
  description: The HTTP Status Code of the response.
  returned: success
  type: int
  sample: 200
status_description:
  description: A summery of the status.
  returned: success
  type: string
  stample: "OK"
raw_content:
  description: The raw content of the HTTP response.
  returned: success
  type: string
  sample: 'HTTP/1.1 200 OK\nX-XSS-Protection: 1; mode=block\nX-Frame-Options: SAMEORIGIN\nAlternate-Protocol: 443:quic,p=1\nAlt-Svc: quic="www.google.com:443"; ma=2592000; v="30,29,28,27,26,25",quic=":443"; ma=2...'
headers:
  description: The Headers of the response.
  returned: success
  type: dict
  sample: {"Content-Type": "application/json"}
raw_content_length:
  description: The byte size of the response.
  returned: success
  type: int
  sample: 54447
"""
