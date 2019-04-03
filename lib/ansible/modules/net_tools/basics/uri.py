#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Romeo Theriault <romeot () hawaii.edu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: uri
short_description: Interacts with webservices
description:
  - Interacts with HTTP and HTTPS web services and supports Digest, Basic and WSSE
    HTTP authentication mechanisms.
  - For Windows targets, use the M(win_uri) module instead.
version_added: "1.1"
options:
  url:
    description:
      - HTTP or HTTPS URL in the form (http|https)://host.domain[:port]/path
    type: str
    required: true
  dest:
    description:
      - A path of where to download the file to (if desired). If I(dest) is a
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
      - The body of the http request/response to the web service. If C(body_format) is set
        to 'json' it will take an already formatted JSON string or convert a data structure
        into JSON. If C(body_format) is set to 'form-urlencoded' it will convert a dictionary
        or list of tuples into an 'application/x-www-form-urlencoded' string. (Added in v2.7)
    type: raw
  body_format:
    description:
      - The serialization format of the body. When set to C(json) or C(form-urlencoded), encodes the
        body argument, if needed, and automatically sets the Content-Type header accordingly.
        As of C(2.3) it is possible to override the `Content-Type` header, when
        set to C(json) or C(form-urlencoded) via the I(headers) option.
    type: str
    choices: [ form-urlencoded, json, raw ]
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
        the dictionary result.
      - Independently of this option, if the reported Content-type is "application/json", then the JSON is
        always loaded into a key called C(json) in the dictionary results.
    type: bool
    default: no
  force_basic_auth:
    description:
      - Force the sending of the Basic authentication header upon initial request.
      - The library used by the uri module only sends authentication information when a webservice
        responds to an initial request with a 401 status. Since some basic auth services do not properly
        send a 401, logins will fail.
    type: bool
    default: no
  follow_redirects:
    description:
      - Whether or not the URI module should follow redirects. C(all) will follow all redirects.
        C(safe) will follow only "safe" redirects, where "safe" means that the client is only
        doing a GET or HEAD on the URI to which it is being redirected. C(none) will not follow
        any redirects. Note that C(yes) and C(no) choices are accepted for backwards compatibility,
        where C(yes) is the equivalent of C(all) and C(no) is the equivalent of C(safe). C(yes) and C(no)
        are deprecated and will be removed in some future version of Ansible.
    type: str
    choices: [ all, 'none', safe ]
    default: safe
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
    default: [ 200 ]
  timeout:
    description:
      - The socket level timeout in seconds
    type: int
    default: 30
  HEADER_:
    description:
      - Any parameter starting with "HEADER_" is a sent with your request as a header.
        For example, HEADER_Content-Type="application/json" would send the header
        "Content-Type" along with your request with a value of "application/json".
      - This option is deprecated as of C(2.1) and will be removed in Ansible 2.9.
        Use I(headers) instead.
    type: dict
  headers:
    description:
        - Add custom HTTP headers to a request in the format of a YAML hash. As
          of C(2.3) supplying C(Content-Type) here will override the header
          generated by supplying C(json) or C(form-urlencoded) for I(body_format).
    type: dict
    version_added: '2.1'
  others:
    description:
      - All arguments accepted by the M(file) module also work here
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated.
      - This should only set to C(no) used on personally controlled sites using self-signed certificates.
      - Prior to 1.9.2 the code defaulted to C(no).
    type: bool
    default: yes
    version_added: '1.9.2'
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client authentication.
      - This file can also include the key as well, and if the key is included, I(client_key) is not required
    type: path
    version_added: '2.4'
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL client authentication.
      - If I(client_cert) contains both the certificate and key, this option is not required.
    type: path
    version_added: '2.4'
  src:
    description:
      - Path to file to be submitted to the remote server.
      - Cannot be used with I(body).
    type: path
    version_added: '2.7'
  remote_src:
    description:
      - If C(no), the module will search for src on originating/master machine.
      - If C(yes) the module will use the C(src) path on the remote/target machine.
    type: bool
    default: no
    version_added: '2.7'
  force:
    description:
      - If C(yes) do not get a cached copy.
    type: bool
    default: no
    aliases: [ thirsty ]
  use_proxy:
    description:
      - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: yes
  unix_socket:
    description:
    - Path to Unix domain socket to use for connection
    version_added: '2.8'
  http_agent:
    description:
      - Header to identify as, generally appears in web server logs.
    type: str
    default: ansible-httpget
notes:
  - The dependency on httplib2 was removed in Ansible 2.1.
  - The module returns all the HTTP headers in lower-case.
  - For Windows targets, use the M(win_uri) module instead.
seealso:
- module: get_url
- module: win_uri
author:
- Romeo Theriault (@romeotheriault)
'''

EXAMPLES = r'''
- name: Check that you can connect (GET) to a page and it returns a status 200
  uri:
    url: http://www.example.com

- name: Check that a page returns a status 200 and fail if the word AWESOME is not in the page contents
  uri:
    url: http://www.example.com
    return_content: yes
  register: this
  failed_when: "'AWESOME' not in this.content"

