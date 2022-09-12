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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import base64
import email.mime.multipart
import email.mime.nonmultipart
import email.mime.application
import email.parser
import email.utils
import functools
import io
import mimetypes
import netrc
import os
import platform
import re
import socket
import sys
import tempfile
import traceback
import types

from contextlib import contextmanager

try:
    import gzip
    HAS_GZIP = True
    GZIP_IMP_ERR = None
except ImportError:
    HAS_GZIP = False
    GZIP_IMP_ERR = traceback.format_exc()
    GzipFile = object
else:
    GzipFile = gzip.GzipFile  # type: ignore[assignment,misc]

try:
    import email.policy
except ImportError:
    # Py2
    import email.generator

try:
    import httplib
except ImportError:
    # Python 3
    import http.client as httplib  # type: ignore[no-redef]

import ansible.module_utils.compat.typing as t
import ansible.module_utils.six.moves.http_cookiejar as cookiejar
import ansible.module_utils.six.moves.urllib.error as urllib_error

from ansible.module_utils.common.collections import Mapping, is_sequence
from ansible.module_utils.six import PY2, PY3, string_types
from ansible.module_utils.six.moves import cStringIO
from ansible.module_utils.basic import get_distribution, missing_required_lib
from ansible.module_utils._text import to_bytes, to_native, to_text

try:
    # python3
    import urllib.request as urllib_request
    from urllib.request import AbstractHTTPHandler, BaseHandler
except ImportError:
    # python2
    import urllib2 as urllib_request  # type: ignore[no-redef]
    from urllib2 import AbstractHTTPHandler, BaseHandler  # type: ignore[no-redef]

urllib_request.HTTPRedirectHandler.http_error_308 = urllib_request.HTTPRedirectHandler.http_error_307  # type: ignore[attr-defined]

try:
    from ansible.module_utils.six.moves.urllib.parse import urlparse, urlunparse, unquote
    HAS_URLPARSE = True
except Exception:
    HAS_URLPARSE = False

try:
    import ssl
    HAS_SSL = True
except Exception:
    HAS_SSL = False

try:
    # SNI Handling needs python2.7.9's SSLContext
    from ssl import create_default_context, SSLContext
    HAS_SSLCONTEXT = True
except ImportError:
    HAS_SSLCONTEXT = False

# SNI Handling for python < 2.7.9 with urllib3 support
HAS_URLLIB3_PYOPENSSLCONTEXT = False
HAS_URLLIB3_SSL_WRAP_SOCKET = False
if not HAS_SSLCONTEXT:
    try:
        # urllib3>=1.15
        try:
            from urllib3.contrib.pyopenssl import PyOpenSSLContext
        except Exception:
            from requests.packages.urllib3.contrib.pyopenssl import PyOpenSSLContext
        HAS_URLLIB3_PYOPENSSLCONTEXT = True
    except Exception:
        # urllib3<1.15,>=1.6
        try:
            try:
                from urllib3.contrib.pyopenssl import ssl_wrap_socket
            except Exception:
                from requests.packages.urllib3.contrib.pyopenssl import ssl_wrap_socket
            HAS_URLLIB3_SSL_WRAP_SOCKET = True
        except Exception:
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


# The following makes it easier for us to script updates of the bundled backports.ssl_match_hostname
# The bundled backports.ssl_match_hostname should really be moved into its own file for processing
_BUNDLED_METADATA = {"pypi_name": "backports.ssl_match_hostname", "version": "3.7.0.1"}

LOADED_VERIFY_LOCATIONS = set()  # type: t.Set[str]

HAS_MATCH_HOSTNAME = True
try:
    from ssl import match_hostname, CertificateError
except ImportError:
    try:
        from backports.ssl_match_hostname import match_hostname, CertificateError  # type: ignore[misc]
    except ImportError:
        HAS_MATCH_HOSTNAME = False

HAS_CRYPTOGRAPHY = True
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.exceptions import UnsupportedAlgorithm
except ImportError:
    HAS_CRYPTOGRAPHY = False

# Old import for GSSAPI authentication, this is not used in urls.py but kept for backwards compatibility.
try:
    import urllib_gssapi
    HAS_GSSAPI = True
except ImportError:
    HAS_GSSAPI = False

GSSAPI_IMP_ERR = None
try:
    import gssapi

    class HTTPGSSAPIAuthHandler(BaseHandler):
        """ Handles Negotiate/Kerberos support through the gssapi library. """

        AUTH_HEADER_PATTERN = re.compile(r'(?:.*)\s*(Negotiate|Kerberos)\s*([^,]*),?', re.I)
        handler_order = 480  # Handle before Digest authentication

        def __init__(self, username=None, password=None):
            self.username = username
            self.password = password
            self._context = None

        def get_auth_value(self, headers):
            auth_match = self.AUTH_HEADER_PATTERN.search(headers.get('www-authenticate', ''))
            if auth_match:
                return auth_match.group(1), base64.b64decode(auth_match.group(2))

        def http_error_401(self, req, fp, code, msg, headers):
            # If we've already attempted the auth and we've reached this again then there was a failure.
            if self._context:
                return

            parsed = generic_urlparse(urlparse(req.get_full_url()))

            auth_header = self.get_auth_value(headers)
            if not auth_header:
                return
            auth_protocol, in_token = auth_header

            username = None
            if self.username:
                username = gssapi.Name(self.username, name_type=gssapi.NameType.user)

            if username and self.password:
                if not hasattr(gssapi.raw, 'acquire_cred_with_password'):
                    raise NotImplementedError("Platform GSSAPI library does not support "
                                              "gss_acquire_cred_with_password, cannot acquire GSSAPI credential with "
                                              "explicit username and password.")

                b_password = to_bytes(self.password, errors='surrogate_or_strict')
                cred = gssapi.raw.acquire_cred_with_password(username, b_password, usage='initiate').creds

            else:
                cred = gssapi.Credentials(name=username, usage='initiate')

            # Get the peer certificate for the channel binding token if possible (HTTPS). A bug on macOS causes the
            # authentication to fail when the CBT is present. Just skip that platform.
            cbt = None
            cert = getpeercert(fp, True)
            if cert and platform.system() != 'Darwin':
                cert_hash = get_channel_binding_cert_hash(cert)
                if cert_hash:
                    cbt = gssapi.raw.ChannelBindings(application_data=b"tls-server-end-point:" + cert_hash)

            # TODO: We could add another option that is set to include the port in the SPN if desired in the future.
            target = gssapi.Name("HTTP@%s" % parsed['hostname'], gssapi.NameType.hostbased_service)
            self._context = gssapi.SecurityContext(usage="initiate", name=target, creds=cred, channel_bindings=cbt)

            resp = None
            while not self._context.complete:
                out_token = self._context.step(in_token)
                if not out_token:
                    break

                auth_header = '%s %s' % (auth_protocol, to_native(base64.b64encode(out_token)))
                req.add_unredirected_header('Authorization', auth_header)
                resp = self.parent.open(req)

                # The response could contain a token that the client uses to validate the server
                auth_header = self.get_auth_value(resp.headers)
                if not auth_header:
                    break
                in_token = auth_header[1]

            return resp

