# -*- coding: utf-8 -*-
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com>, 2015
# Copyright: Contributors to the Ansible project
#
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)


"""
The **urls** utils module offers a replacement for the urllib python library.

urllib is the python stdlib way to retrieve files from the Internet but it
lacks some security features (around verifying SSL certificates) that users
should care about in most situations. Using the functions in this module corrects
deficiencies in the urllib module wherever possible.

There are also third-party libraries (for instance, requests) which can be used
to replace urllib with a more secure library. However, all third party libraries
require that the library be installed on the managed machine. That is an extra step
for users making use of a module. If possible, avoid third party libraries by using
this code instead.
"""

from __future__ import annotations

import base64
import email.encoders
import email.mime.application
import email.mime.multipart
import email.mime.nonmultipart
import email.parser
import email.policy
import email.utils
import http.client
import mimetypes
import netrc
import os
import platform
import re
import socket
import tempfile
import traceback
import types  # pylint: disable=unused-import
import urllib.error
import urllib.request
from contextlib import contextmanager
from http import cookiejar
from urllib.parse import unquote, urlparse, urlunparse
from urllib.request import BaseHandler

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

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.collections import Mapping, is_sequence
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text

try:
    import ssl
    HAS_SSL = True
except Exception:
    HAS_SSL = False

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
    import urllib_gssapi  # pylint: disable=unused-import
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

            parsed = urlparse(req.get_full_url())

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
            target = gssapi.Name("HTTP@%s" % parsed.hostname, gssapi.NameType.hostbased_service)
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


