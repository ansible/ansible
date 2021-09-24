"""
Primitive replacement for requests to avoid extra dependency.
Avoids use of urllib2 due to lack of SNI support.
"""
from __future__ import annotations

import json
import time
import typing as t

from .util import (
    ApplicationError,
    SubprocessError,
    display,
)

from .util_common import (
    CommonConfig,
    run_command,
)


class HttpClient:
    """Make HTTP requests via curl."""
    def __init__(self, args, always=False, insecure=False, proxy=None):  # type: (CommonConfig, bool, bool, t.Optional[str]) -> None
        self.args = args
        self.always = always
        self.insecure = insecure
        self.proxy = proxy

        self.username = None
        self.password = None

    def get(self, url):  # type: (str) -> HttpResponse
        """Perform an HTTP GET and return the response."""
        return self.request('GET', url)

    def delete(self, url):  # type: (str) -> HttpResponse
        """Perform an HTTP DELETE and return the response."""
        return self.request('DELETE', url)

    def put(self, url, data=None, headers=None):  # type: (str, t.Optional[str], t.Optional[t.Dict[str, str]]) -> HttpResponse
        """Perform an HTTP PUT and return the response."""
        return self.request('PUT', url, data, headers)

    def request(self, method, url, data=None, headers=None):  # type: (str, str, t.Optional[str], t.Optional[t.Dict[str, str]]) -> HttpResponse
        """Perform an HTTP request and return the response."""
        cmd = ['curl', '-s', '-S', '-i', '-X', method]

        if self.insecure:
            cmd += ['--insecure']

        if headers is None:
            headers = {}

        headers['Expect'] = ''  # don't send expect continue header

        if self.username:
            if self.password:
                display.sensitive.add(self.password)
                cmd += ['-u', '%s:%s' % (self.username, self.password)]
            else:
                cmd += ['-u', self.username]

        for header in headers.keys():
            cmd += ['-H', '%s: %s' % (header, headers[header])]

        if data is not None:
            cmd += ['-d', data]

        if self.proxy:
            cmd += ['-x', self.proxy]

        cmd += [url]

        attempts = 0
        max_attempts = 3
        sleep_seconds = 3

        # curl error codes which are safe to retry (request never sent to server)
        retry_on_status = (
            6,  # CURLE_COULDNT_RESOLVE_HOST
        )

        stdout = ''

        while True:
            attempts += 1

            try:
                stdout = run_command(self.args, cmd, capture=True, always=self.always, cmd_verbosity=2)[0]
                break
            except SubprocessError as ex:
                if ex.status in retry_on_status and attempts < max_attempts:
                    display.warning(u'%s' % ex)
                    time.sleep(sleep_seconds)
                    continue

                raise

        if self.args.explain and not self.always:
            return HttpResponse(method, url, 200, '')

        header, body = stdout.split('\r\n\r\n', 1)

        response_headers = header.split('\r\n')
        first_line = response_headers[0]
        http_response = first_line.split(' ')
        status_code = int(http_response[1])

        return HttpResponse(method, url, status_code, body)


class HttpResponse:
    """HTTP response from curl."""
    def __init__(self, method, url, status_code, response):  # type: (str, str, int, str) -> None
        self.method = method
        self.url = url
        self.status_code = status_code
        self.response = response

    def json(self):  # type: () -> t.Any
        """Return the response parsed as JSON, raising an exception if parsing fails."""
        try:
            return json.loads(self.response)
        except ValueError:
            raise HttpError(self.status_code, 'Cannot parse response to %s %s as JSON:\n%s' % (self.method, self.url, self.response))


class HttpError(ApplicationError):
    """HTTP response as an error."""
    def __init__(self, status, message):  # type: (int, str) -> None
        super().__init__('%s: %s' % (status, message))
        self.status = status