- name: Create a JIRA issue
  uri:
    url: https://your.jira.example.com/rest/api/2/issue/
    user: your_username
    password: your_pass
    method: POST
    body: "{{ lookup('file','issue.json') }}"
    force_basic_auth: yes
    status_code: 201
    body_format: json

- name: Login to a form based webpage, then use the returned cookie to access the app in later tasks
  uri:
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
  uri:
    url: https://your.form.based.auth.example.com/index.php
    method: POST
    body_format: form-urlencoded
    body:
    - [ name, your_username ]
    - [ password, your_password ]
    - [ enter, Sign in ]
    status_code: 302
  register: login

- name: Connect to website using a previously stored cookie
  uri:
    url: https://your.form.based.auth.example.com/dashboard.php
    method: GET
    return_content: yes
    headers:
      Cookie: "{{ login.set_cookie }}"

- name: Queue build of a project in Jenkins
  uri:
    url: http://{{ jenkins.host }}/job/{{ jenkins.job }}/build?token={{ jenkins.token }}
    user: "{{ jenkins.user }}"
    password: "{{ jenkins.password }}"
    method: GET
    force_basic_auth: yes
    status_code: 201

- name: POST from contents of local file
  uri:
    url: https://httpbin.org/post
    method: POST
    src: file.json

- name: POST from contents of remote file
  uri:
    url: https://httpbin.org/post
    method: POST
    src: /path/to/my/file.json
    remote_src: yes
'''

RETURN = r'''
# The return information includes all the HTTP headers in lower-case.
elapsed:
  description: The number of seconds that elapsed while performing the download
  returned: always
  type: int
  sample: 23
msg:
  description: The HTTP message from the request
  returned: always
  type: str
  sample: OK (unknown bytes)
redirected:
  description: Whether the request was redirected
  returned: always
  type: bool
  sample: false
status:
  description: The HTTP status code from the request
  returned: always
  type: int
  sample: 200
url:
  description: The actual URL used for the request
  returned: always
  type: str
  sample: https://www.ansible.com/
