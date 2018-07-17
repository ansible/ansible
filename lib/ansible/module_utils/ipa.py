# -*- coding: utf-8 -*-
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2016 Thomas Krahn (@Nosmoht)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

try:
    import json
except ImportError:
    import simplejson as json

import re
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import env_fallback


class IPAClient(object):
    def __init__(self, module, host, port, protocol):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.module = module
        self.headers = None

    def get_base_url(self):
        return '%s://%s/ipa' % (self.protocol, self.host)

    def get_json_url(self):
        return '%s/session/json' % self.get_base_url()

    def login(self, username, password):
        url = '%s/session/login_password' % self.get_base_url()
        data = 'user=%s&password=%s' % (quote(username, safe=''), quote(password, safe=''))
        headers = {'referer': self.get_base_url(),
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'text/plain'}
        try:
            resp, info = fetch_url(module=self.module, url=url, data=to_bytes(data), headers=headers)
            status_code = info['status']
            if status_code not in [200, 201, 204]:
                self._fail('login', info['msg'])

            self.headers = {'referer': self.get_base_url(),
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Cookie': resp.info().get('Set-Cookie')}
        except Exception as e:
            self._fail('login', to_native(e))

    def _fail(self, msg, e):
        if 'message' in e:
            err_string = e.get('message')
        else:
            err_string = e
        self.module.fail_json(msg='%s: %s' % (msg, err_string))

    def get_ipa_version(self):
        response = self.ping()['summary']
        ipa_ver_regex = re.compile(r'IPA server version (\d\.\d\.\d).*')
        version_match = ipa_ver_regex.match(response)
        ipa_version = None
        if version_match:
            ipa_version = version_match.groups()[0]
        return ipa_version

    def ping(self):
        return self._post_json(method='ping', name=None)

    def _post_json(self, method, name, item=None):
        if item is None:
            item = {}
        url = '%s/session/json' % self.get_base_url()
        data = dict(method=method)

        # TODO: We should probably handle this a little better.
        if method in ('ping', 'config_show'):
            data['params'] = [[], {}]
        elif method == 'config_mod':
            data['params'] = [[], item]
        else:
            data['params'] = [[name], item]

        try:
            resp, info = fetch_url(module=self.module, url=url, data=to_bytes(json.dumps(data)), headers=self.headers)
            status_code = info['status']
            if status_code not in [200, 201, 204]:
                self._fail(method, info['msg'])
        except Exception as e:
            self._fail('post %s' % method, to_native(e))

        if PY3:
            charset = resp.headers.get_content_charset('latin-1')
        else:
            response_charset = resp.headers.getparam('charset')
            if response_charset:
                charset = response_charset
            else:
                charset = 'latin-1'
        resp = json.loads(to_text(resp.read(), encoding=charset), encoding=charset)
        err = resp.get('error')
        if err is not None:
            self._fail('response %s' % method, err)

        if 'result' in resp:
            result = resp.get('result')
            if 'result' in result:
                result = result.get('result')
                if isinstance(result, list):
                    if len(result) > 0:
                        return result[0]
                    else:
                        return {}
            return result
        return None

    def get_diff(self, ipa_data, module_data):
        result = []
        for key in module_data.keys():
            mod_value = module_data.get(key, None)
            if isinstance(mod_value, list):
                default = []
            else:
                default = None
            ipa_value = ipa_data.get(key, default)
            if isinstance(ipa_value, list) and not isinstance(mod_value, list):
                mod_value = [mod_value]
            if isinstance(ipa_value, list) and isinstance(mod_value, list):
                mod_value = sorted(mod_value)
                ipa_value = sorted(ipa_value)
            if mod_value != ipa_value:
                result.append(key)
        return result

    def modify_if_diff(self, name, ipa_list, module_list, add_method, remove_method, item=None):
        changed = False
        diff = list(set(ipa_list) - set(module_list))
        if len(diff) > 0:
            changed = True
            if not self.module.check_mode:
                if item:
                    remove_method(name=name, item={item: diff})
                else:
                    remove_method(name=name, item=diff)

        diff = list(set(module_list) - set(ipa_list))
        if len(diff) > 0:
            changed = True
            if not self.module.check_mode:
                if item:
                    add_method(name=name, item={item: diff})
                else:
                    add_method(name=name, item=diff)

        return changed


def ipa_argument_spec():
    return dict(
        ipa_prot=dict(type='str', default='https', choices=['http', 'https'], fallback=(env_fallback, ['IPA_PROT'])),
        ipa_host=dict(type='str', default='ipa.example.com', fallback=(env_fallback, ['IPA_HOST'])),
        ipa_port=dict(type='int', default=443, fallback=(env_fallback, ['IPA_PORT'])),
        ipa_user=dict(type='str', default='admin', fallback=(env_fallback, ['IPA_USER'])),
        ipa_pass=dict(type='str', required=True, no_log=True, fallback=(env_fallback, ['IPA_PASS'])),
        validate_certs=dict(type='bool', default=True),
    )
