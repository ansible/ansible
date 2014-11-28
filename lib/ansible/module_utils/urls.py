# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

try:
    import urllib
    HAS_URLLIB = True
except:
    HAS_URLLIB = False

try:
    import urllib2
    HAS_URLLIB2 = True
except:
    HAS_URLLIB2 = False

try:
    import urlparse
    HAS_URLPARSE = True
except:
    HAS_URLPARSE = False

try:
    import ssl
    HAS_SSL=True
except:
    HAS_SSL=False

import httplib
import os
import re
import socket
import tempfile


# This is a dummy cacert provided for Mac OS since you need at least 1
# ca cert, regardless of validity, for Python on Mac OS to use the
# keychain functionality in OpenSSL for validating SSL certificates.
# See: http://mercurial.selenic.com/wiki/CACertificates#Mac_OS_X_10.6_and_higher
DUMMY_CA_CERT = """-----BEGIN CERTIFICATE-----
MIICvDCCAiWgAwIBAgIJAO8E12S7/qEpMA0GCSqGSIb3DQEBBQUAMEkxCzAJBgNV
BAYTAlVTMRcwFQYDVQQIEw5Ob3J0aCBDYXJvbGluYTEPMA0GA1UEBxMGRHVyaGFt
MRAwDgYDVQQKEwdBbnNpYmxlMB4XDTE0MDMxODIyMDAyMloXDTI0MDMxNTIyMDAy
MlowSTELMAkGA1UEBhMCVVMxFzAVBgNVBAgTDk5vcnRoIENhcm9saW5hMQ8wDQYD
VQQHEwZEdXJoYW0xEDAOBgNVBAoTB0Fuc2libGUwgZ8wDQYJKoZIhvcNAQEBBQAD
gY0AMIGJAoGBANtvpPq3IlNlRbCHhZAcP6WCzhc5RbsDqyh1zrkmLi0GwcQ3z/r9
gaWfQBYhHpobK2Tiq11TfraHeNB3/VfNImjZcGpN8Fl3MWwu7LfVkJy3gNNnxkA1
4Go0/LmIvRFHhbzgfuo9NFgjPmmab9eqXJceqZIlz2C8xA7EeG7ku0+vAgMBAAGj
gaswgagwHQYDVR0OBBYEFPnN1nPRqNDXGlCqCvdZchRNi/FaMHkGA1UdIwRyMHCA
FPnN1nPRqNDXGlCqCvdZchRNi/FaoU2kSzBJMQswCQYDVQQGEwJVUzEXMBUGA1UE
CBMOTm9ydGggQ2Fyb2xpbmExDzANBgNVBAcTBkR1cmhhbTEQMA4GA1UEChMHQW5z
aWJsZYIJAO8E12S7/qEpMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADgYEA
MUB80IR6knq9K/tY+hvPsZer6eFMzO3JGkRFBh2kn6JdMDnhYGX7AXVHGflrwNQH
qFy+aenWXsC0ZvrikFxbQnX8GVtDADtVznxOi7XzFw7JOxdsVrpXgSN0eh0aMzvV
zKPZsZ2miVGclicJHzm5q080b1p/sZtuKIEZk6vZqEg=
-----END CERTIFICATE-----
"""

class CustomHTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        "Connect to a host on a given (SSL) port."

        if hasattr(self, 'source_address'):
            sock = socket.create_connection((self.host, self.port), self.timeout, self.source_address)
        else:
            sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        self.sock = ssl.wrap_socket(sock, keyfile=self.key_file, certfile=self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1)

class CustomHTTPSHandler(urllib2.HTTPSHandler):

    def https_open(self, req):
        return self.do_open(CustomHTTPSConnection, req)

    https_request = urllib2.AbstractHTTPHandler.do_request_

