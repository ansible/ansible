#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Romeo Theriault <romeot () hawaii.edu>
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
# see examples/playbooks/uri.yml

import shutil
import tempfile
import base64
import datetime
try:
    import json
except ImportError:
    import simplejson as json

DOCUMENTATION = '''
---
module: uri
short_description: Interacts with webservices
description:
  - Interacts with HTTP and HTTPS web services and supports Digest, Basic and WSSE
    HTTP authentication mechanisms.
version_added: "1.1"
options:
  url:
    description:
      - HTTP or HTTPS URL in the form (http|https)://host.domain[:port]/path
    required: true
    default: null
    aliases: []
  dest:
    description:
      - path of where to download the file to (if desired). If I(dest) is a directory, the basename of the file on the remote server will be used.
    required: false
    default: null
  user:
    description:
      - username for the module to use for Digest, Basic or WSSE authentication.
    required: false
    default: null
  password:
    description:
      - password for the module to use for Digest, Basic or WSSE authentication.
    required: false
    default: null
  body:
    description:
      - The body of the http request/response to the web service.
    required: false
    default: null
  method:
    description:
      - The HTTP method of the request or response.
    required: false
    choices: [ "GET", "POST", "PUT", "HEAD", "DELETE", "OPTIONS", "PATCH" ]
    default: "GET"
  return_content:
    description:
      - Whether or not to return the body of the request as a "content" key in the dictionary result. If the reported Content-type is "application/json", then the JSON is additionally loaded into a key called C(json) in the dictionary results.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
  force_basic_auth:
    description:
      - httplib2, the library used by the uri module only sends authentication information when a webservice
        responds to an initial request with a 401 status. Since some basic auth services do not properly
        send a 401, logins will fail. This option forces the sending of the Basic authentication header
        upon initial request.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
  follow_redirects:
    description:
      - Whether or not the URI module should follow redirects. C(all) will follow all redirects.
        C(safe) will follow only "safe" redirects, where "safe" means that the client is only 
        doing a GET or HEAD on the URI to which it is being redirected. C(none) will not follow
        any redirects. Note that C(yes) and C(no) choices are accepted for backwards compatibility, 
        where C(yes) is the equivalent of C(all) and C(no) is the equivalent of C(safe). C(yes) and C(no)
        are deprecated and will be removed in some future version of Ansible.
    required: false
    choices: [ "all", "safe", "none" ]
    default: "safe"
  creates:
    description:
      - a filename, when it already exists, this step will not be run.
    required: false
  removes:
    description:
      - a filename, when it does not exist, this step will not be run.
    required: false
  status_code:
    description:
      - A valid, numeric, HTTP status code that signifies success of the request. Can also be comma separated list of status codes.
    required: false
    default: 200
  timeout:
    description:
      - The socket level timeout in seconds 
    required: false
    default: 30
  HEADER_:
    description:
      - Any parameter starting with "HEADER_" is a sent with your request as a header.
        For example, HEADER_Content-Type="application/json" would send the header
        "Content-Type" along with your request with a value of "application/json".
    required: false
    default: null
  others:
    description:
      - all arguments accepted by the M(file) module also work here
    required: false

# informational: requirements for nodes
requirements: [ urlparse, httplib2 ]
author: Romeo Theriault
'''

EXAMPLES = '''
# Check that you can connect (GET) to a page and it returns a status 200
- uri: url=http://www.example.com

# Check that a page returns a status 200 and fail if the word AWESOME is not in the page contents.
- action: uri url=http://www.example.com return_content=yes
  register: webpage

- action: fail
  when: 'AWESOME' not in "{{ webpage.content }}"


# Create a JIRA issue

- uri: url=https://your.jira.example.com/rest/api/2/issue/ 
       method=POST user=your_username password=your_pass 
       body="{{ lookup('file','issue.json') }}" force_basic_auth=yes 
       status_code=201 HEADER_Content-Type="application/json"  

# Login to a form based webpage, then use the returned cookie to
# access the app in later tasks

- uri: url=https://your.form.based.auth.examle.com/index.php 
       method=POST body="name=your_username&password=your_password&enter=Sign%20in" 
       status_code=302 HEADER_Content-Type="application/x-www-form-urlencoded"
  register: login

- uri: url=https://your.form.based.auth.example.com/dashboard.php
       method=GET return_content=yes HEADER_Cookie="{{login.set_cookie}}"
            
# Queue build of a project in Jenkins:

- uri: url=http://{{jenkins.host}}/job/{{jenkins.job}}/build?token={{jenkins.token}} 
       method=GET user={{jenkins.user}} password={{jenkins.password}} force_basic_auth=yes status_code=201

'''