except ImportError:
    GSSAPI_IMP_ERR = traceback.format_exc()
    HTTPGSSAPIAuthHandler = None  # type: types.ModuleType | None  # type: ignore[no-redef]

if not HAS_MATCH_HOSTNAME:
    # The following block of code is under the terms and conditions of the
    # Python Software Foundation License

    """The match_hostname() function from Python 3.4, essential when using SSL."""

    try:
        # Divergence: Python-3.7+'s _ssl has this exception type but older Pythons do not
        from _ssl import SSLCertVerificationError
        CertificateError = SSLCertVerificationError  # type: ignore[misc]
    except ImportError:
        class CertificateError(ValueError):  # type: ignore[no-redef]
            pass

    def _dnsname_match(dn, hostname):
        """Matching according to RFC 6125, section 6.4.3

        - Hostnames are compared lower case.
        - For IDNA, both dn and hostname must be encoded as IDN A-label (ACE).
        - Partial wildcards like 'www*.example.org', multiple wildcards, sole
          wildcard or wildcards in labels other then the left-most label are not
          supported and a CertificateError is raised.
        - A wildcard must match at least one character.
        """
        if not dn:
            return False

        wildcards = dn.count('*')
        # speed up common case w/o wildcards
        if not wildcards:
            return dn.lower() == hostname.lower()

        if wildcards > 1:
            # Divergence .format() to percent formatting for Python < 2.6
            raise CertificateError(
                "too many wildcards in certificate DNS name: %s" % repr(dn))

        dn_leftmost, sep, dn_remainder = dn.partition('.')

        if '*' in dn_remainder:
            # Only match wildcard in leftmost segment.
            # Divergence .format() to percent formatting for Python < 2.6
            raise CertificateError(
                "wildcard can only be present in the leftmost label: "
                "%s." % repr(dn))

        if not sep:
            # no right side
            # Divergence .format() to percent formatting for Python < 2.6
            raise CertificateError(
                "sole wildcard without additional labels are not support: "
                "%s." % repr(dn))

        if dn_leftmost != '*':
            # no partial wildcard matching
            # Divergence .format() to percent formatting for Python < 2.6
            raise CertificateError(
                "partial wildcards in leftmost label are not supported: "
                "%s." % repr(dn))

        hostname_leftmost, sep, hostname_remainder = hostname.partition('.')
        if not hostname_leftmost or not sep:
            # wildcard must match at least one char
            return False
        return dn_remainder.lower() == hostname_remainder.lower()

    def _inet_paton(ipname):
        """Try to convert an IP address to packed binary form

        Supports IPv4 addresses on all platforms and IPv6 on platforms with IPv6
        support.
        """
        # inet_aton() also accepts strings like '1'
        # Divergence: We make sure we have native string type for all python versions
        try:
            b_ipname = to_bytes(ipname, errors='strict')
        except UnicodeError:
            raise ValueError("%s must be an all-ascii string." % repr(ipname))

        # Set ipname in native string format
        if sys.version_info < (3,):
            n_ipname = b_ipname
        else:
            n_ipname = ipname

        if n_ipname.count('.') == 3:
            try:
                return socket.inet_aton(n_ipname)
            # Divergence: OSError on late python3.  socket.error earlier.
            # Null bytes generate ValueError on python3(we want to raise
            # ValueError anyway), TypeError # earlier
            except (OSError, socket.error, TypeError):
                pass

        try:
            return socket.inet_pton(socket.AF_INET6, n_ipname)
        # Divergence: OSError on late python3.  socket.error earlier.
        # Null bytes generate ValueError on python3(we want to raise
        # ValueError anyway), TypeError # earlier
        except (OSError, socket.error, TypeError):
            # Divergence .format() to percent formatting for Python < 2.6
            raise ValueError("%s is neither an IPv4 nor an IP6 "
                             "address." % repr(ipname))
        except AttributeError:
            # AF_INET6 not available
            pass

        # Divergence .format() to percent formatting for Python < 2.6
        raise ValueError("%s is not an IPv4 address." % repr(ipname))

    def _ipaddress_match(ipname, host_ip):
        """Exact matching of IP addresses.

        RFC 6125 explicitly doesn't define an algorithm for this
        (section 1.7.2 - "Out of Scope").
        """
        # OpenSSL may add a trailing newline to a subjectAltName's IP address
        ip = _inet_paton(ipname.rstrip())
        return ip == host_ip

    def match_hostname(cert, hostname):  # type: ignore[misc]
        """Verify that *cert* (in decoded format as returned by
        SSLSocket.getpeercert()) matches the *hostname*.  RFC 2818 and RFC 6125
        rules are followed.

        The function matches IP addresses rather than dNSNames if hostname is a
        valid ipaddress string. IPv4 addresses are supported on all platforms.
        IPv6 addresses are supported on platforms with IPv6 support (AF_INET6
        and inet_pton).

        CertificateError is raised on failure. On success, the function
        returns nothing.
        """
        if not cert:
            raise ValueError("empty or no certificate, match_hostname needs a "
                             "SSL socket or SSL context with either "
                             "CERT_OPTIONAL or CERT_REQUIRED")
        try:
            # Divergence: Deal with hostname as bytes
            host_ip = _inet_paton(to_text(hostname, errors='strict'))
        except UnicodeError:
            # Divergence: Deal with hostname as byte strings.
            # IP addresses should be all ascii, so we consider it not
            # an IP address if this fails
            host_ip = None
        except ValueError:
            # Not an IP address (common case)
            host_ip = None
        dnsnames = []
        san = cert.get('subjectAltName', ())
        for key, value in san:
            if key == 'DNS':
                if host_ip is None and _dnsname_match(value, hostname):
                    return
                dnsnames.append(value)
            elif key == 'IP Address':
                if host_ip is not None and _ipaddress_match(value, host_ip):
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
            raise CertificateError("hostname %r doesn't match either of %s" % (hostname, ', '.join(map(repr, dnsnames))))
        elif len(dnsnames) == 1:
            raise CertificateError("hostname %r doesn't match %r" % (hostname, dnsnames[0]))
        else:
            raise CertificateError("no appropriate commonName or subjectAltName fields were found")

    # End of Python Software Foundation Licensed code

    HAS_MATCH_HOSTNAME = True


