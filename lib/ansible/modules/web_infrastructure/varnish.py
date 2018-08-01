#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Abdoul Bah (@helldorado) <bahabdoul at gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: varnish
author: "Abdoul Bah (@helldorado)"
version_added: "2.7"
short_description: Control a running varnish instance
description:
   - Allows to ban and mark obsolete all objects where all the conditions match.
   - Set health status on the backends.
   - Clear the last panic and varnishstat counter(s).
   - Set parameter value.
   - Load and compile VCL file.
   - Switch to or Unload any loaded VCL.
   - This module also return facts that content bans, backends, panic, params, storages and loaded VCL.
options:
  state:
    description:
      - Desired state of the provided I(backend) if state is C(auto), C(healthy) or C(sick).
      - Desired state of the provided I(vcl) if state is C(load), C(discard) or C(use).
      - If C(state=load), C(filename) is required.
    choices: ['auto', 'healthy', 'sick', 'load', 'discard', 'use', 'clear']
    default: auto
  status:
    description:
      - Set the state of the specified C(vcl).
      - Used only if state is C(load) or C(auto).
    choices: ['auto', 'cold', 'warm']
    default: auto
  backend:
    description:
      - Name of the Varnish backend.
      - A backend pattern can be a backend name or a combination of a VCL name and backend name in C("VCL.backend") format.
      - If the VCL name is omitted, the active VCL is assumed.
      - Partial matching on the backend and VCL names is supported using shell-style wilcards, e.g. asterisk C(*).
      - This is mutually exclusive with C(vcl).
    aliases: ['backends']
  ban:
    description:
      - A list of expression to ban.
      - The format of STRING is C(<field> <operator> <arg> [&& <field> <oper> <arg> ...]).
      - C(<field>) can be any of the variables from VCL, C(req.url), C(req.http.*) or C(obj.http), C(obj.http.*)
      - C(<operator>) are C(==) for direct comparison, C(~) for a regular expression match, and C(>|<) for size comparisons.
      - Prepending an operator with C(!) negates the expression.
      - C(<arg>) could be a quoted string, a regexp, or an integer.
      - Integers can have C(KB), C(MB), C(GB) or C(TB) appended for size related fields.
      - Expressions can be chained using the and operator C(&&). For or semantics, use several bans.
      - See U(http://varnish-cache.org/docs/trunk/reference/vcl.html#vcl-7-ban) for more infos.
  address:
    description:
      - Connect to the management interface at the specified address.
      - This is mutually exclusive with C(ident).
  port:
    description:
      - Connect to the management interface at the specified port.
      - This is mutually exclusive with C(ident).
  ident:
    description:
      - Connect to the instance of varnishd with this name.
      - This is mutually exclusive with C(address) and C(port).
    aliases: ['instance', 'name']
  params:
    description:
      - A dict of params to set or edit.
    aliases: ['param']
  panic:
    description:
      - Clear the last panic, if any and related C(varnishstat) counter(s).
      - The C(state=clear) is assumed.
      - If C(panic=last) clear only the last panic, if any.
      - If C(panic=counter) clear the last panic, if any and related C(varnishstat) counter(s).
    choices: ['last', 'counter' ]
  secret:
    description:
      - Specify the authentication secret file.
      - This should be the same C(-S) argument as was given to varnishd.
  vcl:
    description:
      - Name of the VCL to manage
      - This is mutually exclusive with C(bakend).
      - If C(state=load), C(filename) is required.
  filename:
    description:
      - Name of the file to load as VCL. Can be relative from varnish config dir or abolute path.
      - Required if C(state=load).
  timeout:
    description:
      - Wait no longer than this many seconds for an operation to finish.
    default: 10
  facts:
    description:
      - Retrieve facts about available abjects from varnish instance.
      - Filters can be applied to get facts for only matching objects.
      - If C(facts=all) filters return all objects as facts.
    choices: ['all', 'ban', 'backend', 'panic', 'param', 'vcl', 'version']
  version:
    description:
      - Format of returned C(version) in facts.
    choices: ['full', 'strict']
    default: full
requirements:
  - varnish >= 3.x
  - varnishadm
notes:
  - List of Paremeters can be Edit/Set via C(params) can be found here => U(http://varnish-cache.org/docs/trunk/reference/varnishd.html#list-of-parameters).
  - "A backend expression can be a backend name or a combination of backend name, IP address and port in C(name(IP address:port)) format.
    All fields are optional. If no exact matching backend is found, partial matching will be attempted based on the provided name, IP address and port fields."
  - If you need to debug the output when error occured, use C(-vv).
  - More info about the C(varnish-cli) can be found here U(http://varnish-cache.org/docs/trunk/reference/varnish-cli.html).
'''

EXAMPLES = '''
- name: Gather all facts from varnish instance.
  varnish:
    facts: all

- name: Gather backends and vcl facts only.
  varnish:
    facts: vcl,backend

- name: Set backend spyweb1 as sick for maintenance.
  varnish:
    backend: spyweb1
    state: sick

- name: Set all backends begining with <sabrewulf> are healthy.
  varnish:
    backend: 'sabrewulf*'
    state: healthy

- name: Ensure all backends use probe to set health status.
  varnish:
    backend: '*'
    state: auto

- name: Set/Edit params.
  varnish:
    params:
      cli_timeout: '80.000'
      workspace_client: '128k'
      max_retries: '2'

- name: Load production VCL.
  varnish:
    vcl: production
    filename: production.vcl
    state: load

- name: Load VCL with status warm.
  varnish:
    vcl: stage
    filename: stage.vcl
    state: load
    status: warm

- name: Force stage VCL state to cold.
  varnish:
    vcl: stage
    status: cold

- name: Unload production VCL (when possible).
  varnish:
    vcl: production
    state: discard

- name: Switch to the stage VCL configuration immediately.
  varnish:
    vcl: stage
    state: use

- name: Mark obsolete all objects where the conditions match.
  varnish:
    ban:
      - 'req.url == \"/news\"'
      - 'req.url !~ \"\\.ogg$\"'
      - 'req.http.host ~ \"^(?i)(www\\.)helldorado.info$\" && obj.http.set-cookie ~ \"USERID=1663\"'

- name: Clear the last panic and related varnishstat counter(s).
  varnish:
    panic: counter
    state: clear
'''

RETURN = r'''
varnish:
  description: Dictionary of new facts representing discovered properties of the Varnish instance.
  returned: success
  type: complex
  contains:
    backends:
      description: Backends list.
      returned: success
      type: dict
      sample:
        "backends": {
              "spydbo1": {
                  "admin": "probe",
                  "probe": "Healthy",
                  "score": "5",
                  "threshold": "5"
              },
              "spyweb1": {
                  "admin": "probe",
                  "probe": "Healthy",
                  "score": "5",
                  "threshold": "5"
              },
              "spyweb2": {
                  "admin": "probe",
                  "probe": "Healthy",
                  "score": "5",
                  "threshold": "5"
              },
              "spyweb3": {
                  "admin": "probe",
                  "probe": "Sick",
                  "score": "5",
                  "threshold": "5"
              }
        }
    bans:
      description: Ban list.
      returned: success
      type: dict
      sample:
        "bans": {
              "0": {
                  "query": "req.url == /news",
                  "state": "-",
                  "time": "2018-07-30T14:36:28.837500"
              },
              "6": {
                  "query": 'req.http.host ~ ^(?i)(www\.)helldorado.info$ && obj.http.set-cookie ~ USERID=1663',
                  "state": "completed",
                  "time": "2018-07-29T20:34:55.317549"
              }
        }
    panic:
      description: Panic errors.
      returned: success
      type: dict
      sample:
        "panic": {
              "error": "Assert error in ved_stripgzip(), cache/cache_esi_deliver.c line 573: Condition((dbits) != 0) not true.",
              "panicked": true,
              "thread": "cache-worker",
              "time": "Fri, 20 Jul 2018 22:54:41 GMT"
        }
    params:
      description: Params list.
      returned: success
      type: dict
      sample:
        "params": {
              "accept_filter": {
                  "default": true,
                  "type": "bool",
                  "value": "off"
              },
              "acceptor_sleep_decay": {
                  "default": true,
                  "type": "none",
                  "value": "0.9"
              },
              "acceptor_sleep_incr": {
                  "default": true,
                  "type": "seconds",
                  "value": "0.000"
              }
        }
    storages:
      description: Storages list.
      returned: success
      type: dict
      sample:
        "storages": {
              "Transient": {
                  "size": "8G",
                  "type": "malloc"
              },
              "default": {
                  "size": "8G",
                  "type": "malloc"
              },
              "hell": {
                  "file": "/var/lib/varnish/spycache",
                  "size": "12G",
                  "type": "file"
              }
        }
    vcls:
      description: VCL list.
      returned: success
      type: dict
      sample:
        "vcls": {
              "boot": {
                  "active": false,
                  "cooldown": "0",
                  "state": "auto/warm"
              },
              "production": {
                  "active": true,
                  "cooldown": "0",
                  "state": "auto/warm"
              },
              "sabrewulf": {
                  "active": false,
                  "cooldown": "0",
                  "state": "auto/warm"
              },
              "stage": {
                  "active": false,
                  "cooldown": "2",
                  "state": "cold/warm"
              }
        }
    version:
      description: Varnish version.
      returned: success
      type: string
      sample:
         "version": "5.0.0 revision 99d036f"
'''

import datetime
import re
import traceback
import shlex
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class VarnishManager(object):

    def __init__(self, module):
        self.module = module
        self.timeout = module.params['timeout']
        self.state = module.params['state']
        self.ident = module.params['ident']
        self.address = module.params['address']
        self.port = module.params['port']
        self.backend = module.params['backend']
        self.facts = module.params['facts']
        self.panic = module.params['panic']
        self.secret = module.params['secret']
        self.version = module.params['version']

        self._varnishadm = [module.get_bin_path('varnishadm', True)]
        self._varnishd = module.get_bin_path('varnishd', True)
        self._strings = module.get_bin_path('strings', True)

        if self.timeout:
            self._varnishadm.extend(['-t', str(self.timeout)])
        if self.ident:
            self._varnishadm.extend(['-n', self.ident])
        if self.address:
            self._varnishadm.extend(['-T', ':'.join([self.address, self.port])])
        if self.secret:
            self._varnishadm.extend(['-S', self.secret])

        self.debug = self.module._verbosity >= 2

    def run(self, args, **kwargs):
        try:
            rc, out, err = self.module.run_command(args, check_rc=False, **kwargs)
            if rc != 0 and 'Child has not panicked' not in out:
                if self.debug:
                    self.module.fail_json(msg='error running (%s) command (rc=%d): %s' %
                                          (' '.join(args), rc, out or err))
                else:
                    self.module.fail_json(msg='%s' % (out.rstrip() or err.rstrip()))
        except Exception as e:
            if self.debug:
                self.module.fail_json(msg='error running (%s) command: %s' % (' '.join(args),
                                                                              to_native(e)))
            else:
                self.module.fail_json(msg='%s' % (out.rstrip() or err.rstrip()))
        return out or err

    def get_version(self):
        '''
        Return server version from varnishd -V
        '''
        cmd = ['varnishd', '-V']
        if self.version == 'full':
            version = re.search(r'\(varnish-([^\)]+)\)', self.run(cmd)).group(1)
        else:
            version = re.search(r'\(varnish-([^\)]+)\)', self.run(cmd)).group(1).split(' ')[0]
        return version

    def get_backends(self, backend=None):
        if backend:
            cmd = self._varnishadm + ['backend.list', backend]
        else:
            cmd = self._varnishadm + ['backend.list']
        out = self.run(cmd)
        backends = {}
        shortnames = True

        for line in out.split('\n')[1:]:
            # Sample output lines:
            '''
            Backend name                                         Admin      Probe
            0bc2086b-0608-46d5-92a8-11a554be0b62.default_backend probe      Sick 0/5
            0bc2086b-0608-46d5-92a8-11a554be0b62.spyweb2         probe      Healthy 5/5
            0bc2086b-0608-46d5-92a8-11a554be0b62.spyweb1         probe      Healthy 5/5
            '''

            parts = line.split()
            if len(parts) > 1:
                name = ''.join(parts[0])
                if shortnames:
                    name = name.split(".")[-1]
                admin = ''.join(parts[1])
                probe = ''.join(parts[2])
                current = ''.join(parts[3])
                if current == '(no':
                    score = 'no probe'
                    threshold = 'no probe'
                else:
                    score = ''.join(parts[3].split("/")[-1])
                    threshold = ''.join(parts[3].split("/")[-1])

                backends[name] = {
                    'admin': admin,
                    'probe': probe,
                    'score': score,
                    'threshold': threshold
                }
        return backends

    def get_bans(self):
        cmd = self._varnishadm + ['ban.list']
        out = self.run(cmd)
        bans = {}

        for line in out.split('\n')[1:]:
            # Present bans:
            '''
            1532018504.776114    24 -  req.http.host ~ assets.helldorado.info
            1532018504.753444     0 -  req.http.host ~ assets.* && req.url ~ uajax/favorites
            1532018492.831544     8 C
            1532018492.823615     0 C
            '''

            parts = line.split()
            if len(parts) > 1:
                time = float(''.join(parts[0]))
                time = datetime.datetime.fromtimestamp(time)
                object = ''.join(parts[1])
                state = ''.join(parts[2])
                if state == 'C':
                    state = 'completed'
                else:
                    state = state
                query = ' '.join(parts[3:])

                bans[object] = {'time': time, 'state': state, 'query': query}
        return bans

    def get_panic(self):
        cmd = self._varnishadm + ['panic.show']
        out = self.run(cmd)
        panic = {}
        if 'Child has not panicked' in out:
            panic = {'panicked': False}
        else:
            # Sample output
            '''
            Last panic at: Fri, 20 Jul 2018 22:54:41 GMT
            Assert error in ved_stripgzip(), cache/cache_esi_deliver.c line 573:
                Condition((dbits) != 0) not true.
            thread = (cache-worker)
            version = varnish-4.1.6 revision 5ba741b
            ident = Linux,3.2.0-4-amd64,x86_64,-junix,-smalloc,-smalloc,-hcritbit,epoll
            now = 22543391.397030 (mono), 1532127280.205034 (real)
            '''

            line = out.split('\n')
            time = line[0].split('Last panic at:')[1].strip()
            error = (line[1].translate(None, '"') + ' ' + line[2])
            thread = line[3].split('=')[1].translate(None, '()[]"')

            panic = {'panicked': True, 'time': time, 'error': error, 'thread': thread}

        return panic

    def get_params(self, param=None):
        cmd = self._varnishadm + ['param.show']
        out = self.run(cmd)
        params = {}
        for line in out.split('\n'):
            # Sample output lines:
            '''
            Param                     value             type        is_default?
            accept_filter              off              [bool]      (default)
            acceptor_sleep_decay       0.9                          (default)
            acceptor_sleep_incr        0.000            [seconds]   (default)
            acceptor_sleep_max         0.050            [seconds]   (default)
            auto_restart               on               [bool]      (default)
            '''

            line = line.translate(None, '()[]"')
            parts = re.search(r'^(\w+)\s+(.*)$', line)
            if parts is not None:
                if param and param != parts.group(1):
                    continue
                name = parts.group(1)
                val = parts.group(2).split()
                value = val[0]
                default = True if 'default' in val else False
                type = val[1] if default and len(val) == 3 else 'none'
            params[name] = {'value': value, 'type': type, 'default': default}
            if param:
                # Get out of the loop when param found
                break
        return params

    def get_storages(self):
        cmd = ['pidof', '-s', 'varnishd']
        varnishd_pid = self.run(cmd).strip()
        proc = '/proc/{0}/cmdline'.format(varnishd_pid)
        out = self.run([self._strings, '-1', proc])

        storage = self.run(self._varnishadm + ['storage.list'])
        storages = {}
        shortnames = True
        for row in storage.split('\n')[1:]:
            # Sample output lines:
            '''
            Storage devices:
            storage.Transient = malloc
            storage.default = file
            storage.helldorado = file
            storage.sabrewulf = malloc
            '''

            if ' = ' in row:
                key, value = row.split(' = ')
                name = key
                type = value
                if shortnames:
                    name = name.split(".")[-1]
            for sto in shlex.split(out):
                if (type == 'file' and name in sto) and ('=' in sto and ',' in sto):
                    file = sto.split(',')[1]
                    size = sto.split(',')[-1]
                    storages[name] = {'type': type, 'file': file, 'size': size}
                elif type == 'malloc' and (',' in sto and 'file' not in sto):
                    size = sto.split(',')[-1]
                    storages[name] = {'type': type, 'size': size}
        return storages

    def get_vcls(self):
        cmd = self._varnishadm + ['vcl.list']
        out = self.run(cmd)
        vcls = {}
        shortnames = True
        name = None
        active = None
        cooldown = None
        state = None

        for line in out.split('\n'):
            # Sample output lines:
            '''
            available  auto/cold          0 boot
            available  auto/cold          0 9ccb8a1f-0e87-4e33-985a-1b4a752b9ad3
            active     auto/warm        126 d19a8882-d5c6-4320-af0a-67c09804780b
            '''

            parts = line.split()
            if len(parts) > 1:
                name = ''.join(parts[-1])
                if shortnames:
                    name = name.split(".")[-1]
                active = ''.join(parts[0])
                if active == 'active':
                    active = True
                else:
                    active = False
                state = ''.join(parts[1])
                cooldown = ''.join(parts[2])

                vcls[name] = {'active': active, 'cooldown': cooldown, 'state': state}
        return vcls

    def set_param(self, param, value):
        cmd = self._varnishadm + ['param.set', param, value]
        self.run(cmd)
        return True

    def panic_clear(self, counter=False):
        param = '-z' if counter else None
        cmd = self._varnishadm + ['panic.clear', param]
        self.run(cmd)
        return True

    def set_backend(self, name, state):
        cmd = self._varnishadm + ['backend.set_health', name, state]
        self.run(cmd)
        return True

    def ban(self, expr):
        cmd = self._varnishadm + ['ban', expr]
        self.run(cmd)
        return True

    def set_vcl(self, configname, action, filename=None, state=None):
        obj = 'vcl.' + action
        cmd = self._varnishadm + [obj, configname]
        if action in ['load', 'state']:
            if filename:
                cmd.extend([filename, state])
            else:
                cmd.extend([state])
        self.run(cmd)
        return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ident=dict(required=False, type='str', aliases=['instance', 'name']),
            address=dict(required=False, type='str'),
            port=dict(required=False, type='int'),
            backend=dict(required=False, type='str', aliases=['backends']),
            status=dict(required=False, choices=['auto', 'cold', 'warm'], default='auto'),
            timeout=dict(required=False, type='int', default=10),
            secret=dict(required=False, type='str'),
            vcl=dict(required=False, type='str'),
            params=dict(required=False, type='dict', default={}, aliases=['param']),
            panic=dict(required=False, choices=['last', 'counter']),
            ban=dict(required=False, type='list'),
            version=dict(required=False, choices=['full', 'strict'], default='full'),
            filename=dict(required=False, type='str'),
            state=dict(required=False, default='auto',
                       choices=['auto', 'healthy', 'sick', 'load', 'discard', 'use', 'clear']),
            facts=dict(required=False, type='list',
                       choices=['all', 'ban', 'backend', 'panic', 'param', 'vcl', 'version'])
        ),
        mutually_exclusive=[('backend', 'vcl'), ('ident', 'address'), ('ident', 'port')],
        required_one_of=[('backend', 'vcl', 'params', 'panic', 'facts')],
        required_together=[['address', 'port']],
        required_if=[('state', 'healthy', ['backend']), ('state', 'sick', ['backend']),
                     ('state', 'use', ['vcl']), ('state', 'discard', ['vcl']),
                     ('state', 'load', ['vcl']), ('state', 'load', ['filename']),
                     ('status', 'cold', ['vcl']), ('status', 'warm', ['vcl']),
                     ('state', 'clear', ['panic'])],
        supports_check_mode=True
    )

    changed = False
    msg = None
    varnish_facts = {}
    result = {}
    state = module.params['state']
    status = module.params['status']
    backend = module.params['backend']
    filename = module.params['filename']
    configname = module.params['vcl']

    varnish = VarnishManager(module)

    # manage backends
    if module.params['backend']:
        h = 'probe' if state == 'auto' else state
        b = varnish.get_backends(backend)

        if module.check_mode:
            module.exit_json(changed=True)

        if b[backend]['admin'] == h:
            msg = 'Backend <{0}> is already {1}'.format(backend, state)
        else:
            varnish.set_backend(backend, state)
            changed = True

    # manage vcl
    if module.params['vcl']:
        action = state
        if action == 'load':
            state = status
        elif action == 'auto':
            action = 'state'
            state = status
            filename = None
        else:
            state = None

        vcl = varnish.get_vcls()

        if module.check_mode:
            module.exit_json(changed=True)

        if action == 'load' and configname in vcl.keys():
            msg = 'Already a VCL named <{0}>'.format(configname)
        elif action == 'use' and vcl[configname]['active']:
            msg = 'VCL <{0}> is already active.'.format(configname)
        elif action == 'discard' and configname not in vcl.keys():
            msg = 'No VCL named <{0}> known'.format(configname)
        elif action == 'state' and (state == vcl[configname]['state'].split('/')[0]
                                    or state == vcl[configname]['state'].split('/')[1]):
            msg = 'VCL {0} is already loaded with state <{1}>.'.format(
                configname, vcl[configname]['state'])
        else:
            varnish.set_vcl(configname, action, filename, state)
            changed = True

    # manage panic
    if module.params['panic']:
        panic = varnish.get_panic()

        if module.check_mode:
            module.exit_json(changed=True)

        if not panic['panicked'] and module.params['panic'] != 'counter':
            msg = 'No panic to clear.'
        elif module.params['panic'] == 'counter':
            varnish.panic_clear(counter=True)
            changed = True
        else:
            varnish.panic_clear()
            changed = True

    # manage bans
    if module.params['ban']:
        if module.check_mode:
            module.exit_json(changed=True)

        for ban in module.params['ban']:
            varnish.ban(expr=ban)
            changed = True

    # set params
    if module.params['params']:
        params = varnish.get_params()

        if module.check_mode:
            module.exit_json(changed=True)

        for param in module.params['params'].keys():
            if (param not in params.keys() or
                    params[param]['value'] != module.params['params'][param]):
                varnish.set_param(param, module.params['params'][param])
                changed = True

    # manage facts
    if module.params['facts']:
        if module.params['facts'][0] == 'all':
            varnish_facts['varnish'] = {
                'version': varnish.get_version(),
                'backends': varnish.get_backends(),
                'storages': varnish.get_storages(),
                'vcls': varnish.get_vcls(),
                'bans': varnish.get_bans(),
                'params': varnish.get_params(),
                'panic': varnish.get_panic()
            }
        else:
            varnish_facts['varnish'] = {}
            for fact in module.params['facts']:
                if fact == 'version':
                    varnish_facts['varnish']['version'] = varnish.get_version()
                elif fact == 'backend':
                    varnish_facts['varnish']['backends'] = varnish.get_backends()
                elif fact == 'storage':
                    varnish_facts['varnish']['storages'] = varnish.get_storages()
                elif fact == 'vcl':
                    varnish_facts['varnish']['vcls'] = varnish.get_vcls()
                elif fact == 'ban':
                    varnish_facts['varnish']['bans'] = varnish.get_bans()
                elif fact == 'param':
                    varnish_facts['varnish']['params'] = varnish.get_params()
                elif fact == 'panic':
                    varnish_facts['varnish']['panic'] = varnish.get_panic()

        result = dict(ansible_facts=varnish_facts)

    if msg:
        module.exit_json(changed=changed, msg=msg, **result)
    else:
        module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
