# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import os

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO

from ansible.module_utils.urls import urlparse
from ansible.module_utils.urls import generic_urlparse
from ansible.module_utils.urls import Request

try:
    import json as _json
except ImportError:
    import simplejson as _json

try:
    from library.module_utils.network.f5.common import F5ModuleError
except ImportError:
    from ansible.module_utils.network.f5.common import F5ModuleError


"""An F5 REST API URI handler.

Use this module to make calls to an F5 REST server. It is influenced by the same
API that the Python ``requests`` tool uses, but the two are not the same, as the
library here is **much** more simple and targeted specifically to F5's needs.

The ``requests`` design was chosen due to familiarity with the tool. Internally,
the classes contained herein use Ansible native libraries.

The means by which you should use it are similar to ``requests`` basic usage.

Authentication is not handled for you automatically by this library, however it *is*
handled automatically for you in the supporting F5 module_utils code; specifically the
different product module_util files (bigip.py, bigiq.py, etc).

Internal (non-module) usage of this library looks like this.

```
# Create a session instance
mgmt = iControlRestSession()
mgmt.verify = False

server = '1.1.1.1'
port = 443

# Payload used for getting an initial authentication token
payload = {
  'username': 'admin',
  'password': 'secret',
  'loginProviderName': 'tmos'
}

# Create URL to call, injecting server and port
url = f"https://{server}:{port}/mgmt/shared/authn/login"

# Call the API
resp = session.post(url, json=payload)

# View the response
print(resp.json())

# Update the session with the authentication token
session.headers['X-F5-Auth-Token'] = resp.json()['token']['token']

# Create another URL to call, injecting server and port
url = f"https://{server}:{port}/mgmt/tm/ltm/virtual/~Common~virtual1"

# Call the API
resp = session.get(url)

# View the details of a virtual payload
print(resp.json())
```
"""

from ansible.module_utils.six.moves.urllib.error import HTTPError


class Response(object):
    def __init__(self):
        self._content = None
        self.status = None
        self.headers = dict()
        self.url = None
        self.reason = None
        self.request = None
        self.msg = None

    @property
    def content(self):
        return self._content

    @property
    def raw_content(self):
        return self._content

    def json(self):
        return _json.loads(self._content or 'null')

    @property
    def ok(self):
        if self.status is not None and int(self.status) > 400:
            return False
        try:
            response = self.json()
            if 'code' in response and response['code'] > 400:
                return False
        except ValueError:
            pass
        return True


