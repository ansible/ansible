# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com>, 2015
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
#
# The match_hostname function and supporting code is under the terms and
# conditions of the Python Software Foundation License.  They were taken from
# the Python3 standard library and adapted for use in Python2.  See comments in the
# source for which code precisely is under this License.  PSF License text
# follows:
#
# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
# --------------------------------------------
#
# 1. This LICENSE AGREEMENT is between the Python Software Foundation
# ("PSF"), and the Individual or Organization ("Licensee") accessing and
# otherwise using this software ("Python") in source or binary form and
# its associated documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF hereby
# grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
# analyze, test, perform and/or display publicly, prepare derivative works,
# distribute, and otherwise use Python alone or in any derivative version,
# provided, however, that PSF's License Agreement and PSF's notice of copyright,
# i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
# 2011, 2012, 2013, 2014 Python Software Foundation; All Rights Reserved" are
# retained in Python alone or in any derivative version prepared by Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on
# or incorporates Python or any part thereof, and wants to make
# the derivative work available to others as provided herein, then
# Licensee hereby agrees to include in any such work a brief summary of
# the changes made to Python.
#
# 4. PSF is making Python available to Licensee on an "AS IS"
# basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
# IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
# DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
# FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
# INFRINGE ANY THIRD PARTY RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
# FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
# A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
# OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material
# breach of its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any
# relationship of agency, partnership, or joint venture between PSF and
# Licensee.  This License Agreement does not grant permission to use PSF
# trademarks or trade name in a trademark sense to endorse or promote
# products or services of Licensee, or any third party.
#
# 8. By copying, installing or otherwise using Python, Licensee
# agrees to be bound by the terms and conditions of this License
# Agreement.

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
    HAS_SSL = True
except:
    HAS_SSL = False

try:
    # SNI Handling needs python2.7.9's SSLContext
    from ssl import create_default_context, SSLContext
    HAS_SSLCONTEXT = True
except ImportError:
    HAS_SSLCONTEXT = False

# Select a protocol that includes all secure tls protocols
# Exclude insecure ssl protocols if possible

if HAS_SSL:
    # If we can't find extra tls methods, ssl.PROTOCOL_TLSv1 is sufficient
    PROTOCOL = ssl.PROTOCOL_TLSv1
if not HAS_SSLCONTEXT and HAS_SSL:
    try:
        import ctypes, ctypes.util
    except ImportError:
        # python 2.4 (likely rhel5 which doesn't have tls1.1 support in its openssl)
        pass
    else:
        libssl_name = ctypes.util.find_library('ssl')
        libssl = ctypes.CDLL(libssl_name)
        for method in ('TLSv1_1_method', 'TLSv1_2_method'):
            try:
                libssl[method]
                # Found something - we'll let openssl autonegotiate and hope
                # the server has disabled sslv2 and 3.  best we can do.
                PROTOCOL = ssl.PROTOCOL_SSLv23
                break
            except AttributeError:
                pass
        del libssl



HAS_MATCH_HOSTNAME = True
try:
    from ssl import match_hostname, CertificateError
except ImportError:
    try:
        from backports.ssl_match_hostname import match_hostname, CertificateError
    except ImportError:
        HAS_MATCH_HOSTNAME = False

