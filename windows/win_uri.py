#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Corwin Brown <blakfeld@gmail.com>
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
version_added: "2.0"
short_description: Interacts with webservices.
description:
  - Interacts with HTTP and HTTPS services.
options:
  url:
    description:
      - HTTP or HTTPS URL in the form of (http|https)://host.domain:port/path
    required: true
  method:
    description:
      - The HTTP Method of the request or response.
    default: GET
    required: false
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
    required: false
    default: None
  headers:
    description:
      - Key Value pairs for headers. Example "Host: www.somesite.com"
    required: false
    default: None
author: Corwin Brown (@blakfeld)
"""

Examples = """
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
      host: "www.somesite.com

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

# Check if a file is available on a webserver
---
- name: Ensure Build is Available on Fileserver
  when: ensure_build
  win_uri:
    url: "http://www.somesite.com"
    method: HEAD
    headers:
      test: one
      another: two
  register: build_check_output
  until: build_check_output.StatusCode == 200
  retries: 30
  delay: 10
"""