# This is a dummy cacert provided for macOS since you need at least 1
# ca cert, regardless of validity, for Python on macOS to use the
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

b_PEM_CERT_RE = re.compile(
    br'^-----BEGIN CERTIFICATE-----\n.+?-----END CERTIFICATE-----$',
    flags=re.M | re.S
)

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


class MissingModuleError(Exception):
    """Failed to import 3rd party module required by the caller"""
    def __init__(self, message, import_traceback, module=None):
        super(MissingModuleError, self).__init__(message)
        self.import_traceback = import_traceback
        self.module = module


# Some environments (Google Compute Engine's CoreOS deploys) do not compile
# against openssl and thus do not have any HTTPS support.
CustomHTTPSConnection = None
CustomHTTPSHandler = None
HTTPSClientAuthHandler = None
UnixHTTPSConnection = None
if hasattr(httplib, 'HTTPSConnection') and hasattr(urllib_request, 'HTTPSHandler'):
    class CustomHTTPSConnection(httplib.HTTPSConnection):  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            httplib.HTTPSConnection.__init__(self, *args, **kwargs)
            self.context = None
            if HAS_SSLCONTEXT:
                self.context = self._context
            elif HAS_URLLIB3_PYOPENSSLCONTEXT:
                self.context = self._context = PyOpenSSLContext(PROTOCOL)
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
                self.sock = ssl_wrap_socket(sock, keyfile=self.key_file, cert_reqs=ssl.CERT_NONE,  # pylint: disable=used-before-assignment
                                            certfile=self.cert_file, ssl_version=PROTOCOL, server_hostname=server_hostname)
            else:
                self.sock = ssl.wrap_socket(sock, keyfile=self.key_file, certfile=self.cert_file, ssl_version=PROTOCOL)

    class CustomHTTPSHandler(urllib_request.HTTPSHandler):  # type: ignore[no-redef]

        def https_open(self, req):
            kwargs = {}
            if HAS_SSLCONTEXT:
                kwargs['context'] = self._context
            return self.do_open(
                functools.partial(
                    CustomHTTPSConnection,
                    **kwargs
                ),
                req
            )

        https_request = AbstractHTTPHandler.do_request_

    class HTTPSClientAuthHandler(urllib_request.HTTPSHandler):  # type: ignore[no-redef]
        '''Handles client authentication via cert/key

        This is a fairly lightweight extension on HTTPSHandler, and can be used
        in place of HTTPSHandler
        '''

        def __init__(self, client_cert=None, client_key=None, unix_socket=None, **kwargs):
            urllib_request.HTTPSHandler.__init__(self, **kwargs)
            self.client_cert = client_cert
            self.client_key = client_key
            self._unix_socket = unix_socket

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
            if self._unix_socket:
                return UnixHTTPSConnection(self._unix_socket)(host, **kwargs)
            if not HAS_SSLCONTEXT:
                return CustomHTTPSConnection(host, **kwargs)
            return httplib.HTTPSConnection(host, **kwargs)

    @contextmanager
    def unix_socket_patch_httpconnection_connect():
        '''Monkey patch ``httplib.HTTPConnection.connect`` to be ``UnixHTTPConnection.connect``
        so that when calling ``super(UnixHTTPSConnection, self).connect()`` we get the
        correct behavior of creating self.sock for the unix socket
        '''
        _connect = httplib.HTTPConnection.connect
        httplib.HTTPConnection.connect = UnixHTTPConnection.connect
        yield
        httplib.HTTPConnection.connect = _connect

    class UnixHTTPSConnection(httplib.HTTPSConnection):  # type: ignore[no-redef]
        def __init__(self, unix_socket):
            self._unix_socket = unix_socket

        def connect(self):
            # This method exists simply to ensure we monkeypatch
            # httplib.HTTPConnection.connect to call UnixHTTPConnection.connect
            with unix_socket_patch_httpconnection_connect():
                # Disable pylint check for the super() call. It complains about UnixHTTPSConnection
                # being a NoneType because of the initial definition above, but it won't actually
                # be a NoneType when this code runs
                # pylint: disable=bad-super-call
                super(UnixHTTPSConnection, self).connect()

        def __call__(self, *args, **kwargs):
            httplib.HTTPSConnection.__init__(self, *args, **kwargs)
            return self