PEM_CERT_RE = re.compile(
    r'^-----BEGIN CERTIFICATE-----\n.+?-----END CERTIFICATE-----$',
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
    """Failure to connect due to SSL validation failing

    No longer used, but kept for backwards compatibility
    """
    pass


class NoSSLError(SSLValidationError):
    """Needed to connect to an HTTPS url but no ssl library available to verify the certificate

    No longer used, but kept for backwards compatibility
    """
    pass


class MissingModuleError(Exception):
    """Failed to import 3rd party module required by the caller"""
    def __init__(self, message, import_traceback, module=None):
        super().__init__(message)
        self.import_traceback = import_traceback
        self.module = module


UnixHTTPSHandler = None
UnixHTTPSConnection = None
if HAS_SSL:
    @contextmanager
    def unix_socket_patch_httpconnection_connect():
        """Monkey patch ``http.client.HTTPConnection.connect`` to be ``UnixHTTPConnection.connect``
        so that when calling ``super(UnixHTTPSConnection, self).connect()`` we get the
        correct behavior of creating self.sock for the unix socket
        """
        _connect = http.client.HTTPConnection.connect
        http.client.HTTPConnection.connect = UnixHTTPConnection.connect
        yield
        http.client.HTTPConnection.connect = _connect

    class UnixHTTPSConnection(http.client.HTTPSConnection):  # type: ignore[no-redef]
        def __init__(self, unix_socket):
            self._unix_socket = unix_socket

        def connect(self):
            # This method exists simply to ensure we monkeypatch
            # http.client.HTTPConnection.connect to call UnixHTTPConnection.connect
            with unix_socket_patch_httpconnection_connect():
                # Disable pylint check for the super() call. It complains about UnixHTTPSConnection
                # being a NoneType because of the initial definition above, but it won't actually
                # be a NoneType when this code runs
                super().connect()

        def __call__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            return self

    class UnixHTTPSHandler(urllib.request.HTTPSHandler):  # type: ignore[no-redef]
        def __init__(self, unix_socket, **kwargs):
            super().__init__(**kwargs)
            self._unix_socket = unix_socket

        def https_open(self, req):
            kwargs = {}
            try:
                # deprecated: description='deprecated check_hostname' python_version='3.12'
                kwargs['check_hostname'] = self._check_hostname
            except AttributeError:
                pass
            return self.do_open(
                UnixHTTPSConnection(self._unix_socket),
                req,
                context=self._context,
                **kwargs
            )


class UnixHTTPConnection(http.client.HTTPConnection):
    """Handles http requests to a unix socket file"""

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
        super().__init__(*args, **kwargs)
        return self


class UnixHTTPHandler(urllib.request.HTTPHandler):
    """Handler for Unix urls"""

    def __init__(self, unix_socket, **kwargs):
        super().__init__(**kwargs)
        self._unix_socket = unix_socket

    def http_open(self, req):
        return self.do_open(UnixHTTPConnection(self._unix_socket), req)


class ParseResultDottedDict(dict):
    """
    A dict that acts similarly to the ParseResult named tuple from urllib
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def as_list(self):
        """
        Generate a list from this dict, that looks like the ParseResult named tuple
        """
        return [self.get(k, None) for k in ('scheme', 'netloc', 'path', 'params', 'query', 'fragment')]


def generic_urlparse(parts):
    """
    Returns a dictionary of url parts as parsed by urlparse,
    but accounts for the fact that older versions of that
    library do not support named attributes (ie. .netloc)

    This method isn't of much use any longer, but is kept
    in a minimal state for backwards compat.
    """
    result = ParseResultDottedDict(parts._asdict())
    result.update({
        'username': parts.username,
        'password': parts.password,
        'hostname': parts.hostname,
        'port': parts.port,
    })
    return result


def extract_pem_certs(data):
    for match in PEM_CERT_RE.finditer(data):
        yield match.group(0)


def get_response_filename(response):
    if filename := response.headers.get_param('filename', header='content-disposition'):
        filename = os.path.basename(filename)
    else:
        url = response.geturl()
        path = urlparse(url)[2]
        filename = os.path.basename(path.rstrip('/')) or None
        if filename:
            filename = unquote(filename)

    return filename


def parse_content_type(response):
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

        self._io = fp
        super().__init__(mode='rb', fileobj=self._io)

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


class HTTPRedirectHandler(urllib.request.HTTPRedirectHandler):
    """This is an implementation of a RedirectHandler to match the
    functionality provided by httplib2. It will utilize the value of
    ``follow_redirects`` to determine how redirects should be handled in
    urllib.
    """

    def __init__(self, follow_redirects=None):
        self.follow_redirects = follow_redirects

    def __call__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return self

    try:
        urllib.request.HTTPRedirectHandler.http_error_308  # type: ignore[attr-defined]
    except AttributeError:
        # deprecated: description='urllib http 308 support' python_version='3.11'
        http_error_308 = urllib.request.HTTPRedirectHandler.http_error_302

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        follow_redirects = self.follow_redirects

        # Preserve urllib2 compatibility
        if follow_redirects in ('urllib2', 'urllib'):
            return urllib.request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)

        # Handle disabled redirects
        elif follow_redirects in ('no', 'none', False):
            raise urllib.error.HTTPError(newurl, code, msg, headers, fp)

        method = req.get_method()

        # Handle non-redirect HTTP status or invalid follow_redirects
        if follow_redirects in ('all', 'yes', True):
            if code < 300 or code >= 400:
                raise urllib.error.HTTPError(req.get_full_url(), code, msg, headers, fp)
        elif follow_redirects == 'safe':
            if code < 300 or code >= 400 or method not in ('GET', 'HEAD'):
                raise urllib.error.HTTPError(req.get_full_url(), code, msg, headers, fp)
        else:
            raise urllib.error.HTTPError(req.get_full_url(), code, msg, headers, fp)

        data = req.data
        origin_req_host = req.origin_req_host

        # Be conciliant with URIs containing a space
        newurl = newurl.replace(' ', '%20')

        # Support redirect with payload and original headers
        if code in (307, 308):
            # Preserve payload and headers
            req_headers = req.headers
        else:
            # Do not preserve payload and filter headers
            data = None
            req_headers = {k: v for k, v in req.headers.items()
                           if k.lower() not in ("content-length", "content-type", "transfer-encoding")}

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

        return urllib.request.Request(
            newurl,
            data=data,
            headers=req_headers,
            origin_req_host=origin_req_host,
            unverifiable=True,
            method=method.upper(),
        )


def make_context(cafile=None, cadata=None, capath=None, ciphers=None, validate_certs=True, client_cert=None,
                 client_key=None):
    if ciphers is None:
        ciphers = []

    if not is_sequence(ciphers):
        raise TypeError('Ciphers must be a list. Got %s.' % ciphers.__class__.__name__)

    context = ssl.create_default_context(cafile=cafile)

    if not validate_certs:
        context.options |= ssl.OP_NO_SSLv3
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    # If cafile is passed, we are only using that for verification,
    # don't add additional ca certs
    if validate_certs and not cafile:
        if not cadata:
            cadata = bytearray()
        cadata.extend(get_ca_certs(capath=capath)[0])
        if cadata:
            context.load_verify_locations(cadata=cadata)

    if ciphers:
        context.set_ciphers(':'.join(map(to_native, ciphers)))

    if client_cert:
        # TLS 1.3 needs this to be set to True to allow post handshake cert
        # authentication. This functionality was added in Python 3.8 and was
        # backported to 3.6.7, and 3.7.1 so needs a check for now.
        if hasattr(context, "post_handshake_auth"):
            context.post_handshake_auth = True

        context.load_cert_chain(client_cert, keyfile=client_key)

    return context


def get_ca_certs(cafile=None, capath=None):
    # tries to find a valid CA cert in one of the
    # standard locations for the current distribution

    # Using a dict, instead of a set for order, the value is meaningless and will be None
    # Not directly using a bytearray to avoid duplicates with fast lookup
    cadata = {}

    # If cafile is passed, we are only using that for verification,
    # don't add additional ca certs
    if cafile:
        paths_checked = [cafile]
        with open(to_bytes(cafile, errors='surrogate_or_strict'), 'r', errors='surrogateescape') as f:
            for pem in extract_pem_certs(f.read()):
                b_der = ssl.PEM_cert_to_DER_cert(pem)
                cadata[b_der] = None
        return bytearray().join(cadata), paths_checked

    default_verify_paths = ssl.get_default_verify_paths()
    default_capath = default_verify_paths.capath
    paths_checked = {default_capath or default_verify_paths.cafile}

    if capath:
        paths_checked.add(capath)

    system = to_text(platform.system(), errors='surrogate_or_strict')
    # build a list of paths to check for .crt/.pem files
    # based on the platform type
    if system == u'Linux':
        paths_checked.add('/etc/pki/ca-trust/extracted/pem')
        paths_checked.add('/etc/pki/tls/certs')
        paths_checked.add('/usr/share/ca-certificates/cacert.org')
    elif system == u'FreeBSD':
        paths_checked.add('/usr/local/share/certs')
    elif system == u'OpenBSD':
        paths_checked.add('/etc/ssl')
    elif system == u'NetBSD':
        paths_checked.add('/etc/openssl/certs')
    elif system == u'SunOS':
        paths_checked.add('/opt/local/etc/openssl/certs')
    elif system == u'AIX':
        paths_checked.add('/var/ssl/certs')
        paths_checked.add('/opt/freeware/etc/ssl/certs')
    elif system == u'Darwin':
        paths_checked.add('/usr/local/etc/openssl')

    # fall back to a user-deployed cert in a standard
    # location if the OS platform one is not available
    paths_checked.add('/etc/ansible')

    # for all of the paths, find any  .crt or .pem files
    # and compile them into single temp file for use
    # in the ssl check to speed up the test
    for path in paths_checked:
        if not path or path == default_capath or not os.path.isdir(path):
            continue

        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            if os.path.isfile(full_path) and os.path.splitext(f)[1] in {'.pem', '.cer', '.crt'}:
                try:
                    with open(full_path, 'r', errors='surrogateescape') as cert_file:
                        cert = cert_file.read()
                    try:
                        for pem in extract_pem_certs(cert):
                            b_der = ssl.PEM_cert_to_DER_cert(pem)
                            cadata[b_der] = None
                    except Exception:
                        continue
                except OSError:
                    pass

    # paths_checked isn't used any more, but is kept just for ease of debugging
    return bytearray().join(cadata), list(paths_checked)


def getpeercert(response, binary_form=False):
    """ Attempt to get the peer certificate of the response from urlopen. """
    socket = response.fp.raw._sock

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
    if not hash_algorithm or hash_algorithm.name in ('md5', 'sha1'):
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


def _configure_auth(url, url_username, url_password, use_gssapi, force_basic_auth, use_netrc):
    headers = {}
    handlers = []

    parsed = urlparse(url)
    if parsed.scheme == 'ftp':
        return url, headers, handlers

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
        username = unquote(username)
        password = unquote(password)

        # reconstruct url without credentials
        url = urlunparse(parsed._replace(netloc=netloc))

    if use_gssapi:
        if HTTPGSSAPIAuthHandler:  # type: ignore[truthy-function]
            handlers.append(HTTPGSSAPIAuthHandler(username, password))
        else:
            imp_err_msg = missing_required_lib('gssapi', reason='for use_gssapi=True',
                                               url='https://pypi.org/project/gssapi/')
            raise MissingModuleError(imp_err_msg, import_traceback=GSSAPI_IMP_ERR)

    elif username and not force_basic_auth:
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()

        # this creates a password manager
        passman.add_password(None, netloc, username, password)

        # because we have put None at the start it will always
        # use this username/password combination for  urls
        # for which `theurl` is a super-url
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        digest_authhandler = urllib.request.HTTPDigestAuthHandler(passman)

        # create the AuthHandler
        handlers.append(authhandler)
        handlers.append(digest_authhandler)

    elif username and force_basic_auth:
        headers["Authorization"] = basic_auth_header(username, password)

    elif use_netrc:
        try:
            rc = netrc.netrc(os.environ.get('NETRC'))
            login = rc.authenticators(parsed.hostname)
        except OSError:
            login = None

        if login:
            username, dummy, password = login
            if username and password:
                headers["Authorization"] = basic_auth_header(username, password)

    return url, headers, handlers


class Request:
    def __init__(self, headers=None, use_proxy=True, force=False, timeout=10, validate_certs=True,
                 url_username=None, url_password=None, http_agent=None, force_basic_auth=False,
                 follow_redirects='urllib2', client_cert=None, client_key=None, cookies=None, unix_socket=None,
                 ca_path=None, unredirected_headers=None, decompress=True, ciphers=None, use_netrc=True,
                 context=None):
        """This class works somewhat similarly to the ``Session`` class of from requests
        by defining a cookiejar that can be used across requests as well as cascaded defaults that
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
        self.context = context
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
             ciphers=None, use_netrc=None, context=None):
        """
        Sends a request via HTTP(S) or FTP using urllib (Python3)

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
            followed, see HTTPRedirectHandler for more information
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
        :kwarg context: (optional) ssl.Context object for SSL validation. When provided, all other SSL related
            arguments are ignored. See make_context.
        :returns: HTTPResponse. Added in Ansible 2.9
        """

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
        context = self._fallback(context, self.context)

        handlers = []

        if unix_socket:
            handlers.append(UnixHTTPHandler(unix_socket))

        url, auth_headers, auth_handlers = _configure_auth(url, url_username, url_password, use_gssapi, force_basic_auth, use_netrc)
        headers.update(auth_headers)
        handlers.extend(auth_handlers)

        if not use_proxy:
            proxyhandler = urllib.request.ProxyHandler({})
            handlers.append(proxyhandler)

        if not context:
            context = make_context(
                cafile=ca_path,
                ciphers=ciphers,
                validate_certs=validate_certs,
                client_cert=client_cert,
                client_key=client_key,
            )
        if unix_socket:
            ssl_handler = UnixHTTPSHandler(unix_socket=unix_socket, context=context)
        else:
            ssl_handler = urllib.request.HTTPSHandler(context=context)
        handlers.append(ssl_handler)

        handlers.append(HTTPRedirectHandler(follow_redirects))

        # add some nicer cookie handling
        if cookies is not None:
            handlers.append(urllib.request.HTTPCookieProcessor(cookies))

        opener = urllib.request.build_opener(*handlers)
        urllib.request.install_opener(opener)

        data = to_bytes(data, nonstring='passthru')
        request = urllib.request.Request(url, data=data, method=method.upper())

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

        r = urllib.request.urlopen(request, None, timeout)
        if decompress and r.headers.get('content-encoding', '').lower() == 'gzip':
            fp = GzipDecodedReader(r.fp)
            r.fp = fp
            # Content-Length does not match gzip decoded length
            # Prevent ``r.read`` from stopping at Content-Length
            r.length = None
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
    """
    Sends a request via HTTP(S) or FTP using urllib (Python3)

    Does not require the module environment
    """
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
        if isinstance(value, str):
            main_type = 'text'
            sub_type = 'plain'
            content = value
            filename = None
        elif isinstance(value, Mapping):
            filename = value.get('filename')
            multipart_encoding_str = value.get('multipart_encoding') or 'base64'
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
            multipart_encoding = set_multipart_encoding(multipart_encoding_str)
            with open(to_bytes(filename, errors='surrogate_or_strict'), 'rb') as f:
                part = email.mime.application.MIMEApplication(f.read(), _encoder=multipart_encoding)
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

    # Ensure headers are not split over multiple lines
    # The HTTP policy also uses CRLF by default
    b_data = m.as_bytes(policy=email.policy.HTTP)
    del m

    headers, sep, b_content = b_data.partition(b'\r\n\r\n')
    del b_data

    parser = email.parser.BytesHeaderParser().parsebytes

    return (
        parser(headers)['content-type'],  # Message converts to native strings
        b_content
    )