if not HAS_MATCH_HOSTNAME:
    ###
    ### The following block of code is under the terms and conditions of the
    ### Python Software Foundation License
    ###

    """The match_hostname() function from Python 3.4, essential when using SSL."""

    import re

    class CertificateError(ValueError):
        pass


    def _dnsname_match(dn, hostname, max_wildcards=1):
        """Matching according to RFC 6125, section 6.4.3

        http://tools.ietf.org/html/rfc6125#section-6.4.3
        """
        pats = []
        if not dn:
            return False

        # Ported from python3-syntax:
        # leftmost, *remainder = dn.split(r'.')
        parts = dn.split(r'.')
        leftmost = parts[0]
        remainder = parts[1:]

        wildcards = leftmost.count('*')
        if wildcards > max_wildcards:
            # Issue #17980: avoid denials of service by refusing more
            # than one wildcard per fragment.  A survey of established
            # policy among SSL implementations showed it to be a
            # reasonable choice.
            raise CertificateError(
                "too many wildcards in certificate DNS name: " + repr(dn))

        # speed up common case w/o wildcards
        if not wildcards:
            return dn.lower() == hostname.lower()

        # RFC 6125, section 6.4.3, subitem 1.
        # The client SHOULD NOT attempt to match a presented identifier in which
        # the wildcard character comprises a label other than the left-most label.
        if leftmost == '*':
            # When '*' is a fragment by itself, it matches a non-empty dotless
            # fragment.
            pats.append('[^.]+')
        elif leftmost.startswith('xn--') or hostname.startswith('xn--'):
            # RFC 6125, section 6.4.3, subitem 3.
            # The client SHOULD NOT attempt to match a presented identifier
            # where the wildcard character is embedded within an A-label or
            # U-label of an internationalized domain name.
            pats.append(re.escape(leftmost))
        else:
            # Otherwise, '*' matches any dotless string, e.g. www*
            pats.append(re.escape(leftmost).replace(r'\*', '[^.]*'))

        # add the remaining fragments, ignore any wildcards
        for frag in remainder:
            pats.append(re.escape(frag))

        pat = re.compile(r'\A' + r'\.'.join(pats) + r'\Z', re.IGNORECASE)
        return pat.match(hostname)


    def match_hostname(cert, hostname):
        """Verify that *cert* (in decoded format as returned by
        SSLSocket.getpeercert()) matches the *hostname*.  RFC 2818 and RFC 6125
        rules are followed, but IP addresses are not accepted for *hostname*.

        CertificateError is raised on failure. On success, the function
        returns nothing.
        """
        if not cert:
            raise ValueError("empty or no certificate")
        dnsnames = []
        san = cert.get('subjectAltName', ())
        for key, value in san:
            if key == 'DNS':
                if _dnsname_match(value, hostname):
                    return
                dnsnames.append(value)
        if not dnsnames:
            # The subject is only checked when there is no dNSName entry
            # in subjectAltName
            for sub in cert.get('subject', ()):
                for key, value in sub:
                    # XXX according to RFC 2818, the most specific Common Name
                    # must be used.
                    if key == 'commonName':
                        if _dnsname_match(value, hostname):
                            return
                        dnsnames.append(value)
        if len(dnsnames) > 1:
            raise CertificateError("hostname %r "
                "doesn't match either of %s"
                % (hostname, ', '.join(map(repr, dnsnames))))
        elif len(dnsnames) == 1:
            raise CertificateError("hostname %r "
                "doesn't match %r"
                % (hostname, dnsnames[0]))
        else:
            raise CertificateError("no appropriate commonName or "
                "subjectAltName fields were found")

    ###
    ### End of Python Software Foundation Licensed code
    ###

    HAS_MATCH_HOSTNAME = True


import httplib
import os
import re
import sys
import socket
import platform
import tempfile
import base64


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

#
# Exceptions
#

class ConnectionError(Exception):
    """Failed to connect to the server"""
    pass

class ProxyError(ConnectionError):
    """Failure to connect because of a proxy"""
    pass

class SSLValidationError(ConnectionError):
    """Failure to connect due to SSL validation failing"""
    pass

class NoSSLError(SSLValidationError):
    """Needed to connect to an HTTPS url but no ssl library available to verify the certificate"""
    pass

