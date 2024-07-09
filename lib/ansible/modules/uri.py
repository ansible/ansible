# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Romeo Theriault <romeot () hawaii.edu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r'''
---
module: uri
short_description: Interacts with webservices
description:
  - Interacts with HTTP and HTTPS web services and supports Digest, Basic and WSSE
    HTTP authentication mechanisms.
  - For Windows targets, use the M(ansible.windows.win_uri) module instead.
version_added: "1.1"
options:
  ciphers:
    description:
      - SSL/TLS Ciphers to use for the request.
      - 'When a list is provided, all ciphers are joined in order with V(:)'
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
      - HTTP or HTTPS URL in the form (http|https)://host.domain[:port]/path.
    type: str
    required: true
  dest:
    description:
      - A path of where to download the file to (if desired). If O(dest) is a
        directory, the basename of the file on the remote server will be used.
    type: path
  url_username:
    description:
      - A username for the module to use for Digest, Basic or WSSE authentication.
    type: str
    aliases: [ user ]
  url_password:
    description:
      - A password for the module to use for Digest, Basic or WSSE authentication.
    type: str
    aliases: [ password ]
  body:
    description:
      - The body of the http request/response to the web service. If O(body_format) is set
        to V(json) it will take an already formatted JSON string or convert a data structure
        into JSON.
      - If O(body_format) is set to V(form-urlencoded) it will convert a dictionary
        or list of tuples into an C(application/x-www-form-urlencoded) string. (Added in v2.7)
      - If O(body_format) is set to V(form-multipart) it will convert a dictionary
        into C(multipart/form-multipart) body. (Added in v2.10)
    type: raw
  body_format:
    description:
      - The serialization format of the body. When set to V(json), V(form-multipart), or V(form-urlencoded), encodes
        the body argument, if needed, and automatically sets the C(Content-Type) header accordingly.
      - As of v2.3 it is possible to override the C(Content-Type) header, when
        set to V(json) or V(form-urlencoded) via the O(headers) option.
      - The C(Content-Type) header cannot be overridden when using V(form-multipart).
      - V(form-urlencoded) was added in v2.7.
      - V(form-multipart) was added in v2.10.
    type: str
    choices: [ form-urlencoded, json, raw, form-multipart ]
    default: raw
    version_added: "2.0"
  method:
    description:
      - The HTTP method of the request or response.
      - In more recent versions we do not restrict the method at the module level anymore
        but it still must be a valid method accepted by the service handling the request.
    type: str
    default: GET
  return_content:
    description:
      - Whether or not to return the body of the response as a "content" key in
        the dictionary result no matter it succeeded or failed.
      - Independently of this option, if the reported C(Content-Type) is C(application/json), then the JSON is
        always loaded into a key called RV(ignore:json) in the dictionary results.
    type: bool
    default: no
  force_basic_auth:
    description:
      - Force the sending of the Basic authentication header upon initial request.
      - When this setting is V(false), this module will first try an unauthenticated request, and when the server replies
        with an C(HTTP 401) error, it will submit the Basic authentication header.
      - When this setting is V(true), this module will immediately send a Basic authentication header on the first
        request.
      - "Use this setting in any of the following scenarios:"
      - You know the webservice endpoint always requires HTTP Basic authentication, and you want to speed up your
        requests by eliminating the first roundtrip.
      - The web service does not properly send an HTTP 401 error to your client, so Ansible's HTTP library will not
        properly respond with HTTP credentials, and logins will fail.
      - The webservice bans or rate-limits clients that cause any HTTP 401 errors.
    type: bool
    default: no
  follow_redirects:
    description:
      - Whether or not the URI module should follow redirects.
    type: str
    default: safe
    choices:
      all: Will follow all redirects.
      none: Will not follow any redirects.
      safe: Only redirects doing GET or HEAD requests will be followed.
      urllib2: Defer to urllib2 behavior (As of writing this follows HTTP redirects).
      'no': (DEPRECATED, removed in 2.22) alias of V(none).
      'yes': (DEPRECATED, removed in 2.22) alias of V(all).
  creates:
    description:
      - A filename, when it already exists, this step will not be run.
    type: path
  removes:
    description:
      - A filename, when it does not exist, this step will not be run.
    type: path
  status_code:
    description:
      - A list of valid, numeric, HTTP status codes that signifies success of the request.
    type: list
    elements: int
    default: [ 200 ]
  timeout:
    description:
      - The socket level timeout in seconds
    type: int
    default: 30
  headers:
    description:
        - Add custom HTTP headers to a request in the format of a YAML hash. As
          of Ansible 2.3 supplying C(Content-Type) here will override the header
          generated by supplying V(json) or V(form-urlencoded) for O(body_format).
    type: dict
    default: {}
    version_added: '2.1'
  validate_certs:
    description:
      - If V(false), SSL certificates will not be validated.
      - This should only set to V(false) used on personally controlled sites using self-signed certificates.
      - Prior to 1.9.2 the code defaulted to V(false).
    type: bool
    default: true
    version_added: '1.9.2'
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
  ca_path:
    description:
      - PEM formatted file that contains a CA certificate to be used for validation.
    type: path
    version_added: '2.11'
  src:
    description:
      - Path to file to be submitted to the remote server.
      - Cannot be used with O(body).
      - Should be used with O(force_basic_auth) to ensure success when the remote end sends a 401.
    type: path
    version_added: '2.7'
  remote_src:
    description:
      - If V(false), the module will search for the O(src) on the controller node.
      - If V(true), the module will search for the O(src) on the managed (remote) node.
    type: bool
    default: no
    version_added: '2.7'
  force:
    description:
      - If V(true) do not get a cached copy.
    type: bool
    default: no
  use_proxy:
    description:
      - If V(false), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: true
  unix_socket:
    description:
    - Path to Unix domain socket to use for connection.
    type: path
    version_added: '2.8'
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
        C(KRB5CCNAME) that specified a custom Kerberos credential cache.
      - NTLM authentication is B(not) supported even if the GSSAPI mech for NTLM has been installed.
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
extends_documentation_fragment:
  - action_common_attributes
  - files