class UnixHTTPConnection(httplib.HTTPConnection):
    '''Handles http requests to a unix socket file'''

    def __init__(self, unix_socket):
        self._unix_socket = unix_socket

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.connect(self._unix_socket)
        except OSError as e:
            raise OSError('Invalid Socket File (%s): %s' % (self._unix_socket, e))
        if self.timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
            self.sock.settimeout(self.timeout)

    def __call__(self, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
        return self


class UnixHTTPHandler(urllib_request.HTTPHandler):
    '''Handler for Unix urls'''

    def __init__(self, unix_socket, **kwargs):
        urllib_request.HTTPHandler.__init__(self, **kwargs)
        self._unix_socket = unix_socket

    def http_open(self, req):
        return self.do_open(UnixHTTPConnection(self._unix_socket), req)


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
        hostname = parts.hostname
        if hostname and hostname[0] == '[' and '[' in parts.netloc and ']' in parts.netloc:
            # Py2.6 doesn't parse IPv6 addresses correctly
            hostname = parts.netloc.split(']')[0][1:].lower()
        generic_parts['hostname'] = hostname

        try:
            port = parts.port
        except ValueError:
            # Py2.6 doesn't parse IPv6 addresses correctly
            netloc = parts.netloc.split('@')[-1].split(']')[-1]
            if ':' in netloc:
                port = netloc.split(':')[1]
                if port:
                    port = int(port)
            else:
                port = None
        generic_parts['port'] = port
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
        except Exception:
            generic_parts['username'] = None
            generic_parts['password'] = None
            generic_parts['hostname'] = parts[1]
            generic_parts['port'] = None
    return generic_parts


def extract_pem_certs(b_data):
    for match in b_PEM_CERT_RE.finditer(b_data):
        yield match.group(0)


def get_response_filename(response):
    url = response.geturl()
    path = urlparse(url)[2]
    filename = os.path.basename(path.rstrip('/')) or None
    if filename:
        filename = unquote(filename)

    return response.headers.get_param('filename', header='content-disposition') or filename


def parse_content_type(response):
    if PY2:
        get_type = response.headers.gettype
        get_param = response.headers.getparam
    else:
        get_type = response.headers.get_content_type
        get_param = response.headers.get_param

    content_type = (get_type() or 'application/octet-stream').split(',')[0]
    main_type, sub_type = content_type.split('/')
    charset = (get_param('charset') or 'utf-8').split(',')[0]
    return content_type, main_type, sub_type, charset


class GzipDecodedReader(GzipFile):
    """A file-like object to decode a response encoded with the gzip
    method, as described in RFC 1952.

    Largely copied from ``xmlrpclib``/``xmlrpc.client``
    """
    def __init__(self, fp):
        if not HAS_GZIP:
            raise MissingModuleError(self.missing_gzip_error(), import_traceback=GZIP_IMP_ERR)

        if PY3:
            self._io = fp
        else:
            # Py2 ``HTTPResponse``/``addinfourl`` doesn't support all of the file object
            # functionality GzipFile requires
            self._io = io.BytesIO()
            for block in iter(functools.partial(fp.read, 65536), b''):
                self._io.write(block)
            self._io.seek(0)
            fp.close()
        gzip.GzipFile.__init__(self, mode='rb', fileobj=self._io)  # pylint: disable=non-parent-init-called

    def close(self):
        try:
            gzip.GzipFile.close(self)
        finally:
            self._io.close()

    @staticmethod
    def missing_gzip_error():
        return missing_required_lib(
            'gzip',
            reason='to decompress gzip encoded responses. '
                   'Set "decompress" to False, to prevent attempting auto decompression'
        )


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


def RedirectHandlerFactory(follow_redirects=None, validate_certs=True, ca_path=None, ciphers=None):
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
            if not any((HAS_SSLCONTEXT, HAS_URLLIB3_PYOPENSSLCONTEXT)):
                handler = maybe_add_ssl_handler(newurl, validate_certs, ca_path=ca_path, ciphers=ciphers)
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

            # Support redirect with payload and original headers
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
        if not HAS_URLLIB3_PYOPENSSLCONTEXT and not HAS_URLLIB3_SSL_WRAP_SOCKET:
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


def atexit_remove_file(filename):
    if os.path.exists(filename):
        try:
            os.unlink(filename)
        except Exception:
            # just ignore if we cannot delete, things should be ok
            pass


def make_context(cafile=None, cadata=None, ciphers=None, validate_certs=True):
    if ciphers is None:
        ciphers = []

    if not is_sequence(ciphers):
        raise TypeError('Ciphers must be a list. Got %s.' % ciphers.__class__.__name__)

    if HAS_SSLCONTEXT:
        context = create_default_context(cafile=cafile)
    elif HAS_URLLIB3_PYOPENSSLCONTEXT:
        context = PyOpenSSLContext(PROTOCOL)
    else:
        raise NotImplementedError('Host libraries are too old to support creating an sslcontext')

    if not validate_certs:
        if ssl.OP_NO_SSLv2:
            context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    if validate_certs and any((cafile, cadata)):
        context.load_verify_locations(cafile=cafile, cadata=cadata)

    if ciphers:
        context.set_ciphers(':'.join(map(to_native, ciphers)))

    return context


def get_ca_certs(cafile=None):
    # tries to find a valid CA cert in one of the
    # standard locations for the current distribution

    cadata = bytearray()
    paths_checked = []

    if cafile:
        paths_checked = [cafile]
        with open(to_bytes(cafile, errors='surrogate_or_strict'), 'rb') as f:
            if HAS_SSLCONTEXT:
                for b_pem in extract_pem_certs(f.read()):
                    cadata.extend(
                        ssl.PEM_cert_to_DER_cert(
                            to_native(b_pem, errors='surrogate_or_strict')
                        )
                    )
        return cafile, cadata, paths_checked

    if not HAS_SSLCONTEXT:
        paths_checked.append('/etc/ssl/certs')

    system = to_text(platform.system(), errors='surrogate_or_strict')
    # build a list of paths to check for .crt/.pem files
    # based on the platform type
    if system == u'Linux':
        paths_checked.append('/etc/pki/ca-trust/extracted/pem')
        paths_checked.append('/etc/pki/tls/certs')
        paths_checked.append('/usr/share/ca-certificates/cacert.org')
    elif system == u'FreeBSD':
        paths_checked.append('/usr/local/share/certs')
    elif system == u'OpenBSD':
        paths_checked.append('/etc/ssl')
    elif system == u'NetBSD':
        paths_checked.append('/etc/openssl/certs')
    elif system == u'SunOS':
        paths_checked.append('/opt/local/etc/openssl/certs')
    elif system == u'AIX':
        paths_checked.append('/var/ssl/certs')
        paths_checked.append('/opt/freeware/etc/ssl/certs')

    # fall back to a user-deployed cert in a standard
    # location if the OS platform one is not available
    paths_checked.append('/etc/ansible')

    tmp_path = None
    if not HAS_SSLCONTEXT:
        tmp_fd, tmp_path = tempfile.mkstemp()
        atexit.register(atexit_remove_file, tmp_path)

    # Write the dummy ca cert if we are running on macOS
    if system == u'Darwin':
        if HAS_SSLCONTEXT:
            cadata.extend(
                ssl.PEM_cert_to_DER_cert(
                    to_native(b_DUMMY_CA_CERT, errors='surrogate_or_strict')
                )
            )
        else:
            os.write(tmp_fd, b_DUMMY_CA_CERT)
        # Default Homebrew path for OpenSSL certs
        paths_checked.append('/usr/local/etc/openssl')

    # for all of the paths, find any  .crt or .pem files
    # and compile them into single temp file for use
    # in the ssl check to speed up the test
    for path in paths_checked:
        if not os.path.isdir(path):
            continue

        dir_contents = os.listdir(path)
        for f in dir_contents:
            full_path = os.path.join(path, f)
            if os.path.isfile(full_path) and os.path.splitext(f)[1] in ('.crt', '.pem'):
                try:
                    if full_path not in LOADED_VERIFY_LOCATIONS:
                        with open(full_path, 'rb') as cert_file:
                            b_cert = cert_file.read()
                        if HAS_SSLCONTEXT:
                            try:
                                for b_pem in extract_pem_certs(b_cert):
                                    cadata.extend(
                                        ssl.PEM_cert_to_DER_cert(
                                            to_native(b_pem, errors='surrogate_or_strict')
                                        )
                                    )
                            except Exception:
                                continue
                        else:
                            os.write(tmp_fd, b_cert)
                            os.write(tmp_fd, b'\n')
                except (OSError, IOError):
                    pass

    if HAS_SSLCONTEXT:
        default_verify_paths = ssl.get_default_verify_paths()
        paths_checked[:0] = [default_verify_paths.capath]
    else:
        os.close(tmp_fd)

    return (tmp_path, cadata, paths_checked)


class SSLValidationHandler(urllib_request.BaseHandler):
    '''
    A custom handler class for SSL validation.

    Based on:
    http://stackoverflow.com/questions/1087227/validate-ssl-certificates-with-python
    http://techknack.net/python-urllib2-handlers/
    '''
    CONNECT_COMMAND = "CONNECT %s:%s HTTP/1.0\r\n"

    def __init__(self, hostname, port, ca_path=None, ciphers=None, validate_certs=True):
        self.hostname = hostname
        self.port = port
        self.ca_path = ca_path
        self.ciphers = ciphers
        self.validate_certs = validate_certs

    def get_ca_certs(self):
        return get_ca_certs(self.ca_path)

    def validate_proxy_response(self, response, valid_codes=None):
        '''
        make sure we get back a valid code from the proxy
        '''
        valid_codes = [200] if valid_codes is None else valid_codes

        try:
            (http_version, resp_code, msg) = re.match(br'(HTTP/\d\.\d) (\d\d\d) (.*)', response).groups()
            if int(resp_code) not in valid_codes:
                raise Exception
        except Exception:
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

    def make_context(self, cafile, cadata, ciphers=None, validate_certs=True):
        cafile = self.ca_path or cafile
        if self.ca_path:
            cadata = None
        else:
            cadata = cadata or None

        return make_context(cafile=cafile, cadata=cadata, ciphers=ciphers, validate_certs=validate_certs)

    def http_request(self, req):
        tmp_ca_cert_path, cadata, paths_checked = self.get_ca_certs()

        # Detect if 'no_proxy' environment variable is set and if our URL is included
        use_proxy = self.detect_no_proxy(req.get_full_url())
        https_proxy = os.environ.get('https_proxy')

        context = None
        try:
            context = self.make_context(tmp_ca_cert_path, cadata, ciphers=self.ciphers, validate_certs=self.validate_certs)
        except NotImplementedError:
            # We'll make do with no context below
            pass

        try:
            if use_proxy and https_proxy:
                proxy_parts = generic_urlparse(urlparse(https_proxy))
                port = proxy_parts.get('port') or 443
                proxy_hostname = proxy_parts.get('hostname', None)
                if proxy_hostname is None or proxy_parts.get('scheme') == '':
                    raise ProxyError("Failed to parse https_proxy environment variable."
                                     " Please make sure you export https proxy as 'https_proxy=<SCHEME>://<IP_ADDRESS>:<PORT>'")

                s = socket.create_connection((proxy_hostname, port))
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

        return req

    https_request = http_request


def maybe_add_ssl_handler(url, validate_certs, ca_path=None, ciphers=None):
    parsed = generic_urlparse(urlparse(url))
    if parsed.scheme == 'https' and validate_certs:
        if not HAS_SSL:
            raise NoSSLError('SSL validation is not available in your version of python. You can use validate_certs=False,'
                             ' however this is unsafe and not recommended')

        # create the SSL validation handler
        return SSLValidationHandler(parsed.hostname, parsed.port or 443, ca_path=ca_path, ciphers=ciphers, validate_certs=validate_certs)


def getpeercert(response, binary_form=False):
    """ Attempt to get the peer certificate of the response from urlopen. """
    # The response from urllib2.open() is different across Python 2 and 3
    if PY3:
        socket = response.fp.raw._sock
    else:
        socket = response.fp._sock.fp._sock

    try:
        return socket.getpeercert(binary_form)
    except AttributeError:
        pass  # Not HTTPS


def get_channel_binding_cert_hash(certificate_der):
    """ Gets the channel binding app data for a TLS connection using the peer cert. """
    if not HAS_CRYPTOGRAPHY:
        return

    # Logic documented in RFC 5929 section 4 https://tools.ietf.org/html/rfc5929#section-4
    cert = x509.load_der_x509_certificate(certificate_der, default_backend())

    hash_algorithm = None
    try:
        hash_algorithm = cert.signature_hash_algorithm
    except UnsupportedAlgorithm:
        pass

    # If the signature hash algorithm is unknown/unsupported or md5/sha1 we must use SHA256.
    if not hash_algorithm or hash_algorithm.name in ['md5', 'sha1']:
        hash_algorithm = hashes.SHA256()

    digest = hashes.Hash(hash_algorithm, default_backend())
    digest.update(certificate_der)
    return digest.finalize()


def rfc2822_date_string(timetuple, zone='-0000'):
    """Accepts a timetuple and optional zone which defaults to ``-0000``
    and returns a date string as specified by RFC 2822, e.g.:

    Fri, 09 Nov 2001 01:08:47 -0000

    Copied from email.utils.formatdate and modified for separate use
    """
    return '%s, %02d %s %04d %02d:%02d:%02d %s' % (
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][timetuple[6]],
        timetuple[2],
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][timetuple[1] - 1],
        timetuple[0], timetuple[3], timetuple[4], timetuple[5],
        zone)