# Some environments (Google Compute Engine's CoreOS deploys) do not compile
# against openssl and thus do not have any HTTPS support.
CustomHTTPSConnection = CustomHTTPSHandler = None
if hasattr(httplib, 'HTTPSConnection') and hasattr(urllib2, 'HTTPSHandler'):
    class CustomHTTPSConnection(httplib.HTTPSConnection):
        def __init__(self, *args, **kwargs):
            httplib.HTTPSConnection.__init__(self, *args, **kwargs)
            if HAS_SSLCONTEXT:
                self.context = create_default_context()
                if self.cert_file:
                    self.context.load_cert_chain(self.cert_file, self.key_file)

        def connect(self):
            "Connect to a host on a given (SSL) port."

            if hasattr(self, 'source_address'):
                sock = socket.create_connection((self.host, self.port), self.timeout, self.source_address)
            else:
                sock = socket.create_connection((self.host, self.port), self.timeout)

            server_hostname = self.host
            # Note: self._tunnel_host is not available on py < 2.6 but this code
            # isn't used on py < 2.6 (lack of create_connection)
            if self._tunnel_host:
                self.sock = sock
                self._tunnel()
                server_hostname = self._tunnel_host

            if HAS_SSLCONTEXT:
                self.sock = self.context.wrap_socket(sock, server_hostname=server_hostname)
            else:
                self.sock = ssl.wrap_socket(sock, keyfile=self.key_file, certfile=self.cert_file, ssl_version=PROTOCOL)

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
            match = netloc_re.match(parts[1])
            auth = match.group(1)
            hostname = match.group(2)
            port = match.group(3)
            if port:
                # the capture group for the port will include the ':',
                # so remove it and convert the port to an integer
                port = int(port[1:])
            if auth:
                # the capture group above inclues the @, so remove it
                # and then split it up based on the first ':' found
                auth = auth[:-1]
                username, password = auth.split(':', 1)
            else:
                username = password = None
            generic_parts['username'] = username
            generic_parts['password'] = password
            generic_parts['hostname'] = hostname
            generic_parts['port']     = port
        except:
            generic_parts['username'] = None
            generic_parts['password'] = None
            generic_parts['hostname'] = parts[1]
            generic_parts['port']     = None
    return generic_parts

class RequestWithMethod(urllib2.Request):
    '''
    Workaround for using DELETE/PUT/etc with urllib2
    Originally contained in library/net_infrastructure/dnsmadeeasy
    '''

    def __init__(self, url, method, data=None, headers=None):
        if headers is None:
            headers = {}
        self._method = method.upper()
        urllib2.Request.__init__(self, url, data, headers)

    def get_method(self):
        if self._method:
            return self._method
        else:
            return urllib2.Request.get_method(self)


def RedirectHandlerFactory(follow_redirects=None, validate_certs=True):
    """This is a class factory that closes over the value of
    ``follow_redirects`` so that the RedirectHandler class has access to
    that value without having to use globals, and potentially cause problems
    where ``open_url`` or ``fetch_url`` are used multiple times in a module.
    """

    class RedirectHandler(urllib2.HTTPRedirectHandler):
        """This is an implementation of a RedirectHandler to match the
        functionality provided by httplib2. It will utilize the value of
        ``follow_redirects`` that is passed into ``RedirectHandlerFactory``
        to determine how redirects should be handled in urllib2.
        """

        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            handler = maybe_add_ssl_handler(newurl, validate_certs)
            if handler:
                urllib2._opener.add_handler(handler)

            if follow_redirects == 'urllib2':
                return urllib2.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, hdrs, newurl)
            elif follow_redirects in ['no', 'none', False]:
                raise urllib2.HTTPError(newurl, code, msg, hdrs, fp)

            do_redirect = False
            if follow_redirects in ['all', 'yes', True]:
                do_redirect = (code >= 300 and code < 400)

            elif follow_redirects == 'safe':
                m = req.get_method()
                do_redirect = (code >= 300 and code < 400 and m in ('GET', 'HEAD'))

            if do_redirect:
                # be conciliant with URIs containing a space
                newurl = newurl.replace(' ', '%20')
                newheaders = dict((k,v) for k,v in req.headers.items()
                                  if k.lower() not in ("content-length", "content-type")
                                 )
                return urllib2.Request(newurl,
                                       headers=newheaders,
                                       origin_req_host=req.get_origin_req_host(),
                                       unverifiable=True)
            else:
                raise urllib2.HTTPError(req.get_full_url(), code, msg, hdrs,
                                        fp)

    return RedirectHandler