attributes:
    check_mode:
        support: none
    diff_mode:
        support: none
    platform:
        platforms: posix
notes:
  - The dependency on httplib2 was removed in Ansible 2.1.
  - The module returns all the HTTP headers in lower-case.
  - For Windows targets, use the M(ansible.windows.win_uri) module instead.
seealso:
- module: ansible.builtin.get_url
- module: ansible.windows.win_uri
author:
- Romeo Theriault (@romeotheriault)
'''

EXAMPLES = r'''
- name: Check that you can connect (GET) to a page and it returns a status 200
  ansible.builtin.uri:
    url: http://www.example.com

- name: Check that a page returns successfully but fail if the word AWESOME is not in the page contents
  ansible.builtin.uri:
    url: http://www.example.com
    return_content: true
  register: this
  failed_when: this is failed or "'AWESOME' not in this.content"

- name: Create a JIRA issue
  ansible.builtin.uri:
    url: https://your.jira.example.com/rest/api/2/issue/
    user: your_username
    password: your_pass
    method: POST
    body: "{{ lookup('ansible.builtin.file','issue.json') }}"
    force_basic_auth: true
    status_code: 201
    body_format: json

- name: Login to a form based webpage, then use the returned cookie to access the app in later tasks
  ansible.builtin.uri:
    url: https://your.form.based.auth.example.com/index.php
    method: POST
    body_format: form-urlencoded
    body:
      name: your_username
      password: your_password
      enter: Sign in
    status_code: 302
  register: login

- name: Login to a form based webpage using a list of tuples
  ansible.builtin.uri:
    url: https://your.form.based.auth.example.com/index.php
    method: POST
    body_format: form-urlencoded
    body:
    - [ name, your_username ]
    - [ password, your_password ]
    - [ enter, Sign in ]
    status_code: 302
  register: login

