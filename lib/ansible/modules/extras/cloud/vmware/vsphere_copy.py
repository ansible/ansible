#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Dag Wieers <dag@wieers.com>
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
module: vsphere_copy
short_description: Copy a file to a vCenter datastore
description: 
    - Upload files to a vCenter datastore
version_added: 2.0
author: Dag Wieers (@dagwieers) <dag@wieers.com>
options:
  host:
    description:
      - The vCenter server on which the datastore is available.
    required: true
  login:
    description:
      - The login name to authenticate on the vCenter server.
    required: true
  password:
    description:
      - The password to authenticate on the vCenter server.
    required: true
  src:
    description:
      - The file to push to vCenter
    required: true
  datacenter:
    description:
      - The datacenter on the vCenter server that holds the datastore.
    required: true
  datastore:
    description:
      - The datastore on the vCenter server to push files to.
    required: true
  path:
    description:
      - The file to push to the datastore on the vCenter server.
    required: true
notes:
  - "This module ought to be run from a system that can access vCenter directly and has the file to transfer.
    It can be the normal remote target or you can change it either by using C(transport: local) or using C(delegate_to)."
  - Tested on vSphere 5.5
'''

EXAMPLES = '''
- vsphere_copy: host=vhost login=vuser password=vpass src=/some/local/file datacenter='DC1 Someplace' datastore=datastore1 path=some/remote/file
  transport: local
- vsphere_copy: host=vhost login=vuser password=vpass src=/other/local/file datacenter='DC2 Someplace' datastore=datastore2 path=other/remote/file
  delegate_to: other_system
'''

import atexit
import base64
import httplib
import urllib
import mmap
import errno
import socket

def vmware_path(datastore, datacenter, path):
    ''' Constructs a URL path that VSphere accepts reliably '''
    path = "/folder/%s" % path.lstrip("/")
    # Due to a software bug in vSphere, it fails to handle ampersand in datacenter names
    # The solution is to do what vSphere does (when browsing) and double-encode ampersands, maybe others ?
    datacenter = datacenter.replace('&', '%26')
    if not path.startswith("/"):
        path = "/" + path
    params = dict( dsName = datastore )
    if datacenter:
        params["dcPath"] = datacenter
    params = urllib.urlencode(params)
    return "%s?%s" % (path, params)

def main():

    module = AnsibleModule(
        argument_spec = dict(
            host = dict(required=True, aliases=[ 'hostname' ]),
            login = dict(required=True, aliases=[ 'username' ]),
            password = dict(required=True),
            src = dict(required=True, aliases=[ 'name' ]),
            datacenter = dict(required=True),
            datastore = dict(required=True),
            dest = dict(required=True, aliases=[ 'path' ]),
        ),
        # Implementing check-mode using HEAD is impossible, since size/date is not 100% reliable
        supports_check_mode = False,
    )

    host = module.params.get('host')
    login = module.params.get('login')
    password = module.params.get('password')
    src = module.params.get('src')
    datacenter = module.params.get('datacenter')
    datastore = module.params.get('datastore')
    dest = module.params.get('dest')

    fd = open(src, "rb")
    atexit.register(fd.close)

    data = mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ)
    atexit.register(data.close)

    conn = httplib.HTTPSConnection(host)
    atexit.register(conn.close)

    remote_path = vmware_path(datastore, datacenter, dest)
    auth = base64.encodestring('%s:%s' % (login, password)).rstrip()
    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Length": str(len(data)),
        "Authorization": "Basic %s" % auth,
    }

    # URL is only used in JSON output (helps troubleshooting)
    url = 'https://%s%s' % (host, remote_path)

    try:
        conn.request("PUT", remote_path, body=data, headers=headers)
    except socket.error, e:
        if isinstance(e.args, tuple) and e[0] == errno.ECONNRESET:
            # VSphere resets connection if the file is in use and cannot be replaced
            module.fail_json(msg='Failed to upload, image probably in use', status=e[0], reason=str(e), url=url)
        else:
            module.fail_json(msg=str(e), status=e[0], reason=str(e), url=url)

    resp = conn.getresponse()

    if resp.status in range(200, 300):
        module.exit_json(changed=True, status=resp.status, reason=resp.reason, url=url)
    else:
        module.fail_json(msg='Failed to upload', status=resp.status, reason=resp.reason, length=resp.length, version=resp.version, headers=resp.getheaders(), chunked=resp.chunked, url=url)

# Import module snippets
from ansible.module_utils.basic import *

main()
