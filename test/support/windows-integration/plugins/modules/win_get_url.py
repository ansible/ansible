#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Paul Durivage <paul.durivage@rackspace.com>, and others
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_get_url
version_added: "1.7"
short_description: Downloads file from HTTP, HTTPS, or FTP to node
description:
- Downloads files from HTTP, HTTPS, or FTP to the remote server.
- The remote server I(must) have direct access to the remote resource.
- For non-Windows targets, use the M(get_url) module instead.
options:
  url:
    description:
    - The full URL of a file to download.
    type: str
    required: yes
  dest:
    description:
    - The location to save the file at the URL.
    - Be sure to include a filename and extension as appropriate.
    type: path
    required: yes
  force:
    description:
    - If C(yes), will download the file every time and replace the file if the contents change. If C(no), will only
      download the file if it does not exist or the remote file has been
      modified more recently than the local file.
    - This works by sending an http HEAD request to retrieve last modified
      time of the requested resource, so for this to work, the remote web
      server must support HEAD requests.
    type: bool
    default: yes
    version_added: "2.0"
  checksum:
    description:
      - If a I(checksum) is passed to this parameter, the digest of the
        destination file will be calculated after it is downloaded to ensure
        its integrity and verify that the transfer completed successfully.
      - This option cannot be set with I(checksum_url).
    type: str
    version_added: "2.8"
  checksum_algorithm:
    description:
      - Specifies the hashing algorithm used when calculating the checksum of
        the remote and destination file.
    type: str
    choices:
      - md5
      - sha1
      - sha256
      - sha384
      - sha512
    default: sha1
    version_added: "2.8"
  checksum_url:
    description:
      - Specifies a URL that contains the checksum values for the resource at
        I(url).
      - Like C(checksum), this is used to verify the integrity of the remote
        transfer.
      - This option cannot be set with I(checksum).
    type: str
    version_added: "2.8"
  url_username:
    description:
    - The username to use for authentication.
    - The aliases I(user) and I(username) are deprecated and will be removed in
      Ansible 2.14.
    aliases:
    - user
    - username
  url_password:
    description:
    - The password for I(url_username).
    - The alias I(password) is deprecated and will be removed in Ansible 2.14.
    aliases:
    - password
  proxy_url:
    version_added: "2.0"
  proxy_username:
    version_added: "2.0"
  proxy_password:
    version_added: "2.0"
  headers:
    version_added: "2.4"
  use_proxy:
    version_added: "2.4"
  follow_redirects:
    version_added: "2.9"
  maximum_redirection:
    version_added: "2.9"
  client_cert:
    version_added: "2.9"
  client_cert_password:
    version_added: "2.9"
  method:
    description:
    - This option is not for use with C(win_get_url) and should be ignored.
    version_added: "2.9"
notes:
- If your URL includes an escaped slash character (%2F) this module will convert it to a real slash.
  This is a result of the behaviour of the System.Uri class as described in
  L(the documentation,https://docs.microsoft.com/en-us/dotnet/framework/configure-apps/file-schema/network/schemesettings-element-uri-settings#remarks).
- Since Ansible 2.8, the module will skip reporting a change if the remote
  checksum is the same as the local local even when C(force=yes). This is to
  better align with M(get_url).
extends_documentation_fragment:
- url_windows
seealso:
- module: get_url
- module: uri
- module: win_uri
author:
- Paul Durivage (@angstwad)
- Takeshi Kuramochi (@tksarah)
'''

EXAMPLES = r'''
- name: Download earthrise.jpg to specified path
  win_get_url:
    url: http://www.example.com/earthrise.jpg
    dest: C:\Users\RandomUser\earthrise.jpg

- name: Download earthrise.jpg to specified path only if modified
  win_get_url:
    url: http://www.example.com/earthrise.jpg
    dest: C:\Users\RandomUser\earthrise.jpg
    force: no

- name: Download earthrise.jpg to specified path through a proxy server.
  win_get_url:
    url: http://www.example.com/earthrise.jpg
    dest: C:\Users\RandomUser\earthrise.jpg
    proxy_url: http://10.0.0.1:8080
    proxy_username: username
    proxy_password: password

- name: Download file from FTP with authentication
  win_get_url:
    url: ftp://server/file.txt
    dest: '%TEMP%\ftp-file.txt'
    url_username: ftp-user
    url_password: ftp-password

- name: Download src with sha256 checksum url
  win_get_url:
    url: http://www.example.com/earthrise.jpg
    dest: C:\temp\earthrise.jpg
    checksum_url: http://www.example.com/sha256sum.txt
    checksum_algorithm: sha256
    force: True

- name: Download src with sha256 checksum url
  win_get_url:
    url: http://www.example.com/earthrise.jpg
    dest: C:\temp\earthrise.jpg
    checksum: a97e6837f60cec6da4491bab387296bbcd72bdba
    checksum_algorithm: sha1
    force: True
'''

RETURN = r'''
dest:
    description: destination file/path
    returned: always
    type: str
    sample: C:\Users\RandomUser\earthrise.jpg
checksum_dest:
    description: <algorithm> checksum of the file after the download
    returned: success and dest has been downloaded
    type: str
    sample: 6e642bb8dd5c2e027bf21dd923337cbb4214f827
checksum_src:
    description: <algorithm> checksum of the remote resource
    returned: force=yes or dest did not exist
    type: str
    sample: 6e642bb8dd5c2e027bf21dd923337cbb4214f827
elapsed:
    description: The elapsed seconds between the start of poll and the end of the module.
    returned: always
    type: float
    sample: 2.1406487
size:
    description: size of the dest file
    returned: success
    type: int
    sample: 1220
url:
    description: requested url
    returned: always
    type: str
    sample: http://www.example.com/earthrise.jpg
msg:
    description: Error message, or HTTP status message from web-server
    returned: always
    type: str
    sample: OK
status_code:
    description: HTTP status code
    returned: always
    type: int
    sample: 200
'''