HAS_HTTPLIB2 = True
try:
    import httplib2
except ImportError:
    HAS_HTTPLIB2 = False

HAS_URLPARSE = True

try:
    import urlparse
    import socket
except ImportError:
    HAS_URLPARSE = False


def write_file(module, url, dest, content):
    # create a tempfile with some test content
    fd, tmpsrc = tempfile.mkstemp()
    f = open(tmpsrc, 'wb')
    try:
        f.write(content)
    except Exception, err:
        os.remove(tmpsrc)
        module.fail_json(msg="failed to create temporary content file: %s" % str(err))
    f.close()
 
    checksum_src   = None
    checksum_dest  = None
 
    # raise an error if there is no tmpsrc file
    if not os.path.exists(tmpsrc):
        os.remove(tmpsrc)
        module.fail_json(msg="Source %s does not exist" % (tmpsrc))
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
            module.fail_json( msg="Destination dir %s not writable" % (os.path.dirname(dest)))

    if checksum_src != checksum_dest:
        try:
            shutil.copyfile(tmpsrc, dest)
        except Exception, err:
            os.remove(tmpsrc)
            module.fail_json(msg="failed to copy %s to %s: %s" % (tmpsrc, dest, str(err)))

    os.remove(tmpsrc)


def url_filename(url):
    fn = os.path.basename(urlparse.urlsplit(url)[2])
    if fn == '':
        return 'index.html'
    return fn


def uri(module, url, dest, user, password, body, method, headers, redirects, socket_timeout):
    # To debug
    #httplib2.debug = 4

    # Handle Redirects         
    if redirects == "all" or redirects == "yes":
        follow_redirects = True
        follow_all_redirects = True
    elif redirects == "none":
        follow_redirects = False
        follow_all_redirects = False
    else:
        follow_redirects = True
        follow_all_redirects = False

    # Create a Http object and set some default options.
    h = httplib2.Http(disable_ssl_certificate_validation=True, timeout=socket_timeout)
    h.follow_all_redirects = follow_all_redirects
    h.follow_redirects = follow_redirects
    h.forward_authorization_headers = True

    # If they have a username or password verify they have both, then add them to the request
    if user is not None and password is None:
        module.fail_json(msg="Both a username and password need to be set.")
    if password is not None and user is None:
        module.fail_json(msg="Both a username and password need to be set.")
    if user is not None and password is not None:
        h.add_credentials(user, password)

    # is dest is set and is a directory, let's check if we get redirected and
    # set the filename from that url
    redirected = False
    resp_redir = {}
    r = {}
    if dest is not None:
        dest = os.path.expanduser(dest)
        if os.path.isdir(dest):
            # first check if we are redirected to a file download
            h.follow_redirects=False
            # Try the request
            try:
                resp_redir, content_redir = h.request(url, method=method, body=body, headers=headers)
                # if we are redirected, update the url with the location header,
                # and update dest with the new url filename
            except:
                pass
            if 'status' in resp_redir and resp_redir['status'] in ["301", "302", "303", "307"]:
                url = resp_redir['location']
                redirected = True
            dest = os.path.join(dest, url_filename(url))
        # if destination file already exist, only download if file newer
        if os.path.exists(dest):
            t = datetime.datetime.utcfromtimestamp(os.path.getmtime(dest))
            tstamp = t.strftime('%a, %d %b %Y %H:%M:%S +0000')
            headers['If-Modified-Since'] = tstamp

    # do safe redirects now, including 307
    h.follow_redirects=follow_redirects

    # Make the request, or try to :)
    try: 
        resp, content = h.request(url, method=method, body=body, headers=headers)     
        r['redirected'] = redirected
        r.update(resp_redir)
        r.update(resp)
        try:
            return r, unicode(content.decode('unicode_escape')), dest
        except:
            return r, content, dest
    except httplib2.RedirectMissingLocation:
        module.fail_json(msg="A 3xx redirect response code was provided but no Location: header was provided to point to the new location.")
    except httplib2.RedirectLimit:
        module.fail_json(msg="The maximum number of redirections was reached without coming to a final URI.")
    except httplib2.ServerNotFoundError:
        module.fail_json(msg="Unable to resolve the host name given.")
    except httplib2.RelativeURIError:
        module.fail_json(msg="A relative, as opposed to an absolute URI, was passed in.")
    except httplib2.FailedToDecompressContent:
        module.fail_json(msg="The headers claimed that the content of the response was compressed but the decompression algorithm applied to the content failed.")
    except httplib2.UnimplementedDigestAuthOptionError:
        module.fail_json(msg="The server requested a type of Digest authentication that we are unfamiliar with.")
    except httplib2.UnimplementedHmacDigestAuthOptionError:
        module.fail_json(msg="The server requested a type of HMACDigest authentication that we are unfamiliar with.")
    except httplib2.UnimplementedHmacDigestAuthOptionError:
        module.fail_json(msg="The server requested a type of HMACDigest authentication that we are unfamiliar with.")
    except socket.error, e:
        module.fail_json(msg="Socket error: %s to %s" % (e, url))