class iControlRestSession(object):
    """Represents a session that communicates with a BigIP.

    This acts as a loose wrapper around Ansible's ``Request`` class. We're doing
    this as interim work until we move to the httpapi connector.
    """
    def __init__(self, headers=None, use_proxy=True, force=False, timeout=120,
                 validate_certs=True, url_username=None, url_password=None,
                 http_agent=None, force_basic_auth=False, follow_redirects='urllib2',
                 client_cert=None, client_key=None, cookies=None):
        self.request = Request(
            headers=headers,
            use_proxy=use_proxy,
            force=force,
            timeout=timeout,
            validate_certs=validate_certs,
            url_username=url_username,
            url_password=url_password,
            http_agent=http_agent,
            force_basic_auth=force_basic_auth,
            follow_redirects=follow_redirects,
            client_cert=client_cert,
            client_key=client_key,
            cookies=cookies
        )
        self.last_url = None

    def get_headers(self, result):
        try:
            return dict(result.getheaders())
        except AttributeError:
            return result.headers

    def update_response(self, response, result):
        response.headers = self.get_headers(result)
        response._content = result.read()
        response.status = result.getcode()
        response.url = result.geturl()
        response.msg = "OK (%s bytes)" % response.headers.get('Content-Length', 'unknown')

    def send(self, method, url, **kwargs):
        response = Response()

        # Set the last_url called
        #
        # This is used by the object destructor to erase the token when the
        # ModuleManager exits and destroys the iControlRestSession object
        self.last_url = url

        body = None
        data = kwargs.pop('data', None)
        json = kwargs.pop('json', None)

        if not data and json is not None:
            self.request.headers['Content-Type'] = 'application/json'
            body = _json.dumps(json)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
        if data:
            body = data
        if body:
            kwargs['data'] = body

        try:
            result = self.request.open(method, url, **kwargs)
        except HTTPError as e:
            # Catch HTTPError delivered from Ansible
            #
            # The structure of this object, in Ansible 2.8 is
            #
            # HttpError {
            #   args
            #   characters_written
            #   close
            #   code
            #   delete
            #   errno
            #   file
            #   filename
            #   filename2
            #   fp
            #   getcode
            #   geturl
            #   hdrs
            #   headers
            #   info
            #   msg
            #   name
            #   reason
            #   strerror
            #   url
            #   with_traceback
            # }
            self.update_response(response, e)
            return response

        self.update_response(response, result)
        return response

    def delete(self, url, **kwargs):
        return self.send('DELETE', url, **kwargs)

    def get(self, url, **kwargs):
        return self.send('GET', url, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.send('PATCH', url, data=data, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.send('POST', url, data=data, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.send('PUT', url, data=data, **kwargs)

    def __del__(self):
        if self.last_url is None:
            return
        token = self.request.headers.get('X-F5-Auth-Token', None)
        if not token:
            return
        try:
            p = generic_urlparse(urlparse(self.last_url))
            uri = "https://{0}:{1}/mgmt/shared/authz/tokens/{2}".format(
                p['hostname'], p['port'], token
            )
            self.delete(uri)
        except ValueError:
            pass


class TransactionContextManager(object):
    def __init__(self, client, validate_only=False):
        self.client = client
        self.validate_only = validate_only
        self.transid = None

    def __enter__(self):
        uri = "https://{0}:{1}/mgmt/tm/transaction/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json={})
        if resp.status not in [200]:
            raise Exception
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        self.transid = response['transId']
        self.client.api.request.headers['X-F5-REST-Coordination-Id'] = self.transid
        return self.client

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.client.api.request.headers.pop('X-F5-REST-Coordination-Id')
        if exc_tb is None:
            uri = "https://{0}:{1}/mgmt/tm/transaction/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                self.transid
            )
            params = dict(
                state="VALIDATING",
                validateOnly=self.validate_only
            )
            resp = self.client.api.patch(uri, json=params)
            if resp.status not in [200]:
                raise Exception


def download_asm_file(client, url, dest):
    """Download an ASM file from the remote device

    This method handles issues with ASM file endpoints that allow
    downloads of ASM objects on the BIG-IP.

    Arguments:
        client (object): The F5RestClient connection object.
        url (string): The URL to download.
        dest (string): The location on (Ansible controller) disk to store the file.

    Returns:
        bool: True on success. False otherwise.
    """

    with open(dest, 'wb') as fileobj:
        headers = {
            'Content-Type': 'application/json'
        }
        data = {'headers': headers,
                'verify': False
                }

        response = client.api.get(url, headers=headers, json=data)
        if response.status == 200:
            if 'Content-Length' not in response.headers:
                error_message = "The Content-Length header is not present."
                raise F5ModuleError(error_message)

            length = response.headers['Content-Length']

            if int(length) > 0:
                fileobj.write(response.content)
            else:
                error = "Invalid Content-Length value returned: %s ," \
                        "the value should be greater than 0" % length
                raise F5ModuleError(error)


def download_file(client, url, dest):
    """Download a file from the remote device

    This method handles the chunking needed to download a file from
    a given URL on the BIG-IP.

    Arguments:
        client (object): The F5RestClient connection object.
        url (string): The URL to download.
        dest (string): The location on (Ansible controller) disk to store the file.

    Returns:
        bool: True on success. False otherwise.
    """
    with open(dest, 'wb') as fileobj:
        chunk_size = 512 * 1024
        start = 0
        end = chunk_size - 1
        size = 0
        current_bytes = 0

        while True:
            content_range = "%s-%s/%s" % (start, end, size)
            headers = {
                'Content-Range': content_range,
                'Content-Type': 'application/octet-stream'
            }
            data = {
                'headers': headers,
                'verify': False,
                'stream': False
            }
            response = client.api.get(url, headers=headers, json=data)
            if response.status == 200:
                # If the size is zero, then this is the first time through
                # the loop and we don't want to write data because we
                # haven't yet figured out the total size of the file.
                if size > 0:
                    current_bytes += chunk_size
                    fileobj.write(response.raw_content)
            # Once we've downloaded the entire file, we can break out of
            # the loop
            if end == size:
                break
            crange = response.headers['Content-Range']
            # Determine the total number of bytes to read.
            if size == 0:
                size = int(crange.split('/')[-1]) - 1
                # If the file is smaller than the chunk_size, the BigIP
                # will return an HTTP 400. Adjust the chunk_size down to
                # the total file size...
                if chunk_size > size:
                    end = size
                # ...and pass on the rest of the code.
                continue
            start += chunk_size
            if (current_bytes + chunk_size) > size:
                end = size
            else:
                end = start + chunk_size - 1
    return True


def upload_file(client, url, src, dest=None):
    """Upload a file to an arbitrary URL.

    This method is responsible for correctly chunking an upload request to an
    arbitrary file worker URL.

    Arguments:
        client (object): The F5RestClient connection object.
        url (string): The URL to upload a file to.
        src (string): The file to be uploaded.
        dest (string): The file name to create on the remote device.

    Examples:
        The ``dest`` may be either an absolute or relative path. The basename
        of the path is used as the remote file name upon upload. For instance,
        in the example below, ``BIGIP-13.1.0.8-0.0.3.iso`` would be the name
        of the remote file.

        The specified URL should be the full URL to where you want to upload a
        file. BIG-IP has many different URLs that can be used to handle different
        types of files. This is why a full URL is required.

        >>> from ansible.module_utils.network.f5.icontrol import upload_client
        >>> url = 'https://{0}:{1}/mgmt/cm/autodeploy/software-image-uploads'.format(
        ...   self.client.provider['server'],
        ...   self.client.provider['server_port']
        ... )
        >>> dest = '/path/to/BIGIP-13.1.0.8-0.0.3.iso'
        >>> upload_file(self.client, url, dest)
        True

    Returns:
        bool: True on success. False otherwise.

    Raises:
        F5ModuleError: Raised if ``retries`` limit is exceeded.
    """
    if isinstance(src, StringIO) or isinstance(src, BytesIO):
        fileobj = src
    else:
        fileobj = open(src, 'rb')

    try:
        size = os.stat(src).st_size
        is_file = True
    except TypeError:
        src.seek(0, os.SEEK_END)
        size = src.tell()
        src.seek(0)
        is_file = False

    # This appears to be the largest chunk size that iControlREST can handle.
    #
    # The trade-off you are making by choosing a chunk size is speed, over size of
    # transmission. A lower chunk size will be slower because a smaller amount of
    # data is read from disk and sent via HTTP. Lots of disk reads are slower and
    # There is overhead in sending the request to the BIG-IP.
    #
    # Larger chunk sizes are faster because more data is read from disk in one
    # go, and therefore more data is transmitted to the BIG-IP in one HTTP request.
    #
    # If you are transmitting over a slow link though, it may be more reliable to
    # transmit many small chunks that fewer large chunks. It will clearly take
    # longer, but it may be more robust.
    chunk_size = 1024 * 7168
    start = 0
    retries = 0
    if dest is None and is_file:
        basename = os.path.basename(src)
    else:
        basename = dest
    url = '{0}/{1}'.format(url.rstrip('/'), basename)

    while True:
        if retries == 3:
            # Retries are used here to allow the REST API to recover if you kill
            # an upload mid-transfer.
            #
            # There exists a case where retrying a new upload will result in the
            # API returning the POSTed payload (in bytes) with a non-200 response
            # code.
            #
            # Retrying (after seeking back to 0) seems to resolve this problem.
            raise F5ModuleError(
                "Failed to upload file too many times."
            )
        try:
            file_slice = fileobj.read(chunk_size)
            if not file_slice:
                break

            current_bytes = len(file_slice)
            if current_bytes < chunk_size:
                end = size
            else:
                end = start + current_bytes
            headers = {
                'Content-Range': '%s-%s/%s' % (start, end - 1, size),
                'Content-Type': 'application/octet-stream'
            }

            # Data should always be sent using the ``data`` keyword and not the
            # ``json`` keyword. This allows bytes to be sent (such as in the case
            # of uploading ISO files.
            response = client.api.post(url, headers=headers, data=file_slice)

            if response.status != 200:
                # When this fails, the output is usually the body of whatever you
                # POSTed. This is almost always unreadable because it is a series
                # of bytes.
                #
                # Therefore, including an empty exception here.
                raise F5ModuleError()
            start += current_bytes
        except F5ModuleError:
            # You must seek back to the beginning of the file upon exception.
            #
            # If this is not done, then you risk uploading a partial file.
            fileobj.seek(0)
            retries += 1
    return True


def tmos_version(client):
    uri = "https://{0}:{1}/mgmt/tm/sys/".format(
        client.provider['server'],
        client.provider['server_port'],
    )
    resp = client.api.get(uri)

    try:
        response = resp.json()
    except ValueError as ex:
        raise F5ModuleError(str(ex))

    if 'code' in response and response['code'] in [400, 403]:
        if 'message' in response:
            raise F5ModuleError(response['message'])
        else:
            raise F5ModuleError(resp.content)

    to_parse = urlparse(response['selfLink'])
    query = to_parse.query
    version = query.split('=')[1]
    return version


def bigiq_version(client):
    uri = "https://{0}:{1}/mgmt/shared/resolver/device-groups/cm-shared-all-big-iqs/devices".format(
        client.provider['server'],
        client.provider['server_port'],
    )
    query = "?$select=version"

    resp = client.api.get(uri + query)

    try:
        response = resp.json()
    except ValueError as ex:
        raise F5ModuleError(str(ex))

    if 'code' in response and response['code'] in [400, 403]:
        if 'message' in response:
            raise F5ModuleError(response['message'])
        else:
            raise F5ModuleError(resp.content)

    if 'items' in response:
        version = response['items'][0]['version']
        return version

    raise F5ModuleError(
        'Failed to retrieve BIGIQ version information.'
    )


def module_provisioned(client, module_name):
    provisioned = modules_provisioned(client)
    if module_name in provisioned:
        return True
    return False


def modules_provisioned(client):
    """Returns a list of all provisioned modules

    Args:
        client: Client connection to the BIG-IP

    Returns:
        A list of provisioned modules in their short name for.
        For example, ['afm', 'asm', 'ltm']
    """
    uri = "https://{0}:{1}/mgmt/tm/sys/provision".format(
        client.provider['server'],
        client.provider['server_port']
    )
    resp = client.api.get(uri)

    try:
        response = resp.json()
    except ValueError as ex:
        raise F5ModuleError(str(ex))

    if 'code' in response and response['code'] in [400, 403]:
        if 'message' in response:
            raise F5ModuleError(response['message'])
        else:
            raise F5ModuleError(resp.content)
    if 'items' not in response:
        return []
    return [x['name'] for x in response['items'] if x['level'] != 'none']
