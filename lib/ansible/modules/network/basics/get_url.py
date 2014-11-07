#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
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
#
# see examples/playbooks/get_url.yml

import shutil
import datetime
import re
import tempfile

DOCUMENTATION = '''
---
module: get_url
short_description: Downloads files from HTTP, HTTPS, or FTP to node
description:
     - Downloads files from HTTP, HTTPS, or FTP to the remote server. The remote
       server I(must) have direct access to the remote resource.
     - By default, if an environment variable C(<protocol>_proxy) is set on
       the target host, requests will be sent through that proxy. This
       behaviour can be overridden by setting a variable for this task
       (see `setting the environment
       <http://docs.ansible.com/playbooks_environment.html>`_),
       or by using the use_proxy option.
version_added: "0.6"
options:
  url:
    description:
      - HTTP, HTTPS, or FTP URL in the form (http|https|ftp)://[user[:pass]]@host.domain[:port]/path
    required: true
    default: null
    aliases: []
  dest:
    description:
      - absolute path of where to download the file to.
      - If C(dest) is a directory, either the server provided filename or, if
        none provided, the base name of the URL on the remote server will be
        used. If a directory, C(force) has no effect.
        If C(dest) is a directory, the file will always be
        downloaded (regardless of the force option), but replaced only if the contents changed.
    required: true
    default: null
  force:
    description:
      - If C(yes) and C(dest) is not a directory, will download the file every
        time and replace the file if the contents change. If C(no), the file
        will only be downloaded if the destination does not exist. Generally
        should be C(yes) only for small local files. Prior to 0.6, this module
        behaved as if C(yes) was the default.
    version_added: "0.7"
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    aliases: [ "thirsty" ]
  sha256sum:
    description:
      - If a SHA-256 checksum is passed to this parameter, the digest of the
        destination file will be calculated after it is downloaded to ensure
        its integrity and verify that the transfer completed successfully.
    version_added: "1.3"
    required: false
    default: null
  use_proxy:
    description:
      - if C(no), it will not use a proxy, even if one is defined in
        an environment variable on the target hosts.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
  timeout:
    description:
      - Timeout for URL request
    required: false
    default: 10
    version_added: '1.8'
  url_username:
    description:
      - The username for use in HTTP basic authentication. This parameter can be used
        without C(url_password) for sites that allow empty passwords.
    required: false
    version_added: '1.6'
  url_password:
    description:
      - The password for use in HTTP basic authentication. If the C(url_username)
        parameter is not specified, the C(url_password) parameter will not be used.
    required: false
    version_added: '1.6'
  others:
    description:
      - all arguments accepted by the M(file) module also work here
    required: false
notes:
    - This module doesn't yet support configuration for proxies.
# informational: requirements for nodes
requirements: [ urllib2, urlparse ]
author: Jan-Piet Mens
'''

EXAMPLES='''
- name: download foo.conf
  get_url: url=http://example.com/path/file.conf dest=/etc/foo.conf mode=0440

- name: download file with sha256 check
  get_url: url=http://example.com/path/file.conf dest=/etc/foo.conf sha256sum=b5bb9d8014a0f9b1d61e21e796d78dccdf1352f23cd32812f4850b878ae4944c
'''

try:
    import hashlib
    HAS_HASHLIB=True
except ImportError:
    HAS_HASHLIB=False

# ==============================================================
# url handling

def url_filename(url):
    fn = os.path.basename(urlparse.urlsplit(url)[2])
    if fn == '':
        return 'index.html'
    return fn

def url_get(module, url, dest, use_proxy, last_mod_time, force, timeout=10):
    """
    Download data from the url and store in a temporary file.

    Return (tempfile, info about the request)
    """

    rsp, info = fetch_url(module, url, use_proxy=use_proxy, force=force, last_mod_time=last_mod_time, timeout=timeout)

    if info['status'] == 304:
        module.exit_json(url=url, dest=dest, changed=False, msg=info.get('msg', ''))

    # create a temporary file and copy content to do checksum-based replacement
    if info['status'] != 200:
        module.fail_json(msg="Request failed", status_code=info['status'], response=info['msg'], url=url, dest=dest)

    fd, tempname = tempfile.mkstemp()
    f = os.fdopen(fd, 'wb')
    try:
        shutil.copyfileobj(rsp, f)
    except Exception, err:
        os.remove(tempname)
        module.fail_json(msg="failed to create temporary content file: %s" % str(err))
    f.close()
    rsp.close()
    return tempname, info

