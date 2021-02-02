#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Corwin Brown <corwin@corwinbrown.com>
# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r'''
---
module: win_uri
short_description: Interacts with webservices
description:
- Interacts with FTP, HTTP and HTTPS web services.
- Supports Digest, Basic and WSSE HTTP authentication mechanisms.
- For non-Windows targets, use the M(ansible.builtin.uri) module instead.
options:
  url:
    description:
    - Supports FTP, HTTP or HTTPS URLs in the form of (ftp|http|https)://host.domain:port/path.
    type: str
    required: yes
  content_type:
    description:
    - Sets the "Content-Type" header.
    type: str
  body:
    description:
    - The body of the HTTP request/response to the web service.
    type: raw
  dest:
    description:
    - Output the response body to a file.
    type: path
  creates:
    description:
    - A filename, when it already exists, this step will be skipped.
    type: path
  removes:
    description:
    - A filename, when it does not exist, this step will be skipped.
    type: path
  return_content:
    description:
    - Whether or not to return the body of the response as a "content" key in
      the dictionary result. If the reported Content-type is
      "application/json", then the JSON is additionally loaded into a key
      called C(json) in the dictionary results.
    type: bool
    default: no
  status_code:
    description:
    - A valid, numeric, HTTP status code that signifies success of the request.
    - Can also be comma separated list of status codes.
    type: list
    elements: int
    default: [ 200 ]

  url_method:
    default: GET
    aliases:
    - method
  url_timeout:
    aliases:
    - timeout

  # Following defined in the web_request fragment but the module contains deprecated aliases for backwards compatibility.
  url_username:
    description:
    - The username to use for authentication.
    - The alias I(user) and I(username) is deprecated and will be removed on
      the major release after C(2022-07-01).
    aliases:
    - user
    - username
  url_password:
    description:
    - The password for I(url_username).
    - The alias I(password) is deprecated and will be removed on the major
      release after C(2022-07-01).
    aliases:
    - password
extends_documentation_fragment:
- ansible.windows.web_request

seealso:
- module: ansible.builtin.uri
- module: ansible.windows.win_get_url
author:
- Corwin Brown (@blakfeld)
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Perform a GET and Store Output
  ansible.windows.win_uri:
    url: http://example.com/endpoint
  register: http_output

# Set a HOST header to hit an internal webserver:
- name: Hit a Specific Host on the Server
  ansible.windows.win_uri:
    url: http://example.com/
    method: GET
    headers:
      host: www.somesite.com

- name: Perform a HEAD on an Endpoint
  ansible.windows.win_uri:
    url: http://www.example.com/
    method: HEAD

- name: POST a Body to an Endpoint
  ansible.windows.win_uri:
    url: http://www.somesite.com/
    method: POST
    body: "{ 'some': 'json' }"
'''

RETURN = r'''
elapsed:
  description: The number of seconds that elapsed while performing the download.
  returned: always
  type: float
  sample: 23.2
url:
  description: The Target URL.
  returned: always
  type: str
  sample: https://www.ansible.com
status_code:
  description: The HTTP Status Code of the response.
  returned: success
  type: int
  sample: 200
status_description:
  description: A summary of the status.
  returned: success
  type: str
  sample: OK
content:
  description: The raw content of the HTTP response.
  returned: success and return_content is True
  type: str
  sample: '{"foo": "bar"}'
content_length:
  description: The byte size of the response.
  returned: success
  type: int
  sample: 54447
json:
  description: The json structure returned under content as a dictionary.
  returned: success and Content-Type is "application/json" or "application/javascript" and return_content is True
  type: dict
  sample: {"this-is-dependent": "on the actual return content"}
'''