def generic_urlparse(parts):
    '''
    Returns a dictionary of url parts as parsed by urlparse,
    but accounts for the fact that older versions of that
    library do not support named attributes (ie. .netloc)
    '''
    generic_parts = dict()
    if hasattr(parts, 'netloc'):
        # urlparse is newer, just read the fields straight
        # from the parts object
        generic_parts['scheme']   = parts.scheme
        generic_parts['netloc']   = parts.netloc
        generic_parts['path']     = parts.path
        generic_parts['params']   = parts.params
        generic_parts['query']    = parts.query
        generic_parts['fragment'] = parts.fragment
        generic_parts['username'] = parts.username
        generic_parts['password'] = parts.password
        generic_parts['hostname'] = parts.hostname
        generic_parts['port']     = parts.port
    else:
        # we have to use indexes, and then parse out
        # the other parts not supported by indexing
        generic_parts['scheme']   = parts[0]
        generic_parts['netloc']   = parts[1]
        generic_parts['path']     = parts[2]
        generic_parts['params']   = parts[3]
        generic_parts['query']    = parts[4]
        generic_parts['fragment'] = parts[5]
        # get the username, password, etc.
        try:
            netloc_re = re.compile(r'^((?:\w)+(?::(?:\w)+)?@)?([A-Za-z0-9.-]+)(:\d+)?$')
            (auth, hostname, port) = netloc_re.match(parts[1])
            if port:
                # the capture group for the port will include the ':',
                # so remove it and convert the port to an integer
                port = int(port[1:])
            if auth:
                # the capture group above inclues the @, so remove it
                # and then split it up based on the first ':' found
                auth = auth[:-1]
                username, password = auth.split(':', 1)
            generic_parts['username'] = username
            generic_parts['password'] = password
            generic_parts['hostname'] = hostnme
            generic_parts['port']     = port
        except:
            generic_parts['username'] = None
            generic_parts['password'] = None
            generic_parts['hostname'] = None
            generic_parts['port']     = None
    return generic_parts

class RequestWithMethod(urllib2.Request):
    '''
    Workaround for using DELETE/PUT/etc with urllib2
    Originally contained in library/net_infrastructure/dnsmadeeasy
    '''

    def __init__(self, url, method, data=None, headers={}):
        self._method = method
        urllib2.Request.__init__(self, url, data, headers)

    def get_method(self):
        if self._method:
            return self._method
        else:
            return urllib2.Request.get_method(self)