- name: Upload a file via multipart/form-multipart
  ansible.builtin.uri:
    url: https://httpbin.org/post
    method: POST
    body_format: form-multipart
    body:
      file1:
        filename: /bin/true
        mime_type: application/octet-stream
      file2:
        content: text based file content
        filename: fake.txt
        mime_type: text/plain
      text_form_field: value

- name: Connect to website using a previously stored cookie
  ansible.builtin.uri:
    url: https://your.form.based.auth.example.com/dashboard.php
    method: GET
    return_content: true
    headers:
      Cookie: "{{ login.cookies_string }}"

- name: Queue build of a project in Jenkins
  ansible.builtin.uri:
    url: http://{{ jenkins.host }}/job/{{ jenkins.job }}/build?token={{ jenkins.token }}
    user: "{{ jenkins.user }}"
    password: "{{ jenkins.password }}"
    method: GET
    force_basic_auth: true
    status_code: 201

- name: POST from contents of local file
  ansible.builtin.uri:
    url: https://httpbin.org/post
    method: POST
    src: file.json

- name: POST from contents of remote file
  ansible.builtin.uri:
    url: https://httpbin.org/post
    method: POST
    src: /path/to/my/file.json
    remote_src: true

- name: Create workspaces in Log analytics Azure
  ansible.builtin.uri:
    url: https://www.mms.microsoft.com/Embedded/Api/ConfigDataSources/LogManagementData/Save
    method: POST
    body_format: json
    status_code: [200, 202]
    return_content: true
    headers:
      Content-Type: application/json
      x-ms-client-workspace-path: /subscriptions/{{ sub_id }}/resourcegroups/{{ res_group }}/providers/microsoft.operationalinsights/workspaces/{{ w_spaces }}
      x-ms-client-platform: ibiza
      x-ms-client-auth-token: "{{ token_az }}"
    body:

- name: Pause play until a URL is reachable from this host
  ansible.builtin.uri:
    url: "http://192.0.2.1/some/test"
    follow_redirects: none
    method: GET
  register: _result
  until: _result.status == 200
  retries: 720 # 720 * 5 seconds = 1hour (60*60/5)
  delay: 5 # Every 5 seconds

- name: Provide SSL/TLS ciphers as a list
  uri:
    url: https://example.org
    ciphers:
      - '@SECLEVEL=2'
      - ECDH+AESGCM
      - ECDH+CHACHA20
      - ECDH+AES
      - DHE+AES
      - '!aNULL'
      - '!eNULL'
      - '!aDSS'
      - '!SHA1'
      - '!AESCCM'

- name: Provide SSL/TLS ciphers as an OpenSSL formatted cipher list
  uri:
    url: https://example.org
    ciphers: '@SECLEVEL=2:ECDH+AESGCM:ECDH+CHACHA20:ECDH+AES:DHE+AES:!aNULL:!eNULL:!aDSS:!SHA1:!AESCCM'
'''

RETURN = r'''
# The return information includes all the HTTP headers in lower-case.
content:
  description: The response body content.
  returned: status not in status_code or return_content is true
  type: str
  sample: "{}"
cookies:
  description: The cookie values placed in cookie jar.
  returned: on success
  type: dict
  sample: {"SESSIONID": "[SESSIONID]"}
  version_added: "2.4"
cookies_string:
  description: The value for future request Cookie headers.
  returned: on success
  type: str
  sample: "SESSIONID=[SESSIONID]"
  version_added: "2.6"
elapsed:
  description: The number of seconds that elapsed while performing the download.
  returned: on success
  type: int
  sample: 23
msg:
  description: The HTTP message from the request.
  returned: always
  type: str
  sample: OK (unknown bytes)
path:
  description: destination file/path
  returned: dest is defined
  type: str
  sample: /path/to/file.txt
redirected:
  description: Whether the request was redirected.
  returned: on success
  type: bool
  sample: false
status:
  description: The HTTP status code from the request.
  returned: always
  type: int
  sample: 200