def extract_filename_from_headers(headers):
    """
    Extracts a filename from the given dict of HTTP headers.

    Looks for the content-disposition header and applies a regex.
    Returns the filename if successful, else None."""
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

# ==============================================================
# main

def main():

    argument_spec = url_argument_spec()
    argument_spec.update(
        url = dict(required=True),
        dest = dict(required=True),
        sha256sum = dict(default=''),
        timeout = dict(required=False, type='int', default=10),
    )

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec = argument_spec,
        add_file_common_args=True
    )

    url  = module.params['url']
    dest = os.path.expanduser(module.params['dest'])
    force = module.params['force']
    sha256sum = module.params['sha256sum']
    use_proxy = module.params['use_proxy']
    timeout = module.params['timeout']

    dest_is_dir = os.path.isdir(dest)
    last_mod_time = None

    if not dest_is_dir and os.path.exists(dest):
        if not force:
            module.exit_json(msg="file already exists", dest=dest, url=url, changed=False)

        # If the file already exists, prepare the last modified time for the
        # request.
        mtime = os.path.getmtime(dest)
        last_mod_time = datetime.datetime.utcfromtimestamp(mtime)

    # download to tmpsrc
    tmpsrc, info = url_get(module, url, dest, use_proxy, last_mod_time, force, timeout)

    # Now the request has completed, we can finally generate the final
    # destination file name from the info dict.

    if dest_is_dir:
        filename = extract_filename_from_headers(info)
        if not filename:
            # Fall back to extracting the filename from the URL.
            # Pluck the URL from the info, since a redirect could have changed
            # it.
            filename = url_filename(info['url'])
        dest = os.path.join(dest, filename)

    checksum_src   = None
    checksum_dest  = None

    # raise an error if there is no tmpsrc file
    if not os.path.exists(tmpsrc):
        os.remove(tmpsrc)
        module.fail_json(msg="Request failed", status_code=info['status'], response=info['msg'])
    if not os.access(tmpsrc, os.R_OK):
        os.remove(tmpsrc)
        module.fail_json( msg="Source %s not readable" % (tmpsrc))
    checksum_src = module.sha1(tmpsrc)

    # check if there is no dest file
    if os.path.exists(dest):
        # raise an error if copy has no permission on dest
        if not os.access(dest, os.W_OK):
            os.remove(tmpsrc)
            module.fail_json( msg="Destination %s not writable" % (dest))
        if not os.access(dest, os.R_OK):
            os.remove(tmpsrc)
            module.fail_json( msg="Destination %s not readable" % (dest))
        checksum_dest = module.sha1(dest)
    else:
        if not os.access(os.path.dirname(dest), os.W_OK):
            os.remove(tmpsrc)
            module.fail_json( msg="Destination %s not writable" % (os.path.dirname(dest)))

    if checksum_src != checksum_dest:
        try:
            shutil.copyfile(tmpsrc, dest)
        except Exception, err:
            os.remove(tmpsrc)
            module.fail_json(msg="failed to copy %s to %s: %s" % (tmpsrc, dest, str(err)))
        changed = True
    else:
        changed = False

    # Check the digest of the destination file and ensure that it matches the
    # sha256sum parameter if it is present
    if sha256sum != '':
        # Remove any non-alphanumeric characters, including the infamous
        # Unicode zero-width space
        stripped_sha256sum = re.sub(r'\W+', '', sha256sum)

        if not HAS_HASHLIB:
            os.remove(dest)
            module.fail_json(msg="The sha256sum parameter requires hashlib, which is available in Python 2.5 and higher")
        else:
            destination_checksum = module.sha256(dest)

        if stripped_sha256sum.lower() != destination_checksum:
            os.remove(dest)
            module.fail_json(msg="The SHA-256 checksum for %s did not match %s; it was %s." % (dest, sha256sum, destination_checksum))

    os.remove(tmpsrc)

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

    # Mission complete

    module.exit_json(url=url, dest=dest, src=tmpsrc, md5sum=md5sum, checksum=checksum_src,
        sha256sum=sha256sum, changed=changed, msg=info.get('msg', ''))

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
