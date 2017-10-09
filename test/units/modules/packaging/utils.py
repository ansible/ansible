import json

from ansible.compat.tests.mock import patch
from ansible.module_utils import basic
from ansible.module_utils.six.moves import xmlrpc_client
from ansible.module_utils._text import to_bytes


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


def get_method_name(request_body):
    return xmlrpc_client.loads(request_body)[1]


def mock_request(responses, module_name):
    def transport_request(host, handler, request_body, verbose=0):
        """Fake request"""
        method_name = get_method_name(request_body)
        excepted_name, response = responses.pop(0)
        if method_name == excepted_name:
            if isinstance(response, Exception):
                raise response
            else:
                return response
        else:
            raise Exception('Expected call: %r, called with: %r' % (excepted_name, method_name))

    target = '{0}.xmlrpc_client.Transport.request'.format(module_name)
    return patch(target, side_effect=transport_request)