url:
  description: The actual URL used for the request.
  returned: always
  type: str
  sample: https://www.ansible.com/
'''

import json
import os
import re
import shutil
import tempfile

from ansible.module_utils.basic import AnsibleModule, sanitize_keys
from ansible.module_utils.six import binary_type, iteritems, string_types
from ansible.module_utils.six.moves.urllib.parse import urlencode, urlsplit
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.compat.datetime import utcnow, utcfromtimestamp
from ansible.module_utils.six.moves.collections_abc import Mapping, Sequence
from ansible.module_utils.urls import fetch_url, get_response_filename, parse_content_type, prepare_multipart, url_argument_spec

JSON_CANDIDATES = {'json', 'javascript'}

# List of response key names we do not want sanitize_keys() to change.
NO_MODIFY_KEYS = frozenset(
    ('msg', 'exception', 'warnings', 'deprecations', 'failed', 'skipped',
     'changed', 'rc', 'stdout', 'stderr', 'elapsed', 'path', 'location',
     'content_type')
)


def format_message(err, resp):
    msg = resp.pop('msg')
    return err + (' %s' % msg if msg else '')


def write_file(module, dest, content, resp):
    """
    Create temp file and write content to dest file only if content changed
    """

    tmpsrc = None

    try:
        fd, tmpsrc = tempfile.mkstemp(dir=module.tmpdir)
        with os.fdopen(fd, 'wb') as f:
            if isinstance(content, binary_type):
                f.write(content)
            else:
                shutil.copyfileobj(content, f)
    except Exception as e:
        if tmpsrc and os.path.exists(tmpsrc):
            os.remove(tmpsrc)
        msg = format_message("Failed to create temporary content file: %s" % to_native(e), resp)
        module.fail_json(msg=msg, **resp)

    checksum_src = module.sha1(tmpsrc)
    checksum_dest = module.sha1(dest)

    if checksum_src != checksum_dest:
        try:
            module.atomic_move(tmpsrc, dest)
        except Exception as e:
            if os.path.exists(tmpsrc):
                os.remove(tmpsrc)
            msg = format_message("failed to copy %s to %s: %s" % (tmpsrc, dest, to_native(e)), resp)
            module.fail_json(msg=msg, **resp)

    if os.path.exists(tmpsrc):
        os.remove(tmpsrc)


def absolute_location(url, location):
    """Attempts to create an absolute URL based on initial URL, and
    next URL, specifically in the case of a ``Location`` header.
    """

    if '://' in location:
        return location

    elif location.startswith('/'):
        parts = urlsplit(url)
        base = url.replace(parts[2], '')
        return '%s%s' % (base, location)

    elif not location.startswith('/'):
        base = os.path.dirname(url)
        return '%s/%s' % (base, location)

    else:
        return location


def kv_list(data):
    ''' Convert data into a list of key-value tuples '''
    if data is None:
        return None

    if isinstance(data, Sequence):
        return list(data)

    if isinstance(data, Mapping):
        return list(data.items())

    raise TypeError('cannot form-urlencode body, expect list or dict')


def form_urlencoded(body):
    ''' Convert data into a form-urlencoded string '''
    if isinstance(body, string_types):
        return body

    if isinstance(body, (Mapping, Sequence)):
        result = []
        # Turn a list of lists into a list of tuples that urlencode accepts
        for key, values in kv_list(body):
            if isinstance(values, string_types) or not isinstance(values, (Mapping, Sequence)):
                values = [values]
            for value in values:
                if value is not None:
                    result.append((to_text(key), to_text(value)))
        return urlencode(result, doseq=True)

    return body


def uri(module, url, dest, body, body_format, method, headers, socket_timeout, ca_path, unredirected_headers, decompress,
        ciphers, use_netrc):
    # is dest is set and is a directory, let's check if we get redirected and
    # set the filename from that url

    src = module.params['src']
    if src:
        try:
            headers.update({
                'Content-Length': os.stat(src).st_size
            })
            data = open(src, 'rb')
        except OSError:
            module.fail_json(msg='Unable to open source file %s' % src, elapsed=0)
    else:
        data = body

    kwargs = {}
    if dest is not None and os.path.isfile(dest):
        # if destination file already exist, only download if file newer
        kwargs['last_mod_time'] = utcfromtimestamp(os.path.getmtime(dest))

    if module.params.get('follow_redirects') in ('no', 'yes'):
        module.deprecate(
            "Using 'yes' or 'no' for 'follow_redirects' parameter is deprecated.",
            version='2.22'
        )

    resp, info = fetch_url(module, url, data=data, headers=headers,
                           method=method, timeout=socket_timeout, unix_socket=module.params['unix_socket'],
                           ca_path=ca_path, unredirected_headers=unredirected_headers,
                           use_proxy=module.params['use_proxy'], decompress=decompress,
                           ciphers=ciphers, use_netrc=use_netrc, force=module.params['force'], **kwargs)

    if src:
        # Try to close the open file handle
        try:
            data.close()
        except Exception:
            pass

    return resp, info


def main():
    argument_spec = url_argument_spec()
    argument_spec.update(
        dest=dict(type='path'),
        url_username=dict(type='str', aliases=['user']),
        url_password=dict(type='str', aliases=['password'], no_log=True),
        body=dict(type='raw'),
        body_format=dict(type='str', default='raw', choices=['form-urlencoded', 'json', 'raw', 'form-multipart']),
        src=dict(type='path'),
        method=dict(type='str', default='GET'),
        return_content=dict(type='bool', default=False),
        follow_redirects=dict(type='str', default='safe', choices=['all', 'no', 'none', 'safe', 'urllib2', 'yes']),
        creates=dict(type='path'),
        removes=dict(type='path'),
        status_code=dict(type='list', elements='int', default=[200]),
        timeout=dict(type='int', default=30),
        headers=dict(type='dict', default={}),
        unix_socket=dict(type='path'),
        remote_src=dict(type='bool', default=False),
        ca_path=dict(type='path', default=None),
        unredirected_headers=dict(type='list', elements='str', default=[]),
        decompress=dict(type='bool', default=True),
        ciphers=dict(type='list', elements='str'),
        use_netrc=dict(type='bool', default=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        add_file_common_args=True,
        mutually_exclusive=[['body', 'src']],
    )

    url = module.params['url']
    body = module.params['body']
    body_format = module.params['body_format'].lower()
    method = module.params['method'].upper()
    dest = module.params['dest']
    return_content = module.params['return_content']
    creates = module.params['creates']
    removes = module.params['removes']
    status_code = [int(x) for x in list(module.params['status_code'])]
    socket_timeout = module.params['timeout']
    ca_path = module.params['ca_path']
    dict_headers = module.params['headers']
    unredirected_headers = module.params['unredirected_headers']
    decompress = module.params['decompress']
    ciphers = module.params['ciphers']
    use_netrc = module.params['use_netrc']

    if not re.match('^[A-Z]+$', method):
        module.fail_json(msg="Parameter 'method' needs to be a single word in uppercase, like GET or POST.")

    if body_format == 'json':
        # Encode the body unless its a string, then assume it is pre-formatted JSON
        if not isinstance(body, string_types):
            body = json.dumps(body)
        if 'content-type' not in [header.lower() for header in dict_headers]:
            dict_headers['Content-Type'] = 'application/json'
    elif body_format == 'form-urlencoded':
        if not isinstance(body, string_types):
            try:
                body = form_urlencoded(body)
            except ValueError as e:
                module.fail_json(msg='failed to parse body as form_urlencoded: %s' % to_native(e), elapsed=0)
        if 'content-type' not in [header.lower() for header in dict_headers]:
            dict_headers['Content-Type'] = 'application/x-www-form-urlencoded'
    elif body_format == 'form-multipart':
        try:
            content_type, body = prepare_multipart(body)
        except (TypeError, ValueError) as e:
            module.fail_json(msg='failed to parse body as form-multipart: %s' % to_native(e))
        dict_headers['Content-Type'] = content_type

    if creates is not None:
        # do not run the command if the line contains creates=filename
        # and the filename already exists.  This allows idempotence
        # of uri executions.
        if os.path.exists(creates):
            module.exit_json(stdout="skipped, since '%s' exists" % creates, changed=False)

    if removes is not None:
        # do not run the command if the line contains removes=filename
        # and the filename does not exist.  This allows idempotence
        # of uri executions.
        if not os.path.exists(removes):
            module.exit_json(stdout="skipped, since '%s' does not exist" % removes, changed=False)

    # Make the request
    start = utcnow()
    r, info = uri(module, url, dest, body, body_format, method,
                  dict_headers, socket_timeout, ca_path, unredirected_headers,
                  decompress, ciphers, use_netrc)

    elapsed = (utcnow() - start).seconds

    if r and dest is not None and os.path.isdir(dest):
        filename = get_response_filename(r) or 'index.html'
        dest = os.path.join(dest, filename)

    if r and r.fp is not None:
        # r may be None for some errors
        # r.fp may be None depending on the error, which means there are no headers either
        content_type, main_type, sub_type, content_encoding = parse_content_type(r)
    else:
        content_type = 'application/octet-stream'
        main_type = 'application'
        sub_type = 'octet-stream'
        content_encoding = 'utf-8'

    if sub_type and '+' in sub_type:
        # https://www.rfc-editor.org/rfc/rfc6839#section-3.1
        sub_type_suffix = sub_type.partition('+')[2]
        maybe_json = content_type and sub_type_suffix.lower() in JSON_CANDIDATES
    elif sub_type:
        maybe_json = content_type and sub_type.lower() in JSON_CANDIDATES
    else:
        maybe_json = False

    maybe_output = maybe_json or return_content or info['status'] not in status_code

    if maybe_output:
        try:
            if r.fp is None or r.closed:
                raise TypeError
            content = r.read()
        except (AttributeError, TypeError):
            # there was no content, but the error read()
            # may have been stored in the info as 'body'
            content = info.pop('body', b'')
    elif r:
        content = r
    else:
        content = None

    resp = {}
    resp['redirected'] = info['url'] != url
    resp.update(info)

    resp['elapsed'] = elapsed
    resp['status'] = int(resp['status'])
    resp['changed'] = False

    # Write the file out if requested
    if r and dest is not None:
        if resp['status'] in status_code and resp['status'] != 304:
            write_file(module, dest, content, resp)
            # allow file attribute changes
            resp['changed'] = True
            module.params['path'] = dest
            file_args = module.load_file_common_arguments(module.params, path=dest)
            resp['changed'] = module.set_fs_attributes_if_different(file_args, resp['changed'])
        resp['path'] = dest

    # Transmogrify the headers, replacing '-' with '_', since variables don't
    # work with dashes.
    # In python3, the headers are title cased.  Lowercase them to be
    # compatible with the python2 behaviour.
    uresp = {}
    for key, value in iteritems(resp):
        ukey = key.replace("-", "_").lower()
        uresp[ukey] = value

    if 'location' in uresp:
        uresp['location'] = absolute_location(url, uresp['location'])

    # Default content_encoding to try
    if isinstance(content, binary_type):
        u_content = to_text(content, encoding=content_encoding)
        if maybe_json:
            try:
                js = json.loads(u_content)
                uresp['json'] = js
            except Exception:
                ...
    else:
        u_content = None

    if module.no_log_values:
        uresp = sanitize_keys(uresp, module.no_log_values, NO_MODIFY_KEYS)

    if resp['status'] not in status_code:
        uresp['msg'] = 'Status code was %s and not %s: %s' % (resp['status'], status_code, uresp.get('msg', ''))
        if return_content:
            module.fail_json(content=u_content, **uresp)
        else:
            module.fail_json(**uresp)
    elif return_content:
        module.exit_json(content=u_content, **uresp)
    else:
        module.exit_json(**uresp)


if __name__ == '__main__':
    main()