class SSLValidationHandler(urllib2.BaseHandler):
    '''
    A custom handler class for SSL validation.

    Based on:
    http://stackoverflow.com/questions/1087227/validate-ssl-certificates-with-python
    http://techknack.net/python-urllib2-handlers/
    '''
    CONNECT_COMMAND = "CONNECT %s:%s HTTP/1.0\r\nConnection: close\r\n"

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

    def get_ca_certs(self):
        # tries to find a valid CA cert in one of the
        # standard locations for the current distribution

        ca_certs = []
        paths_checked = []

        system = platform.system()
        # build a list of paths to check for .crt/.pem files
        # based on the platform type
        paths_checked.append('/etc/ssl/certs')
        if system == 'Linux':
            paths_checked.append('/etc/pki/ca-trust/extracted/pem')
            paths_checked.append('/etc/pki/tls/certs')
            paths_checked.append('/usr/share/ca-certificates/cacert.org')
        elif system == 'FreeBSD':
            paths_checked.append('/usr/local/share/certs')
        elif system == 'OpenBSD':
            paths_checked.append('/etc/ssl')
        elif system == 'NetBSD':
            ca_certs.append('/etc/openssl/certs')
        elif system == 'SunOS':
            paths_checked.append('/opt/local/etc/openssl/certs')

        # fall back to a user-deployed cert in a standard
        # location if the OS platform one is not available
        paths_checked.append('/etc/ansible')

        tmp_fd, tmp_path = tempfile.mkstemp()

        # Write the dummy ca cert if we are running on Mac OS X
        if system == 'Darwin':
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
            raise ProxyError('Connection to proxy failed')

    def detect_no_proxy(self, url):
        '''
        Detect if the 'no_proxy' environment variable is set and honor those locations.
        '''
        env_no_proxy = os.environ.get('no_proxy')
        if env_no_proxy:
            env_no_proxy = env_no_proxy.split(',')
            netloc = urlparse.urlparse(url).netloc

            for host in env_no_proxy:
                if netloc.endswith(host) or netloc.split(':')[0].endswith(host):
                    # Our requested URL matches something in no_proxy, so don't
                    # use the proxy for this
                    return False
        return True

    def _make_context(self, tmp_ca_cert_path):
        context = create_default_context()
        context.load_verify_locations(tmp_ca_cert_path)
        return context

    def http_request(self, req):
        tmp_ca_cert_path, paths_checked = self.get_ca_certs()
        https_proxy = os.environ.get('https_proxy')
        context = None
        if HAS_SSLCONTEXT:
            context = self._make_context(tmp_ca_cert_path)

        # Detect if 'no_proxy' environment variable is set and if our URL is included
        use_proxy = self.detect_no_proxy(req.get_full_url())

        if not use_proxy:
            # ignore proxy settings for this host request
            return req

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if https_proxy:
                proxy_parts = generic_urlparse(urlparse.urlparse(https_proxy))
                port = proxy_parts.get('port') or 443
                s.connect((proxy_parts.get('hostname'), port))
                if proxy_parts.get('scheme') == 'http':
                    s.sendall(self.CONNECT_COMMAND % (self.hostname, self.port))
                    if proxy_parts.get('username'):
                        credentials = "%s:%s" % (proxy_parts.get('username',''), proxy_parts.get('password',''))
                        s.sendall('Proxy-Authorization: Basic %s\r\n' % credentials.encode('base64').strip())
                    s.sendall('\r\n')
                    connect_result = s.recv(4096)
                    self.validate_proxy_response(connect_result)
                    if context:
                        ssl_s = context.wrap_socket(s, server_hostname=self.hostname)
                    else:
                        ssl_s = ssl.wrap_socket(s, ca_certs=tmp_ca_cert_path, cert_reqs=ssl.CERT_REQUIRED, ssl_version=PROTOCOL)
                        match_hostname(ssl_s.getpeercert(), self.hostname)
                else:
                    raise ProxyError('Unsupported proxy scheme: %s. Currently ansible only supports HTTP proxies.' % proxy_parts.get('scheme'))
            else:
                s.connect((self.hostname, self.port))
                if context:
                    ssl_s = context.wrap_socket(s, server_hostname=self.hostname)
                else:
                    ssl_s = ssl.wrap_socket(s, ca_certs=tmp_ca_cert_path, cert_reqs=ssl.CERT_REQUIRED, ssl_version=PROTOCOL)
                    match_hostname(ssl_s.getpeercert(), self.hostname)
            # close the ssl connection
            #ssl_s.unwrap()
            s.close()
        except (ssl.SSLError, socket.error), e:
            # fail if we tried all of the certs but none worked
            if 'connection refused' in str(e).lower():
                raise ConnectionError('Failed to connect to %s:%s.' % (self.hostname, self.port))
            else:
                raise SSLValidationError('Failed to validate the SSL certificate for %s:%s.'
                    ' Make sure your managed systems have a valid CA'
                    ' certificate installed.  If the website serving the url'
                    ' uses SNI you need python >= 2.7.9 on your managed'
                    ' machine.  You can use validate_certs=False if you do'
                    ' not need to confirm the server\s identity but this is'
                    ' unsafe and not recommended'
                    ' Paths checked for this platform: %s' % (self.hostname, self.port, ", ".join(paths_checked))
                )
        except CertificateError:
            raise SSLValidationError("SSL Certificate does not belong to %s.  Make sure the url has a certificate that belongs to it or use validate_certs=False (insecure)" % self.hostname)

        try:
            # cleanup the temp file created, don't worry
            # if it fails for some reason
            os.remove(tmp_ca_cert_path)
        except:
            pass

        return req

    https_request = http_request

