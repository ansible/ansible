# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from abc import abstractmethod

from ansible.plugins import AnsiblePlugin


class HttpApiBase(AnsiblePlugin):
    def __init__(self, connection):
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

    @abstractmethod
    def send_request(self, data, **message_kwargs):
        """Prepares and sends request(s) to device."""
        pass
