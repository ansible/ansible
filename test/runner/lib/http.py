"""
Primitive replacement for requests to avoid extra dependency.
Avoids use of urllib2 due to lack of SNI support.
"""

from __future__ import absolute_import, print_function

import json

try:
    from urllib import urlencode
except ImportError:
    # noinspection PyCompatibility,PyUnresolvedReferences,PyUnresolvedReferences
    from urllib.parse import urlencode  # pylint: disable=locally-disabled, import-error, no-name-in-module

from lib.util import (
    CommonConfig,
    ApplicationError,
    run_command,
)


class HttpClient(object):
    """Make HTTP requests via curl."""
    def __init__(self, args, always=False):
        """
        :type args: CommonConfig
        :type always: bool
        """
        self.args = args
        self.always = always

    def get(self, url):
        """
        :type url: str
        :rtype: HttpResponse
        """
        return self.request('GET', url)

    def delete(self, url):
        """
        :type url: str
        :rtype: HttpResponse
        """
        return self.request('DELETE', url)

    def put(self, url, data=None, headers=None):
        """
        :type url: str
        :type data: str | None
        :type headers: dict[str, str] | None
        :rtype: HttpResponse
        """
        return self.request('PUT', url, data, headers)

    def request(self, method, url, data=None, headers=None):
        """
        :type method: str
        :type url: str
        :type data: str | None
        :type headers: dict[str, str] | None
        :rtype: HttpResponse
        """
        cmd = ['curl', '-s', '-S', '-i', '-X', method]

        if headers is None:
            headers = {}

        headers['Expect'] = ''  # don't send expect continue header

        for header in headers.keys():
            cmd += ['-H', '%s: %s' % (header, headers[header])]

        if data is not None:
            cmd += ['-d', data]

        cmd += [url]

        stdout, _ = run_command(self.args, cmd, capture=True, always=self.always, cmd_verbosity=2)

        if self.args.explain and not self.always:
            return HttpResponse(200, '')

        header, body = stdout.split('\r\n\r\n', 1)

        response_headers = header.split('\r\n')
        first_line = response_headers[0]
        http_response = first_line.split(' ')
        status_code = int(http_response[1])

        return HttpResponse(status_code, body)


class HttpResponse(object):
    """HTTP response from curl."""
    def __init__(self, status_code, response):
        """
        :type status_code: int
        :type response: str
        """
        self.status_code = status_code
        self.response = response

    def json(self):
        """
        :rtype: any
        """
        try:
            return json.loads(self.response)
        except ValueError:
            raise HttpError(self.status_code, 'Cannot parse response as JSON:\n%s' % self.response)


class HttpError(ApplicationError):
    """HTTP response as an error."""
    def __init__(self, status, message):
        """
        :type status: int
        :type message: str
        """
        super(HttpError, self).__init__('%s: %s' % (status, message))
        self.status = status