def maybe_add_ssl_handler(url, validate_certs):
    # FIXME: change the following to use the generic_urlparse function
    #        to remove the indexed references for 'parsed'
    parsed = urlparse.urlparse(url)
    if parsed[0] == 'https' and validate_certs:
        if not HAS_SSL:
            raise NoSSLError('SSL validation is not available in your version of python. You can use validate_certs=False, however this is unsafe and not recommended')

        # do the cert validation
        netloc = parsed[1]
        if '@' in netloc:
            netloc = netloc.split('@', 1)[1]
        if ':' in netloc:
            hostname, port = netloc.split(':', 1)
            port = int(port)
        else:
            hostname = netloc
            port = 443
        # create the SSL validation handler and
        # add it to the list of handlers
        return SSLValidationHandler(hostname, port)

# Rewrite of fetch_url to not require the module environment
def open_url(url, data=None, headers=None, method=None, use_proxy=True,
        force=False, last_mod_time=None, timeout=10, validate_certs=True,
        url_username=None, url_password=None, http_agent=None,
        force_basic_auth=False, follow_redirects='urllib2'):
    '''
    Fetches a file from an HTTP/FTP server using urllib2
    '''
    handlers = []
    ssl_handler = maybe_add_ssl_handler(url, validate_certs)
    if ssl_handler:
        handlers.append(ssl_handler)

    # FIXME: change the following to use the generic_urlparse function
    #        to remove the indexed references for 'parsed'
    parsed = urlparse.urlparse(url)
    if parsed[0] != 'ftp':
        username = url_username

        if username:
            password = url_password
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

        if username and not force_basic_auth:
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()

            # this creates a password manager
            passman.add_password(None, netloc, username, password)

            # because we have put None at the start it will always
            # use this username/password combination for  urls
            # for which `theurl` is a super-url
            authhandler = urllib2.HTTPBasicAuthHandler(passman)

            # create the AuthHandler
            handlers.append(authhandler)

        elif username and force_basic_auth:
            if headers is None:
                headers = {}

            headers["Authorization"] = "Basic %s" % base64.b64encode("%s:%s" % (username, password))

    if not use_proxy:
        proxyhandler = urllib2.ProxyHandler({})
        handlers.append(proxyhandler)

    # pre-2.6 versions of python cannot use the custom https
    # handler, since the socket class is lacking create_connection.
    # Some python builds lack HTTPS support.
    if hasattr(socket, 'create_connection') and CustomHTTPSHandler:
        handlers.append(CustomHTTPSHandler)

    handlers.append(RedirectHandlerFactory(follow_redirects, validate_certs))

    opener = urllib2.build_opener(*handlers)
    urllib2.install_opener(opener)

    if method:
        if method.upper() not in ('OPTIONS','GET','HEAD','POST','PUT','DELETE','TRACE','CONNECT','PATCH'):
            raise ConnectionError('invalid HTTP request method; %s' % method.upper())
        request = RequestWithMethod(url, method.upper(), data)
    else:
        request = urllib2.Request(url, data)

    # add the custom agent header, to help prevent issues
    # with sites that block the default urllib agent string
    request.add_header('User-agent', http_agent)

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
            raise ValueError("headers provided to fetch_url() must be a dict")
        for header in headers:
            request.add_header(header, headers[header])

    urlopen_args = [request, None]
    if sys.version_info >= (2,6,0):
        # urlopen in python prior to 2.6.0 did not
        # have a timeout parameter
        urlopen_args.append(timeout)

    if HAS_SSLCONTEXT and not validate_certs:
        # In 2.7.9, the default context validates certificates
        context = SSLContext(ssl.PROTOCOL_SSLv23)
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        urlopen_args += (None, None, None, context)

    r = urllib2.urlopen(*urlopen_args)
    return r

