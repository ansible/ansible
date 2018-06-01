# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com>, 2015
#
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
#
# The match_hostname function and supporting code is under the terms and
# conditions of the Python Software Foundation License.  They were taken from
# the Python3 standard library and adapted for use in Python2.  See comments in the
# source for which code precisely is under this License.
#
# PSF License (see licenses/PSF-license.txt or https://opensource.org/licenses/Python-2.0)


'''
The **urls** utils module offers a replacement for the urllib2 python library.

urllib2 is the python stdlib way to retrieve files from the Internet but it
lacks some security features (around verifying SSL certificates) that users
should care about in most situations. Using the functions in this module corrects
deficiencies in the urllib2 module wherever possible.

There are also third-party libraries (for instance, requests) which can be used
to replace urllib2 with a more secure library. However, all third party libraries
require that the library be installed on the managed machine. That is an extra step
for users making use of a module. If possible, avoid third party libraries by using
this code instead.
'''

import base64
import netrc
import os
import platform
import re
import socket
import sys
import tempfile
import traceback

try:
    import httplib
except ImportError:
    # Python 3
    import http.client as httplib

import ansible.module_utils.six.moves.http_cookiejar as cookiejar
import ansible.module_utils.six.moves.urllib.request as urllib_request
import ansible.module_utils.six.moves.urllib.error as urllib_error

from ansible.module_utils.six import PY3

from ansible.module_utils.basic import get_distribution
from ansible.module_utils._text import to_bytes, to_native, to_text

try:
    # python3
    import urllib.request as urllib_request
    from urllib.request import AbstractHTTPHandler
except ImportError:
    # python2
    import urllib2 as urllib_request
    from urllib2 import AbstractHTTPHandler

urllib_request.HTTPRedirectHandler.http_error_308 = urllib_request.HTTPRedirectHandler.http_error_307

try:
    from ansible.module_utils.six.moves.urllib.parse import urlparse, urlunparse
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

# SNI Handling for python < 2.7.9 with urllib3 support
try:
    # urllib3>=1.15
    HAS_URLLIB3_SSL_WRAP_SOCKET = False
    try:
        from urllib3.contrib.pyopenssl import PyOpenSSLContext
    except ImportError:
        from requests.packages.urllib3.contrib.pyopenssl import PyOpenSSLContext
    HAS_URLLIB3_PYOPENSSLCONTEXT = True
except ImportError:
    # urllib3<1.15,>=1.6
    HAS_URLLIB3_PYOPENSSLCONTEXT = False
    try:
        try:
            from urllib3.contrib.pyopenssl import ssl_wrap_socket
        except ImportError:
            from requests.packages.urllib3.contrib.pyopenssl import ssl_wrap_socket
        HAS_URLLIB3_SSL_WRAP_SOCKET = True
    except ImportError:
        pass

# Select a protocol that includes all secure tls protocols
# Exclude insecure ssl protocols if possible

if HAS_SSL:
    # If we can't find extra tls methods, ssl.PROTOCOL_TLSv1 is sufficient
    PROTOCOL = ssl.PROTOCOL_TLSv1
if not HAS_SSLCONTEXT and HAS_SSL:
    try:
        import ctypes
        import ctypes.util
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


LOADED_VERIFY_LOCATIONS = set()

HAS_MATCH_HOSTNAME = True
try:
    from ssl import match_hostname, CertificateError
except ImportError:
    try:
        from backports.ssl_match_hostname import match_hostname, CertificateError
    except ImportError:
        HAS_MATCH_HOSTNAME = False

if not HAS_MATCH_HOSTNAME:
    # The following block of code is under the terms and conditions of the
    # Python Software Foundation License

    """The match_hostname() function from Python 3.4, essential when using SSL."""

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
            raise CertificateError("hostname %r " "doesn't match either of %s" % (hostname, ', '.join(map(repr, dnsnames))))
        elif len(dnsnames) == 1:
            raise CertificateError("hostname %r doesn't match %r" % (hostname, dnsnames[0]))
        else:
            raise CertificateError("no appropriate commonName or subjectAltName fields were found")

    # End of Python Software Foundation Licensed code

    HAS_MATCH_HOSTNAME = True


