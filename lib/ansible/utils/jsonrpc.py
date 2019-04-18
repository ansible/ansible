# (c) 2017, Peter Sprygada <psprygad@redhat.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import traceback

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.six import binary_type
from ansible.utils.display import Display

display = Display()


class JsonRpcServer(object):

    _objects = set()

    def handle_request(self, request):
        request = json.loads(to_text(request, errors='surrogate_then_replace'))

        method = request.get('method')

        if method.startswith('rpc.') or method.startswith('_'):
            error = self.invalid_request()
            return json.dumps(error)

        args, kwargs = request.get('params')
        setattr(self, '_identifier', request.get('id'))

        rpc_method = None
        for obj in self._objects:
            rpc_method = getattr(obj, method, None)
            if rpc_method:
                break

        if not rpc_method:
            error = self.method_not_found()
            response = json.dumps(error)
        else:
            try:
                result = rpc_method(*args, **kwargs)
            except ConnectionError as exc:
                display.vvv(traceback.format_exc())
                try:
                    error = self.error(code=exc.code, message=to_text(exc))
                except AttributeError:
                    error = self.internal_error(data=to_text(exc))
                response = json.dumps(error)
            except Exception as exc:
                display.vvv(traceback.format_exc())
                error = self.internal_error(data=to_text(exc, errors='surrogate_then_replace'))
                response = json.dumps(error)
            else:
                if isinstance(result, dict) and 'jsonrpc' in result:
                    response = result
                else:
                    response = self.response(result)

                response = json.dumps(response)

        delattr(self, '_identifier')

        return response

    def register(self, obj):
        self._objects.add(obj)

    def header(self):
        return {'jsonrpc': '2.0', 'id': self._identifier}

    def response(self, result=None):
        response = self.header()
        if isinstance(result, binary_type):
            result = to_text(result)
        response['result'] = result
        return response

    def error(self, code, message, data=None):
        response = self.header()
        error = {'code': code, 'message': message}
        if data:
            error['data'] = data
        response['error'] = error
        return response

    # json-rpc standard errors (-32768 .. -32000)
    def parse_error(self, data=None):
        return self.error(-32700, 'Parse error', data)

    def method_not_found(self, data=None):
        return self.error(-32601, 'Method not found', data)

    def invalid_request(self, data=None):
        return self.error(-32600, 'Invalid request', data)

    def invalid_params(self, data=None):
        return self.error(-32602, 'Invalid params', data)

    def internal_error(self, data=None):
        return self.error(-32603, 'Internal error', data)