class Request:
    def __init__(self, headers=None, use_proxy=True, force=False, timeout=10, validate_certs=True,
                 url_username=None, url_password=None, http_agent=None, force_basic_auth=False,
                 follow_redirects='urllib2', client_cert=None, client_key=None, cookies=None, unix_socket=None,
                 ca_path=None, unredirected_headers=None, decompress=True, ciphers=None, use_netrc=True):
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
            raise ValueError("headers must be a dict: %r" % self.headers)
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
        self.unix_socket = unix_socket
        self.ca_path = ca_path
        self.unredirected_headers = unredirected_headers
        self.decompress = decompress
        self.ciphers = ciphers
        self.use_netrc = use_netrc
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
             client_cert=None, client_key=None, cookies=None, use_gssapi=False,
             unix_socket=None, ca_path=None, unredirected_headers=None, decompress=None,
             ciphers=None, use_netrc=None):
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
        :kwarg use_gssapi: (optional) Use GSSAPI handler of requests.
        :kwarg unix_socket: (optional) String of file system path to unix socket file to use when establishing
            connection to the provided url
        :kwarg ca_path: (optional) String of file system path to CA cert bundle to use
        :kwarg unredirected_headers: (optional) A list of headers to not attach on a redirected request
        :kwarg decompress: (optional) Whether to attempt to decompress gzip content-encoded responses
        :kwarg ciphers: (optional) List of ciphers to use
        :kwarg use_netrc: (optional) Boolean determining whether to use credentials from ~/.netrc file
        :returns: HTTPResponse. Added in Ansible 2.9
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
        unix_socket = self._fallback(unix_socket, self.unix_socket)
        ca_path = self._fallback(ca_path, self.ca_path)
        unredirected_headers = self._fallback(unredirected_headers, self.unredirected_headers)
        decompress = self._fallback(decompress, self.decompress)
        ciphers = self._fallback(ciphers, self.ciphers)
        use_netrc = self._fallback(use_netrc, self.use_netrc)

        handlers = []

        if unix_socket:
            handlers.append(UnixHTTPHandler(unix_socket))

        parsed = generic_urlparse(urlparse(url))
        if parsed.scheme != 'ftp':
            username = url_username
            password = url_password

            if username:
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

            if use_gssapi:
                if HTTPGSSAPIAuthHandler:
                    handlers.append(HTTPGSSAPIAuthHandler(username, password))
                else:
                    imp_err_msg = missing_required_lib('gssapi', reason='for use_gssapi=True',
                                                       url='https://pypi.org/project/gssapi/')
                    raise MissingModuleError(imp_err_msg, import_traceback=GSSAPI_IMP_ERR)

            elif username and not force_basic_auth:
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

            elif use_netrc:
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

        if not any((HAS_SSLCONTEXT, HAS_URLLIB3_PYOPENSSLCONTEXT)):
            ssl_handler = maybe_add_ssl_handler(url, validate_certs, ca_path=ca_path, ciphers=ciphers)
            if ssl_handler:
                handlers.append(ssl_handler)
        else:
            tmp_ca_path, cadata, paths_checked = get_ca_certs(ca_path)
            context = make_context(
                cafile=tmp_ca_path,
                cadata=cadata,
                ciphers=ciphers,
                validate_certs=validate_certs,
            )
            handlers.append(HTTPSClientAuthHandler(client_cert=client_cert,
                                                   client_key=client_key,
                                                   unix_socket=unix_socket,
                                                   context=context))

        handlers.append(RedirectHandlerFactory(follow_redirects, validate_certs, ca_path=ca_path, ciphers=ciphers))

        # add some nicer cookie handling
        if cookies is not None:
            handlers.append(urllib_request.HTTPCookieProcessor(cookies))

        opener = urllib_request.build_opener(*handlers)
        urllib_request.install_opener(opener)

        data = to_bytes(data, nonstring='passthru')
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
            tstamp = rfc2822_date_string(last_mod_time.timetuple(), 'GMT')
            request.add_header('If-Modified-Since', tstamp)

        # user defined headers now, which may override things we've set above
        unredirected_headers = [h.lower() for h in (unredirected_headers or [])]
        for header in headers:
            if header.lower() in unredirected_headers:
                request.add_unredirected_header(header, headers[header])
            else:
                request.add_header(header, headers[header])

        r = urllib_request.urlopen(request, None, timeout)
        if decompress and r.headers.get('content-encoding', '').lower() == 'gzip':
            fp = GzipDecodedReader(r.fp)
            if PY3:
                r.fp = fp
                # Content-Length does not match gzip decoded length
                # Prevent ``r.read`` from stopping at Content-Length
                r.length = None
            else:
                # Py2 maps ``r.read`` to ``fp.read``, create new ``addinfourl``
                # object to compensate
                msg = r.msg
                r = urllib_request.addinfourl(
                    fp,
                    r.info(),
                    r.geturl(),
                    r.getcode()
                )
                r.msg = msg
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
             client_cert=None, client_key=None, cookies=None,
             use_gssapi=False, unix_socket=None, ca_path=None,
             unredirected_headers=None, decompress=True, ciphers=None, use_netrc=True):
    '''
    Sends a request via HTTP(S) or FTP using urllib2 (Python2) or urllib (Python3)

    Does not require the module environment
    '''
    method = method or ('POST' if data else 'GET')
    return Request().open(method, url, data=data, headers=headers, use_proxy=use_proxy,
                          force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                          url_username=url_username, url_password=url_password, http_agent=http_agent,
                          force_basic_auth=force_basic_auth, follow_redirects=follow_redirects,
                          client_cert=client_cert, client_key=client_key, cookies=cookies,
                          use_gssapi=use_gssapi, unix_socket=unix_socket, ca_path=ca_path,
                          unredirected_headers=unredirected_headers, decompress=decompress, ciphers=ciphers, use_netrc=use_netrc)


