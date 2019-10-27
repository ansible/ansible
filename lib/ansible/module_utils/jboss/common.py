# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.urls import open_url
import ansible.module_utils.jboss.operation_request as op
import json
import socket


class OperationError(Exception):
    """Error response from Management API"""

class Client(object):

    def __init__(self, username, password, host, port, timeout, headers):
        self.url = 'http://{0}:{1}/management'.format(host, port)
        self.username = username
        self.password = password
        self.timeout = timeout
        self.headers = {'operation-headers': headers}

    @classmethod
    def from_config(cls, params):
        return cls(params['username'],
                   params['password'],
                   params['host'],
                   params['port'],
                   params['timeout'],
                   params['operation_headers'])

    def _request(self, payload, unsafe=False):
        content_type_header = {'Content-Type': 'application/json'}

        if self.headers['operation-headers'] and not payload['operation'] == 'read-resource':
            payload.update(self.headers)

        try:
            response = open_url(
                self.url,
                data=json.dumps(payload),
                headers=content_type_header,
                method='POST',
                use_proxy=False,
                url_username=self.username,
                url_password=self.password,
                timeout=self.timeout,
                follow_redirects=True)
        except HTTPError as err:
            if err.getcode() == 401:
                raise OperationError('Invalid credentials')
            if err.getcode() == 500:
                api_response = json.loads(err.read().decode('utf-8'))

                if not unsafe:
                    raise OperationError(api_response['failure-description'])
                else:
                    return api_response
            raise OperationError(err)
        except socket.timeout:
            raise OperationError("Operation timeout")
        except Exception as err:
            raise OperationError(err)

        return json.loads(response.read().decode('utf-8'))

    def execute(self, operation, parameters, ignore_failed_outcome, path=None):
        payload = op.execute(operation, parameters, path)
        return self._request(payload, ignore_failed_outcome)

    def read(self, path):
        response = self._request(op.read(path), True)

        exists = response['outcome'] == 'success'

        state = response['result'] if exists else {}

        return exists, state

    def add(self, path, attributes):
        return self._request(op.add(path, attributes))

    def remove(self, path):
        return self._request(op.remove(path))

    def update(self, path, attributes):
        operations = []
        for name, value in attributes.items():
            operations.append(op.write_attribute(path, name, value))

        payload = op.composite(operations)

        return self._request(payload)

    def deploy(self, name, src, server_group=None):
        payload = op.composite(
            op.deploy(name, src, server_group))

        return self._request(payload)

    def undeploy(self, name, server_group=None):
        payload = op.composite(
            op.undeploy(name, server_group))

        return self._request(payload)

    def update_deploy(self, name, src, server_group=None):
        operations = op.undeploy(name, server_group) + op.deploy(name, src, server_group)
        payload = op.composite(operations)

        return self._request(payload)


JBOSS_COMMON_ARGS = dict(
    username=dict(type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_USER']), required=True),
    password=dict(no_log=True, type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_PASSWORD']), required=True),
    host=dict(type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_HOST']), default='localhost'),
    port=dict(type='int', fallback=(env_fallback, ['JBOSS_MANAGEMENT_PORT']), default=9990),
    timeout=dict(type='int', default=300),
    operation_headers=dict(type='dict', require=False))


class JBossAnsibleModule(AnsibleModule):

    def __init__(self, argument_spec, supports_check_mode, required_if=None):
        argument_spec.update(JBOSS_COMMON_ARGS)

        AnsibleModule.__init__(self,
                               argument_spec=argument_spec,
                               supports_check_mode=supports_check_mode,
                               required_if=required_if)
