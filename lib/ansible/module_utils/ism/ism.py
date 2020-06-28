#!/usr/bin/python
# coding: utf-8 -*-



from ansible.plugins.inspur_sdk import ism
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems


ism_provider_spec = {
    'host': dict(),
    'username': dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
}
ism_argument_spec = {
    'provider': dict(type='dict', options=ism_provider_spec),
}
ism_top_spec = {
    'host': dict(removed_in_version=2.9),
    'username': dict(removed_in_version=2.9),
    'password': dict(removed_in_version=2.9, no_log=True),
}
ism_argument_spec.update(ism_top_spec)

def load_params(module):
    """load_params"""
    provider = module.params.get('provider') or dict()
    for key, value in iteritems(provider):
        if key in ism_argument_spec:
            if module.params.get(key) is None and value is not None:
                module.params[key] = value


def get_connection(module):
    """get_connection"""
    load_params(module)
    dict_cpu = module.params
    result = ism.main(dict_cpu)
    return result