#
# Module-related functions
#

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
        force_basic_auth = dict(required=False, type='bool', default='no'),

    )

def fetch_url(module, url, data=None, headers=None, method=None,
              use_proxy=True, force=False, last_mod_time=None, timeout=10):
    '''
    Fetches a file from an HTTP/FTP server using urllib2.  Requires the module environment
    '''

    if not HAS_URLLIB2:
        module.fail_json(msg='urllib2 is not installed')
    elif not HAS_URLPARSE:
        module.fail_json(msg='urlparse is not installed')

    # Get validate_certs from the module params
    validate_certs = module.params.get('validate_certs', True)

    username = module.params.get('url_username', '')
    password = module.params.get('url_password', '')
    http_agent = module.params.get('http_agent', None)
    force_basic_auth = module.params.get('force_basic_auth', '')

    follow_redirects = module.params.get('follow_redirects', 'urllib2')

    r = None
    info = dict(url=url)
    try:
        r = open_url(url, data=data, headers=headers, method=method,
                     use_proxy=use_proxy, force=force, last_mod_time=last_mod_time, timeout=timeout,
                     validate_certs=validate_certs, url_username=username,
                     url_password=password, http_agent=http_agent, force_basic_auth=force_basic_auth,
                     follow_redirects=follow_redirects)
        info.update(r.info())
        info['url'] = r.geturl()  # The URL goes in too, because of redirects.
        info.update(dict(msg="OK (%s bytes)" % r.headers.get('Content-Length', 'unknown'), status=200))
    except NoSSLError, e:
        distribution = get_distribution()
        if distribution.lower() == 'redhat':
            module.fail_json(msg='%s. You can also install python-ssl from EPEL' % str(e))
        else:
            module.fail_json(msg='%s' % str(e))
    except (ConnectionError, ValueError), e:
        module.fail_json(msg=str(e))
    except urllib2.HTTPError, e:
        info.update(dict(msg=str(e), status=e.code, **e.info()))
    except urllib2.URLError, e:
        code = int(getattr(e, 'code', -1))
        info.update(dict(msg="Request failed: %s" % str(e), status=code))
    except socket.error, e:
        info.update(dict(msg="Connection failure: %s" % str(e), status=-1))
    except Exception, e:
        info.update(dict(msg="An unknown error occurred: %s" % str(e), status=-1))

    return r, info
