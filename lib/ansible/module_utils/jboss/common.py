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
import os
import socket
import re

import logging.handlers

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(module)s.%(funcName)s: %(message)s', "%Y-%m-%d %H:%M:%S")
path_logfile = os.path.join(os.path.abspath('.'), "autodeploy_wf.log")
handler = logging.FileHandler(filename=path_logfile)
handler.setFormatter(formatter)
log.addHandler(handler)

class OperationError(Exception):
    """Error response from Management API"""

class Client(object):

    def __init__(self, username, password, host='127.0.0.1', port=9990, timeout=90, headers=None):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 9990
        if timeout is None:
            timeout = 90
        log.info("Class init host - {0}".format(host))
        log.info("Class init port - {0}".format(port))
        log.info("Class init timeout - {0}".format(timeout))
        self.url = 'http://{0}:{1}/management'.format(host, port)
        log.info("Class init url - {0}".format(self.url))
        self.username = username
        self.password = password
        self.timeout = timeout
        self.headers = {'operation-headers': headers}

    @classmethod
    def from_config(cls, params):
        log.info("merge config host - {0}".format(params['host']))
        log.info("merge config port - {0}".format(params['port']))
        log.info("merge config password - {0}".format(params['password']))
        log.info("merge config timeout - {0}".format(params['timeout']))
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

        log.info("url {0}".format(self.url))
        log.info("request {0}".format(json.dumps(payload)))
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
                log.critical('Invalid credentials')
                raise OperationError('Invalid credentials')

            if err.getcode() == 500:
                log.info("HTTP/1.1 500 Internal Server Error")
                api_response = json.loads(err.read().decode('utf-8'))
                log.info("Ignore_errors: {0}".format(unsafe))
                log.info(api_response)
                if not unsafe:
                    raise OperationError(api_response['failure-description'])
                else:
                    return api_response
        except ValueError as e:
            log.critical("No HTTP/1.1 error code")
            log.critical("Error '{0}' occured. Arguments {1}.".format(e.message, e.args))
            raise OperationError("Wrong url management")
        except socket.timeout as e:
            log.critical("Operation timeout")
            log.critical("Error '{0}' occured. Arguments {1}.".format(e.message, e.args))
            raise OperationError("Operation timeout")
        except Exception as e:
            log.critical("Others errors")
            log.critical("Error '{0}' occured. Arguments {1}.".format(e.message, e.args))
            ## Clear HTML tags
            cleanr = re.compile('<')
            e_message = re.sub(cleanr, '', str(e))
            cleanr2 = re.compile('>')
            e_message = re.sub(cleanr2, '', e_message)
            raise OperationError(e_message)

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
    username=dict(type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_USER'])),
    password=dict(no_log=True, type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_PASSWORD'])),
    host=dict(type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_HOST'])),
    port=dict(type='int', fallback=(env_fallback, ['JBOSS_MANAGEMENT_PORT'])),
    timeout=dict(type='int', default=300),
    operation_headers=dict(type='dict', require=False))


class JBossAnsibleModule(AnsibleModule):

    def __init__(self, argument_spec, supports_check_mode):
        argument_spec.update(JBOSS_COMMON_ARGS)

        AnsibleModule.__init__(self, argument_spec=argument_spec, supports_check_mode=supports_check_mode)