def prepare_multipart(fields):
    """Takes a mapping, and prepares a multipart/form-data body

    :arg fields: Mapping
    :returns: tuple of (content_type, body) where ``content_type`` is
        the ``multipart/form-data`` ``Content-Type`` header including
        ``boundary`` and ``body`` is the prepared bytestring body

    Payload content from a file will be base64 encoded and will include
    the appropriate ``Content-Transfer-Encoding`` and ``Content-Type``
    headers.

    Example:
        {
            "file1": {
                "filename": "/bin/true",
                "mime_type": "application/octet-stream"
            },
            "file2": {
                "content": "text based file content",
                "filename": "fake.txt",
                "mime_type": "text/plain",
            },
            "text_form_field": "value"
        }
    """

    if not isinstance(fields, Mapping):
        raise TypeError(
            'Mapping is required, cannot be type %s' % fields.__class__.__name__
        )

    m = email.mime.multipart.MIMEMultipart('form-data')
    for field, value in sorted(fields.items()):
        if isinstance(value, string_types):
            main_type = 'text'
            sub_type = 'plain'
            content = value
            filename = None
        elif isinstance(value, Mapping):
            filename = value.get('filename')
            content = value.get('content')
            if not any((filename, content)):
                raise ValueError('at least one of filename or content must be provided')

            mime = value.get('mime_type')
            if not mime:
                try:
                    mime = mimetypes.guess_type(filename or '', strict=False)[0] or 'application/octet-stream'
                except Exception:
                    mime = 'application/octet-stream'
            main_type, sep, sub_type = mime.partition('/')
        else:
            raise TypeError(
                'value must be a string, or mapping, cannot be type %s' % value.__class__.__name__
            )

        if not content and filename:
            with open(to_bytes(filename, errors='surrogate_or_strict'), 'rb') as f:
                part = email.mime.application.MIMEApplication(f.read())
                del part['Content-Type']
                part.add_header('Content-Type', '%s/%s' % (main_type, sub_type))
        else:
            part = email.mime.nonmultipart.MIMENonMultipart(main_type, sub_type)
            part.set_payload(to_bytes(content))

        part.add_header('Content-Disposition', 'form-data')
        del part['MIME-Version']
        part.set_param(
            'name',
            field,
            header='Content-Disposition'
        )
        if filename:
            part.set_param(
                'filename',
                to_native(os.path.basename(filename)),
                header='Content-Disposition'
            )

        m.attach(part)

    if PY3:
        # Ensure headers are not split over multiple lines
        # The HTTP policy also uses CRLF by default
        b_data = m.as_bytes(policy=email.policy.HTTP)
    else:
        # Py2
        # We cannot just call ``as_string`` since it provides no way
        # to specify ``maxheaderlen``
        fp = cStringIO()  # cStringIO seems to be required here
        # Ensure headers are not split over multiple lines
        g = email.generator.Generator(fp, maxheaderlen=0)
        g.flatten(m)
        # ``fix_eols`` switches from ``\n`` to ``\r\n``
        b_data = email.utils.fix_eols(fp.getvalue())
    del m

    headers, sep, b_content = b_data.partition(b'\r\n\r\n')
    del b_data

    if PY3:
        parser = email.parser.BytesHeaderParser().parsebytes
    else:
        # Py2
        parser = email.parser.HeaderParser().parsestr

    return (
        parser(headers)['content-type'],  # Message converts to native strings
        b_content
    )