def main():

    module = AnsibleModule(
        argument_spec = dict(
            url = dict(required=True),
            dest = dict(required=False, default=None),
            user = dict(required=False, default=None),
            password = dict(required=False, default=None),
            body = dict(required=False, default=None),
            method = dict(required=False, default='GET', choices=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH']),
            return_content = dict(required=False, default='no', type='bool'),
            force_basic_auth = dict(required=False, default='no', type='bool'),
            follow_redirects = dict(required=False, default='safe', choices=['all', 'safe', 'none', 'yes', 'no']),
            creates = dict(required=False, default=None),
            removes = dict(required=False, default=None),
            status_code = dict(required=False, default=[200], type='list'),
            timeout = dict(required=False, default=30, type='int'),
        ),
        check_invalid_arguments=False,
        add_file_common_args=True
    )

    if not HAS_HTTPLIB2:
        module.fail_json(msg="httplib2 is not installed")
    if not HAS_URLPARSE:
        module.fail_json(msg="urlparse is not installed")

    url  = module.params['url']
    user = module.params['user']
    password = module.params['password']
    body = module.params['body']
    method = module.params['method']
    dest = module.params['dest']
    return_content = module.params['return_content']
    force_basic_auth = module.params['force_basic_auth']
    redirects = module.params['follow_redirects']
    creates = module.params['creates']
    removes = module.params['removes']
    status_code = [int(x) for x in list(module.params['status_code'])]
    socket_timeout = module.params['timeout']

    # Grab all the http headers. Need this hack since passing multi-values is currently a bit ugly. (e.g. headers='{"Content-Type":"application/json"}')
    dict_headers = {}
    for key, value in module.params.iteritems():
        if key.startswith("HEADER_"):
            skey = key.replace("HEADER_", "")
            dict_headers[skey] = value

  
    if creates is not None:
        # do not run the command if the line contains creates=filename
        # and the filename already exists.  This allows idempotence
        # of uri executions.
        creates = os.path.expanduser(creates)
        if os.path.exists(creates):
            module.exit_json(stdout="skipped, since %s exists" % creates, skipped=True, changed=False, stderr=False, rc=0)

    if removes is not None:
        # do not run the command if the line contains removes=filename
        # and the filename do not exists.  This allows idempotence
        # of uri executions.
        v = os.path.expanduser(removes)
        if not os.path.exists(removes):
            module.exit_json(stdout="skipped, since %s does not exist" % removes, skipped=True, changed=False, stderr=False, rc=0)


    # httplib2 only sends authentication after the server asks for it with a 401.
    # Some 'basic auth' servies fail to send a 401 and require the authentication
    # up front. This creates the Basic authentication header and sends it immediately. 
    if force_basic_auth:
        dict_headers["Authorization"] = "Basic {0}".format(base64.b64encode("{0}:{1}".format(user, password))) 


    # Make the request
    resp, content, dest = uri(module, url, dest, user, password, body, method, dict_headers, redirects, socket_timeout)
    resp['status'] = int(resp['status'])

    # Write the file out if requested
    if dest is not None:
        if resp['status'] == 304:
            changed = False
        else:
            write_file(module, url, dest, content)
            # allow file attribute changes
            changed = True
            module.params['path'] = dest
            file_args = module.load_file_common_arguments(module.params)
            file_args['path'] = dest
            changed = module.set_fs_attributes_if_different(file_args, changed)
        resp['path'] = dest
    else:
        changed = False

    # Transmogrify the headers, replacing '-' with '_', since variables dont work with dashes.
    uresp = {}
    for key, value in resp.iteritems():
        ukey = key.replace("-", "_")  
        uresp[ukey] = value

    if 'content_type' in uresp:
        if uresp['content_type'].startswith('application/json'):
            try:
                js = json.loads(content)
                uresp['json'] = js
            except:
                pass
    if resp['status'] not in status_code:
        module.fail_json(msg="Status code was not " + str(status_code), content=content, **uresp)
    elif return_content:
        module.exit_json(changed=changed, content=content, **uresp)
    else:
        module.exit_json(changed=changed, **uresp)


# import module snippets
from ansible.module_utils.basic import *
main()
