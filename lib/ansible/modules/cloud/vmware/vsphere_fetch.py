#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017 Tim Rightnour
# (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# Copyright 2015 Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vsphere_fetch
short_description: Fetch a file from a vCenter datastore
description:
    - Download files from a vCenter datastore
version_added: 2.5
author: Tim Rightnour (@garbled1)
options:
  host:
    description:
      - The vCenter server on which the datastore is available.
    required: true
  url_username:
    description:
      - The login name to authenticate on the vCenter server.
    required: true
    aliases: ['username', 'login']
  url_password:
    description:
      - The password to authenticate on the vCenter server.
    required: true
    aliases: ['password']
  src:
    description:
      - The file on the datastore to fetch
    required: true
  datacenter:
    description:
      - The datacenter on the vCenter server that holds the datastore.
    required: true
  datastore:
    description:
      - The datastore on the vCenter server to fetch files from.
    required: true
  dest:
    description:
      - The file path to save the file to locally
    required: true
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be
        set to C(no) when no other option exists.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
  tmp_dest:
    description:
      - Absolute path of where temporary file is downloaded to.
      - Defaults to C(TMPDIR), C(TEMP) or C(TMP) env variables or a platform specific value.
      - U(https://docs.python.org/2/library/tempfile.html#tempfile.tempdir)
  force:
    description:
      - If C(yes) and C(dest) is not a directory, will download the file every
        time and replace the file if the contents change. If C(no), the file
        will only be downloaded if the destination does not exist. Generally
        should be C(yes) only for small local files.
      - Prior to 0.6, this module behaved as if C(yes) was the default.
    default: 'no'
    type: bool
    aliases: ['thirsty']
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    required: false
    default: 'no'
    type: bool
  timeout:
    description:
      - Timeout in seconds for URL request.
    default: 10
  others:
    description:
      - all arguments accepted by the M(file) module also work here
# informational: requirements for nodes
extends_documentation_fragment:
    - files
notes:
  - "This module ought to be run from a system that can access vCenter directly.
    It can be the normal remote target or you can change it either by using C(transport: local) or using C(delegate_to)."
  - Tested on vSphere 5.5, 6.0
'''

EXAMPLES = '''
- name: Fetch a file to the ansible server
  vsphere_fetch:
    host: vhost
    login: vuser
    password: vpass
    src: some/remote/file
    datacenter: DC1 Someplace
    datastore: datastore1
    dest: /some/local/file
  transport: local
- name: Fetch a file to the managed node, set mode and ownership
  vsphere_fetch:
    host: vhost
    login: vuser
    password: vpass
    src: other/remote/file
    datacenter: DC2 Someplace
    datastore: datastore2
    dest: /other/local/directory/
    owner: root
    group: root
    mode: 0644
  delegate_to: other_system
'''

RETURN = r'''
backup_file:
    description: name of backup file created after download
    returned: changed and if backup=yes
    type: string
    sample: /path/to/file.txt.2015-02-12@22:09~
dest:
    description: destination file/path
    returned: success
    type: string
    sample: /path/to/file.txt
gid:
    description: group id of the file
    returned: success
    type: int
    sample: 100
group:
    description: group of the file
    returned: success
    type: string
    sample: "httpd"
md5sum:
    description: md5 checksum of the file after download
    returned: when supported
    type: string
    sample: "2a5aeecc61dc98c4d780b14b330e3282"
mode:
    description: permissions of the target
    returned: success
    type: string
    sample: "0644"
msg:
    description: the HTTP message from the request
    returned: always
    type: string
    sample: OK (unknown bytes)
owner:
    description: owner of the file
    returned: success
    type: string
    sample: httpd
secontext:
    description: the SELinux security context of the file
    returned: success
    type: string
    sample: unconfined_u:object_r:user_tmp_t:s0
size:
    description: size of the target
    returned: success
    type: int
    sample: 1220
src:
    description: source file used after download
    returned: changed
    type: string
    sample: /tmp/tmpAdFLdV
state:
    description: state of the target
    returned: success
    type: string
    sample: file
status:
    description: the HTTP status code from the request
    returned: always
    type: int
    sample: 200
uid:
    description: owner id of the file, after execution
    returned: success
    type: int
    sample: 100
url:
    description: the actual URL used for the request
    returned: always
    type: string
    sample: https://www.ansible.com/
datastore:
    description: the datastore we fetched the file from
    returned: success
    type: string
    sample: datastore1
datacenter:
    description: the datacenter the datastore was located on
    returned: success
    type: string
    sample: dc_1
'''


import os
import tempfile
import shutil
import traceback
import re
import datetime

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlsplit, urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


def vmware_path(datastore, datacenter, path):
    ''' Constructs a URL path that VSphere accepts reliably '''
    path = "/folder/%s" % path.lstrip("/")
    # Due to a software bug in vSphere, it fails to handle ampersand in datacenter names
    # The solution is to do what vSphere does (when browsing) and double-encode ampersands, maybe others ?
    datacenter = datacenter.replace('&', '%26')
    if not path.startswith("/"):
        path = "/" + path
    params = dict(dsName=datastore)
    if datacenter:
        params["dcPath"] = datacenter
    params = urlencode(params)
    return "%s?%s" % (path, params)


def vmware_get(module, url, dest, last_mod_time, force, timeout, tmp_dest):
    """
    Download the file from vsphere and store in a temporary file.
    Code based on get_url module

    Return (tempfile, info about the request)
    """
    if module.check_mode:
        method = 'HEAD'
    else:
        method = 'GET'

    # I'm not sure if vmware does an ECONNRESET on download of file in use
    r, info = fetch_url(module, url, force=force)

    if info['status'] == 304:
        module.exit_json(url=url, dest=dest, changed=False, msg=info.get('msg', ''))

    # Exceptions in fetch_url may result in a status -1, the ensures a proper error to the user in all cases
    if info['status'] == -1:
        module.fail_json(msg=info['msg'], url=url, dest=dest)

    if info['status'] != 200:
        module.fail_json(msg="Request failed", status_code=info['status'], response=info['msg'], url=url, dest=dest)

    # create a temporary file and copy content to do checksum-based replacement
    if tmp_dest:
        # tmp_dest should be an existing dir
        tmp_dest_is_dir = os.path.isdir(tmp_dest)
        if not tmp_dest_is_dir:
            if os.path.exists(tmp_dest):
                module.fail_json(msg="%s is a file but should be a directory." % tmp_dest)
            else:
                module.fail_json(msg="%s directory does not exist." % tmp_dest)

        fd, tempname = tempfile.mkstemp(dir=tmp_dest)
    else:
        fd, tempname = tempfile.mkstemp()

    f = os.fdopen(fd, 'wb')
    try:
        shutil.copyfileobj(r, f)
    except Exception as e:
        os.remove(tempname)
        module.fail_json(msg="{0} {1}".format(str(r), str(info)))
        module.fail_json(msg="failed to create temporary content file: %s" % to_native(e),
                         exception=traceback.format_exc())
    f.close()
    r.close()
    return tempname, info


def extract_filename_from_headers(headers):
    """
    Extracts a filename from the given dict of HTTP headers.
    Looks for the content-disposition header and applies a regex.
    Returns the filename if successful, else None.
    Taken from get_url module
    """
    cont_disp_regex = 'attachment; ?filename="?([^"]+)'
    res = None

    if 'content-disposition' in headers:
        cont_disp = headers['content-disposition']
        match = re.match(cont_disp_regex, cont_disp)
        if match:
            res = match.group(1)
            # Try preventing any funny business.
            res = os.path.basename(res)

    return res


def url_filename(url):
    fn = os.path.basename(urlsplit(url)[2])
    if fn == '':
        return 'index.html'
    return fn


def main():

    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True, aliases=['hostname']),
            url_username=dict(required=True, aliases=['username', 'login']),
            url_password=dict(required=True, no_log=True, aliases=['password']),
            src=dict(required=True, aliases=['name']),
            datacenter=dict(required=True),
            datastore=dict(required=True),
            dest=dict(required=True, aliases=['path'], type='path'),
            backup=dict(type='bool'),
            tmp_dest=dict(type='path'),
            timeout=dict(type='int', default=10),
            force=dict(default='no', aliases=['thirsty'], type='bool'),
            validate_certs=dict(required=False, default=True, type='bool'),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    host = module.params.get('host')
    login = module.params.get('url_username')
    password = module.params.get('url_password')
    src = module.params.get('src')
    datacenter = module.params.get('datacenter')
    datastore = module.params.get('datastore')
    dest = module.params.get('dest')
    validate_certs = module.params.get('validate_certs')
    tmp_dest = module.params.get('tmp_dest')
    backup = module.params.get('backup')
    force = module.params.get('force')
    timeout = module.params.get('timeout')

    dest_is_dir = os.path.isdir(dest)
    last_mod_time = None

    remote_path = vmware_path(datastore, datacenter, src)
    url = 'https://%s%s' % (host, remote_path)

    if not dest_is_dir and os.path.exists(dest):
        if not force:
            # allow file attribute changes
            module.params['path'] = dest
            file_args = module.load_file_common_arguments(module.params)
            file_args['path'] = dest
            changed = module.set_fs_attributes_if_different(file_args, False)

            if changed:
                module.exit_json(msg="file already exists but file attributes changed", dest=dest, url=url, changed=changed)
            module.exit_json(msg="file already exists", dest=dest, url=url, changed=changed)

        # If the file already exists, prepare the last modified time for the
        # request.
        mtime = os.path.getmtime(dest)
        last_mod_time = datetime.datetime.utcfromtimestamp(mtime)

    tmpsrc, info = vmware_get(module, url=url, dest=dest, last_mod_time=last_mod_time,
                              force=force, timeout=timeout, tmp_dest=tmp_dest)

    if dest_is_dir:
        filename = extract_filename_from_headers(info)
        if not filename:
            # Fall back to extracting the filename from the URL.
            # Pluck the URL from the info, since a redirect could have changed
            # it.
            filename = url_filename(info['url'])
        dest = os.path.join(dest, filename)

    # If the remote URL exists, we're done with check mode
    if module.check_mode:
        os.remove(tmpsrc)
        res_args = dict(url=url, dest=dest, src=tmpsrc, changed=True, msg=info.get('msg', ''))
        module.exit_json(**res_args)

    # raise an error if there is no tmpsrc file
    if not os.path.exists(tmpsrc):
        os.remove(tmpsrc)
        module.fail_json(msg="Request failed", status_code=info['status'], response=info['msg'])
    if not os.access(tmpsrc, os.R_OK):
        os.remove(tmpsrc)
        module.fail_json(msg="Source %s is not readable" % (tmpsrc))
    checksum_src = module.sha1(tmpsrc)

    # check if there is no dest file
    if os.path.exists(dest):
        # raise an error if copy has no permission on dest
        if not os.access(dest, os.W_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not writable" % (dest))
        if not os.access(dest, os.R_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not readable" % (dest))
    else:
        if not os.path.exists(os.path.dirname(dest)):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s does not exist" % (os.path.dirname(dest)))
        if not os.access(os.path.dirname(dest), os.W_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not writable" % (os.path.dirname(dest)))

    backup_file = None
    try:
        if backup:
            if os.path.exists(dest):
                backup_file = module.backup_local(dest)
        module.atomic_move(tmpsrc, dest)
    except Exception as e:
        if os.path.exists(tmpsrc):
            os.remove(tmpsrc)
        module.fail_json(msg="failed to copy %s to %s: %s" % (tmpsrc, dest, to_native(e)),
                         exception=traceback.format_exc())
    changed = True

    # allow file attribute changes
    module.params['path'] = dest
    file_args = module.load_file_common_arguments(module.params)
    file_args['path'] = dest
    changed = module.set_fs_attributes_if_different(file_args, changed)

    # Backwards compat only.  We'll return None on FIPS enabled systems
    try:
        md5sum = module.md5(dest)
    except ValueError:
        md5sum = None

    res_args = dict(
        url=url, dest=dest, src=tmpsrc, md5sum=md5sum, datacenter=datacenter,
        datastore=datastore, changed=changed, msg=info.get('msg', ''),
        status_code=info.get('status', '')
    )
    if backup_file:
        res_args['backup_file'] = backup_file

    # Mission complete
    module.exit_json(**res_args)


if __name__ == '__main__':
    main()
