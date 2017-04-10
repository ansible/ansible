# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
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

import os

# import module snippets
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.six import integer_types, string_types
from ansible.module_utils._text import to_text
from ansible.module_utils.urls import fetch_url

EXO_DNS_BASEURL = "https://api.exoscale.ch/dns/v1"


def exo_dns_argument_spec():
    return dict(
        api_key=dict(default=None, no_log=True),
        api_secret=dict(default=None, no_log=True),
        api_timeout=dict(type='int', default=10),
        api_region=dict(default='cloudstack'),
        validate_certs=dict(default='yes', type='bool'),
    )


def exo_dns_required_together():
    return [['api_key', 'api_secret']]


class ExoDns(object):

    def __init__(self, module):
        self.module = module

        self.api_key = self.module.params. get('api_key')
        self.api_secret = self.module.params.get('api_secret')
        if not (self.api_key and self.api_secret):
            try:
                region = self.module.params.get('api_region')
                config = self.read_config(ini_group=region)
                self.api_key = config['key']
                self.api_secret = config['secret']
            except Exception:
                e = get_exception()
                self.module.fail_json(msg="Error while processing config: %s" % e)

        self.headers = {
            'X-DNS-Token': "%s:%s" % (self.api_key, self.api_secret),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        self.result = {
            'changed': False,
            'diff': {
                'before': {},
                'after': {},
            }
        }

    def read_config(self, ini_group=None):
        if not ini_group:
            ini_group = os.environ.get('CLOUDSTACK_REGION', 'cloudstack')

        keys = ['key', 'secret']
        env_conf = {}
        for key in keys:
            if 'CLOUDSTACK_%s' % key.upper() not in os.environ:
                break
            else:
                env_conf[key] = os.environ['CLOUDSTACK_%s' % key.upper()]
        else:
            return env_conf

        # Config file: $PWD/cloudstack.ini or $HOME/.cloudstack.ini
        # Last read wins in configparser
        paths = (
            os.path.join(os.path.expanduser('~'), '.cloudstack.ini'),
            os.path.join(os.getcwd(), 'cloudstack.ini'),
        )
        # Look at CLOUDSTACK_CONFIG first if present
        if 'CLOUDSTACK_CONFIG' in os.environ:
            paths += (os.path.expanduser(os.environ['CLOUDSTACK_CONFIG']),)
        if not any([os.path.exists(c) for c in paths]):
            self.module.fail_json(msg="Config file not found. Tried : %s" % ", ".join(paths))

        conf = configparser.ConfigParser()
        conf.read(paths)
        return dict(conf.items(ini_group))

    def api_query(self, resource="/domains", method="GET", data=None):
        url = EXO_DNS_BASEURL + resource
        if data:
            data = self.module.jsonify(data)

        response, info = fetch_url(
            module=self.module,
            url=url,
            data=data,
            method=method,
            headers=self.headers,
            timeout=self.module.params.get('api_timeout'),
        )

        if info['status'] not in (200, 201, 204):
            self.module.fail_json(msg="%s returned %s, with body: %s" % (url, info['status'], info['msg']))

        try:
            return self.module.from_json(to_text(response.read()))

        except Exception:
            e = get_exception()
            self.module.fail_json(msg="Could not process response into json: %s" % e)

    def has_changed(self, want_dict, current_dict, only_keys=None):
        changed = False
        for key, value in want_dict.items():
            # Optionally limit by a list of keys
            if only_keys and key not in only_keys:
                continue
            # Skip None values
            if value is None:
                continue
            if key in current_dict:
                if isinstance(current_dict[key], integer_types):
                    if value != current_dict[key]:
                        self.result['diff']['before'][key] = current_dict[key]
                        self.result['diff']['after'][key] = value
                        changed = True
                elif isinstance(current_dict[key], string_types):
                    if value.lower() != current_dict[key].lower():
                        self.result['diff']['before'][key] = current_dict[key]
                        self.result['diff']['after'][key] = value
                        changed = True
                else:
                    self.module.fail_json(msg="Unable to determine comparison for key %s" % key)
            else:
                self.result['diff']['after'][key] = value
                changed = True
        return changed