'''

import cgi
import datetime
import json
import os
import re
import shutil
import sys
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import PY2, iteritems, string_types
from ansible.module_utils.six.moves.urllib.parse import urlencode, urlsplit
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.common._collections_compat import Mapping, Sequence
from ansible.module_utils.urls import fetch_url, url_argument_spec

JSON_CANDIDATES = ('text', 'json', 'javascript')


def format_message(err, resp):
    msg = resp.pop('msg')
    return err + (' %s' % msg if msg else '')


def write_file(module, url, dest, content, resp):
    # create a tempfile with some test content
    fd, tmpsrc = tempfile.mkstemp(dir=module.tmpdir)
    f = open(tmpsrc, 'wb')
    try:
        f.write(content)
    except Exception as e:
        os.remove(tmpsrc)
        msg = format_message("Failed to create temporary content file: %s" % to_native(e), resp)
        module.fail_json(msg=msg, **resp)
    f.close()

    checksum_src = None
    checksum_dest = None

    # raise an error if there is no tmpsrc file
    if not os.path.exists(tmpsrc):
        os.remove(tmpsrc)
        msg = format_message("Source '%s' does not exist" % tmpsrc, resp)
        module.fail_json(msg=msg, **resp)
    if not os.access(tmpsrc, os.R_OK):
        os.remove(tmpsrc)
        msg = format_message("Source '%s' not readable" % tmpsrc, resp)
        module.fail_json(msg=msg, **resp)
    checksum_src = module.sha1(tmpsrc)

    # check if there is no dest file
    if os.path.exists(dest):
        # raise an error if copy has no permission on dest
        if not os.access(dest, os.W_OK):
            os.remove(tmpsrc)
            msg = format_message("Destination '%s' not writable" % dest, resp)
            module.fail_json(msg=msg, **resp)
        if not os.access(dest, os.R_OK):
            os.remove(tmpsrc)
            msg = format_message("Destination '%s' not readable" % dest, resp)
            module.fail_json(msg=msg, **resp)
        checksum_dest = module.sha1(dest)
    else:
        if not os.access(os.path.dirname(dest), os.W_OK):
            os.remove(tmpsrc)
            msg = format_message("Destination dir '%s' not writable" % os.path.dirname(dest), resp)
            module.fail_json(msg=msg, **resp)

    if checksum_src != checksum_dest:
        try:
            shutil.copyfile(tmpsrc, dest)
        except Exception as e:
            os.remove(tmpsrc)
            msg = format_message("failed to copy %s to %s: %s" % (tmpsrc, dest, to_native(e)), resp)
            module.fail_json(msg=msg, **resp)

    os.remove(tmpsrc)


def url_filename(url):
    fn = os.path.basename(urlsplit(url)[2])
    if fn == '':
        return 'index.html'
    return fn


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
        # Turn a list of lists into a list of tupples that urlencode accepts
        for key, values in kv_list(body):
            if isinstance(values, string_types) or not isinstance(values, (Mapping, Sequence)):
                values = [values]
            for value in values:
                if value is not None:
                    result.append((to_text(key), to_text(value)))
        return urlencode(result, doseq=True)

    return body


def uri(module, url, dest, body, body_format, method, headers, socket_timeout):
    # is dest is set and is a directory, let's check if we get redirected and
    # set the filename from that url
    redirected = False
    redir_info = {}
    r = {}

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
    if dest is not None:
        # Stash follow_redirects, in this block we don't want to follow
        # we'll reset back to the supplied value soon
        follow_redirects = module.params['follow_redirects']
        module.params['follow_redirects'] = False
        if os.path.isdir(dest):
            # first check if we are redirected to a file download
            _, redir_info = fetch_url(module, url, data=body,
                                      headers=headers,
                                      method=method,
                                      timeout=socket_timeout, unix_socket=module.params['unix_socket'])
            # if we are redirected, update the url with the location header,
            # and update dest with the new url filename
            if redir_info['status'] in (301, 302, 303, 307):
                url = redir_info['location']
                redirected = True
            dest = os.path.join(dest, url_filename(url))
        # if destination file already exist, only download if file newer
        if os.path.exists(dest):
            kwargs['last_mod_time'] = datetime.datetime.utcfromtimestamp(os.path.getmtime(dest))

        # Reset follow_redirects back to the stashed value
        module.params['follow_redirects'] = follow_redirects

    resp, info = fetch_url(module, url, data=data, headers=headers,
                           method=method, timeout=socket_timeout, unix_socket=module.params['unix_socket'],
                           **kwargs)

    try:
        content = resp.read()
    except AttributeError:
        # there was no content, but the error read()
        # may have been stored in the info as 'body'
        content = info.pop('body', '')

    if src:
        # Try to close the open file handle
        try:
            data.close()
        except Exception:
            pass

    r['redirected'] = redirected or info['url'] != url
    r.update(redir_info)
    r.update(info)

    return r, content, dest


def main():
    argument_spec = url_argument_spec()
    argument_spec.update(
        dest=dict(type='path'),
        url_username=dict(type='str', aliases=['user']),
        url_password=dict(type='str', aliases=['password'], no_log=True),
        body=dict(type='raw'),
        body_format=dict(type='str', default='raw', choices=['form-urlencoded', 'json', 'raw']),
        src=dict(type='path'),
        method=dict(type='str', default='GET'),
        return_content=dict(type='bool', default=False),
        follow_redirects=dict(type='str', default='safe', choices=['all', 'no', 'none', 'safe', 'urllib2', 'yes']),
        creates=dict(type='path'),
        removes=dict(type='path'),
        status_code=dict(type='list', default=[200]),
        timeout=dict(type='int', default=30),
        headers=dict(type='dict', default={}),
        unix_socket=dict(type='path'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        # TODO: Remove check_invalid_arguments in 2.9
        check_invalid_arguments=False,
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

    dict_headers = module.params['headers']

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

    # TODO: Deprecated section.  Remove in Ansible 2.9
    # Grab all the http headers. Need this hack since passing multi-values is
    # currently a bit ugly. (e.g. headers='{"Content-Type":"application/json"}')
    for key, value in iteritems(module.params):
        if key.startswith("HEADER_"):
            module.deprecate('Supplying headers via HEADER_* is deprecated. Please use `headers` to'
                             ' supply headers for the request', version='2.9')
            skey = key.replace("HEADER_", "")
            dict_headers[skey] = value
    # End deprecated section

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
    start = datetime.datetime.utcnow()
    resp, content, dest = uri(module, url, dest, body, body_format, method,
                              dict_headers, socket_timeout)
    resp['elapsed'] = (datetime.datetime.utcnow() - start).seconds
    resp['status'] = int(resp['status'])
    resp['changed'] = False

    # Write the file out if requested
    if dest is not None:
        if resp['status'] in status_code and resp['status'] != 304:
            write_file(module, url, dest, content, resp)
            # allow file attribute changes
            resp['changed'] = True
            module.params['path'] = dest
            file_args = module.load_file_common_arguments(module.params)
            file_args['path'] = dest
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
    content_encoding = 'utf-8'
    if 'content_type' in uresp:
        content_type, params = cgi.parse_header(uresp['content_type'])
        if 'charset' in params:
            content_encoding = params['charset']
        u_content = to_text(content, encoding=content_encoding)
        if any(candidate in content_type for candidate in JSON_CANDIDATES):
            try:
                js = json.loads(u_content)
                uresp['json'] = js
            except Exception:
                if PY2:
                    sys.exc_clear()  # Avoid false positive traceback in fail_json() on Python 2
    else:
        u_content = to_text(content, encoding=content_encoding)

    if resp['status'] not in status_code:
        uresp['msg'] = 'Status code was %s and not %s: %s' % (resp['status'], status_code, uresp.get('msg', ''))
        module.fail_json(content=u_content, **uresp)
    elif return_content:
        module.exit_json(content=u_content, **uresp)
    else:
        module.exit_json(**uresp)


if __name__ == '__main__':
    main()