#
# Module-related functions
#


def basic_auth_header(username, password):
    """Takes a username and password and returns a byte string suitable for
    using as value of an Authorization header to do basic auth.
    """
    if password is None:
        password = ''
    return b"Basic %s" % base64.b64encode(to_bytes("%s:%s" % (username, password), errors='surrogate_or_strict'))


def url_argument_spec():
    '''
    Creates an argument spec that can be used with any module
    that will be requesting content via urllib/urllib2
    '''
    return dict(
        url=dict(type='str'),
        force=dict(type='bool', default=False),
        http_agent=dict(type='str', default='ansible-httpget'),
        use_proxy=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
        url_username=dict(type='str'),
        url_password=dict(type='str', no_log=True),
        force_basic_auth=dict(type='bool', default=False),
        client_cert=dict(type='path'),
        client_key=dict(type='path'),
        use_gssapi=dict(type='bool', default=False),
    )


def fetch_url(module, url, data=None, headers=None, method=None,
              use_proxy=None, force=False, last_mod_time=None, timeout=10,
              use_gssapi=False, unix_socket=None, ca_path=None, cookies=None, unredirected_headers=None,
              decompress=True, ciphers=None, use_netrc=True):
    """Sends a request via HTTP(S) or FTP (needs the module as parameter)

    :arg module: The AnsibleModule (used to get username, password etc. (s.b.).
    :arg url:             The url to use.

    :kwarg data:          The data to be sent (in case of POST/PUT).
    :kwarg headers:       A dict with the request headers.
    :kwarg method:        "POST", "PUT", etc.
    :kwarg use_proxy:     (optional) whether or not to use proxy (Default: True)
    :kwarg boolean force: If True: Do not get a cached copy (Default: False)
    :kwarg last_mod_time: Default: None
    :kwarg int timeout:   Default: 10
    :kwarg boolean use_gssapi:   Default: False
    :kwarg unix_socket: (optional) String of file system path to unix socket file to use when establishing
        connection to the provided url
    :kwarg ca_path: (optional) String of file system path to CA cert bundle to use
    :kwarg cookies: (optional) CookieJar object to send with the request
    :kwarg unredirected_headers: (optional) A list of headers to not attach on a redirected request
    :kwarg decompress: (optional) Whether to attempt to decompress gzip content-encoded responses
    :kwarg cipher: (optional) List of ciphers to use
    :kwarg boolean use_netrc: (optional) If False: Ignores login and password in ~/.netrc file (Default: True)

    :returns: A tuple of (**response**, **info**). Use ``response.read()`` to read the data.
        The **info** contains the 'status' and other meta data. When a HttpError (status >= 400)
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

    if not HAS_GZIP and decompress is True:
        decompress = False
        module.deprecate(
            '%s. "decompress" has been automatically disabled to prevent a failure' % GzipDecodedReader.missing_gzip_error(),
            version='2.16'
        )

    # ensure we use proper tempdir
    old_tempdir = tempfile.tempdir
    tempfile.tempdir = module.tmpdir

    # Get validate_certs from the module params
    validate_certs = module.params.get('validate_certs', True)

    if use_proxy is None:
        use_proxy = module.params.get('use_proxy', True)

    username = module.params.get('url_username', '')
    password = module.params.get('url_password', '')
    http_agent = module.params.get('http_agent', 'ansible-httpget')
    force_basic_auth = module.params.get('force_basic_auth', '')

    follow_redirects = module.params.get('follow_redirects', 'urllib2')

    client_cert = module.params.get('client_cert')
    client_key = module.params.get('client_key')
    use_gssapi = module.params.get('use_gssapi', use_gssapi)

    if not isinstance(cookies, cookiejar.CookieJar):
        cookies = cookiejar.LWPCookieJar()

    r = None
    info = dict(url=url, status=-1)
    try:
        r = open_url(url, data=data, headers=headers, method=method,
                     use_proxy=use_proxy, force=force, last_mod_time=last_mod_time, timeout=timeout,
                     validate_certs=validate_certs, url_username=username,
                     url_password=password, http_agent=http_agent, force_basic_auth=force_basic_auth,
                     follow_redirects=follow_redirects, client_cert=client_cert,
                     client_key=client_key, cookies=cookies, use_gssapi=use_gssapi,
                     unix_socket=unix_socket, ca_path=ca_path, unredirected_headers=unredirected_headers,
                     decompress=decompress, ciphers=ciphers, use_netrc=use_netrc)
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
            module.fail_json(msg='%s. You can also install python-ssl from EPEL' % to_native(e), **info)
        else:
            module.fail_json(msg='%s' % to_native(e), **info)
    except (ConnectionError, ValueError) as e:
        module.fail_json(msg=to_native(e), **info)
    except MissingModuleError as e:
        module.fail_json(msg=to_text(e), exception=e.import_traceback)
    except urllib_error.HTTPError as e:
        r = e
        try:
            if e.fp is None:
                # Certain HTTPError objects may not have the ability to call ``.read()`` on Python 3
                # This is not handled gracefully in Python 3, and instead an exception is raised from
                # tempfile, due to ``urllib.response.addinfourl`` not being initialized
                raise AttributeError
            body = e.read()
        except AttributeError:
            body = ''
        else:
            e.close()

        # Try to add exception info to the output but don't fail if we can't
        try:
            # Lowercase keys, to conform to py2 behavior, so that py3 and py2 are predictable
            info.update(dict((k.lower(), v) for k, v in e.info().items()))
        except Exception:
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


def _suffixes(name):
    """A list of the final component's suffixes, if any."""
    if name.endswith('.'):
        return []
    name = name.lstrip('.')
    return ['.' + s for s in name.split('.')[1:]]


