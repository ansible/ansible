# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from abc import abstractmethod

from ansible.plugins import AnsiblePlugin


class HttpApiBase(AnsiblePlugin):
    def __init__(self, connection):
        super(HttpApiBase, self).__init__()

        self.connection = connection
        self._become = False
        self._become_pass = ''

    def set_become(self, become_context):
        self._become = become_context.become
        self._become_pass = getattr(become_context, 'become_pass') or ''

    def login(self, username, password):
        """Call a defined login endpoint to receive an authentication token.

        This should only be implemented if the API has a single endpoint which
        can turn HTTP basic auth into a token which can be reused for the rest
        of the calls for the session.
        """
        pass

    def logout(self):
        """ Call to implement session logout.

        Method to clear session gracefully e.g. tokens granted in login
        need to be revoked.
        """
        pass

    def update_auth(self, response, response_text):
        """Return per-request auth token.

        The response should be a dictionary that can be plugged into the
        headers of a request. The default implementation uses cookie data.
        If no authentication data is found, return None
        """
        cookie = response.info().get('Set-Cookie')
        if cookie:
            return {'Cookie': cookie}

        return None

    def handle_httperror(self, exc):
        """Overridable method for dealing with HTTP codes.

        This method will attempt to handle known cases of HTTP status codes.
        If your API uses status codes to convey information in a regular way,
        you can override this method to handle it appropriately.

        :returns:
            * True if the code has been handled in a way that the request
            may be resent without changes.
            * False if the error cannot be handled or recovered from by the
            plugin. This will result in the HTTPError being raised as an
            exception for the caller to deal with as appropriate (most likely
            by failing).
            * Any other value returned is taken as a valid response from the
            server without making another request. In many cases, this can just
            be the original exception.
            """
        if exc.code == 401:
            if self.connection._auth:
                # Stored auth appears to be invalid, clear and retry
                self.connection._auth = None
                self.login(self.connection.get_option('remote_user'), self.connection.get_option('password'))
                return True
            else:
                # Unauthorized and there's no token. Return an error
                return False

        return exc

    @abstractmethod
    def send_request(self, data, **message_kwargs):
        """Prepares and sends request(s) to device."""
        pass
