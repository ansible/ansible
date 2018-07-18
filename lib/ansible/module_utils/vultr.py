# -*- coding: utf-8 -*-
# (c) 2017, René Moser <mail@renemoser.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import time
import urllib
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.urls import fetch_url


VULTR_API_ENDPOINT = "https://api.vultr.com"


def vultr_argument_spec():
    return dict(
        api_key=dict(default=os.environ.get('VULTR_API_KEY'), no_log=True),
        api_timeout=dict(type='int', default=os.environ.get('VULTR_API_TIMEOUT')),
        api_retries=dict(type='int', default=os.environ.get('VULTR_API_RETRIES')),
        api_account=dict(default=os.environ.get('VULTR_API_ACCOUNT') or 'default'),
        api_endpoint=dict(default=os.environ.get('VULTR_API_ENDPOINT')),
        validate_certs=dict(default=True, type='bool'),
    )


class Vultr:

    def __init__(self, module, namespace):
        self.module = module

        # Namespace use for returns
        self.namespace = namespace
        self.result = {
            'changed': False,
            namespace: dict(),
            'diff': dict(before=dict(), after=dict())
        }

        # For caching HTTP API responses
        self.api_cache = dict()

        try:
            config = self.read_env_variables()
            config.update(self.read_ini_config())
        except KeyError:
            config = {}

        try:
            self.api_config = {
                'api_key': self.module.params.get('api_key') or config.get('key'),
                'api_timeout': self.module.params.get('api_timeout') or int(config.get('timeout') or 60),
                'api_retries': self.module.params.get('api_retries') or int(config.get('retries') or 5),
                'api_endpoint': self.module.params.get('api_endpoint') or config.get('endpoint') or VULTR_API_ENDPOINT,
            }
        except ValueError as e:
            self.fail_json(msg="One of the following settings, "
                               "in section '%s' in the ini config file has not an int value: timeout, retries. "
                               "Error was %s" % (self.module.params.get('api_account'), to_native(e)))

        if not self.api_config.get('api_key'):
            self.module.fail_json(msg="The API key is not speicied. Please refer to the documentation.")

        # Common vultr returns
        self.result['vultr_api'] = {
            'api_account': self.module.params.get('api_account'),
            'api_timeout': self.api_config['api_timeout'],
            'api_retries': self.api_config['api_retries'],
            'api_endpoint': self.api_config['api_endpoint'],
        }

        # Headers to be passed to the API
        self.headers = {
            'API-Key': "%s" % self.api_config['api_key'],
            'User-Agent': "Ansible Vultr",
            'Accept': 'application/json',
        }

    def read_env_variables(self):
        keys = ['key', 'timeout', 'retries', 'endpoint']
        env_conf = {}
        for key in keys:
            if 'VULTR_API_%s' % key.upper() not in os.environ:
                continue
            env_conf[key] = os.environ['VULTR_API_%s' % key.upper()]

        return env_conf

    def read_ini_config(self):
        ini_group = self.module.params.get('api_account')

        paths = (
            os.path.join(os.path.expanduser('~'), '.vultr.ini'),
            os.path.join(os.getcwd(), 'vultr.ini'),
        )
        if 'VULTR_API_CONFIG' in os.environ:
            paths += (os.path.expanduser(os.environ['VULTR_API_CONFIG']),)

        conf = configparser.ConfigParser()
        conf.read(paths)

        if not conf._sections.get(ini_group):
            return dict()

        return dict(conf.items(ini_group))

    def fail_json(self, **kwargs):
        self.result.update(kwargs)
        self.module.fail_json(**self.result)

    def get_yes_or_no(self, key):
        if self.module.params.get(key) is not None:
            return 'yes' if self.module.params.get(key) is True else 'no'

    def switch_enable_disable(self, resource, param_key, resource_key=None):
        if resource_key is None:
            resource_key = param_key

        param = self.module.params.get(param_key)
        if param is None:
            return

        r_value = resource.get(resource_key)
        if isinstance(param, bool):
            if param is True and r_value not in ['yes', 'enable']:
                return "enable"
            elif param is False and r_value not in ['no', 'disable']:
                return "disable"
        else:
            if r_value is None:
                return "enable"
            else:
                return "disable"

    def api_query(self, path="/", method="GET", data=None):
        url = self.api_config['api_endpoint'] + path

        if data:
            data_encoded = dict()
            data_list = ""
            for k, v in data.items():
                if isinstance(v, list):
                    for s in v:
                        try:
                            data_list += '&%s[]=%s' % (k, urllib.quote(s))
                        except AttributeError:
                            data_list += '&%s[]=%s' % (k, urllib.parse.quote(s))
                elif v is not None:
                    data_encoded[k] = v
            try:
                data = urllib.urlencode(data_encoded) + data_list
            except AttributeError:
                data = urllib.parse.urlencode(data_encoded) + data_list

        for s in range(0, self.api_config['api_retries']):
            response, info = fetch_url(
                module=self.module,
                url=url,
                data=data,
                method=method,
                headers=self.headers,
                timeout=self.api_config['api_timeout'],
            )

            # Did we hit the rate limit?
            if info.get('status') and info.get('status') != 503:
                break

            # Vultr has a rate limiting requests per second, try to be polite
            time.sleep(1)

        else:
            self.fail_json(msg="Reached API retries limit %s for URL %s, method %s with data %s. Returned %s, with body: %s %s" % (
                self.api_config['api_retries'],
                url,
                method,
                data,
                info['status'],
                info['msg'],
                info.get('body')
            ))

        if info.get('status') != 200:
            self.fail_json(msg="URL %s, method %s with data %s. Returned %s, with body: %s %s" % (
                url,
                method,
                data,
                info['status'],
                info['msg'],
                info.get('body')
            ))

        res = response.read()
        if not res:
            return {}

        try:
            return self.module.from_json(to_text(res))
        except ValueError as e:
            self.module.fail_json(msg="Could not process response into json: %s" % e)

    def query_resource_by_key(self, key, value, resource='regions', query_by='list', params=None, use_cache=False):
        if not value:
            return {}

        if use_cache:
            if resource in self.api_cache:
                if self.api_cache[resource] and self.api_cache[resource].get(key) == value:
                    return self.api_cache[resource]

        r_list = self.api_query(path="/v1/%s/%s" % (resource, query_by), data=params)

        if not r_list:
            return {}

        for r_id, r_data in r_list.items():
            if r_data[key] == value:
                self.api_cache.update({
                    resource: r_data
                })
                return r_data

        self.module.fail_json(msg="Could not find %s with %s: %s" % (resource, key, value))

    def normalize_result(self, resource):
        for search_key, config in self.returns.items():
            if search_key in resource:
                if 'convert_to' in config:
                    if config['convert_to'] == 'int':
                        resource[search_key] = int(resource[search_key])
                    elif config['convert_to'] == 'float':
                        resource[search_key] = float(resource[search_key])
                    elif config['convert_to'] == 'bool':
                        resource[search_key] = True if resource[search_key] == 'yes' else False

                if 'key' in config:
                    resource[config['key']] = resource[search_key]
                    del resource[search_key]

        return resource

    def get_result(self, resource):
        if resource:
            if isinstance(resource, list):
                self.result[self.namespace] = [self.normalize_result(item) for item in resource]
            else:
                self.result[self.namespace] = self.normalize_result(resource)

        return self.result