def _split_multiext(name, min=3, max=4, count=2):
    """Split a multi-part extension from a file name.

    Returns '([name minus extension], extension)'.

    Define the valid extension length (including the '.') with 'min' and 'max',
    'count' sets the number of extensions, counting from the end, to evaluate.
    Evaluation stops on the first file extension that is outside the min and max range.

    If no valid extensions are found, the original ``name`` is returned
    and ``extension`` is empty.

    :arg name: File name or path.
    :kwarg min: Minimum length of a valid file extension.
    :kwarg max: Maximum length of a valid file extension.
    :kwarg count: Number of suffixes from the end to evaluate.

    """
    extension = ''
    for i, sfx in enumerate(reversed(_suffixes(name))):
        if i >= count:
            break

        if min <= len(sfx) <= max:
            extension = '%s%s' % (sfx, extension)
            name = name.rstrip(sfx)
        else:
            # Stop on the first invalid extension
            break

    return name, extension


def fetch_file(module, url, data=None, headers=None, method=None,
               use_proxy=True, force=False, last_mod_time=None, timeout=10,
               unredirected_headers=None, decompress=True, ciphers=None):
    '''Download and save a file via HTTP(S) or FTP (needs the module as parameter).
    This is basically a wrapper around fetch_url().

    :arg module: The AnsibleModule (used to get username, password etc. (s.b.).
    :arg url:             The url to use.

    :kwarg data:          The data to be sent (in case of POST/PUT).
    :kwarg headers:       A dict with the request headers.
    :kwarg method:        "POST", "PUT", etc.
    :kwarg boolean use_proxy:     Default: True
    :kwarg boolean force: If True: Do not get a cached copy (Default: False)
    :kwarg last_mod_time: Default: None
    :kwarg int timeout:   Default: 10
    :kwarg unredirected_headers: (optional) A list of headers to not attach on a redirected request
    :kwarg decompress: (optional) Whether to attempt to decompress gzip content-encoded responses
    :kwarg ciphers: (optional) List of ciphers to use

    :returns: A string, the path to the downloaded file.
    '''
    # download file
    bufsize = 65536
    parts = urlparse(url)
    file_prefix, file_ext = _split_multiext(os.path.basename(parts.path), count=2)
    fetch_temp_file = tempfile.NamedTemporaryFile(dir=module.tmpdir, prefix=file_prefix, suffix=file_ext, delete=False)
    module.add_cleanup_file(fetch_temp_file.name)
    try:
        rsp, info = fetch_url(module, url, data, headers, method, use_proxy, force, last_mod_time, timeout,
                              unredirected_headers=unredirected_headers, decompress=decompress, ciphers=ciphers)
        if not rsp:
            module.fail_json(msg="Failure downloading %s, %s" % (url, info['msg']))
        data = rsp.read(bufsize)
        while data:
            fetch_temp_file.write(data)
            data = rsp.read(bufsize)
        fetch_temp_file.close()
    except Exception as e:
        module.fail_json(msg="Failure downloading %s, %s" % (url, to_native(e)))
    return fetch_temp_file.name
