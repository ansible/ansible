#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Corwin Brown <corwin@corwinbrown.com>
# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_uri
version_added: '2.1'
short_description: Interacts with webservices
description:
- Interacts with FTP, HTTP and HTTPS web services.
- Supports Digest, Basic and WSSE HTTP authentication mechanisms.
- For non-Windows targets, use the M(uri) module instead.
options:
  url:
    description:
    - Supports FTP, HTTP or HTTPS URLs in the form of (ftp|http|https)://host.domain:port/path.
    type: str
    required: yes
  method:
    description:
    - The HTTP Method of the request or response.
    type: str
    default: GET
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
    version_added: '2.3'
  creates:
    description:
    - A filename, when it already exists, this step will be skipped.
    type: path
    version_added: '2.4'
  removes:
    description:
    - A filename, when it does not exist, this step will be skipped.
    type: path
    version_added: '2.4'
  return_content:
    description:
    - Whether or not to return the body of the response as a "content" key in
      the dictionary result. If the reported Content-type is
      "application/json", then the JSON is additionally loaded into a key
      called C(json) in the dictionary results.
    type: bool
    default: no
    version_added: '2.4'
  status_code:
    description:
    - A valid, numeric, HTTP status code that signifies success of the request.
    - Can also be comma separated list of status codes.
    type: list
    default: [ 200 ]
    version_added: '2.4'
  url_username:
    description:
    - The username to use for authentication.
    - Was originally called I(user) but was changed to I(url_username) in
      Ansible 2.9.
    version_added: "2.4"
  url_password:
    description:
    - The password for I(url_username).
    - Was originally called I(password) but was changed to I(url_password) in
      Ansible 2.9.
    version_added: "2.4"
  follow_redirects:
    version_added: "2.4"
  maximum_redirection:
    version_added: "2.4"
  client_cert:
    version_added: "2.4"
  client_cert_password:
    version_added: "2.5"
  use_proxy:
    version_added: "2.9"
  proxy_url:
    version_added: "2.9"
  proxy_username:
    version_added: "2.9"
  proxy_password:
    version_added: "2.9"
extends_documentation_fragment:
- url_windows
seealso:
- module: uri
- module: win_get_url
author:
- Corwin Brown (@blakfeld)
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Perform a GET and Store Output
  win_uri:
    url: http://example.com/endpoint
  register: http_output

# Set a HOST header to hit an internal webserver:
- name: Hit a Specific Host on the Server
  win_uri:
    url: http://example.com/
    method: GET
    headers:
      host: www.somesite.com

- name: Perform a HEAD on an Endpoint
  win_uri:
    url: http://www.example.com/
    method: HEAD

- name: POST a Body to an Endpoint
  win_uri:
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