def set_multipart_encoding(encoding):
    """Takes an string with specific encoding type for multipart data.
    Will return reference to function from email.encoders library.
    If given string key doesn't exist it will raise a ValueError"""
    encoders_dict = {
        "base64": email.encoders.encode_base64,
        "7or8bit": email.encoders.encode_7or8bit
    }
    if encoders_dict.get(encoding):
        return encoders_dict.get(encoding)
    else:
        raise ValueError("multipart_encoding must be one of %s." % repr(encoders_dict.keys()))


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
    """
    Creates an argument spec that can be used with any module
    that will be requesting content via urllib/urllib2
    """
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


def url_redirect_argument_spec():
    """
    Creates an addition argument spec to `url_argument_spec`
    for  `follow_redirects` argument
    """
    return dict(
        follow_redirects=dict(type='str', default='safe', choices=['all', 'no', 'none', 'safe', 'urllib2', 'yes']),
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
                               data=json.dumps(data),
                               headers={'Content-type': 'application/json'},
                               method="POST")
        status_code = info["status"]
        body = resp.read()
        if status_code >= 400 :
            body = info['body']
    """

    if not HAS_GZIP:
        module.fail_json(msg=GzipDecodedReader.missing_gzip_error())

    # ensure we use proper tempdir
    old_tempdir = tempfile.tempdir
    tempfile.tempdir = module.tmpdir

    # Get validate_certs from the module params
    validate_certs = module.params.get('validate_certs', True)

    if use_proxy is None:
        use_proxy = module.params.get('use_proxy', True)

    username = module.params.get('url_username', '')
    password = module.params.get('url_password', '')
    http_agent = module.params.get('http_agent', get_user_agent())
    force_basic_auth = module.params.get('force_basic_auth', '')

    follow_redirects = module.params.get('follow_redirects', 'urllib2')

    client_cert = module.params.get('client_cert')
    client_key = module.params.get('client_key')
    use_gssapi = module.params.get('use_gssapi', use_gssapi)

    if not isinstance(cookies, cookiejar.CookieJar):
        cookies = cookiejar.CookieJar()

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
        # Lowercase keys, to conform to py2 behavior
        info.update({k.lower(): v for k, v in r.info().items()})

        # Don't be lossy, append header values for duplicate headers
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
        cookie_dict = {}
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
    except (ConnectionError, ValueError) as e:
        module.fail_json(msg=to_native(e), **info)
    except MissingModuleError as e:
        module.fail_json(msg=to_text(e))
    except urllib.error.HTTPError as e:
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
            info.update({k.lower(): v for k, v in e.info().items()})
        except Exception:
            pass

        info.update({'msg': to_native(e), 'body': body, 'status': e.code})

    except urllib.error.URLError as e:
        code = int(getattr(e, 'code', -1))
        info.update(dict(msg="Request failed: %s" % to_native(e), status=code))
    except OSError as ex:
        info.update(dict(msg=f"Connection failure: {ex}", status=-1))
    except http.client.BadStatusLine as e:
        info.update(dict(msg="Connection failure: connection was closed before a valid response was received: %s" % to_native(e.line), status=-1))
    except Exception as ex:
        info.update(dict(msg="An unknown error occurred: %s" % to_native(ex), status=-1, exception=traceback.format_exc()))
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
    """Download and save a file via HTTP(S) or FTP (needs the module as parameter).
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
    """
    # download file
    bufsize = 65536
    parts = urlparse(url)
    file_prefix, file_ext = _split_multiext(os.path.basename(parts.path), count=2)
    fetch_temp_file = tempfile.NamedTemporaryFile(dir=module.tmpdir, prefix=file_prefix, suffix=file_ext, delete=False)
    module.add_cleanup_file(fetch_temp_file.name)
    try:
        rsp, info = fetch_url(module, url, data, headers, method, use_proxy, force, last_mod_time, timeout,
                              unredirected_headers=unredirected_headers, decompress=decompress, ciphers=ciphers)
        if not rsp or (rsp.code and rsp.code >= 400):
            module.fail_json(msg="Failure downloading %s, %s" % (url, info['msg']))
        data = rsp.read(bufsize)
        while data:
            fetch_temp_file.write(data)
            data = rsp.read(bufsize)
        fetch_temp_file.close()
    except Exception as e:
        module.fail_json(msg="Failure downloading %s, %s" % (url, to_native(e)))
    return fetch_temp_file.name


def get_user_agent():
    """Returns a user agent used by open_url"""
    return u"ansible-httpget"