# This is a dummy cacert provided for Mac OS since you need at least 1
# ca cert, regardless of validity, for Python on Mac OS to use the
# keychain functionality in OpenSSL for validating SSL certificates.
# See: http://mercurial.selenic.com/wiki/CACertificates#Mac_OS_X_10.6_and_higher
b_DUMMY_CA_CERT = b"""-----BEGIN CERTIFICATE-----
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
if hasattr(httplib, 'HTTPSConnection') and hasattr(urllib_request, 'HTTPSHandler'):
    class CustomHTTPSConnection(httplib.HTTPSConnection):
        def __init__(self, *args, **kwargs):
            httplib.HTTPSConnection.__init__(self, *args, **kwargs)
            self.context = None
            if HAS_SSLCONTEXT:
                self.context = create_default_context()
            elif HAS_URLLIB3_PYOPENSSLCONTEXT:
                self.context = PyOpenSSLContext(PROTOCOL)
            if self.context and self.cert_file:
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

            if HAS_SSLCONTEXT or HAS_URLLIB3_PYOPENSSLCONTEXT:
                self.sock = self.context.wrap_socket(sock, server_hostname=server_hostname)
            elif HAS_URLLIB3_SSL_WRAP_SOCKET:
                self.sock = ssl_wrap_socket(sock, keyfile=self.key_file, cert_reqs=ssl.CERT_NONE, certfile=self.cert_file, ssl_version=PROTOCOL,
                                            server_hostname=server_hostname)
            else:
                self.sock = ssl.wrap_socket(sock, keyfile=self.key_file, certfile=self.cert_file, ssl_version=PROTOCOL)

    class CustomHTTPSHandler(urllib_request.HTTPSHandler):

        def https_open(self, req):
            return self.do_open(CustomHTTPSConnection, req)

        https_request = AbstractHTTPHandler.do_request_


class HTTPSClientAuthHandler(urllib_request.HTTPSHandler):
    '''Handles client authentication via cert/key

    This is a fairly lightweight extension on HTTPSHandler, and can be used
    in place of HTTPSHandler
    '''

    def __init__(self, client_cert=None, client_key=None, **kwargs):
        urllib_request.HTTPSHandler.__init__(self, **kwargs)
        self.client_cert = client_cert
        self.client_key = client_key

    def https_open(self, req):
        return self.do_open(self._build_https_connection, req)

    def _build_https_connection(self, host, **kwargs):
        kwargs.update({
            'cert_file': self.client_cert,
            'key_file': self.client_key,
        })
        try:
            kwargs['context'] = self._context
        except AttributeError:
            pass
        return httplib.HTTPSConnection(host, **kwargs)


class ParseResultDottedDict(dict):
    '''
    A dict that acts similarly to the ParseResult named tuple from urllib
    '''
    def __init__(self, *args, **kwargs):
        super(ParseResultDottedDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def as_list(self):
        '''
        Generate a list from this dict, that looks like the ParseResult named tuple
        '''
        return [self.get(k, None) for k in ('scheme', 'netloc', 'path', 'params', 'query', 'fragment')]


def generic_urlparse(parts):
    '''
    Returns a dictionary of url parts as parsed by urlparse,
    but accounts for the fact that older versions of that
    library do not support named attributes (ie. .netloc)
    '''
    generic_parts = ParseResultDottedDict()
    if hasattr(parts, 'netloc'):
        # urlparse is newer, just read the fields straight
        # from the parts object
        generic_parts['scheme'] = parts.scheme
        generic_parts['netloc'] = parts.netloc
        generic_parts['path'] = parts.path
        generic_parts['params'] = parts.params
        generic_parts['query'] = parts.query
        generic_parts['fragment'] = parts.fragment
        generic_parts['username'] = parts.username
        generic_parts['password'] = parts.password
        generic_parts['hostname'] = parts.hostname
        generic_parts['port'] = parts.port
    else:
        # we have to use indexes, and then parse out
        # the other parts not supported by indexing
        generic_parts['scheme'] = parts[0]
        generic_parts['netloc'] = parts[1]
        generic_parts['path'] = parts[2]
        generic_parts['params'] = parts[3]
        generic_parts['query'] = parts[4]
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
                # the capture group above includes the @, so remove it
                # and then split it up based on the first ':' found
                auth = auth[:-1]
                username, password = auth.split(':', 1)
            else:
                username = password = None
            generic_parts['username'] = username
            generic_parts['password'] = password
            generic_parts['hostname'] = hostname
            generic_parts['port'] = port
        except:
            generic_parts['username'] = None
            generic_parts['password'] = None
            generic_parts['hostname'] = parts[1]
            generic_parts['port'] = None
    return generic_parts


class RequestWithMethod(urllib_request.Request):
    '''
    Workaround for using DELETE/PUT/etc with urllib2
    Originally contained in library/net_infrastructure/dnsmadeeasy
    '''

    def __init__(self, url, method, data=None, headers=None, origin_req_host=None, unverifiable=True):
        if headers is None:
            headers = {}
        self._method = method.upper()
        urllib_request.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)

    def get_method(self):
        if self._method:
            return self._method
        else:
            return urllib_request.Request.get_method(self)


def RedirectHandlerFactory(follow_redirects=None, validate_certs=True):
    """This is a class factory that closes over the value of
    ``follow_redirects`` so that the RedirectHandler class has access to
    that value without having to use globals, and potentially cause problems
    where ``open_url`` or ``fetch_url`` are used multiple times in a module.
    """

    class RedirectHandler(urllib_request.HTTPRedirectHandler):
        """This is an implementation of a RedirectHandler to match the
        functionality provided by httplib2. It will utilize the value of
        ``follow_redirects`` that is passed into ``RedirectHandlerFactory``
        to determine how redirects should be handled in urllib2.
        """

        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            handler = maybe_add_ssl_handler(newurl, validate_certs)
            if handler:
                urllib_request._opener.add_handler(handler)

            # Preserve urllib2 compatibility
            if follow_redirects == 'urllib2':
                return urllib_request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, hdrs, newurl)

            # Handle disabled redirects
            elif follow_redirects in ['no', 'none', False]:
                raise urllib_error.HTTPError(newurl, code, msg, hdrs, fp)

            method = req.get_method()

            # Handle non-redirect HTTP status or invalid follow_redirects
            if follow_redirects in ['all', 'yes', True]:
                if code < 300 or code >= 400:
                    raise urllib_error.HTTPError(req.get_full_url(), code, msg, hdrs, fp)
            elif follow_redirects == 'safe':
                if code < 300 or code >= 400 or method not in ('GET', 'HEAD'):
                    raise urllib_error.HTTPError(req.get_full_url(), code, msg, hdrs, fp)
            else:
                raise urllib_error.HTTPError(req.get_full_url(), code, msg, hdrs, fp)

            try:
                # Python 2-3.3
                data = req.get_data()
                origin_req_host = req.get_origin_req_host()
            except AttributeError:
                # Python 3.4+
                data = req.data
                origin_req_host = req.origin_req_host

            # Be conciliant with URIs containing a space
            newurl = newurl.replace(' ', '%20')

            # Suport redirect with payload and original headers
            if code in (307, 308):
                # Preserve payload and headers
                headers = req.headers
            else:
                # Do not preserve payload and filter headers
                data = None
                headers = dict((k, v) for k, v in req.headers.items()
                               if k.lower() not in ("content-length", "content-type", "transfer-encoding"))

                # http://tools.ietf.org/html/rfc7231#section-6.4.4
                if code == 303 and method != 'HEAD':
                    method = 'GET'

                # Do what the browsers do, despite standards...
                # First, turn 302s into GETs.
                if code == 302 and method != 'HEAD':
                    method = 'GET'

                # Second, if a POST is responded to with a 301, turn it into a GET.
                if code == 301 and method == 'POST':
                    method = 'GET'

            return RequestWithMethod(newurl,
                                     method=method,
                                     headers=headers,
                                     data=data,
                                     origin_req_host=origin_req_host,
                                     unverifiable=True,
                                     )

    return RedirectHandler


def build_ssl_validation_error(hostname, port, paths, exc=None):
    '''Inteligently build out the SSLValidationError based on what support
    you have installed
    '''

    msg = [
        ('Failed to validate the SSL certificate for %s:%s.'
         ' Make sure your managed systems have a valid CA'
         ' certificate installed.')
    ]
    if not HAS_SSLCONTEXT:
        msg.append('If the website serving the url uses SNI you need'
                   ' python >= 2.7.9 on your managed machine')
        msg.append(' (the python executable used (%s) is version: %s)' %
                   (sys.executable, ''.join(sys.version.splitlines())))
        if not HAS_URLLIB3_PYOPENSSLCONTEXT or not HAS_URLLIB3_SSL_WRAP_SOCKET:
            msg.append('or you can install the `urllib3`, `pyOpenSSL`,'
                       ' `ndg-httpsclient`, and `pyasn1` python modules')

        msg.append('to perform SNI verification in python >= 2.6.')

    msg.append('You can use validate_certs=False if you do'
               ' not need to confirm the servers identity but this is'
               ' unsafe and not recommended.'
               ' Paths checked for this platform: %s.')

    if exc:
        msg.append('The exception msg was: %s.' % to_native(exc))

    raise SSLValidationError(' '.join(msg) % (hostname, port, ", ".join(paths)))


class SSLValidationHandler(urllib_request.BaseHandler):
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

        system = to_text(platform.system(), errors='surrogate_or_strict')
        # build a list of paths to check for .crt/.pem files
        # based on the platform type
        paths_checked.append('/etc/ssl/certs')
        if system == u'Linux':
            paths_checked.append('/etc/pki/ca-trust/extracted/pem')
            paths_checked.append('/etc/pki/tls/certs')
            paths_checked.append('/usr/share/ca-certificates/cacert.org')
        elif system == u'FreeBSD':
            paths_checked.append('/usr/local/share/certs')
        elif system == u'OpenBSD':
            paths_checked.append('/etc/ssl')
        elif system == u'NetBSD':
            ca_certs.append('/etc/openssl/certs')
        elif system == u'SunOS':
            paths_checked.append('/opt/local/etc/openssl/certs')

        # fall back to a user-deployed cert in a standard
        # location if the OS platform one is not available
        paths_checked.append('/etc/ansible')

        tmp_fd, tmp_path = tempfile.mkstemp()
        to_add_fd, to_add_path = tempfile.mkstemp()
        to_add = False

        # Write the dummy ca cert if we are running on Mac OS X
        if system == u'Darwin':
            os.write(tmp_fd, b_DUMMY_CA_CERT)
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
                    if os.path.isfile(full_path) and os.path.splitext(f)[1] in ('.crt', '.pem'):
                        try:
                            cert_file = open(full_path, 'rb')
                            cert = cert_file.read()
                            cert_file.close()
                            os.write(tmp_fd, cert)
                            os.write(tmp_fd, b'\n')
                            if full_path not in LOADED_VERIFY_LOCATIONS:
                                to_add = True
                                os.write(to_add_fd, cert)
                                os.write(to_add_fd, b'\n')
                                LOADED_VERIFY_LOCATIONS.add(full_path)
                        except (OSError, IOError):
                            pass

        if not to_add:
            try:
                os.remove(to_add_path)
            except OSError:
                pass
            to_add_path = None
        return (tmp_path, to_add_path, paths_checked)

    def validate_proxy_response(self, response, valid_codes=None):
        '''
        make sure we get back a valid code from the proxy
        '''
        valid_codes = [200] if valid_codes is None else valid_codes

        try:
            (http_version, resp_code, msg) = re.match(br'(HTTP/\d\.\d) (\d\d\d) (.*)', response).groups()
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
            netloc = urlparse(url).netloc

            for host in env_no_proxy:
                if netloc.endswith(host) or netloc.split(':')[0].endswith(host):
                    # Our requested URL matches something in no_proxy, so don't
                    # use the proxy for this
                    return False
        return True

    def _make_context(self, to_add_ca_cert_path):
        if HAS_SSLCONTEXT:
            context = create_default_context()
        elif HAS_URLLIB3_PYOPENSSLCONTEXT:
            context = PyOpenSSLContext(PROTOCOL)
        else:
            raise NotImplementedError('Host libraries are too old to support creating an sslcontext')

        if to_add_ca_cert_path:
            context.load_verify_locations(to_add_ca_cert_path)
        return context

    def http_request(self, req):
        tmp_ca_cert_path, to_add_ca_cert_path, paths_checked = self.get_ca_certs()
        https_proxy = os.environ.get('https_proxy')
        context = None
        try:
            context = self._make_context(to_add_ca_cert_path)
        except Exception:
            # We'll make do with no context below
            pass

        # Detect if 'no_proxy' environment variable is set and if our URL is included
        use_proxy = self.detect_no_proxy(req.get_full_url())

        if not use_proxy:
            # ignore proxy settings for this host request
            if tmp_ca_cert_path:
                try:
                    os.remove(tmp_ca_cert_path)
                except OSError:
                    pass
            if to_add_ca_cert_path:
                try:
                    os.remove(to_add_ca_cert_path)
                except OSError:
                    pass
            return req

        try:
            if https_proxy:
                proxy_parts = generic_urlparse(urlparse(https_proxy))
                port = proxy_parts.get('port') or 443
                s = socket.create_connection((proxy_parts.get('hostname'), port))
                if proxy_parts.get('scheme') == 'http':
                    s.sendall(to_bytes(self.CONNECT_COMMAND % (self.hostname, self.port), errors='surrogate_or_strict'))
                    if proxy_parts.get('username'):
                        credentials = "%s:%s" % (proxy_parts.get('username', ''), proxy_parts.get('password', ''))
                        s.sendall(b'Proxy-Authorization: Basic %s\r\n' % base64.b64encode(to_bytes(credentials, errors='surrogate_or_strict')).strip())
                    s.sendall(b'\r\n')
                    connect_result = b""
                    while connect_result.find(b"\r\n\r\n") <= 0:
                        connect_result += s.recv(4096)
                        # 128 kilobytes of headers should be enough for everyone.
                        if len(connect_result) > 131072:
                            raise ProxyError('Proxy sent too verbose headers. Only 128KiB allowed.')
                    self.validate_proxy_response(connect_result)
                    if context:
                        ssl_s = context.wrap_socket(s, server_hostname=self.hostname)
                    elif HAS_URLLIB3_SSL_WRAP_SOCKET:
                        ssl_s = ssl_wrap_socket(s, ca_certs=tmp_ca_cert_path, cert_reqs=ssl.CERT_REQUIRED, ssl_version=PROTOCOL, server_hostname=self.hostname)
                    else:
                        ssl_s = ssl.wrap_socket(s, ca_certs=tmp_ca_cert_path, cert_reqs=ssl.CERT_REQUIRED, ssl_version=PROTOCOL)
                        match_hostname(ssl_s.getpeercert(), self.hostname)
                else:
                    raise ProxyError('Unsupported proxy scheme: %s. Currently ansible only supports HTTP proxies.' % proxy_parts.get('scheme'))
            else:
                s = socket.create_connection((self.hostname, self.port))
                if context:
                    ssl_s = context.wrap_socket(s, server_hostname=self.hostname)
                elif HAS_URLLIB3_SSL_WRAP_SOCKET:
                    ssl_s = ssl_wrap_socket(s, ca_certs=tmp_ca_cert_path, cert_reqs=ssl.CERT_REQUIRED, ssl_version=PROTOCOL, server_hostname=self.hostname)
                else:
                    ssl_s = ssl.wrap_socket(s, ca_certs=tmp_ca_cert_path, cert_reqs=ssl.CERT_REQUIRED, ssl_version=PROTOCOL)
                    match_hostname(ssl_s.getpeercert(), self.hostname)
            # close the ssl connection
            # ssl_s.unwrap()
            s.close()
        except (ssl.SSLError, CertificateError) as e:
            build_ssl_validation_error(self.hostname, self.port, paths_checked, e)
        except socket.error as e:
            raise ConnectionError('Failed to connect to %s at port %s: %s' % (self.hostname, self.port, to_native(e)))

        try:
            # cleanup the temp file created, don't worry
            # if it fails for some reason
            os.remove(tmp_ca_cert_path)
        except:
            pass

        try:
            # cleanup the temp file created, don't worry
            # if it fails for some reason
            if to_add_ca_cert_path:
                os.remove(to_add_ca_cert_path)
        except:
            pass

        return req

    https_request = http_request


def maybe_add_ssl_handler(url, validate_certs):
    parsed = generic_urlparse(urlparse(url))
    if parsed.scheme == 'https' and validate_certs:
        if not HAS_SSL:
            raise NoSSLError('SSL validation is not available in your version of python. You can use validate_certs=False,'
                             ' however this is unsafe and not recommended')

        # do the cert validation
        netloc = parsed.netloc
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


class Request:
    def __init__(self, headers=None, use_proxy=True, force=False, timeout=10, validate_certs=True,
                 url_username=None, url_password=None, http_agent=None, force_basic_auth=False,
                 follow_redirects='urllib2', client_cert=None, client_key=None, cookies=None):
        """This class works somewhat similarly to the ``Session`` class of from requests
        by defining a cookiejar that an be used across requests as well as cascaded defaults that
        can apply to repeated requests

        For documentation of params, see ``Request.open``

        >>> from ansible.module_utils.urls import Request
        >>> r = Request()
        >>> r.open('GET', 'http://httpbin.org/cookies/set?k1=v1').read()
        '{\n  "cookies": {\n    "k1": "v1"\n  }\n}\n'
        >>> r = Request(url_username='user', url_password='passwd')
        >>> r.open('GET', 'http://httpbin.org/basic-auth/user/passwd').read()
        '{\n  "authenticated": true, \n  "user": "user"\n}\n'
        >>> r = Request(headers=dict(foo='bar'))
        >>> r.open('GET', 'http://httpbin.org/get', headers=dict(baz='qux')).read()

        """

        self.headers = headers or {}
        if not isinstance(self.headers, dict):
            raise ValueError("headers must be a dict")
        self.use_proxy = use_proxy
        self.force = force
        self.timeout = timeout
        self.validate_certs = validate_certs
        self.url_username = url_username
        self.url_password = url_password
        self.http_agent = http_agent
        self.force_basic_auth = force_basic_auth
        self.follow_redirects = follow_redirects
        self.client_cert = client_cert
        self.client_key = client_key
        if isinstance(cookies, cookiejar.CookieJar):
            self.cookies = cookies
        else:
            self.cookies = cookiejar.CookieJar()

    def _fallback(self, value, fallback):
        if value is None:
            return fallback
        return value

    def open(self, method, url, data=None, headers=None, use_proxy=None,
             force=None, last_mod_time=None, timeout=None, validate_certs=None,
             url_username=None, url_password=None, http_agent=None,
             force_basic_auth=None, follow_redirects=None,
             client_cert=None, client_key=None, cookies=None):
        """
        Sends a request via HTTP(S) or FTP using urllib2 (Python2) or urllib (Python3)

        Does not require the module environment

        Returns :class:`HTTPResponse` object.

        :arg method: method for the request
        :arg url: URL to request

        :kwarg data: (optional) bytes, or file-like object to send
            in the body of the request
        :kwarg headers: (optional) Dictionary of HTTP Headers to send with the
            request
        :kwarg use_proxy: (optional) Boolean of whether or not to use proxy
        :kwarg force: (optional) Boolean of whether or not to set `cache-control: no-cache` header
        :kwarg last_mod_time: (optional) Datetime object to use when setting If-Modified-Since header
        :kwarg timeout: (optional) How long to wait for the server to send
            data before giving up, as a float
        :kwarg validate_certs: (optional) Booleani that controls whether we verify
            the server's TLS certificate
        :kwarg url_username: (optional) String of the user to use when authenticating
        :kwarg url_password: (optional) String of the password to use when authenticating
        :kwarg http_agent: (optional) String of the User-Agent to use in the request
        :kwarg force_basic_auth: (optional) Boolean determining if auth header should be sent in the initial request
        :kwarg follow_redirects: (optional) String of urllib2, all/yes, safe, none to determine how redirects are
            followed, see RedirectHandlerFactory for more information
        :kwarg client_cert: (optional) PEM formatted certificate chain file to be used for SSL client authentication.
            This file can also include the key as well, and if the key is included, client_key is not required
        :kwarg client_key: (optional) PEM formatted file that contains your private key to be used for SSL client
            authentication. If client_cert contains both the certificate and key, this option is not required
        :kwarg cookies: (optional) CookieJar object to send with the
            request
        :returns: HTTPResponse
        """

        method = method.upper()

        if headers is None:
            headers = {}
        elif not isinstance(headers, dict):
            raise ValueError("headers must be a dict")
        headers = dict(self.headers, **headers)

        use_proxy = self._fallback(use_proxy, self.use_proxy)
        force = self._fallback(force, self.force)
        timeout = self._fallback(timeout, self.timeout)
        validate_certs = self._fallback(validate_certs, self.validate_certs)
        url_username = self._fallback(url_username, self.url_username)
        url_password = self._fallback(url_password, self.url_password)
        http_agent = self._fallback(http_agent, self.http_agent)
        force_basic_auth = self._fallback(force_basic_auth, self.force_basic_auth)
        follow_redirects = self._fallback(follow_redirects, self.follow_redirects)
        client_cert = self._fallback(client_cert, self.client_cert)
        client_key = self._fallback(client_key, self.client_key)
        cookies = self._fallback(cookies, self.cookies)

        handlers = []
        ssl_handler = maybe_add_ssl_handler(url, validate_certs)
        if ssl_handler:
            handlers.append(ssl_handler)

        parsed = generic_urlparse(urlparse(url))
        if parsed.scheme != 'ftp':
            username = url_username

            if username:
                password = url_password
                netloc = parsed.netloc
            elif '@' in parsed.netloc:
                credentials, netloc = parsed.netloc.split('@', 1)
                if ':' in credentials:
                    username, password = credentials.split(':', 1)
                else:
                    username = credentials
                    password = ''

                parsed_list = parsed.as_list()
                parsed_list[1] = netloc

                # reconstruct url without credentials
                url = urlunparse(parsed_list)

            if username and not force_basic_auth:
                passman = urllib_request.HTTPPasswordMgrWithDefaultRealm()

                # this creates a password manager
                passman.add_password(None, netloc, username, password)

                # because we have put None at the start it will always
                # use this username/password combination for  urls
                # for which `theurl` is a super-url
                authhandler = urllib_request.HTTPBasicAuthHandler(passman)
                digest_authhandler = urllib_request.HTTPDigestAuthHandler(passman)

                # create the AuthHandler
                handlers.append(authhandler)
                handlers.append(digest_authhandler)

            elif username and force_basic_auth:
                headers["Authorization"] = basic_auth_header(username, password)

            else:
                try:
                    rc = netrc.netrc(os.environ.get('NETRC'))
                    login = rc.authenticators(parsed.hostname)
                except IOError:
                    login = None

                if login:
                    username, _, password = login
                    if username and password:
                        headers["Authorization"] = basic_auth_header(username, password)

        if not use_proxy:
            proxyhandler = urllib_request.ProxyHandler({})
            handlers.append(proxyhandler)

        if HAS_SSLCONTEXT and not validate_certs:
            # In 2.7.9, the default context validates certificates
            context = SSLContext(ssl.PROTOCOL_SSLv23)
            if ssl.OP_NO_SSLv2:
                context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.verify_mode = ssl.CERT_NONE
            context.check_hostname = False
            handlers.append(HTTPSClientAuthHandler(client_cert=client_cert,
                                                   client_key=client_key,
                                                   context=context))
        elif client_cert:
            handlers.append(HTTPSClientAuthHandler(client_cert=client_cert,
                                                   client_key=client_key))

        # pre-2.6 versions of python cannot use the custom https
        # handler, since the socket class is lacking create_connection.
        # Some python builds lack HTTPS support.
        if hasattr(socket, 'create_connection') and CustomHTTPSHandler:
            handlers.append(CustomHTTPSHandler)

        handlers.append(RedirectHandlerFactory(follow_redirects, validate_certs))

        # add some nicer cookie handling
        if cookies is not None:
            handlers.append(urllib_request.HTTPCookieProcessor(cookies))

        opener = urllib_request.build_opener(*handlers)
        urllib_request.install_opener(opener)

        data = to_bytes(data, nonstring='passthru')
        if method not in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT', 'PATCH'):
            raise ConnectionError('invalid HTTP request method; %s' % method)
        request = RequestWithMethod(url, method, data)

        # add the custom agent header, to help prevent issues
        # with sites that block the default urllib agent string
        if http_agent:
            request.add_header('User-agent', http_agent)

        # Cache control
        # Either we directly force a cache refresh
        if force:
            request.add_header('cache-control', 'no-cache')
        # or we do it if the original is more recent than our copy
        elif last_mod_time:
            tstamp = last_mod_time.strftime('%a, %d %b %Y %H:%M:%S +0000')
            request.add_header('If-Modified-Since', tstamp)

        # user defined headers now, which may override things we've set above
        for header in headers:
            request.add_header(header, headers[header])

        urlopen_args = [request, None]
        if sys.version_info >= (2, 6, 0):
            # urlopen in python prior to 2.6.0 did not
            # have a timeout parameter
            urlopen_args.append(timeout)

        r = urllib_request.urlopen(*urlopen_args)
        return r

    def get(self, url, **kwargs):
        r"""Sends a GET request. Returns :class:`HTTPResponse` object.

        :arg url: URL to request
        :kwarg \*\*kwargs: Optional arguments that ``open`` takes.
        :returns: HTTPResponse
        """

        return self.open('GET', url, **kwargs)

    def options(self, url, **kwargs):
        r"""Sends a OPTIONS request. Returns :class:`HTTPResponse` object.

        :arg url: URL to request
        :kwarg \*\*kwargs: Optional arguments that ``open`` takes.
        :returns: HTTPResponse
        """

        return self.open('OPTIONS', url, **kwargs)

    def head(self, url, **kwargs):
        r"""Sends a HEAD request. Returns :class:`HTTPResponse` object.

        :arg url: URL to request
        :kwarg \*\*kwargs: Optional arguments that ``open`` takes.
        :returns: HTTPResponse
        """

        return self.open('HEAD', url, **kwargs)

    def post(self, url, data=None, **kwargs):
        r"""Sends a POST request. Returns :class:`HTTPResponse` object.

        :arg url: URL to request.
        :kwarg data: (optional) bytes, or file-like object to send in the body of the request.
        :kwarg \*\*kwargs: Optional arguments that ``open`` takes.
        :returns: HTTPResponse
        """

        return self.open('POST', url, data=data, **kwargs)

    def put(self, url, data=None, **kwargs):
        r"""Sends a PUT request. Returns :class:`HTTPResponse` object.

        :arg url: URL to request.
        :kwarg data: (optional) bytes, or file-like object to send in the body of the request.
        :kwarg \*\*kwargs: Optional arguments that ``open`` takes.
        :returns: HTTPResponse
        """

        return self.open('PUT', url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        r"""Sends a PATCH request. Returns :class:`HTTPResponse` object.

        :arg url: URL to request.
        :kwarg data: (optional) bytes, or file-like object to send in the body of the request.
        :kwarg \*\*kwargs: Optional arguments that ``open`` takes.
        :returns: HTTPResponse
        """

        return self.open('PATCH', url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        r"""Sends a DELETE request. Returns :class:`HTTPResponse` object.

        :arg url: URL to request
        :kwargs \*\*kwargs: Optional arguments that ``open`` takes.
        :returns: HTTPResponse
        """

        return self.open('DELETE', url, **kwargs)


def open_url(url, data=None, headers=None, method=None, use_proxy=True,
             force=False, last_mod_time=None, timeout=10, validate_certs=True,
             url_username=None, url_password=None, http_agent=None,
             force_basic_auth=False, follow_redirects='urllib2',
             client_cert=None, client_key=None, cookies=None):
    '''
    Sends a request via HTTP(S) or FTP using urllib2 (Python2) or urllib (Python3)

    Does not require the module environment
    '''
    method = method or 'GET'
    return Request().open(method, url, data=data, headers=headers, use_proxy=use_proxy,
                          force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                          url_username=url_username, url_password=url_password, http_agent=http_agent,
                          force_basic_auth=force_basic_auth, follow_redirects=follow_redirects,
                          client_cert=client_cert, client_key=client_key, cookies=cookies)


#
# Module-related functions
#


def basic_auth_header(username, password):
    """Takes a username and password and returns a byte string suitable for
    using as value of an Authorization header to do basic auth.
    """
    return b"Basic %s" % base64.b64encode(to_bytes("%s:%s" % (username, password), errors='surrogate_or_strict'))


def url_argument_spec():
    '''
    Creates an argument spec that can be used with any module
    that will be requesting content via urllib/urllib2
    '''
    return dict(
        url=dict(),
        force=dict(default='no', aliases=['thirsty'], type='bool'),
        http_agent=dict(default='ansible-httpget'),
        use_proxy=dict(default='yes', type='bool'),
        validate_certs=dict(default='yes', type='bool'),
        url_username=dict(required=False),
        url_password=dict(required=False, no_log=True),
        force_basic_auth=dict(required=False, type='bool', default='no'),
        client_cert=dict(required=False, type='path', default=None),
        client_key=dict(required=False, type='path', default=None),
    )


def fetch_url(module, url, data=None, headers=None, method=None,
              use_proxy=True, force=False, last_mod_time=None, timeout=10):
    """Sends a request via HTTP(S) or FTP (needs the module as parameter)

    :arg module: The AnsibleModule (used to get username, password etc. (s.b.).
    :arg url:             The url to use.

    :kwarg data:          The data to be sent (in case of POST/PUT).
    :kwarg headers:       A dict with the request headers.
    :kwarg method:        "POST", "PUT", etc.
    :kwarg boolean use_proxy:     Default: True
    :kwarg boolean force: If True: Do not get a cached copy (Default: False)
    :kwarg last_mod_time: Default: None
    :kwarg int timeout:   Default: 10

    :returns: A tuple of (**response**, **info**). Use ``response.read()`` to read the data.
        The **info** contains the 'status' and other meta data. When a HttpError (status > 400)
        occurred then ``info['body']`` contains the error response data::

    Example::

        data={...}
        resp, info = fetch_url(module,
                               "http://example.com",
                               data=module.jsonify(data),
                               headers={'Content-type': 'application/json'},
                               method="POST")
        status_code = info["status"]
        body = resp.read()
        if status_code >= 400 :
            body = info['body']
    """

    if not HAS_URLPARSE:
        module.fail_json(msg='urlparse is not installed')

    # ensure we use proper tempdir
    old_tempdir = tempfile.tempdir
    tempfile.tempdir = module.tmpdir

    # Get validate_certs from the module params
    validate_certs = module.params.get('validate_certs', True)

    username = module.params.get('url_username', '')
    password = module.params.get('url_password', '')
    http_agent = module.params.get('http_agent', 'ansible-httpget')
    force_basic_auth = module.params.get('force_basic_auth', '')

    follow_redirects = module.params.get('follow_redirects', 'urllib2')

    client_cert = module.params.get('client_cert')
    client_key = module.params.get('client_key')

    cookies = cookiejar.LWPCookieJar()

    r = None
    info = dict(url=url)
    try:
        r = open_url(url, data=data, headers=headers, method=method,
                     use_proxy=use_proxy, force=force, last_mod_time=last_mod_time, timeout=timeout,
                     validate_certs=validate_certs, url_username=username,
                     url_password=password, http_agent=http_agent, force_basic_auth=force_basic_auth,
                     follow_redirects=follow_redirects, client_cert=client_cert,
                     client_key=client_key, cookies=cookies)
        # Lowercase keys, to conform to py2 behavior, so that py3 and py2 are predictable
        info.update(dict((k.lower(), v) for k, v in r.info().items()))

        # Don't be lossy, append header values for duplicate headers
        # In Py2 there is nothing that needs done, py2 does this for us
        if PY3:
            temp_headers = {}
            for name, value in r.headers.items():
                # The same as above, lower case keys to match py2 behavior, and create more consistent results
                name = name.lower()
                if name in temp_headers:
                    temp_headers[name] = ', '.join((temp_headers[name], value))
                else:
                    temp_headers[name] = value
            info.update(temp_headers)

        # parse the cookies into a nice dictionary
        cookie_list = []
        cookie_dict = dict()
        # Python sorts cookies in order of most specific (ie. longest) path first. See ``CookieJar._cookie_attrs``
        # Cookies with the same path are reversed from response order.
        # This code makes no assumptions about that, and accepts the order given by python
        for cookie in cookies:
            cookie_dict[cookie.name] = cookie.value
            cookie_list.append((cookie.name, cookie.value))
        info['cookies_string'] = '; '.join('%s=%s' % c for c in cookie_list)

        info['cookies'] = cookie_dict
        # finally update the result with a message about the fetch
        info.update(dict(msg="OK (%s bytes)" % r.headers.get('Content-Length', 'unknown'), url=r.geturl(), status=r.code))
    except NoSSLError as e:
        distribution = get_distribution()
        if distribution is not None and distribution.lower() == 'redhat':
            module.fail_json(msg='%s. You can also install python-ssl from EPEL' % to_native(e))
        else:
            module.fail_json(msg='%s' % to_native(e))
    except (ConnectionError, ValueError) as e:
        module.fail_json(msg=to_native(e))
    except urllib_error.HTTPError as e:
        try:
            body = e.read()
        except AttributeError:
            body = ''

        # Try to add exception info to the output but don't fail if we can't
        try:
            info.update(dict(**e.info()))
        except:
            pass

        info.update({'msg': to_native(e), 'body': body, 'status': e.code})

    except urllib_error.URLError as e:
        code = int(getattr(e, 'code', -1))
        info.update(dict(msg="Request failed: %s" % to_native(e), status=code))
    except socket.error as e:
        info.update(dict(msg="Connection failure: %s" % to_native(e), status=-1))
    except httplib.BadStatusLine as e:
        info.update(dict(msg="Connection failure: connection was closed before a valid response was received: %s" % to_native(e.line), status=-1))
    except Exception as e:
        info.update(dict(msg="An unknown error occurred: %s" % to_native(e), status=-1),
                    exception=traceback.format_exc())
    finally:
        tempfile.tempdir = old_tempdir

    return r, info
