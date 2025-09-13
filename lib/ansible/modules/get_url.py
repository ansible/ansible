# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: get_url
short_description: Downloads files from HTTP, HTTPS, or FTP to node
description:
     - Downloads files from HTTP, HTTPS, or FTP to the remote server. The remote
       server I(must) have direct access to the remote resource.
     - By default, if an environment variable E(<protocol>_proxy) is set on
       the target host, requests will be sent through that proxy. This
       behaviour can be overridden by setting a variable for this task
       (see R(setting the environment,playbooks_environment)),
       or by using the use_proxy option.
     - HTTP redirects can redirect from HTTP to HTTPS so you should be sure that
       your proxy environment for both protocols is correct.
     - From Ansible 2.4 when run with C(--check), it will do a HEAD request to validate the URL but
       will not download the entire file or verify it against hashes and will report incorrect changed status.
     - For Windows targets, use the M(ansible.windows.win_get_url) module instead.
version_added: '0.6'
options:
  ciphers:
    description:
      - SSL/TLS Ciphers to use for the request.
      - 'When a list is provided, all ciphers are joined in order with C(:).'
      - See the L(OpenSSL Cipher List Format,https://www.openssl.org/docs/manmaster/man1/openssl-ciphers.html#CIPHER-LIST-FORMAT)
        for more details.
      - The available ciphers is dependent on the Python and OpenSSL/LibreSSL versions.
    type: list
    elements: str
    version_added: '2.14'
  decompress:
    description:
      - Whether to attempt to decompress gzip content-encoded responses.
    type: bool
    default: true
    version_added: '2.14'
  url:
    description:
      - HTTP, HTTPS, or FTP URL in the form C((http|https|ftp)://[user[:pass]]@host.domain[:port]/path).
    type: str
    required: true
  dest:
    description:
      - Absolute path of where to download the file to.
      - If O(dest) is a directory, either the server provided filename or, if
        none provided, the base name of the URL on the remote server will be
        used. If a directory, O(force) has no effect.
      - If O(dest) is a directory, the file will always be downloaded
        (regardless of the O(force) and O(checksum) option), but
        replaced only if the contents changed.
    type: path
    required: true
  tmp_dest:
    description:
      - Absolute path of where temporary file is downloaded to.
      - When run on Ansible 2.5 or greater, path defaults to ansible's C(remote_tmp) setting.
      - When run on Ansible prior to 2.5, it defaults to E(TMPDIR), E(TEMP) or E(TMP) env variables or a platform specific value.
      - U(https://docs.python.org/3/library/tempfile.html#tempfile.tempdir).
    type: path
    version_added: '2.1'
  force:
    description:
      - If V(true) and O(dest) is not a directory, will download the file every
        time and replace the file if the contents change. If V(false), the file
        will only be downloaded if the destination does not exist. Generally
        should be V(true) only for small local files.
      - Prior to 0.6, this module behaved as if V(true) was the default.
    type: bool
    default: no
    version_added: '0.7'
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
    version_added: '2.1'
  checksum:
    description:
      - 'If a checksum is passed to this parameter, the digest of the
        destination file will be calculated after it is downloaded to ensure
        its integrity and verify that the transfer completed successfully.
        Format: <algorithm>:<checksum|url>, for example C(checksum="sha256:D98291AC[...]B6DC7B97"),
        C(checksum="sha256:http://example.com/path/sha256sum.txt").'
      - If you worry about portability, only the sha1 algorithm is available
        on all platforms and python versions.
      - The Python C(hashlib) module is responsible for providing the available algorithms.
        The choices vary based on Python version and OpenSSL version.
      - On systems running in FIPS compliant mode, the C(md5) algorithm may be unavailable.
      - Additionally, if a checksum is passed to this parameter, and the file exist under
        the O(dest) location, the C(destination_checksum) would be calculated, and if
        checksum equals C(destination_checksum), the file download would be skipped
        (unless O(force=true)). If the checksum does not equal C(destination_checksum),
        the destination file is deleted.
      - If the checksum URL requires username and password, O(url_username) and O(url_password) are used
        to download the checksum file.
    type: str
    default: ''
    version_added: "2.0"
  use_proxy:
    description:
      - if V(false), it will not use a proxy, even if one is defined in
        an environment variable on the target hosts.
    type: bool
    default: yes
  validate_certs:
    description:
      - If V(false), SSL certificates will not be validated.
      - This should only be used on personally controlled sites using self-signed certificates.
    type: bool
    default: yes
  timeout:
    description:
      - Timeout in seconds for URL request.
    type: int
    default: 10
    version_added: '1.8'
  headers:
    description:
        - Add custom HTTP headers to a request in hash/dict format.
        - The hash/dict format was added in Ansible 2.6.
        - Previous versions used a C("key:value,key:value") string format.
        - The C("key:value,key:value") string format is deprecated and has been removed in version 2.10.
    type: dict
    version_added: '2.0'
  url_username:
    description:
      - The username for use in HTTP basic authentication.
      - This parameter can be used without O(url_password) for sites that allow empty passwords.
      - Since version 2.8 you can also use the O(username) alias for this option.
    type: str
    aliases: ['username']
    version_added: '1.6'
  url_password:
    description:
        - The password for use in HTTP basic authentication.
        - If the O(url_username) parameter is not specified, the O(url_password) parameter will not be used.
        - Since version 2.8 you can also use the O(password) alias for this option.
    type: str
    aliases: ['password']
    version_added: '1.6'
  force_basic_auth:
    description:
      - Force the sending of the Basic authentication header upon initial request.
      - httplib2, the library used by the uri module only sends authentication information when a webservice
        responds to an initial request with a 401 status. Since some basic auth services do not properly
        send a 401, logins will fail.
    type: bool
    default: no
    version_added: '2.0'
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client authentication.
      - This file can also include the key as well, and if the key is included, O(client_key) is not required.
    type: path
    version_added: '2.4'
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL client authentication.
      - If O(client_cert) contains both the certificate and key, this option is not required.
    type: path
    version_added: '2.4'
  http_agent:
    description:
      - Header to identify as, generally appears in web server logs.
    type: str
    default: ansible-httpget
  unredirected_headers:
    description:
      - A list of header names that will not be sent on subsequent redirected requests. This list is case
        insensitive. By default all headers will be redirected. In some cases it may be beneficial to list
        headers such as C(Authorization) here to avoid potential credential exposure.
    default: []
    type: list
    elements: str
    version_added: '2.12'
  use_gssapi:
    description:
      - Use GSSAPI to perform the authentication, typically this is for Kerberos or Kerberos through Negotiate
        authentication.
      - Requires the Python library L(gssapi,https://github.com/pythongssapi/python-gssapi) to be installed.
      - Credentials for GSSAPI can be specified with O(url_username)/O(url_password) or with the GSSAPI env var
        E(KRB5CCNAME) that specified a custom Kerberos credential cache.
      - NTLM authentication is I(not) supported even if the GSSAPI mech for NTLM has been installed.
    type: bool
    default: no
    version_added: '2.11'
  use_netrc:
    description:
      - Determining whether to use credentials from C(~/.netrc) file.
      - By default C(.netrc) is used with Basic authentication headers.
      - When V(false), C(.netrc) credentials are ignored.
    type: bool
    default: true
    version_added: '2.14'
# informational: requirements for nodes
extends_documentation_fragment:
    - files
    - action_common_attributes
attributes:
    check_mode:
        details: the changed status will reflect comparison to an empty source file
        support: partial
    diff_mode:
        support: none
    platform:
        platforms: posix
notes:
     - For Windows targets, use the M(ansible.windows.win_get_url) module instead.
seealso:
- module: ansible.builtin.uri
- module: ansible.windows.win_get_url
author:
- Jan-Piet Mens (@jpmens)
"""

EXAMPLES = r"""
- name: Download foo.conf
  ansible.builtin.get_url:
    url: http://example.com/path/file.conf
    dest: /etc/foo.conf
    mode: '0440'

- name: Download file and force basic auth
  ansible.builtin.get_url:
    url: http://example.com/path/file.conf
    dest: /etc/foo.conf
    force_basic_auth: yes

- name: Download file with custom HTTP headers
  ansible.builtin.get_url:
    url: http://example.com/path/file.conf
    dest: /etc/foo.conf
    headers:
      key1: one
      key2: two

- name: Download file with check (sha256)
  ansible.builtin.get_url:
    url: http://example.com/path/file.conf
    dest: /etc/foo.conf
    checksum: sha256:b5bb9d8014a0f9b1d61e21e796d78dccdf1352f23cd32812f4850b878ae4944c

- name: Download file with check (md5)
  ansible.builtin.get_url:
    url: http://example.com/path/file.conf
    dest: /etc/foo.conf
    checksum: md5:66dffb5228a211e61d6d7ef4a86f5758

- name: Download file with checksum url (sha256)
  ansible.builtin.get_url:
    url: http://example.com/path/file.conf
    dest: /etc/foo.conf
    checksum: sha256:http://example.com/path/sha256sum.txt

- name: Download file from a file path
  ansible.builtin.get_url:
    url: file:///tmp/a_file.txt
    dest: /tmp/afilecopy.txt

- name: < Fetch file that requires authentication.
        username/password only available since 2.8, in older versions you need to use url_username/url_password
  ansible.builtin.get_url:
    url: http://example.com/path/file.conf
    dest: /etc/foo.conf
    username: bar
    password: '{{ mysecret }}'
"""

RETURN = r"""
backup_file:
    description: name of backup file created after download
    returned: changed and if backup=yes
    type: str
    sample: /path/to/file.txt.2015-02-12@22:09~
checksum_dest:
    description: sha1 checksum of the file after copy
    returned: success
    type: str
    sample: 6e642bb8dd5c2e027bf21dd923337cbb4214f827
checksum_src:
    description: sha1 checksum of the file
    returned: success
    type: str
    sample: 6e642bb8dd5c2e027bf21dd923337cbb4214f827
dest:
    description: destination file/path
    returned: success
    type: str
    sample: /path/to/file.txt
elapsed:
    description: The number of seconds that elapsed while performing the download
    returned: always
    type: int
    sample: 23
gid:
    description: group id of the file
    returned: success
    type: int
    sample: 100
group:
    description: group of the file
    returned: success
    type: str
    sample: "httpd"
md5sum:
    description: md5 checksum of the file after download
    returned: when supported
    type: str
    sample: "2a5aeecc61dc98c4d780b14b330e3282"
mode:
    description: permissions of the target
    returned: success
    type: str
    sample: "0644"
msg:
    description: the HTTP message from the request
    returned: always
    type: str
    sample: OK (unknown bytes)
owner:
    description: owner of the file
    returned: success
    type: str
    sample: httpd
secontext:
    description: the SELinux security context of the file
    returned: success
    type: str
    sample: unconfined_u:object_r:user_tmp_t:s0
size:
    description: size of the target
    returned: success
    type: int
    sample: 1220
src:
    description: source file used after download
    returned: always
    type: str
    sample: /tmp/tmpAdFLdV
state:
    description: state of the target
    returned: success
    type: str
    sample: file
status_code:
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
    type: str
    sample: https://www.ansible.com/
"""

import email.message
import os
import re
import shutil
import tempfile

from datetime import datetime, timezone
from urllib.parse import urlsplit

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.urls import fetch_url, url_argument_spec

# ==============================================================
# url handling


def url_filename(url):
    fn = os.path.basename(urlsplit(url)[2])
    if fn == '':
        return 'index.html'
    return fn


def url_get(module, url, dest, use_proxy, last_mod_time, force, timeout=10, headers=None, tmp_dest='', method='GET', unredirected_headers=None,
            decompress=True, ciphers=None, use_netrc=True):
    """
    Download data from the url and store in a temporary file.

    Return (tempfile, info about the request)
    """

    start = datetime.now(timezone.utc)
    rsp, info = fetch_url(module, url, use_proxy=use_proxy, force=force, last_mod_time=last_mod_time, timeout=timeout, headers=headers, method=method,
                          unredirected_headers=unredirected_headers, decompress=decompress, ciphers=ciphers, use_netrc=use_netrc)
    elapsed = (datetime.now(timezone.utc) - start).seconds

    if info['status'] == 304:
        module.exit_json(url=url, dest=dest, changed=False, msg=info.get('msg', ''), status_code=info['status'], elapsed=elapsed)

    # Exceptions in fetch_url may result in a status -1, the ensures a proper error to the user in all cases
    if info['status'] == -1:
        module.fail_json(msg=info['msg'], url=url, dest=dest, elapsed=elapsed)

    if info['status'] != 200 and not url.startswith('file:/') and not (url.startswith('ftp:/') and info.get('msg', '').startswith('OK')):
        module.fail_json(msg="Request failed", status_code=info['status'], response=info['msg'], url=url, dest=dest, elapsed=elapsed)

    # create a temporary file and copy content to do checksum-based replacement
    if tmp_dest:
        # tmp_dest should be an existing dir
        tmp_dest_is_dir = os.path.isdir(tmp_dest)
        if not tmp_dest_is_dir:
            if os.path.exists(tmp_dest):
                module.fail_json(msg="%s is a file but should be a directory." % tmp_dest, elapsed=elapsed)
            else:
                module.fail_json(msg="%s directory does not exist." % tmp_dest, elapsed=elapsed)
    else:
        tmp_dest = module.tmpdir

    fd, tempname = tempfile.mkstemp(dir=tmp_dest)

    f = os.fdopen(fd, 'wb')
    try:
        shutil.copyfileobj(rsp, f)
    except Exception as e:
        os.remove(tempname)
        module.fail_json(msg="failed to create temporary content file: %s" % to_native(e), elapsed=elapsed)
    f.close()
    rsp.close()

    # Since shutil.copyfileobj() will read from HTTPResponse in chunks, HTTPResponse.read() will not recognize
    # if the entire content-length of data was not read. We need to do that validation here, unless a 'chunked'
    # transfer-encoding was used, in which case we will not know content-length because it will not be returned.
    # But in that case, HTTPResponse will behave correctly and recognize an IncompleteRead.

    is_gzip = info.get('content-encoding') == 'gzip'

    if not module.check_mode and 'content-length' in info:
        # If data is decompressed, then content-length won't match the amount of data we've read, so skip.
        if not is_gzip or (is_gzip and not decompress):
            st = os.stat(tempname)
            cl = int(info['content-length'])
            if st.st_size != cl:
                diff = cl - st.st_size
                module.fail_json(msg=f'Incomplete read, ({rsp.length=}, {cl=}, {st.st_size=}) failed to read remaining {diff} bytes')

    return tempname, info


def extract_filename_from_headers(headers):
    """Extracts a filename from the given dict of HTTP headers.

    Returns the filename if successful, else None.
    """
    msg = email.message.Message()
    msg['content-disposition'] = headers.get('content-disposition', '')
    if filename := msg.get_param('filename', header='content-disposition'):
        # Avoid directory traversal
        filename = os.path.basename(filename)
    return filename


def is_url(checksum):
    """
    Returns True if checksum value has supported URL scheme, else False."""
    supported_schemes = ('http', 'https', 'ftp', 'file')

    return urlsplit(checksum).scheme in supported_schemes


def parse_digest_lines(filename, lines):
    """Returns a list of tuple containing the filename and digest depending upon
      the lines provided

    Args:
        filename (str): Name of the filename, used only when the digest is one-liner
        lines (list): A list of lines containing filenames and checksums
    """
    checksum_map = []
    BSD_DIGEST_LINE = re.compile(r'^(\w+) ?\((?P<path>.+)\) ?= (?P<digest>[\w.]+)$')
    GNU_DIGEST_LINE = re.compile(r'^(?P<digest>[\w.]+) ([ *])(?P<path>.+)$')

    if len(lines) == 1 and len(lines[0].split()) == 1:
        # Only a single line with a single string
        # treat it as a checksum only file
        checksum_map.append((lines[0], filename))
        return checksum_map
    # The assumption here is the file is in the format of
    # checksum filename
    for line in lines:
        match = BSD_DIGEST_LINE.match(line)
        if match:
            checksum_map.append((match.group('digest'), match.group('path')))
        else:
            match = GNU_DIGEST_LINE.match(line)
            if match:
                checksum_map.append((match.group('digest'), match.group('path').lstrip("./")))

    return checksum_map


# ==============================================================
# main

def main():
    argument_spec = url_argument_spec()

    # setup aliases
    argument_spec['url_username']['aliases'] = ['username']
    argument_spec['url_password']['aliases'] = ['password']

    argument_spec.update(
        url=dict(type='str', required=True),
        dest=dict(type='path', required=True),
        backup=dict(type='bool', default=False),
        checksum=dict(type='str', default=''),
        timeout=dict(type='int', default=10),
        headers=dict(type='dict'),
        tmp_dest=dict(type='path'),
        unredirected_headers=dict(type='list', elements='str', default=[]),
        decompress=dict(type='bool', default=True),
        ciphers=dict(type='list', elements='str'),
        use_netrc=dict(type='bool', default=True),
    )

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=argument_spec,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    url = module.params['url']
    dest = module.params['dest']
    backup = module.params['backup']
    force = module.params['force']
    checksum = module.params['checksum']
    use_proxy = module.params['use_proxy']
    timeout = module.params['timeout']
    headers = module.params['headers']
    tmp_dest = module.params['tmp_dest']
    unredirected_headers = module.params['unredirected_headers']
    decompress = module.params['decompress']
    ciphers = module.params['ciphers']
    use_netrc = module.params['use_netrc']

    result = dict(
        changed=False,
        checksum_dest=None,
        checksum_src=None,
        dest=dest,
        elapsed=0,
        url=url,
    )

    dest_is_dir = os.path.isdir(dest)
    last_mod_time = None

    # checksum specified, parse for algorithm and checksum
    if checksum:
        try:
            algorithm, checksum = checksum.split(':', 1)
        except ValueError:
            module.fail_json(msg="The checksum parameter has to be in format <algorithm>:<checksum>", **result)

        if is_url(checksum):
            checksum_url = checksum
            # download checksum file to checksum_tmpsrc
            checksum_tmpsrc, _dummy = url_get(module, checksum_url, dest, use_proxy, last_mod_time, force, timeout, headers, tmp_dest,
                                              unredirected_headers=unredirected_headers, ciphers=ciphers, use_netrc=use_netrc)
            with open(checksum_tmpsrc) as f:
                lines = [line.rstrip('\n') for line in f]
            os.remove(checksum_tmpsrc)
            filename = url_filename(url)
            checksum_map = parse_digest_lines(filename=filename, lines=lines)
            # Look through each line in the checksum file for a hash corresponding to
            # the filename in the url, returning the first hash that is found.
            for cksum in (s for (s, f) in checksum_map if f == filename):
                checksum = cksum
                break
            else:
                checksum = None

            if checksum is None:
                module.fail_json(msg="Unable to find a checksum for file '%s' in '%s'" % (filename, checksum_url))
        # Remove any non-alphanumeric characters, including the infamous
        # Unicode zero-width space
        checksum = re.sub(r'\W+', '', checksum).lower()
        # Ensure the checksum portion is a hexdigest
        try:
            int(checksum, 16)
        except ValueError:
            module.fail_json(msg='The checksum format is invalid', **result)

    if not dest_is_dir and os.path.exists(dest):
        checksum_mismatch = False

        # If the download is not forced and there is a checksum, allow
        # checksum match to skip the download.
        if not force and checksum != '':
            destination_checksum = module.digest_from_file(dest, algorithm)

            if checksum != destination_checksum:
                checksum_mismatch = True

        # Not forcing redownload, unless checksum does not match
        if not force and checksum and not checksum_mismatch:
            # Not forcing redownload, unless checksum does not match
            # allow file attribute changes
            file_args = module.load_file_common_arguments(module.params, path=dest)
            result['changed'] = module.set_fs_attributes_if_different(file_args, False)
            if result['changed']:
                module.exit_json(msg="file already exists but file attributes changed", **result)
            module.exit_json(msg="file already exists", **result)

        # If the file already exists, prepare the last modified time for the
        # request.
        mtime = os.path.getmtime(dest)
        last_mod_time = datetime.fromtimestamp(mtime, timezone.utc)

        # If the checksum does not match we have to force the download
        # because last_mod_time may be newer than on remote
        if checksum_mismatch:
            force = True

    # download to tmpsrc
    start = datetime.now(timezone.utc)
    method = 'HEAD' if module.check_mode else 'GET'
    tmpsrc, info = url_get(module, url, dest, use_proxy, last_mod_time, force, timeout, headers, tmp_dest, method,
                           unredirected_headers=unredirected_headers, decompress=decompress, ciphers=ciphers, use_netrc=use_netrc)
    result['elapsed'] = (datetime.now(timezone.utc) - start).seconds
    result['src'] = tmpsrc

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
        result['dest'] = dest

    # raise an error if there is no tmpsrc file
    if not os.path.exists(tmpsrc):
        os.remove(tmpsrc)
        module.fail_json(msg="Request failed", status_code=info['status'], response=info['msg'], **result)
    if not os.access(tmpsrc, os.R_OK):
        os.remove(tmpsrc)
        module.fail_json(msg="Source %s is not readable" % (tmpsrc), **result)
    result['checksum_src'] = module.sha1(tmpsrc)

    # check if there is no dest file
    if os.path.exists(dest):
        # raise an error if copy has no permission on dest
        if not os.access(dest, os.W_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not writable" % (dest), **result)
        if not os.access(dest, os.R_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not readable" % (dest), **result)
        result['checksum_dest'] = module.sha1(dest)
    else:
        if not os.path.exists(os.path.dirname(dest)):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s does not exist" % (os.path.dirname(dest)), **result)
        if not os.access(os.path.dirname(dest), os.W_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s is not writable" % (os.path.dirname(dest)), **result)

    if module.check_mode:
        if os.path.exists(tmpsrc):
            os.remove(tmpsrc)
        result['changed'] = ('checksum_dest' not in result or
                             result['checksum_src'] != result['checksum_dest'])
        module.exit_json(msg=info.get('msg', ''), **result)

    # If a checksum was provided, ensure that the temporary file matches this checksum
    # before moving it to the destination.
    if checksum != '':
        tmpsrc_checksum = module.digest_from_file(tmpsrc, algorithm)

        if checksum != tmpsrc_checksum:
            os.remove(tmpsrc)
            module.fail_json(msg=f"The checksum for {tmpsrc} did not match {checksum}; it was {tmpsrc_checksum}.", **result)

    # Copy temporary file to destination if necessary
    backup_file = None
    if result['checksum_src'] != result['checksum_dest']:
        try:
            if backup:
                if os.path.exists(dest):
                    backup_file = module.backup_local(dest)
            module.atomic_move(tmpsrc, dest, unsafe_writes=module.params['unsafe_writes'])
        except Exception as e:
            if os.path.exists(tmpsrc):
                os.remove(tmpsrc)
            module.fail_json(msg="failed to copy %s to %s: %s" % (tmpsrc, dest, to_native(e)), **result)
        result['changed'] = True
    else:
        result['changed'] = False
        if os.path.exists(tmpsrc):
            os.remove(tmpsrc)

    # allow file attribute changes
    file_args = module.load_file_common_arguments(module.params, path=dest)
    result['changed'] = module.set_fs_attributes_if_different(file_args, result['changed'])

    # Backwards compat only.  We'll return None on FIPS enabled systems
    try:
        result['md5sum'] = module.md5(dest)
    except ValueError:
        result['md5sum'] = None

    if backup_file:
        result['backup_file'] = backup_file

    # Mission complete
    module.exit_json(msg=info.get('msg', ''), status_code=info.get('status', ''), **result)


if __name__ == '__main__':
    main()