class SSLValidationHandler(urllib2.BaseHandler):
    '''
    A custom handler class for SSL validation.

    Based on:
    http://stackoverflow.com/questions/1087227/validate-ssl-certificates-with-python
    http://techknack.net/python-urllib2-handlers/
    '''
    CONNECT_COMMAND = "CONNECT %s:%s HTTP/1.0\r\nConnection: close\r\n"

    def __init__(self, module, hostname, port):
        self.module = module
        self.hostname = hostname
        self.port = port

    def get_ca_certs(self):
        # tries to find a valid CA cert in one of the
        # standard locations for the current distribution

        ca_certs = []
        paths_checked = []
        platform = get_platform()
        distribution = get_distribution()

        # build a list of paths to check for .crt/.pem files
        # based on the platform type
        paths_checked.append('/etc/ssl/certs')
        if platform == 'Linux':
            paths_checked.append('/etc/pki/ca-trust/extracted/pem')
            paths_checked.append('/etc/pki/tls/certs')
            paths_checked.append('/usr/share/ca-certificates/cacert.org')
        elif platform == 'FreeBSD':
            paths_checked.append('/usr/local/share/certs')
        elif platform == 'OpenBSD':
            paths_checked.append('/etc/ssl')
        elif platform == 'NetBSD':
            ca_certs.append('/etc/openssl/certs')
        elif platform == 'SunOS':
            paths_checked.append('/opt/local/etc/openssl/certs')

        # fall back to a user-deployed cert in a standard
        # location if the OS platform one is not available
        paths_checked.append('/etc/ansible')

        tmp_fd, tmp_path = tempfile.mkstemp()

        # Write the dummy ca cert if we are running on Mac OS X
        if platform == 'Darwin':
            os.write(tmp_fd, DUMMY_CA_CERT)
            # Default Homebrew path for OpenSSL certs 
            paths_checked.append('/usr/local/etc/openssl')

        # for all of the paths, find any  .crt or .pem files
        # and compile them into single temp file for use
        # in the ssl check to speed up the test
        for path in paths_checked:
            if os.path.exists(path) and os.path.isdir(path):
                dir_contents = os.listdir(path)
                for f in dir_contents:
                    full_path = os.path.join(path, f)
                    if os.path.isfile(full_path) and os.path.splitext(f)[1] in ('.crt','.pem'):
                        try:
                            cert_file = open(full_path, 'r')
                            os.write(tmp_fd, cert_file.read())
                            os.write(tmp_fd, '\n')
                            cert_file.close()
                        except:
                            pass

        return (tmp_path, paths_checked)

    def validate_proxy_response(self, response, valid_codes=[200]):
        '''
        make sure we get back a valid code from the proxy
        '''
        try:
            (http_version, resp_code, msg) = re.match(r'(HTTP/\d\.\d) (\d\d\d) (.*)', response).groups()
            if int(resp_code) not in valid_codes:
                raise Exception
        except:
            self.module.fail_json(msg='Connection to proxy failed')

    def http_request(self, req):
        tmp_ca_cert_path, paths_checked = self.get_ca_certs()
        https_proxy = os.environ.get('https_proxy')
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if https_proxy:
                proxy_parts = generic_urlparse(urlparse.urlparse(https_proxy))
                s.connect((proxy_parts.get('hostname'), proxy_parts.get('port')))
                if proxy_parts.get('scheme') == 'http':
                    s.sendall(self.CONNECT_COMMAND % (self.hostname, self.port))
                    if proxy_parts.get('username'):
                        credentials = "%s:%s" % (proxy_parts.get('username',''), proxy_parts.get('password',''))
                        s.sendall('Proxy-Authorization: Basic %s\r\n' % credentials.encode('base64').strip())
                    s.sendall('\r\n')
                    connect_result = s.recv(4096)
                    self.validate_proxy_response(connect_result)
                    ssl_s = ssl.wrap_socket(s, ca_certs=tmp_ca_cert_path, cert_reqs=ssl.CERT_REQUIRED)
                else:
                    self.module.fail_json(msg='Unsupported proxy scheme: %s. Currently ansible only supports HTTP proxies.' % proxy_parts.get('scheme'))
            else:
                s.connect((self.hostname, self.port))
                ssl_s = ssl.wrap_socket(s, ca_certs=tmp_ca_cert_path, cert_reqs=ssl.CERT_REQUIRED)
            # close the ssl connection
            #ssl_s.unwrap()
            s.close()
        except (ssl.SSLError, socket.error), e:
            # fail if we tried all of the certs but none worked
            if 'connection refused' in str(e).lower():
                self.module.fail_json(msg='Failed to connect to %s:%s.' % (self.hostname, self.port))
            else:
                self.module.fail_json(
                    msg='Failed to validate the SSL certificate for %s:%s. ' % (self.hostname, self.port) + \
                    'Use validate_certs=no or make sure your managed systems have a valid CA certificate installed. ' + \
                    'Paths checked for this platform: %s' % ", ".join(paths_checked)
                )
        try:
            # cleanup the temp file created, don't worry
            # if it fails for some reason
            os.remove(tmp_ca_cert_path)
        except:
            pass

        return req

    https_request = http_request


def url_argument_spec():
    '''
    Creates an argument spec that can be used with any module
    that will be requesting content via urllib/urllib2
    '''
    return dict(
        url = dict(),
        force = dict(default='no', aliases=['thirsty'], type='bool'),
        http_agent = dict(default='ansible-httpget'),
        use_proxy = dict(default='yes', type='bool'),
        validate_certs = dict(default='yes', type='bool'),
        url_username = dict(required=False),
        url_password = dict(required=False),
    )


