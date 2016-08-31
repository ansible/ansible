#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
#
# This file is part of Ansible
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
#

import re

try:
    import ovs.poller
    import ops.dc
    from ops.settings import settings
    from opslib import restparser
    HAS_OPS = True
except ImportError:
    HAS_OPS = False

from ansible.module_utils.basic import json, json_dict_bytes_to_unicode
from ansible.module_utils.network import NetworkModule, ModuleStub, NetworkError
from ansible.module_utils.network import add_argument, register_transport, to_list
from ansible.module_utils.shell import CliBase
from ansible.module_utils.urls import fetch_url, url_argument_spec

# temporary fix until modules are update.  to be removed before 2.2 final
from ansible.module_utils.network import get_module

add_argument('use_ssl', dict(default=True, type='bool'))
add_argument('validate_certs', dict(default=True, type='bool'))

def get_opsidl():
    extschema = restparser.parseSchema(settings.get('ext_schema'))
    ovsschema = settings.get('ovs_schema')
    ovsremote = settings.get('ovs_remote')
    opsidl = ops.dc.register(extschema, ovsschema, ovsremote)

    init_seqno = opsidl.change_seqno
    while True:
        opsidl.run()
        if init_seqno != opsidl.change_seqno:
            break
        poller = ovs.poller.Poller()
        opsidl.wait(poller)
        poller.block()

    return (extschema, opsidl)

class Response(object):

    def __init__(self, resp, hdrs):
        self.body = None
        self.headers = hdrs

        if resp:
            self.body = resp.read()

    @property
    def json(self):
        if not self.body:
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

class Rest(object):
    def __init__(self):
        self.url = None
        self.url_args = ModuleStub(url_argument_spec(), self._error)
        self.headers = dict({'Content-Type': 'application/json', 'Accept': 'application/json'})
        self.default_output = 'json'
        self._connected = False

    def _error(self, msg):
        raise NetworkError(msg, url=self.url)

    def connect(self, params, **kwargs):
        host = params['host']
        port = params['port']

        # sets the module_utils/urls.py req parameters
        self.url_args.params['url_username'] = params['username']
        self.url_args.params['url_password'] = params['password']
        self.url_args.params['validate_certs'] = params['validate_certs']

        if params['use_ssl']:
            proto = 'https'
            if not port:
                port = 443
        else:
            proto = 'http'
            if not port:
                port = 80

        baseurl = '%s://%s:%s' % (proto, host, port)
        headers = dict({'Content-Type': 'application/x-www-form-urlencoded'})
        # Get a cookie and save it the rest of the operations.
        url = '%s/%s' % (baseurl, 'login')
        data = 'username=%s&password=%s' % (params['username'], params['password'])
        resp, hdrs = fetch_url(self.url_args, url, data=data, headers=headers, method='POST')

        # Update the base url for the rest of the operations.
        self.url = '%s/rest/v1' % (baseurl)
        self.headers['Cookie'] = hdrs['set-cookie']

    def disconnect(self, **kwargs):
        self.url = None
        self._connected = False

    def authorize(self, params, **kwargs):
        raise NotImplementedError

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.url, path)

    def request(self, method, path, data=None, headers=None):
        url = self._url_builder(path)
        data = self._jsonify(data)

        if headers is None:
            headers = dict()
        headers.update(self.headers)

        resp, hdrs = fetch_url(self.url_args, url, data=data, headers=headers, method=method)

        return Response(resp, hdrs)

    def get(self, path, data=None, headers=None):
        return self.request('GET', path, data, headers)

    def put(self, path, data=None, headers=None):
        return self.request('PUT', path, data, headers)

    def post(self, path, data=None, headers=None):
        return self.request('POST', path, data, headers)

    def delete(self, path, data=None, headers=None):
        return self.request('DELETE', path, data, headers)

    def run_commands(self, commands):
        raise NotImplementedError

    def configure(self, commands):
        path = '/system/full-configuration'
        return self.put(path, data=commands)

    def load_config(self, commands, **kwargs):
        return self.configure(commands)

    def get_config(self, **kwargs):
        resp = self.get('/system/full-configuration')
        return resp.json

    def save_config(self):
        raise NotImplementedError

    def _jsonify(self, data):
        for encoding in ("utf-8", "latin-1"):
            try:
                return json.dumps(data, encoding=encoding)
            # Old systems using old simplejson module does not support encoding keyword.
            except TypeError:
                try:
                    new_data = json_dict_bytes_to_unicode(data, encoding=encoding)
                except UnicodeDecodeError:
                    continue
                return json.dumps(new_data)
            except UnicodeDecodeError:
                continue
        self._error(msg='Invalid unicode encoding encountered')

Rest = register_transport('rest')(Rest)


class Cli(CliBase):

    NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

    CLI_PROMPTS_RE = [
        re.compile(r"[\r\n]?[\w+\-\.:\/\[\]]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
        re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
    ]

    CLI_ERRORS_RE = [
        re.compile(r"% ?Error"),
        re.compile(r"% ?Bad secret"),
        re.compile(r"invalid input", re.I),
        re.compile(r"(?:incomplete|ambiguous) command", re.I),
        re.compile(r"connection timed out", re.I),
        re.compile(r"[^\r\n]+ not found", re.I),
        re.compile(r"'[^']' +returned error code: ?\d+"),
    ]

    ### implementation of netcli.Cli

    def run_commands(self, commands):
        return self.execute(to_list(commands))

    ### implementation of netcfg.Config

    def configure(self, commands, **kwargs):
        cmds = ['configure terminal']
        cmds.extend(to_list(commands))
        if cmds[-1] != 'end':
            cmds.append('end')
        responses = self.execute(cmds)
        return responses[1:]

    def get_config(self):
        return self.execute('show running-config')[0]

    def load_config(self, commands):
        return self.configure(commands)

    def save_config(self):
        self.execute(['copy running-config startup-config'])

Cli = register_transport('cli', default=True)(Cli)