def fetch_url(module, url, data=None, headers=None, method=None, 
              use_proxy=True, force=False, last_mod_time=None, timeout=10):
    '''
    Fetches a file from an HTTP/FTP server using urllib2
    '''

    if not HAS_URLLIB:
        module.fail_json(msg='urllib is not installed')
    if not HAS_URLLIB2:
        module.fail_json(msg='urllib2 is not installed')
    elif not HAS_URLPARSE:
        module.fail_json(msg='urlparse is not installed')

    r = None
    handlers = []
    info = dict(url=url)

    distribution = get_distribution()
    # Get validate_certs from the module params
    validate_certs = module.params.get('validate_certs', True)

    # FIXME: change the following to use the generic_urlparse function
    #        to remove the indexed references for 'parsed'
    parsed = urlparse.urlparse(url)
    if parsed[0] == 'https':
        if not HAS_SSL and validate_certs:
            if distribution == 'Redhat':
                module.fail_json(msg='SSL validation is not available in your version of python. You can use validate_certs=no, however this is unsafe and not recommended. You can also install python-ssl from EPEL')
            else:
                module.fail_json(msg='SSL validation is not available in your version of python. You can use validate_certs=no, however this is unsafe and not recommended')

        elif validate_certs:
            # do the cert validation
            netloc = parsed[1]
            if '@' in netloc:
                netloc = netloc.split('@', 1)[1]
            if ':' in netloc:
                hostname, port = netloc.split(':', 1)
            else:
                hostname = netloc
                port = 443
            # create the SSL validation handler and
            # add it to the list of handlers
            ssl_handler = SSLValidationHandler(module, hostname, port)
            handlers.append(ssl_handler)

    if parsed[0] != 'ftp':
        username = module.params.get('url_username', '')
        if username:
            password = module.params.get('url_password', '')
            netloc = parsed[1]
        elif '@' in parsed[1]:
            credentials, netloc = parsed[1].split('@', 1)
            if ':' in credentials:
                username, password = credentials.split(':', 1)
            else:
                username = credentials
                password = ''

            parsed = list(parsed)
            parsed[1] = netloc

            # reconstruct url without credentials
            url = urlparse.urlunparse(parsed)

        if username:
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()

            # this creates a password manager
            passman.add_password(None, netloc, username, password)

            # because we have put None at the start it will always
            # use this username/password combination for  urls
            # for which `theurl` is a super-url
            authhandler = urllib2.HTTPBasicAuthHandler(passman)

            # create the AuthHandler
            handlers.append(authhandler)

    if not use_proxy:
        proxyhandler = urllib2.ProxyHandler({})
        handlers.append(proxyhandler)

    # pre-2.6 versions of python cannot use the custom https
    # handler, since the socket class is lacking this method
    if hasattr(socket, 'create_connection'):
        handlers.append(CustomHTTPSHandler)

    opener = urllib2.build_opener(*handlers)
    urllib2.install_opener(opener)

    if method:
        if method.upper() not in ('OPTIONS','GET','HEAD','POST','PUT','DELETE','TRACE','CONNECT'):
            module.fail_json(msg='invalid HTTP request method; %s' % method.upper())
        request = RequestWithMethod(url, method.upper(), data)
    else:
        request = urllib2.Request(url, data)

    # add the custom agent header, to help prevent issues 
    # with sites that block the default urllib agent string 
    request.add_header('User-agent', module.params.get('http_agent'))

    # if we're ok with getting a 304, set the timestamp in the 
    # header, otherwise make sure we don't get a cached copy
    if last_mod_time and not force:
        tstamp = last_mod_time.strftime('%a, %d %b %Y %H:%M:%S +0000')
        request.add_header('If-Modified-Since', tstamp)
    else:
        request.add_header('cache-control', 'no-cache')

    # user defined headers now, which may override things we've set above
    if headers:
        if not isinstance(headers, dict):
            module.fail_json("headers provided to fetch_url() must be a dict")
        for header in headers:
            request.add_header(header, headers[header])

    try:
        if sys.version_info < (2,6,0):
            # urlopen in python prior to 2.6.0 did not
            # have a timeout parameter
            r = urllib2.urlopen(request, None)
        else:
            r = urllib2.urlopen(request, None, timeout)
        info.update(r.info())
        info['url'] = r.geturl()  # The URL goes in too, because of redirects.
        info.update(dict(msg="OK (%s bytes)" % r.headers.get('Content-Length', 'unknown'), status=200))
    except urllib2.HTTPError, e:
        info.update(dict(msg=str(e), status=e.code))
    except urllib2.URLError, e:
        code = int(getattr(e, 'code', -1))
        info.update(dict(msg="Request failed: %s" % str(e), status=code))
    except socket.error, e:
        info.update(dict(msg="Connection failure: %s" % str(e), status=-1))
    except Exception, e:
        info.update(dict(msg="An unknown error occurred: %s" % str(e), status=-1))

    return r, info

